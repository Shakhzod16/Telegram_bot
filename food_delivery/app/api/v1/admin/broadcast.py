from __future__ import annotations

import asyncio
import re
import secrets
import time
from collections import OrderedDict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from aiogram.types import BufferedInputFile
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.bot_instance import bot
from app.core.logging import get_logger
from app.db.session import async_session, get_db
from app.models.user import User

router = APIRouter()
logger = get_logger(__name__)

BROADCAST_IMAGE_DIR = Path("app/webapp/static/images/broadcast")
BROADCAST_ALLOWED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
BROADCAST_MAX_IMAGE_BYTES = 10 * 1024 * 1024
BROADCAST_DELAY_SECONDS = 0.05
MAX_TRACKED_JOBS = 200

BROADCAST_JOBS: OrderedDict[str, dict[str, Any]] = OrderedDict()


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _trim_jobs() -> None:
    while len(BROADCAST_JOBS) > MAX_TRACKED_JOBS:
        BROADCAST_JOBS.popitem(last=False)


def _create_job(message: str, requested_by_user_id: int, image_url: str | None) -> dict[str, Any]:
    job_id = uuid4().hex
    job = {
        "job_id": job_id,
        "status": "queued",
        "message": message,
        "image_url": image_url,
        "requested_by_user_id": requested_by_user_id,
        "total": 0,
        "sent": 0,
        "failed": 0,
        "error": None,
        "created_at": _now_iso(),
        "started_at": None,
        "finished_at": None,
    }
    BROADCAST_JOBS[job_id] = job
    _trim_jobs()
    return job


def _get_job_or_404(job_id: str) -> dict[str, Any]:
    job = BROADCAST_JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Broadcast job topilmadi")
    return job


def _require_admin_or_superadmin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.is_admin or current_user.is_superadmin:
        return current_user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Faqat admin yoki superadmin ruxsat etilgan")


def _is_forbidden_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return (
        "forbidden" in text
        or "bot was blocked by the user" in text
        or "user is deactivated" in text
        or "chat not found" in text
    )


async def _save_broadcast_image(image: UploadFile | None) -> tuple[str | None, str | None]:
    if image is None or not image.filename:
        return None, None

    suffix = Path(image.filename).suffix.lower()
    if suffix not in BROADCAST_ALLOWED_IMAGE_SUFFIXES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Rasm formati qo'llab-quvvatlanmaydi (jpg, jpeg, png, webp)",
        )

    data = await image.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Rasm bo'sh")
    if len(data) > BROADCAST_MAX_IMAGE_BYTES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Rasm hajmi 10MB dan oshmasin")

    BROADCAST_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^a-zA-Z0-9_-]+", "-", Path(image.filename).stem).strip("-") or "broadcast"
    filename = f"{stem}-{int(time.time())}-{secrets.token_hex(4)}{suffix}"
    file_path = BROADCAST_IMAGE_DIR / filename
    file_path.write_bytes(data)

    return str(file_path), f"/static/images/broadcast/{filename}"


async def _load_active_telegram_ids() -> list[int]:
    async with async_session() as session:
        result = await session.execute(
            select(User.telegram_id)
            .where(User.is_active.is_(True))
            .order_by(User.id)
        )
        ids = [int(row[0]) for row in result.all() if row[0] is not None]
        await session.rollback()
        return ids


async def _run_broadcast_job(job_id: str, message: str, image_path: str | None) -> None:
    job = _get_job_or_404(job_id)
    job["status"] = "running"
    job["started_at"] = _now_iso()
    job["error"] = None

    try:
        telegram_ids = await _load_active_telegram_ids()
        job["total"] = len(telegram_ids)

        image_bytes: bytes | None = None
        image_name: str | None = None
        if image_path:
            path_obj = Path(image_path)
            image_bytes = path_obj.read_bytes()
            image_name = path_obj.name

        for telegram_id in telegram_ids:
            try:
                if image_bytes and image_name:
                    photo = BufferedInputFile(image_bytes, filename=image_name)
                    await bot.send_photo(chat_id=telegram_id, photo=photo, caption=message)
                else:
                    await bot.send_message(chat_id=telegram_id, text=message)
                job["sent"] += 1
            except Exception as exc:  # noqa: BLE001
                job["failed"] += 1
                if _is_forbidden_error(exc):
                    logger.info("broadcast_user_skipped chat_id=%s reason=%s", telegram_id, str(exc))
                else:
                    logger.warning("broadcast_send_failed chat_id=%s reason=%s", telegram_id, str(exc))
            await asyncio.sleep(BROADCAST_DELAY_SECONDS)

        job["status"] = "completed"
    except Exception as exc:  # noqa: BLE001
        job["status"] = "failed"
        job["error"] = str(exc)
        logger.exception("broadcast_job_failed job_id=%s", job_id)
    finally:
        job["finished_at"] = _now_iso()


@router.get("/recipients-count")
async def get_broadcast_recipients_count(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_require_admin_or_superadmin),
) -> dict[str, int]:
    result = await db.execute(
        select(func.count(User.id))
        .where(User.is_active.is_(True))
    )
    total = int(result.scalar_one() or 0)
    return {"total": total}


@router.post("")
async def start_broadcast(
    background_tasks: BackgroundTasks,
    message: str = Form(...),
    image: UploadFile | None = File(default=None),
    current_user: User = Depends(_require_admin_or_superadmin),
) -> dict[str, Any]:
    text = (message or "").strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="message majburiy")
    if len(text) > 4096:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="message 4096 belgidan oshmasin")
    if image is not None and len(text) > 1024:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Rasm bilan yuborishda message 1024 belgidan oshmasin",
        )

    image_path, image_url = await _save_broadcast_image(image)
    job = _create_job(message=text, requested_by_user_id=current_user.id, image_url=image_url)
    background_tasks.add_task(_run_broadcast_job, job["job_id"], text, image_path)

    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "sent": job["sent"],
        "failed": job["failed"],
        "total": job["total"],
    }


@router.get("/{job_id}")
async def get_broadcast_job_status(
    job_id: str,
    _: User = Depends(_require_admin_or_superadmin),
) -> dict[str, Any]:
    job = _get_job_or_404(job_id)
    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "message": job["message"],
        "image_url": job["image_url"],
        "total": job["total"],
        "sent": job["sent"],
        "failed": job["failed"],
        "error": job["error"],
        "created_at": job["created_at"],
        "started_at": job["started_at"],
        "finished_at": job["finished_at"],
    }
