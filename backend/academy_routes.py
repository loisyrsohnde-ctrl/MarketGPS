"""
MarketGPS Academy Routes
- Video streaming from local filesystem (with range request support)
- Admin endpoints for scanning/seeding video content into Supabase
"""

import os
import logging
import mimetypes
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Header, Query, Request
from fastapi.responses import StreamingResponse, JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/academy", tags=["academy"])

# ═══════════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════════

# Videos base path (mounted via Docker volume)
VIDEOS_BASE_PATH = os.environ.get("ACADEMY_VIDEOS_PATH", "/app/data/academy-videos")

# Admin key (same as other admin endpoints)
ADMIN_KEY = os.environ.get("ADMIN_KEY", "")

MIME_TYPES = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".vtt": "text/vtt",
    ".srt": "text/plain",
    ".m4v": "video/mp4",
}


def _require_admin(x_admin_key: Optional[str] = Header(None)) -> str:
    """Validate admin key."""
    import secrets
    expected = os.environ.get("ADMIN_KEY", "")
    if not expected:
        raise HTTPException(status_code=500, detail="ADMIN_KEY not configured")
    if not x_admin_key or not secrets.compare_digest(x_admin_key, expected):
        raise HTTPException(status_code=403, detail="Invalid admin key")
    return x_admin_key


