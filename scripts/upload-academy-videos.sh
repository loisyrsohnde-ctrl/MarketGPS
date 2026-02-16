#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Upload Academy Videos to VPS
# ═══════════════════════════════════════════════════════════════
# Usage: ./scripts/upload-academy-videos.sh
#
# Ce script copie toutes les vidéos MP4 du dossier cours vers
# le VPS Hostinger dans le dossier academy-videos.
# Les vidéos sont renommées en format propre: part-XX/module-YY/lesson-ZZ/video-NNN.mp4
# ═══════════════════════════════════════════════════════════════

VPS_HOST="root@72.62.190.58"
VPS_DEST="/root/MarketGPS-src/data/academy-videos"
COURSE_DIR="$HOME/Documents/[CourseClub.Me] Udacity - Artificial Intelligence AI for Trading v1.0.0"

echo "╔══════════════════════════════════════════════╗"
echo "║   QuantAI Academy - Upload des vidéos       ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Vérifier que le dossier cours existe
if [ ! -d "$COURSE_DIR" ]; then
  echo "❌ Dossier cours non trouvé: $COURSE_DIR"
  echo "   Modifiez la variable COURSE_DIR dans ce script."
  exit 1
fi

echo "📁 Dossier source: $COURSE_DIR"
echo "🌐 Destination VPS: $VPS_HOST:$VPS_DEST"
echo ""

# Compter les vidéos
VIDEO_COUNT=$(find "$COURSE_DIR" -name "*.mp4" | wc -l | tr -d ' ')
echo "📹 $VIDEO_COUNT vidéos MP4 trouvées"
echo ""

# Calculer la taille totale
TOTAL_SIZE=$(find "$COURSE_DIR" -name "*.mp4" -exec du -ch {} + 2>/dev/null | tail -1 | cut -f1)
echo "💾 Taille totale: $TOTAL_SIZE"
echo ""

read -p "▶ Lancer l'upload ? (o/N) " confirm
if [ "$confirm" != "o" ] && [ "$confirm" != "O" ]; then
  echo "Annulé."
  exit 0
fi

echo ""
echo "🚀 Upload en cours via rsync (avec reprise en cas d'interruption)..."
echo ""

# Créer la structure de dossiers et uploader les vidéos
# rsync avec compression et progression
rsync -avz --progress \
  --include="*/" \
  --include="*.mp4" \
  --exclude="*" \
  "$COURSE_DIR/" \
  "$VPS_HOST:$VPS_DEST/"

echo ""
echo "✅ Upload terminé !"
echo ""
echo "📌 Les vidéos sont disponibles sur le VPS dans:"
echo "   $VPS_DEST/"
echo ""
echo "💡 Pour vérifier sur le VPS:"
echo "   ssh $VPS_HOST 'find $VPS_DEST -name \"*.mp4\" | wc -l'"
