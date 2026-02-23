#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
MarketGPS Academy - Seed Lesson Contents into Supabase
═══════════════════════════════════════════════════════════════════════════════

Ce script scanne le dossier academy-videos, parse la structure de dossiers
(Part X / Module Y / Lesson Z) et peuple la table academy_lesson_contents
dans Supabase avec les URLs de vidéos.

Usage depuis le VPS:
    cd /root/MarketGPS-src
    python scripts/seed_academy_contents.py

Usage local (avec .env):
    python scripts/seed_academy_contents.py --videos-dir ./data/academy-videos

Options:
    --videos-dir PATH   Dossier des vidéos (default: ./data/academy-videos)
    --api-base-url URL  Base URL pour les video_url (default: https://api.marketgps.online)
    --dry-run           Afficher ce qui serait fait sans modifier la DB
    --clear-first       Supprimer tous les lesson_contents avant de re-seeder
    --create-missing    Créer les modules et leçons manquants si nécessaire
"""

import os
import re
import sys
import argparse
import urllib.parse
from pathlib import Path
from collections import defaultdict

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def load_env():
    """Load environment variables from .env files."""
    try:
        from dotenv import load_dotenv
        # Try multiple env file locations
        for env_path in [".env.prod", ".env", "backend/.env"]:
            p = Path(env_path)
            if p.exists():
                load_dotenv(p)
                print(f"  Loaded env from: {p}")
                return
        print("  Warning: No .env file found, using existing environment")
    except ImportError:
        print("  Warning: python-dotenv not installed, using existing environment")


def get_supabase_client():
    """Create Supabase admin client."""
    from supabase import create_client
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        sys.exit(1)
    return create_client(url, key)


def scan_videos(videos_dir: Path):
    """Scan directory for video files and parse structure."""
    if not videos_dir.exists():
        print(f"ERROR: Videos directory not found: {videos_dir}")
        sys.exit(1)

    video_files = sorted(videos_dir.rglob("*.mp4"))
    print(f"\n  Found {len(video_files)} .mp4 files")

    # Parse each video's location in the hierarchy
    parsed = []
    unmatched = []

    for vf in video_files:
        rel = vf.relative_to(videos_dir)
        parts_list = list(rel.parts)

        part_num = None
        module_num = None
        lesson_num = None

        for segment in parts_list:
            pm = re.search(r'Part\s*(\d+)', segment, re.IGNORECASE)
            if pm:
                part_num = int(pm.group(1))

            mm = re.search(r'Module\s*(\d+)', segment, re.IGNORECASE)
            if mm:
                module_num = int(mm.group(1))

            lm = re.search(r'Lesson\s*(\d+)', segment, re.IGNORECASE)
            if lm:
                lesson_num = int(lm.group(1))

        if part_num and module_num and lesson_num:
            # Extract a clean title from the video filename
            title = vf.stem
            # Remove leading numbers and dots: "01. Welcome" -> "Welcome"
            title = re.sub(r'^\d+[\.\)\-\s]+', '', title).strip() or title

            parsed.append({
                "part_num": part_num,
                "module_num": module_num,
                "lesson_num": lesson_num,
                "rel_path": str(rel),
                "full_path": str(vf),
                "title": title,
                "filename": vf.name,
            })
        else:
            unmatched.append(str(rel))

    if unmatched:
        print(f"  Warning: {len(unmatched)} files could not be matched to Part/Module/Lesson:")
        for u in unmatched[:5]:
            print(f"    - {u}")
        if len(unmatched) > 5:
            print(f"    ... and {len(unmatched) - 5} more")

    return parsed, unmatched


def create_missing_structure(supabase, parsed_videos, existing_parts, existing_modules, existing_lessons):
    """Create any missing parts, modules, or lessons in Supabase."""
    parts_by_num = {p["part_number"]: p for p in existing_parts}
    modules_key = {}
    for m in existing_modules:
        modules_key[(m["part_id"], m["module_number"])] = m
    lessons_key = {}
    for l in existing_lessons:
        lessons_key[(l["module_id"], l["lesson_number"])] = l

    # Collect unique structures needed
    needed = set()
    for v in parsed_videos:
        needed.add((v["part_num"], v["module_num"], v["lesson_num"]))

    parts_created = 0
    modules_created = 0
    lessons_created = 0

    # Part titles (default French titles for each part)
    PART_TITLES = {
        1: "Fondamentaux du Trading Quantitatif",
        2: "IA et NLP pour la Finance",
        3: "Programmation Python",
        4: "Algèbre Linéaire",
        5: "Outils de Data Science",
        6: "Statistiques et Probabilités",
        7: "Machine Learning",
        8: "Réseaux de Neurones",
        9: "Vision par Ordinateur",
        10: "Traitement du Langage Naturel",
    }

    for part_num, module_num, lesson_num in sorted(needed):
        # Ensure part exists
        if part_num not in parts_by_num:
            title = PART_TITLES.get(part_num, f"Partie {part_num}")
            try:
                resp = supabase.table("academy_parts").insert({
                    "part_number": part_num,
                    "title_fr": title,
                    "order_index": part_num,
                }).execute()
                if resp.data:
                    parts_by_num[part_num] = resp.data[0]
                    parts_created += 1
                    print(f"    Created Part {part_num}: {title}")
            except Exception as e:
                print(f"    Error creating Part {part_num}: {e}")
                continue

        part = parts_by_num.get(part_num)
        if not part:
            continue

        # Ensure module exists
        mk = (part["id"], module_num)
        if mk not in modules_key:
            try:
                resp = supabase.table("academy_modules").insert({
                    "part_id": part["id"],
                    "module_number": module_num,
                    "title_fr": f"Module {module_num}",
                    "order_index": module_num,
                }).execute()
                if resp.data:
                    modules_key[mk] = resp.data[0]
                    modules_created += 1
                    print(f"    Created Module {module_num} in Part {part_num}")
            except Exception as e:
                print(f"    Error creating Module {module_num}: {e}")
                continue

        module = modules_key.get(mk)
        if not module:
            continue

        # Ensure lesson exists
        lk = (module["id"], lesson_num)
        if lk not in lessons_key:
            try:
                resp = supabase.table("academy_lessons").insert({
                    "module_id": module["id"],
                    "lesson_number": lesson_num,
                    "title_fr": f"Leçon {lesson_num}",
                    "order_index": lesson_num,
                }).execute()
                if resp.data:
                    lessons_key[lk] = resp.data[0]
                    lessons_created += 1
                    print(f"    Created Lesson {lesson_num} in Module {module_num}/Part {part_num}")
            except Exception as e:
                print(f"    Error creating Lesson {lesson_num}: {e}")
                continue

    print(f"\n  Structure: +{parts_created} parts, +{modules_created} modules, +{lessons_created} lessons")
    return parts_by_num, modules_key, lessons_key


def seed_contents(supabase, parsed_videos, parts_by_num, modules_key, lessons_key, api_base_url, videos_dir, dry_run=False):
    """Insert academy_lesson_contents rows for each video."""
    # Group videos by lesson
    lesson_videos = defaultdict(list)
    for v in parsed_videos:
        key = (v["part_num"], v["module_num"], v["lesson_num"])
        lesson_videos[key].append(v)

    total_created = 0
    total_skipped = 0

    for (part_num, module_num, lesson_num), videos in sorted(lesson_videos.items()):
        part = parts_by_num.get(part_num)
        if not part:
            continue

        module = modules_key.get((part["id"], module_num))
        if not module:
            continue

        lesson = lessons_key.get((module["id"], lesson_num))
        if not lesson:
            continue

        for order_idx, video in enumerate(sorted(videos, key=lambda v: v["filename"])):
            encoded_path = urllib.parse.quote(video["rel_path"])
            video_url = f"{api_base_url}/api/academy/videos/{encoded_path}"

            # Check for VTT subtitle
            vtt_url = None
            for vtt_suffix in [".en.vtt", ".fr.vtt", ".vtt"]:
                vtt_path = Path(video["full_path"]).with_suffix(vtt_suffix)
                if vtt_path.exists():
                    vtt_rel = vtt_path.relative_to(videos_dir)
                    vtt_url = f"{api_base_url}/api/academy/videos/{urllib.parse.quote(str(vtt_rel))}"
                    break

            if dry_run:
                print(f"  [DRY RUN] Part {part_num}/Mod {module_num}/Les {lesson_num}: {video['title']}")
                print(f"            -> {video_url}")
                total_created += 1
            else:
                try:
                    resp = supabase.table("academy_lesson_contents").insert({
                        "lesson_id": lesson["id"],
                        "title_fr": video["title"],
                        "content_type": "video",
                        "video_url": video_url,
                        "vtt_url": vtt_url,
                        "order_index": order_idx + 1,
                    }).execute()
                    if resp.data:
                        total_created += 1
                    else:
                        total_skipped += 1
                except Exception as e:
                    print(f"  Error inserting content for {video['rel_path']}: {e}")
                    total_skipped += 1

    return total_created, total_skipped


def main():
    parser = argparse.ArgumentParser(description="Seed QuantAI Academy lesson contents into Supabase")
    parser.add_argument("--videos-dir", default="./data/academy-videos", help="Path to academy videos directory")
    parser.add_argument("--api-base-url", default="https://api.marketgps.online", help="Base URL for video streaming API")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without modifying DB")
    parser.add_argument("--clear-first", action="store_true", help="Clear all lesson_contents before seeding")
    parser.add_argument("--create-missing", action="store_true", help="Create missing parts/modules/lessons")
    args = parser.parse_args()

    print("╔══════════════════════════════════════════════╗")
    print("║  QuantAI Academy - Seed Lesson Contents      ║")
    print("╚══════════════════════════════════════════════╝")
    print()

    # Load environment
    print("1. Loading environment...")
    load_env()

    # Connect to Supabase
    print("\n2. Connecting to Supabase...")
    supabase = get_supabase_client()
    print("  Connected!")

    # Scan videos
    videos_dir = Path(args.videos_dir).resolve()
    print(f"\n3. Scanning videos in: {videos_dir}")
    parsed_videos, unmatched = scan_videos(videos_dir)

    if not parsed_videos:
        print("\n  No matched videos found. Nothing to seed.")
        return

    # Fetch existing structure from Supabase
    print("\n4. Fetching existing academy structure from Supabase...")
    parts_resp = supabase.table("academy_parts").select("id, part_number, title_fr, order_index").execute()
    modules_resp = supabase.table("academy_modules").select("id, part_id, module_number, title_fr, order_index").execute()
    lessons_resp = supabase.table("academy_lessons").select("id, module_id, lesson_number, title_fr, order_index").execute()

    existing_parts = parts_resp.data or []
    existing_modules = modules_resp.data or []
    existing_lessons = lessons_resp.data or []

    print(f"  Existing: {len(existing_parts)} parts, {len(existing_modules)} modules, {len(existing_lessons)} lessons")

    # Build lookup maps
    parts_by_num = {p["part_number"]: p for p in existing_parts}
    modules_key = {}
    for m in existing_modules:
        modules_key[(m["part_id"], m["module_number"])] = m
    lessons_key = {}
    for l in existing_lessons:
        lessons_key[(l["module_id"], l["lesson_number"])] = l

    # Create missing structure if requested
    if args.create_missing:
        print("\n5. Creating missing structure...")
        parts_by_num, modules_key, lessons_key = create_missing_structure(
            supabase, parsed_videos, existing_parts, existing_modules, existing_lessons
        )
    else:
        print("\n5. Skipping structure creation (use --create-missing to enable)")

    # Clear existing contents if requested
    if args.clear_first and not args.dry_run:
        print("\n6. Clearing existing lesson_contents...")
        try:
            resp = supabase.table("academy_lesson_contents").delete().gte("id", 0).execute()
            deleted = len(resp.data) if resp.data else 0
            print(f"  Deleted {deleted} existing rows")
        except Exception as e:
            print(f"  Warning: Could not clear contents: {e}")
    else:
        print("\n6. Skipping clear (use --clear-first to enable)")

    # Seed lesson contents
    mode = "[DRY RUN] " if args.dry_run else ""
    print(f"\n7. {mode}Seeding lesson contents...")
    created, skipped = seed_contents(
        supabase, parsed_videos, parts_by_num, modules_key, lessons_key,
        args.api_base_url, videos_dir, args.dry_run
    )

    # Summary
    print("\n" + "═" * 50)
    print(f"  Videos found: {len(parsed_videos)}")
    print(f"  Unmatched: {len(unmatched)}")
    print(f"  Contents {'would be ' if args.dry_run else ''}created: {created}")
    if skipped:
        print(f"  Skipped/errors: {skipped}")
    print("═" * 50)

    if args.dry_run:
        print("\n  This was a DRY RUN. Run without --dry-run to apply changes.")
    else:
        print(f"\n  Done! {created} lesson contents seeded in Supabase.")
        print(f"  Videos will be served via: {args.api_base_url}/api/academy/videos/...")


if __name__ == "__main__":
    main()