# ═══════════════════════════════════════════════════════════════════════════════
# VIDEO STREAMING
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/videos/{file_path:path}")
async def stream_video(file_path: str, request: Request):
    """
    Stream a video file with range request support for seeking.
    Videos are served from the mounted academy-videos directory.

    Example: GET /api/academy/videos/Part 1/Module 01/Lesson 01/01. Welcome.mp4
    """
    import urllib.parse

    # Decode URL-encoded path
    decoded_path = urllib.parse.unquote(file_path)

    # Resolve the full filesystem path
    base = Path(VIDEOS_BASE_PATH).resolve()
    full_path = (base / decoded_path).resolve()

    # Security: prevent path traversal
    if not str(full_path).startswith(str(base)):
        raise HTTPException(status_code=403, detail="Forbidden")

    # Check file exists
    if not full_path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {decoded_path}")

    # Determine content type
    ext = full_path.suffix.lower()
    content_type = MIME_TYPES.get(ext, "application/octet-stream")
    file_size = full_path.stat().st_size

    # Parse Range header
    range_header = request.headers.get("range")

    if range_header:
        # Handle range request (for video seeking)
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
                    read_size = min(remaining, 1024 * 1024)  # 1MB chunks
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
                "Cache-Control": "public, max-age=2592000",  # 30 days
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
                "Access-Control-Expose-Headers": "Content-Length, Content-Range, Accept-Ranges",
            },
        )

    # Full file streaming (no range)
    def iter_file():
        with open(full_path, "rb") as f:
            while True:
                data = f.read(1024 * 1024)  # 1MB chunks
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


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN: SCAN VIDEO FILES
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/admin/scan-videos")
async def scan_video_files(x_admin_key: Optional[str] = Header(None)):
    """
    Scan the academy-videos directory and return all video files found.
    Used to understand the directory structure before seeding.
    """
    _require_admin(x_admin_key)

    base = Path(VIDEOS_BASE_PATH)
    if not base.exists():
        return JSONResponse({
            "status": "error",
            "message": f"Videos directory not found: {VIDEOS_BASE_PATH}",
            "files": []
        })

    video_files = []
    for ext in ["*.mp4", "*.webm", "*.m4v"]:
        for f in base.rglob(ext):
            rel_path = f.relative_to(base)
            video_files.append({
                "path": str(rel_path),
                "size_mb": round(f.stat().st_size / (1024 * 1024), 1),
                "url": f"/api/academy/videos/{str(rel_path)}",
            })

    # Also find VTT subtitle files
    vtt_files = []
    for f in base.rglob("*.vtt"):
        rel_path = f.relative_to(base)
        vtt_files.append({
            "path": str(rel_path),
            "url": f"/api/academy/videos/{str(rel_path)}",
        })

    # Sort by path
    video_files.sort(key=lambda x: x["path"])
    vtt_files.sort(key=lambda x: x["path"])

    return JSONResponse({
        "status": "ok",
        "videos_base_path": VIDEOS_BASE_PATH,
        "total_videos": len(video_files),
        "total_vtt": len(vtt_files),
        "videos": video_files,
        "subtitles": vtt_files,
    })


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN: SEED LESSON CONTENTS INTO SUPABASE
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/admin/seed-contents")
async def seed_lesson_contents(
    x_admin_key: Optional[str] = Header(None),
    dry_run: bool = Query(False, description="If true, only show what would be done"),
    api_base_url: str = Query(
        "https://api.marketgps.online",
        description="Base URL for video URLs in the database"
    ),
):
    """
    Scan the video directory and populate academy_lesson_contents in Supabase.

    This endpoint:
    1. Scans the video directory for .mp4 files
    2. Parses the directory structure (Part X / Module Y / Lesson Z)
    3. Matches videos to existing lessons in Supabase
    4. Creates academy_lesson_contents rows with video_url pointing to the streaming endpoint

    Call /api/academy/admin/scan-videos first to verify the directory structure.
    """
    _require_admin(x_admin_key)

    try:
        from supabase_admin import get_supabase_admin_client
        supabase = get_supabase_admin_client()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase client not available: {e}")

    base = Path(VIDEOS_BASE_PATH)
    if not base.exists():
        raise HTTPException(status_code=404, detail=f"Videos directory not found: {VIDEOS_BASE_PATH}")

    # Step 1: Get existing lessons from Supabase
    try:
        lessons_resp = supabase.table("academy_lessons").select(
            "id, module_id, lesson_number, title_fr, folder_name, order_index"
        ).execute()
        existing_lessons = lessons_resp.data or []

        modules_resp = supabase.table("academy_modules").select(
            "id, part_id, module_number, title_fr, order_index"
        ).execute()
        existing_modules = modules_resp.data or []

        parts_resp = supabase.table("academy_parts").select(
            "id, part_number, title_fr, order_index"
        ).execute()
        existing_parts = parts_resp.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase query error: {e}")

    # Step 2: Scan video directory
    video_files = sorted(base.rglob("*.mp4"))

    if not video_files:
        return JSONResponse({
            "status": "warning",
            "message": "No .mp4 files found in the videos directory",
            "videos_path": str(base),
        })

    # Step 3: Build lookup maps
    # part_id -> part data
    parts_by_number = {p["part_number"]: p for p in existing_parts}
    # Build module lookup: (part_id, module_number) -> module
    modules_lookup = {}
    for m in existing_modules:
        modules_lookup[(m["part_id"], m["module_number"])] = m
    # Build lesson lookup: (module_id, lesson_number) -> lesson
    lessons_lookup = {}
    for l in existing_lessons:
        lessons_lookup[(l["module_id"], l["lesson_number"])] = l

    # Step 4: Parse directory structure and map videos to lessons
    import re

    results = {
        "matched": [],
        "unmatched": [],
        "contents_created": 0,
        "errors": [],
    }

    # Group videos by lesson directory
    from collections import defaultdict
    lesson_videos = defaultdict(list)

    for video_path in video_files:
        rel_path = video_path.relative_to(base)
        parts_list = list(rel_path.parts)

        # Try to extract Part/Module/Lesson numbers from directory structure ONLY
        # (exclude the filename to avoid false matches like "PyTorch - Part 4" in video names)
        # Common patterns:
        # "Part 01-Module 01-Lesson 01_Name/video.mp4"
        # "Part 1 - Name/Module 01 - Name/Lesson 01 - Name/video.mp4"
        part_num = None
        module_num = None
        lesson_num = None

        # Only iterate directory segments, NOT the filename (last element)
        dir_parts = parts_list[:-1] if len(parts_list) > 1 else parts_list
        for part in dir_parts:
            part_match = re.search(r'Part\s*(\d+)', part, re.IGNORECASE)
            if part_match:
                part_num = int(part_match.group(1))

            module_match = re.search(r'Module\s*(\d+)', part, re.IGNORECASE)
            if module_match:
                module_num = int(module_match.group(1))

            lesson_match = re.search(r'Lesson\s*(\d+)', part, re.IGNORECASE)
            if lesson_match:
                lesson_num = int(lesson_match.group(1))

        if part_num and module_num and lesson_num:
            key = (part_num, module_num, lesson_num)
            lesson_videos[key].append({
                "path": str(rel_path),
                "name": video_path.stem,
                "full_path": str(video_path),
            })
        else:
            results["unmatched"].append({
                "path": str(rel_path),
                "reason": f"Could not parse Part/Module/Lesson from path (found: P={part_num}, M={module_num}, L={lesson_num})"
            })

    # Step 5: Create lesson_contents entries
    for (part_num, module_num, lesson_num), videos in sorted(lesson_videos.items()):
        # Find the lesson in Supabase
        part = parts_by_number.get(part_num)
        if not part:
            results["unmatched"].extend([
                {"path": v["path"], "reason": f"Part {part_num} not found in Supabase"}
                for v in videos
            ])
            continue

        module = modules_lookup.get((part["id"], module_num))
        if not module:
            results["unmatched"].extend([
                {"path": v["path"], "reason": f"Module {module_num} in Part {part_num} not found in Supabase"}
                for v in videos
            ])
            continue

        lesson = lessons_lookup.get((module["id"], lesson_num))
        if not lesson:
            results["unmatched"].extend([
                {"path": v["path"], "reason": f"Lesson {lesson_num} in Module {module_num}/Part {part_num} not found in Supabase"}
                for v in videos
            ])
            continue

        # Create content entries for each video in this lesson
        for order_idx, video in enumerate(sorted(videos, key=lambda v: v["name"])):
            import urllib.parse
            encoded_path = urllib.parse.quote(video["path"])
            video_url = f"{api_base_url}/api/academy/videos/{encoded_path}"

            # Check for matching VTT subtitle file
            vtt_path = Path(video["full_path"]).with_suffix(".en.vtt")
            vtt_url = None
            if vtt_path.exists():
                vtt_rel = vtt_path.relative_to(base)
                vtt_url = f"{api_base_url}/api/academy/videos/{urllib.parse.quote(str(vtt_rel))}"

            # Also check for .vtt (without language prefix)
            if not vtt_url:
                vtt_path2 = Path(video["full_path"]).with_suffix(".vtt")
                if vtt_path2.exists():
                    vtt_rel = vtt_path2.relative_to(base)
                    vtt_url = f"{api_base_url}/api/academy/videos/{urllib.parse.quote(str(vtt_rel))}"

            content_data = {
                "lesson_id": lesson["id"],
                "title_fr": video["name"].lstrip("0123456789. ") or video["name"],
                "content_type": "video",
                "video_url": video_url,
                "vtt_url": vtt_url,
                "order_index": order_idx + 1,
            }

            results["matched"].append({
                "lesson": f"Part {part_num} > Module {module_num} > Lesson {lesson_num}",
                "lesson_id": lesson["id"],
                "video": video["path"],
                "video_url": video_url,
                "vtt_url": vtt_url,
            })

            if not dry_run:
                try:
                    resp = supabase.table("academy_lesson_contents").insert(content_data).execute()
                    if resp.data:
                        results["contents_created"] += 1
                    else:
                        results["errors"].append(f"Insert failed for {video['path']}")
                except Exception as e:
                    results["errors"].append(f"Insert error for {video['path']}: {str(e)}")

    return JSONResponse({
        "status": "ok",
        "dry_run": dry_run,
        "total_videos_found": len(video_files),
        "matched_to_lessons": len(results["matched"]),
        "unmatched": len(results["unmatched"]),
        "contents_created": results["contents_created"],
        "matched_details": results["matched"][:50],  # Limit output
        "unmatched_details": results["unmatched"][:50],
        "errors": results["errors"][:20],
        "existing_parts": len(existing_parts),
        "existing_modules": len(existing_modules),
        "existing_lessons": len(existing_lessons),
    })


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN: CLEAR LESSON CONTENTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.delete("/admin/clear-contents")
async def clear_lesson_contents(x_admin_key: Optional[str] = Header(None)):
    """
    Delete all academy_lesson_contents rows. Used before re-seeding.
    """
    _require_admin(x_admin_key)

    try:
        from supabase_admin import get_supabase_admin_client
        supabase = get_supabase_admin_client()

        # Delete all rows (Supabase requires a filter, use id > 0)
        resp = supabase.table("academy_lesson_contents").delete().gte("id", 0).execute()
        deleted = len(resp.data) if resp.data else 0

        return JSONResponse({
            "status": "ok",
            "deleted": deleted,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
