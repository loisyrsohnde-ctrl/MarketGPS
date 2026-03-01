"""
MarketGPS Article Video Routes
- Video upload (admin only, up to 500 MB)
- Video streaming with HTTP 206 range request support (public)
"""

import os
import re
import uuid
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Header, Request, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse

from admin_auth import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/article-videos", tags=["Article Videos"])

# Storage path (mounted via Docker volume)
VIDEOS_BASE_PATH = os.environ.get("ARTICLE_VIDEOS_PATH", "/app/data/article-videos")

# 500 MB max
MAX_VIDEO_SIZE = 500 * 1024 * 1024

MIME_TYPES = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".m4v": "video/mp4",
}

# Only allow safe filenames (UUID + extension)
SAFE_FILENAME_RE = re.compile(r'^[a-f0-9\-]+\.(mp4|webm|m4v)$')


# ═══════════════════════════════════════════════════════════════════════════════
# UPLOAD (admin only)
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/upload")
async def upload_article_video(
    file: UploadFile = File(...),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Upload a video file for an article.
    Accepts .mp4, .webm, .m4v up to 500 MB.
    Returns the video URL path for use in article creation.
    """
    require_admin(x_admin_key)

    # Validate file type
    ext = Path(file.filename).suffix.lower() if file.filename else ""
    if ext not in MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporté ({ext}). Formats acceptés : .mp4, .webm, .m4v"
        )

    # Generate unique filename
    video_id = str(uuid.uuid4())
    filename = f"{video_id}{ext}"

    # Ensure directory exists
    os.makedirs(VIDEOS_BASE_PATH, exist_ok=True)
    filepath = os.path.join(VIDEOS_BASE_PATH, filename)

    # Stream file to disk in chunks (handles large files without loading into memory)
    total_size = 0
    try:
        with open(filepath, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)  # 1 MB chunks
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > MAX_VIDEO_SIZE:
                    f.close()
                    os.remove(filepath)
                    raise HTTPException(
                        status_code=400,
                        detail=f"La vidéo dépasse la taille maximale ({MAX_VIDEO_SIZE // (1024 * 1024)} MB)"
                    )
                f.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        # Clean up on error
        if os.path.exists(filepath):
            os.remove(filepath)
        logger.error(f"Video upload failed: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'upload de la vidéo")

    video_url = f"/api/article-videos/{filename}"
    size_mb = round(total_size / (1024 * 1024), 1)

    logger.info(f"Video uploaded: {filename} ({size_mb} MB)")

    return {
        "success": True,
        "filename": filename,
        "video_url": video_url,
        "size_mb": size_mb,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# STREAMING (public, with range request support)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/{filename}")
async def stream_article_video(filename: str, request: Request):
    """
    Stream an article video with HTTP 206 range request support for seeking.
    """
    # Security: validate filename (only UUID + extension)
    if not SAFE_FILENAME_RE.match(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    full_path = Path(VIDEOS_BASE_PATH) / filename

    if not full_path.is_file():
        raise HTTPException(status_code=404, detail="Video not found")

    ext = full_path.suffix.lower()
    content_type = MIME_TYPES.get(ext, "application/octet-stream")
    file_size = full_path.stat().st_size

    # Parse Range header
    range_header = request.headers.get("range")

    if range_header:
        try:
            range_spec = range_header.replace("bytes=", "")
            parts = range_spec.split("-")
            start = int(parts[0])
            end = int(parts[1]) if parts[1] else file_size - 1
        except (ValueError, IndexError):
            raise HTTPException(status_code=416, detail="Invalid range")

        if start >= file_size or end >= file_size or start > end:
            raise HTTPException(
                status_code=416,
                detail="Range not satisfiable",
                headers={"Content-Range": f"bytes */{file_size}"}
            )

        chunk_size = end - start + 1

        def iter_range():
            with open(full_path, "rb") as f:
                f.seek(start)
                remaining = chunk_size
                while remaining > 0:
                    read_size = min(remaining, 1024 * 1024)  # 1 MB chunks
                    data = f.read(read_size)
                    if not data:
                        break
                    remaining -= len(data)
                    yield data

        return StreamingResponse(
            iter_range(),
            status_code=206,
            media_type=content_type,
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(chunk_size),
                "Cache-Control": "public, max-age=2592000",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
                "Access-Control-Expose-Headers": "Content-Length, Content-Range, Accept-Ranges",
            },
        )

    # Full file streaming (no range)
    def iter_file():
        with open(full_path, "rb") as f:
            while True:
                data = f.read(1024 * 1024)
                if not data:
                    break
                yield data

    return StreamingResponse(
        iter_file(),
        media_type=content_type,
        headers={
            "Content-Length": str(file_size),
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=2592000",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Expose-Headers": "Content-Length, Content-Range, Accept-Ranges",
        },
    )
