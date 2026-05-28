import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import AUDIO_DIR
from app.database import get_db
from app.models.user import User
from app.models.white_noise import WhiteNoiseTrack
from app.schemas.white_noise import WhiteNoiseTrackResponse
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/white-noise", tags=["white_noise"])

ALLOWED_TYPES = {"audio/mpeg": ".mp3", "audio/wav": ".wav", "audio/ogg": ".ogg", "audio/mp4": ".m4a"}
MAX_SIZE = 30 * 1024 * 1024  # 30MB


@router.get("/tracks", response_model=list[WhiteNoiseTrackResponse])
async def list_tracks(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(WhiteNoiseTrack).order_by(WhiteNoiseTrack.category, WhiteNoiseTrack.name))
    tracks = result.scalars().all()
    return [
        WhiteNoiseTrackResponse(
            id=t.id,
            name=t.name,
            name_cn=t.name_cn,
            category=t.category,
            file_path=t.file_path,
            duration_s=t.duration_s,
            is_builtin=bool(t.is_builtin),
        )
        for t in tracks
    ]


@router.post("/upload", response_model=WhiteNoiseTrackResponse)
async def upload_track(
    file: UploadFile = File(...),
    name_cn: str = Form(""),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported audio format. Use MP3, WAV, or OGG.")

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large (max 30MB)")

    ext = ALLOWED_TYPES[file.content_type]
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(AUDIO_DIR, filename)

    os.makedirs(AUDIO_DIR, exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(content)

    track = WhiteNoiseTrack(
        name=file.filename.rsplit(".", 1)[0],
        name_cn=name_cn or file.filename.rsplit(".", 1)[0],
        category="custom",
        file_path=filename,
        duration_s=None,
        is_builtin=0,
    )
    db.add(track)
    await db.commit()
    await db.refresh(track)

    return WhiteNoiseTrackResponse(
        id=track.id, name=track.name, name_cn=track.name_cn,
        category=track.category, file_path=track.file_path,
        duration_s=track.duration_s, is_builtin=False,
    )


@router.delete("/tracks/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_track(
    track_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    r = await db.execute(select(WhiteNoiseTrack).where(WhiteNoiseTrack.id == track_id))
    track = r.scalar_one_or_none()
    if not track:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Track not found")
    if track.is_builtin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete built-in tracks")

    filepath = os.path.join(AUDIO_DIR, track.file_path)
    if os.path.isfile(filepath):
        os.remove(filepath)

    await db.delete(track)
    await db.commit()


@router.get("/stream/{track_id}")
async def stream_track(
    track_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(WhiteNoiseTrack).where(WhiteNoiseTrack.id == track_id))
    track = result.scalar_one_or_none()
    if not track:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Track not found")

    file_path = os.path.join(AUDIO_DIR, track.file_path)
    if not os.path.isfile(file_path):
        # Try alternate extensions
        base = os.path.splitext(os.path.join(AUDIO_DIR, track.file_path))[0]
        for alt_ext in ['.wav', '.mp3', '.m4a', '.ogg']:
            alt_path = base + alt_ext
            if os.path.isfile(alt_path):
                file_path = alt_path
                break
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio file not found")

    file_size = os.path.getsize(file_path)

    async def file_iterator():
        chunk_size = 64 * 1024
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                yield chunk

    ext = os.path.splitext(file_path)[1].lower()
    mime_map = {'.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.ogg': 'audio/ogg', '.m4a': 'audio/mp4'}
    return StreamingResponse(
        file_iterator(),
        media_type=mime_map.get(ext, 'audio/mpeg'),
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Cache-Control": "public, max-age=86400",
        },
    )
