#!/bin/bash
# Script to download logos for MarketGPS
# Run: bash download_logos.sh

cd "$(dirname "$0")"
mkdir -p data/logos

echo "=== Téléchargement des logos MarketGPS ==="
echo ""

# Function to download logo
download_logo() {
    local ticker=$1
    local domain=$2
    local output="data/logos/${ticker}.png"
    
    if [ -f "$output" ]; then
        echo "✓ $ticker - Déjà présent"
        return 0
    fi
    
    echo -n "Téléchargement $ticker ($domain)... "
    
    if curl -s -f -o "$output" "https://logo.clearbit.com/${domain}" 2>/dev/null; then
        # Check if file is valid (more than 500 bytes)
        size=$(wc -c < "$output" | tr -d ' ')
        if [ "$size" -gt 500 ]; then
            echo "OK ($size bytes)"
            return 0
        else
            rm -f "$output"
            echo "Fichier trop petit"
            return 1
        fi
    else
        rm -f "$output" 2>/dev/null
        echo "Échec"
        return 1
    fi
}

# France
echo ""
echo "=== FRANCE ==="
download_logo "MC" "lvmh.com"
download_logo "OR" "loreal.com"
download_logo "SAN" "sanofi.com"
download_logo "AI" "airliquide.com"
download_logo "BNP" "bnpparibas.com"
download_logo "TTE" "totalenergies.com"
download_logo "CAP" "capgemini.com"
download_logo "DG" "vinci.com"
download_logo "CS" "axa.com"
download_logo "ORA" "orange.com"

# Germany
echo ""
echo "=== ALLEMAGNE ==="
download_logo "SAP" "sap.com"
download_logo "SIE" "siemens.com"
download_logo "ALV" "allianz.com"
download_logo "DTE" "telekom.com"
download_logo "BAS" "basf.com"
download_logo "BMW" "bmw.com"
download_logo "ADS" "adidas.com"
download_logo "VOW3" "volkswagen.com"
download_logo "DBK" "db.com"

# UK
echo ""
echo "=== ROYAUME-UNI ==="
download_logo "SHEL" "shell.com"
download_logo "AZN" "astrazeneca.com"
download_logo "HSBA" "hsbc.com"
download_logo "ULVR" "unilever.com"
download_logo "BP" "bp.com"
download_logo "GSK" "gsk.com"
download_logo "RIO" "riotinto.com"
download_logo "LLOY" "lloydsbank.com"
download_logo "VOD" "vodafone.com"
download_logo "BARC" "barclays.com"

# South Africa
echo ""
echo "=== AFRIQUE DU SUD ==="
download_logo "NPN" "naspers.com"
download_logo "BTI" "bat.com"
download_logo "AGL" "angloamerican.com"
download_logo "SOL" "sasol.com"
download_logo "SBK" "standardbank.com"
download_logo "FSR" "firstrand.co.za"
download_logo "MTN" "mtn.com"
download_logo "BID" "bidcorp.com"
download_logo "SHP" "shopriteholdings.co.za"
download_logo "DSY" "discovery.co.za"

# US companies (additional)
echo ""
echo "=== USA (compléments) ==="
download_logo "AAPL" "apple.com"
download_logo "MSFT" "microsoft.com"
download_logo "GOOGL" "google.com"
download_logo "AMZN" "amazon.com"
download_logo "META" "meta.com"
download_logo "TSLA" "tesla.com"
download_logo "NVDA" "nvidia.com"
download_logo "JPM" "jpmorganchase.com"
download_logo "V" "visa.com"
download_logo "MA" "mastercard.com"

echo ""
echo "=== TERMINÉ ==="
echo "Logos disponibles: $(ls -1 data/logos/*.png 2>/dev/null | wc -l | tr -d ' ') fichiers"
