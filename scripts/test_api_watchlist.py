#!/usr/bin/env python3
"""
Test script pour vérifier si l'API backend est accessible et fonctionnelle
"""
import requests
import json
import sys
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
USER_ID = "test_user"
TICKER = "AAPL"

def test_api():
    print("=" * 70)
    print("TEST API WATCHLIST")
    print("=" * 70)
    
    # Test 1: GET /watchlist
    print("\n[1] GET /api/watchlist")
    try:
        resp = requests.get(f"{BASE_URL}/api/watchlist", params={"user_id": USER_ID})
        print(f"  Status: {resp.status_code}")
        if resp.ok:
            data = resp.json()
            print(f"  Items: {len(data)}")
        else:
            print(f"  Erreur: {resp.text}")
    except Exception as e:
        print(f"  ❌ Connexion impossible: {e}")
        return
    
    # Test 2: POST /watchlist (add)
    print(f"\n[2] POST /api/watchlist (ajouter {TICKER})")
    try:
        resp = requests.post(
            f"{BASE_URL}/api/watchlist",
            params={"user_id": USER_ID},
            json={
                "ticker": TICKER,
                "market_scope": "US_EU",
                "notes": "Test"
            }
        )
        print(f"  Status: {resp.status_code}")
        print(f"  Response: {resp.json()}")
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
    
    # Test 3: GET /watchlist/check (verify)
    print(f"\n[3] GET /api/watchlist/check/{TICKER}")
    try:
        resp = requests.get(
            f"{BASE_URL}/api/watchlist/check/{TICKER}",
            params={"user_id": USER_ID}
        )
        print(f"  Status: {resp.status_code}")
        print(f"  Response: {resp.json()}")
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
    
    # Test 4: DELETE /watchlist (remove)
    print(f"\n[4] DELETE /api/watchlist/{TICKER}")
    try:
        resp = requests.delete(
            f"{BASE_URL}/api/watchlist/{TICKER}",
            params={"user_id": USER_ID}
        )
        print(f"  Status: {resp.status_code}")
        print(f"  Response: {resp.json()}")
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
    
    print("\n" + "=" * 70)
    print("Test complété")
    print("=" * 70)

if __name__ == "__main__":
    test_api()
