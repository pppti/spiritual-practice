import json
import os
import httpx
from datetime import datetime

GITHUB_REPO = os.getenv("GITHUB_REPO", "pppti/spiritual-practice")
GITHUB_PAT = os.getenv("GITHUB_PAT", "")
BACKUP_PATH = "backups/backup.json"


async def export_data(db) -> dict:
    from sqlalchemy import select
    from app.models.user import User
    from app.models.content import Content, Tag, ContentTag
    from app.models.practice import PracticeRecord, PracticeContent
    from app.models.lot import Lot, LotDraw
    from app.models.message import CultivationMessage
    from app.models.white_noise import WhiteNoiseTrack

    tables = {
        "user": User,
        "content": Content,
        "tag": Tag,
        "content_tag": ContentTag,
        "practice_record": PracticeRecord,
        "practice_content": PracticeContent,
        "lot_draw": LotDraw,
        "cultivation_message": CultivationMessage,
        "white_noise_track": WhiteNoiseTrack,
    }

    data = {}
    for name, model in tables:
        result = await db.execute(select(model))
        rows = result.scalars().all()
        data[name] = [{c.name: getattr(r, c.name) for c in model.__table__.columns} for r in rows]

    return data


async def import_data(db, data: dict):
    from app.models.user import User
    from app.models.content import Content, Tag, ContentTag
    from app.models.practice import PracticeRecord, PracticeContent
    from app.models.lot import Lot, LotDraw
    from app.models.message import CultivationMessage
    from app.models.white_noise import WhiteNoiseTrack

    model_map = {
        "user": User,
        "content": Content,
        "tag": Tag,
        "content_tag": ContentTag,
        "practice_record": PracticeRecord,
        "practice_content": PracticeContent,
        "lot_draw": LotDraw,
        "cultivation_message": CultivationMessage,
        "white_noise_track": WhiteNoiseTrack,
    }

    for name, model in model_map.items():
        rows = data.get(name, [])
        for row_data in rows:
            db.add(model(**row_data))

    await db.commit()


async def upload_to_github(data: dict) -> bool:
    """Upload backup JSON to GitHub repository."""
    if not GITHUB_PAT:
        return False

    content = json.dumps(data, ensure_ascii=False, indent=2)

    # Get current file SHA if it exists (needed for update)
    sha = None
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"https://api.github.com/repos/{GITHUB_REPO}/contents/{BACKUP_PATH}",
                headers={
                    "Authorization": f"Bearer {GITHUB_PAT}",
                    "Accept": "application/vnd.github+json",
                },
            )
            if r.status_code == 200:
                sha = r.json().get("sha")
    except Exception:
        pass

    # Upload/create file
    import base64
    body = {
        "message": f"Auto backup {datetime.utcnow().isoformat()}",
        "content": base64.b64encode(content.encode()).decode(),
    }
    if sha:
        body["sha"] = sha

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.put(
                f"https://api.github.com/repos/{GITHUB_REPO}/contents/{BACKUP_PATH}",
                headers={
                    "Authorization": f"Bearer {GITHUB_PAT}",
                    "Accept": "application/vnd.github+json",
                },
                json=body,
            )
            return r.status_code in (200, 201)
    except Exception:
        return False


async def download_from_github() -> dict | None:
    """Download backup JSON from GitHub repository."""
    if not GITHUB_PAT:
        return None

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"https://api.github.com/repos/{GITHUB_REPO}/contents/{BACKUP_PATH}",
                headers={
                    "Authorization": f"Bearer {GITHUB_PAT}",
                    "Accept": "application/vnd.github.raw+json",
                },
            )
            if r.status_code == 200:
                return r.json()
    except Exception:
        pass
    return None
