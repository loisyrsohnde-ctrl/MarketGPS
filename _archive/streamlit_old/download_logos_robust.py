"""
MarketGPS - Robust Logo Downloader
Downloads company logos from multiple sources with fallback
Run: python download_logos_robust.py
"""

import os
import requests
import time

# Configuration
LOGO_DIR = "data/logos"
os.makedirs(LOGO_DIR, exist_ok=True)

# Headers pour imiter un navigateur (évite le blocage 403 Forbidden)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Liste précise basée sur votre log d'erreur
DATA = {
    # FRANCE
    "MC": "lvmh.com",
    "OR": "loreal.com",
    "SAN": "sanofi.com",
    "AI": "airliquide.com",
    "BNP": "group.bnpparibas",  # Domaine corrigé pour logo
    "TTE": "totalenergies.com",
    "CAP": "capgemini.com",
    "DG": "vinci.com",
    "CS": "axa.com",
    "ORA": "orange.com",

    # ALLEMAGNE
    "SAP": "sap.com",
    "SIE": "siemens.com",
    "ALV": "allianz.com",
    "DTE": "telekom.com",
    "BAS": "basf.com",
    "BMW": "bmw.com",
    "ADS": "adidas.com",
    "VOW3": "volkswagen.com",
    "DBK": "db.com",

    # UK
    "SHEL": "shell.com",
    "AZN": "astrazeneca.com",
    "HSBA": "hsbc.com",
    "ULVR": "unilever.com",
    "BP": "bp.com",
    "GSK": "gsk.com",
    "RIO": "riotinto.com",
    "LLOY": "lloydsbankinggroup.com",  # Domaine plus précis
    "VOD": "vodafone.com",
    "BARC": "home.barclays",

    # AFRIQUE DU SUD
    "NPN": "naspers.com",
    "BTI": "bat.com",
    "AGL": "angloamerican.com",
    "SOL": "sasol.com",
    "SBK": "standardbank.com",
    "FSR": "firstrand.co.za",
    "MTN": "mtn.com",
    "BID": "bidcorp.com",
    "SHP": "shopriteholdings.co.za",
    "DSY": "discovery.co.za"
}


def download_logo(ticker, domain):
    filepath = os.path.join(LOGO_DIR, f"{ticker}.png")
    
    # Skip if already exists
    if os.path.exists(filepath) and os.path.getsize(filepath) > 500:
        print(f"✓ {ticker} - Déjà présent")
        return True
    
    # Sources possibles (Clearbit est top, Google en fallback)
    urls = [
        f"https://logo.clearbit.com/{domain}?size=128",
        f"https://www.google.com/s2/favicons?domain={domain}&sz=128"
    ]

    print(f"⏳ {ticker} ({domain})... ", end="", flush=True)

    for url in urls:
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 200 and len(response.content) > 500:
                with open(filepath, "wb") as f:
                    f.write(response.content)
                print("✅ OK")
                return True
        except Exception as e:
            continue
    
    print("❌ Échec")
    return False


def main():
    print("=" * 60)
    print("MarketGPS - Téléchargement robuste des logos")
    print(f"Dossier: {LOGO_DIR}")
    print("=" * 60)
    print()
    
    success = 0
    failed = 0
    skipped = 0
    
    for ticker, domain in DATA.items():
        filepath = os.path.join(LOGO_DIR, f"{ticker}.png")
        if os.path.exists(filepath) and os.path.getsize(filepath) > 500:
            print(f"✓ {ticker} - Déjà présent")
            skipped += 1
            continue
            
        if download_logo(ticker, domain):
            success += 1
        else:
            failed += 1
        time.sleep(0.3)  # Pause pour être poli avec l'API
    
    print()
    print("=" * 60)
    print(f"Résultats: {success} téléchargés, {skipped} déjà présents, {failed} échecs")
    print(f"Total logos: {len([f for f in os.listdir(LOGO_DIR) if f.endswith('.png')])} fichiers")
    print("=" * 60)


if __name__ == "__main__":
    main()
