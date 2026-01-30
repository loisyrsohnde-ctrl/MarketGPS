#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# MarketGPS - News Pipeline Scheduler Deployment Script
# ═══════════════════════════════════════════════════════════════════════════
#
# This script sets up and runs the news pipeline scheduler.
# Options:
#   --once    : Run pipeline once and exit (for cron)
#   --daemon  : Run continuously with APScheduler (for Docker/systemd)
#   --test    : Test mode - run with limit of 5 sources
#
# Environment variables required:
#   - OPENAI_API_KEY or GEMINI_API_KEY (for article rewriting)
#
# ═══════════════════════════════════════════════════════════════════════════

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}    MarketGPS News Pipeline Scheduler${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"

# Determine script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${YELLOW}Project root: $PROJECT_ROOT${NC}"

# Change to project root
cd "$PROJECT_ROOT"

# Check Python environment
if [ -d "backend/venv" ]; then
    echo -e "${GREEN}✓ Activating virtual environment...${NC}"
    source backend/venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check required packages
echo -e "${YELLOW}Checking dependencies...${NC}"

python -c "import feedparser" 2>/dev/null || {
    echo -e "${RED}✗ feedparser not installed. Installing...${NC}"
    pip install feedparser
}

python -c "import apscheduler" 2>/dev/null || {
    echo -e "${RED}✗ APScheduler not installed. Installing...${NC}"
    pip install apscheduler
}

# Check LLM availability
if [ -n "$OPENAI_API_KEY" ]; then
    echo -e "${GREEN}✓ OpenAI API key configured${NC}"
elif [ -n "$GEMINI_API_KEY" ]; then
    echo -e "${GREEN}✓ Gemini API key configured${NC}"
else
    echo -e "${YELLOW}⚠ No LLM API key found. Running in fallback mode (no rewriting).${NC}"
fi

# Parse arguments
MODE="daemon"
EXTRA_ARGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --once)
            MODE="once"
            EXTRA_ARGS="--once"
            shift
            ;;
        --daemon)
            MODE="daemon"
            shift
            ;;
        --test)
            MODE="test"
            shift
            ;;
        --interval)
            export NEWS_INTERVAL_MINUTES="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}Mode: $MODE${NC}"
echo -e "${GREEN}Interval: ${NEWS_INTERVAL_MINUTES:-30} minutes${NC}"

# Run the scheduler
if [ "$MODE" = "test" ]; then
    echo -e "${YELLOW}Running test mode (5 sources limit)...${NC}"
    python -m pipeline.news.news_scheduler --once
elif [ "$MODE" = "once" ]; then
    echo -e "${YELLOW}Running once and exiting...${NC}"
    python -m pipeline.news.news_scheduler --once
else
    echo -e "${YELLOW}Starting daemon mode...${NC}"
    python -m pipeline.news.news_scheduler
fi

echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}    Done!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
