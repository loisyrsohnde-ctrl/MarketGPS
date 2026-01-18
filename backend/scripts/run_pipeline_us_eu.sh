#!/bin/bash
#
# MarketGPS - US_EU Pipeline Runner
# ==================================
# Orchestrateur shell pour l'exécution automatisée du pipeline.
# Appelle le guard Python, puis exécute le pipeline si autorisé.
#
# Usage:
#   ./run_pipeline_us_eu.sh open|close [--dry-run] [--force]
#
# Exit codes:
#   0  = Success
#   10 = Skipped (market closed)
#   11 = Skipped (wrong time window)
#   20 = Skipped (lock active)
#   1  = Error
#

set -o pipefail

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
LOG_DIR="$BACKEND_DIR/logs"
LOCK_FILE="$BACKEND_DIR/.pipeline_us_eu.lock"
VENV_PATH="$PROJECT_ROOT/venv"

# Guard script
GUARD_SCRIPT="$SCRIPT_DIR/scheduler_guard.py"

# Python interpreter
if [ -f "$VENV_PATH/bin/python" ]; then
    PYTHON="$VENV_PATH/bin/python"
else
    PYTHON="python3"
fi

# Ensure logs directory exists
mkdir -p "$LOG_DIR"

# ═══════════════════════════════════════════════════════════════════════════
# FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

log() {
    local level=$1
    local message=$2
    local timestamp=$(TZ=America/New_York date "+%Y-%m-%d %H:%M:%S %Z")
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

cleanup() {
    local exit_code=$?
    log "INFO" "Cleanup: removing lock file"
    rm -f "$LOCK_FILE"
    log "INFO" "=== PIPELINE END (exit=$exit_code) ==="
    exit $exit_code
}

show_usage() {
    echo "Usage: $0 <mode> [options]"
    echo ""
    echo "Modes:"
    echo "  open     Run at market open (09:35 ET)"
    echo "  close    Run at market close (16:10 ET)"
    echo ""
    echo "Options:"
    echo "  --dry-run    Check guards but don't run pipeline"
    echo "  --force      Skip all guard checks (force run)"
    echo "  --help       Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 open"
    echo "  $0 close --dry-run"
    echo "  $0 open --force"
}

# ═══════════════════════════════════════════════════════════════════════════
# ARGUMENT PARSING
# ═══════════════════════════════════════════════════════════════════════════

MODE=""
DRY_RUN=0
FORCE=0

while [[ $# -gt 0 ]]; do
    case $1 in
        open|close)
            MODE=$1
            shift
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --force)
            FORCE=1
            shift
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        *)
            echo "ERROR: Unknown argument: $1"
            show_usage
            exit 1
            ;;
    esac
done

if [ -z "$MODE" ]; then
    echo "ERROR: Mode required (open or close)"
    show_usage
    exit 1
fi

# Set log file based on mode
LOG_FILE="$LOG_DIR/pipeline_us_eu_${MODE}.log"

# ═══════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

log "INFO" "=== PIPELINE START ==="
log "INFO" "Mode: $MODE"
log "INFO" "Project root: $PROJECT_ROOT"
log "INFO" "Python: $PYTHON"

# Build guard arguments
GUARD_ARGS="--mode $MODE"
if [ $DRY_RUN -eq 1 ]; then
    GUARD_ARGS="$GUARD_ARGS --dry-run"
fi
if [ $FORCE -eq 1 ]; then
    GUARD_ARGS="$GUARD_ARGS --skip-all-checks"
fi

# Run guard check
log "INFO" "Running guard: $PYTHON $GUARD_SCRIPT $GUARD_ARGS"
$PYTHON "$GUARD_SCRIPT" $GUARD_ARGS
GUARD_EXIT=$?

log "INFO" "Guard exit code: $GUARD_EXIT"

# Handle guard results
case $GUARD_EXIT in
    0)
        log "INFO" "Guard passed - proceeding with pipeline"
        ;;
    10)
        log "INFO" "SKIP: Market closed"
        exit 10
        ;;
    11)
        log "INFO" "SKIP: Not in run window"
        exit 11
        ;;
    20)
        log "INFO" "SKIP: Pipeline already running (lock active)"
        exit 20
        ;;
    *)
        log "ERROR" "Guard failed with unexpected code: $GUARD_EXIT"
        exit 1
        ;;
esac

# Dry run stops here
if [ $DRY_RUN -eq 1 ]; then
    log "INFO" "DRY RUN - pipeline not executed"
    # Clean up lock in dry run mode too
    $PYTHON "$GUARD_SCRIPT" --release-lock
    exit 0
fi

# Set trap to cleanup lock on exit
trap cleanup EXIT INT TERM

# Change to project root
cd "$PROJECT_ROOT" || exit 1

# Activate virtual environment if exists
if [ -f "$VENV_PATH/bin/activate" ]; then
    log "INFO" "Activating virtual environment"
    source "$VENV_PATH/bin/activate"
fi

# ═══════════════════════════════════════════════════════════════════════════
# PIPELINE EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

log "INFO" "Starting pipeline execution..."

if [ "$MODE" == "open" ]; then
    # OPEN: Quick rotation/scoring update
    log "INFO" "Mode OPEN: Running rotation + scoring"
    
    PIPELINE_CMD="python -m pipeline.jobs --run-rotation --scope US_EU --run-longterm-scoring --batch-size 100"
    
elif [ "$MODE" == "close" ]; then
    # CLOSE: Full pipeline with production publish
    log "INFO" "Mode CLOSE: Running full pipeline + publish"
    
    PIPELINE_CMD="python -m pipeline.jobs --full-pipeline --scope US_EU --production --run-longterm-scoring"
    
else
    log "ERROR" "Unknown mode: $MODE"
    exit 1
fi

log "INFO" "Executing: $PIPELINE_CMD"

# Run pipeline and capture output
PIPELINE_START=$(date +%s)

$PIPELINE_CMD 2>&1 | while IFS= read -r line; do
    echo "[$MODE] $line" >> "$LOG_FILE"
    echo "$line"
done

PIPELINE_EXIT=${PIPESTATUS[0]}
PIPELINE_END=$(date +%s)
PIPELINE_DURATION=$((PIPELINE_END - PIPELINE_START))

log "INFO" "Pipeline completed in ${PIPELINE_DURATION}s with exit code: $PIPELINE_EXIT"

# ═══════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════

if [ $PIPELINE_EXIT -eq 0 ]; then
    log "INFO" "✓ Pipeline $MODE completed successfully"
else
    log "ERROR" "✗ Pipeline $MODE failed with exit code: $PIPELINE_EXIT"
fi

# Exit with pipeline's exit code (cleanup trap will run)
exit $PIPELINE_EXIT
