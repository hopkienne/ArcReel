"""Trích xuất thumbnail từ khung hình đầu của video."""

import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


async def extract_video_thumbnail(
    video_path: Path,
    thumbnail_path: Path,
) -> Path | None:
    """
    Dùng ffmpeg để trích khung hình đầu tiên của video làm thumbnail JPEG.

    Args:
        video_path: Đường dẫn tệp video
        thumbnail_path: Đường dẫn thumbnail đầu ra

    Returns:
        Đường dẫn thumbnail (thành công) hoặc None (thất bại)
    """
    if not video_path.exists():
        return None

    thumbnail_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-i",
            str(video_path),
            "-vframes",
            "1",
            "-q:v",
            "2",
            "-y",
            str(thumbnail_path),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()

        if proc.returncode != 0 or not thumbnail_path.exists():
            return None

        return thumbnail_path
    except Exception:
        logger.warning("Trích xuất thumbnail video thất bại: %s", video_path, exc_info=True)
        return None
