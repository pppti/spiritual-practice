from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.services.backup_service import export_data, upload_to_github, download_from_github, import_data
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/backup", tags=["backup"])


@router.post("/create")
async def create_backup(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await export_data(db)
    success = await upload_to_github(data)
    if success:
        return {"status": "ok", "message": "Backup saved to GitHub"}
    return {"status": "warning", "message": "Backup created locally but GitHub upload failed (GITHUB_PAT not set?)"}


@router.post("/restore")
async def restore_backup(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await download_from_github()
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No backup found")

    await import_data(db, data)
    return {"status": "ok", "message": "Data restored from backup"}
