#!/usr/bin/env python3
"""
MarketGPS - Test Script for Phases 2-5
======================================

Run this script to verify all new endpoints are working correctly.

Usage:
    python scripts/test_all_phases.py [--local] [--prod]
    
Options:
    --local  Test against localhost:8501 (default)
    --prod   Test against api.marketgps.online
"""

import sys
import json
import urllib.request
import urllib.error
from typing import Tuple, Optional
from datetime import datetime

# =============================================================================
# Configuration
# =============================================================================

LOCAL_BASE = "http://localhost:8501"
PROD_BASE = "https://api.marketgps.online"

# Test cases: (name, method, endpoint, body, expected_status)
TEST_CASES = [
    # Health
    ("Health Check", "GET", "/health", None, 200),
    ("Extended Health", "GET", "/health/extended", None, 200),
    
    # Phase 2 - News Pipeline
    ("News List", "GET", "/api/news?limit=3", None, 200),
    ("News Status", "GET", "/api/news/status", None, 200),
    
    # Phase 4 - AI Concierge
    ("Concierge Prompts", "GET", "/api/concierge/prompts", None, 200),
    ("Concierge Analyze", "POST", "/api/concierge/analyze", {
        "prompt": "Analyse mon portefeuille",
        "coach_profile": "balanced",
        "portfolio_score": 72
    }, 200),
    ("Concierge Suggest", "POST", "/api/concierge/suggest", {
        "coach_profile": "balanced",
        "portfolio_score": 72
    }, 200),
    
    # Phase 5 - Notifications
    ("Notifications List", "GET", "/api/notifications", None, 200),
    ("Notifications Settings", "GET", "/api/notifications/settings", None, 200),
    ("Morning Brief", "GET", "/api/notifications/brief?portfolio_value=250000&portfolio_score=72", None, 200),
    ("Test Alert", "POST", "/api/notifications/test-alert?alert_type=score_drop", None, 200),
    
    # Existing endpoints (verification)
    ("Strategies Templates", "GET", "/api/strategies/templates", None, 200),
    ("Wealth Pulse Rates", "GET", "/api/wealth/pulse/rates", None, 200),
]


# =============================================================================
# Test Runner
# =============================================================================

def make_request(base_url: str, method: str, endpoint: str, body: Optional[dict]) -> Tuple[int, dict]:
    """Make HTTP request and return (status_code, response_json)."""
    url = f"{base_url}{endpoint}"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    data = None
    if body:
        data = json.dumps(body).encode('utf-8')
    
    try:
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(request, timeout=10) as response:
            status = response.status
            try:
                result = json.loads(response.read().decode('utf-8'))
            except:
                result = {}
            return status, result
    except urllib.error.HTTPError as e:
        try:
            result = json.loads(e.read().decode('utf-8'))
        except:
            result = {"error": str(e)}
        return e.code, result
    except urllib.error.URLError as e:
        return 0, {"error": f"Connection failed: {e.reason}"}
    except Exception as e:
        return 0, {"error": str(e)}


def run_tests(base_url: str):
    """Run all tests against the specified base URL."""
    print(f"\n{'='*70}")
    print(f"  MarketGPS - API Test Suite")
    print(f"  Target: {base_url}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    results = []
    passed = 0
    failed = 0
    skipped = 0
    
    for name, method, endpoint, body, expected_status in TEST_CASES:
        status, response = make_request(base_url, method, endpoint, body)
        
        if status == 0:
            # Connection error
            result = "SKIP"
            skipped += 1
            details = response.get("error", "Unknown error")
        elif status == expected_status:
            result = "PASS"
            passed += 1
            details = "OK"
        else:
            result = "FAIL"
            failed += 1
            details = f"Expected {expected_status}, got {status}"
        
        # Print result
        status_icon = {
            "PASS": "✅",
            "FAIL": "❌",
            "SKIP": "⚠️",
        }[result]
        
        print(f"{status_icon} [{result}] {name}")
        print(f"   {method} {endpoint}")
        if result != "PASS":
            print(f"   → {details}")
        print()
        
        results.append({
            "name": name,
            "endpoint": endpoint,
            "status": status,
            "result": result,
            "details": details,
        })
    
    # Summary
    print(f"{'='*70}")
    print(f"  SUMMARY")
    print(f"{'='*70}")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    print(f"  ⚠️  Skipped: {skipped}")
    print(f"  Total: {len(TEST_CASES)}")
    print(f"{'='*70}\n")
    
    # Return exit code
    return 0 if failed == 0 else 1


def main():
    # Parse arguments
    args = sys.argv[1:]
    
    if "--prod" in args:
        base_url = PROD_BASE
    elif "--local" in args or not args:
        base_url = LOCAL_BASE
    else:
        print(f"Usage: {sys.argv[0]} [--local] [--prod]")
        sys.exit(1)
    
    exit_code = run_tests(base_url)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
