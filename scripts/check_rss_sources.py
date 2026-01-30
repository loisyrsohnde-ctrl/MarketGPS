#!/usr/bin/env python3
"""
MarketGPS - RSS Sources Health Check

Vérifie la disponibilité de toutes les sources RSS configurées.
Génère un rapport avec les sources fonctionnelles et en erreur.

Usage:
    python scripts/check_rss_sources.py [--fix]
    
Options:
    --fix    Désactiver automatiquement les sources en erreur
"""

import json
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple

try:
    import requests
    import feedparser
except ImportError:
    print("Dépendances manquantes. Installer avec: pip install requests feedparser")
    sys.exit(1)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
SOURCES_FILE = PROJECT_ROOT / "pipeline" / "news" / "sources_registry.json"

# Constants
TIMEOUT = 15
USER_AGENT = "MarketGPS/1.0 RSS Health Check"


def check_source(source: Dict) -> Tuple[str, bool, str]:
    """
    Check if a single RSS source is accessible.
    
    Returns:
        (source_name, is_ok, error_message)
    """
    name = source.get("name", "Unknown")
    rss_url = source.get("rss_url") or source.get("url")
    
    if not rss_url:
        return name, False, "No RSS URL"
    
    try:
        # Fetch the feed
        response = requests.get(
            rss_url,
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
            allow_redirects=True
        )
        
        if response.status_code != 200:
            return name, False, f"HTTP {response.status_code}"
        
        # Parse the feed
        feed = feedparser.parse(response.content)
        
        if feed.bozo and not feed.entries:
            error = str(feed.bozo_exception)[:50] if hasattr(feed, 'bozo_exception') else "Parse error"
            return name, False, error
        
        entries_count = len(feed.entries)
        if entries_count == 0:
            return name, False, "No entries"
        
        return name, True, f"OK ({entries_count} entries)"
        
    except requests.Timeout:
        return name, False, "Timeout"
    except requests.RequestException as e:
        return name, False, str(e)[:50]
    except Exception as e:
        return name, False, str(e)[:50]


def main():
    print("=" * 70)
    print("MarketGPS - RSS Sources Health Check")
    print("=" * 70)
    
    # Parse args
    fix_mode = "--fix" in sys.argv
    
    if not SOURCES_FILE.exists():
        print(f"❌ Sources file not found: {SOURCES_FILE}")
        sys.exit(1)
    
    # Load sources
    with open(SOURCES_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    sources = data.get("sources", [])
    enabled_sources = [s for s in sources if s.get("enabled", True)]
    
    print(f"\nTotal sources: {len(sources)}")
    print(f"Enabled sources: {len(enabled_sources)}")
    print(f"\nChecking {len(enabled_sources)} sources...\n")
    
    # Check sources in parallel
    results = []
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_source, s): s for s in enabled_sources}
        
        for i, future in enumerate(as_completed(futures), 1):
            source = futures[future]
            name, is_ok, message = future.result()
            results.append((name, is_ok, message, source.get("region", "?")))
            
            status = "✅" if is_ok else "❌"
            print(f"[{i:2d}/{len(enabled_sources)}] {status} {name}: {message}")
    
    elapsed = time.time() - start_time
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    ok_sources = [r for r in results if r[1]]
    error_sources = [r for r in results if not r[1]]
    
    print(f"\n✅ Working sources: {len(ok_sources)}/{len(results)}")
    print(f"❌ Failed sources: {len(error_sources)}/{len(results)}")
    print(f"⏱️  Total time: {elapsed:.1f}s")
    
    # Group by region
    print("\n--- By Region ---")
    by_region = {}
    for name, is_ok, msg, region in results:
        if region not in by_region:
            by_region[region] = {"ok": 0, "error": 0}
        if is_ok:
            by_region[region]["ok"] += 1
        else:
            by_region[region]["error"] += 1
    
    for region in sorted(by_region.keys()):
        stats = by_region[region]
        total = stats["ok"] + stats["error"]
        pct = (stats["ok"] / total * 100) if total > 0 else 0
        print(f"  {region}: {stats['ok']}/{total} ({pct:.0f}%)")
    
    # List errors
    if error_sources:
        print("\n--- Failed Sources ---")
        for name, _, msg, region in sorted(error_sources, key=lambda x: x[0]):
            print(f"  [{region}] {name}: {msg}")
    
    # Fix mode
    if fix_mode and error_sources:
        print("\n" + "=" * 70)
        print("FIX MODE - Disabling failed sources")
        print("=" * 70)
        
        error_names = {r[0] for r in error_sources}
        disabled_count = 0
        
        for source in data["sources"]:
            if source.get("name") in error_names:
                source["enabled"] = False
                disabled_count += 1
                print(f"  Disabled: {source['name']}")
        
        # Save
        with open(SOURCES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Disabled {disabled_count} sources and saved to {SOURCES_FILE}")
    
    # Exit code
    if len(error_sources) > len(results) * 0.5:  # >50% errors
        print("\n⚠️  More than 50% of sources are failing!")
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
