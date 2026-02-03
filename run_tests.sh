#!/bin/bash
# MarketGPS Test Runner Script
# Provides convenient test execution commands

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Ensure pytest is in PATH
export PATH="/sessions/funny-exciting-einstein/.local/bin:$PATH"

# Function: Print header
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Function: Print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function: Print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function: Print info
print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Function: Show usage
show_usage() {
    echo "MarketGPS Test Runner"
    echo ""
    echo "Usage: ./run_tests.sh [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  all              Run all tests"
    echo "  config           Run configuration tests only"
    echo "  models           Run data model tests only"
    echo "  utils            Run utility function tests only"
    echo "  quick            Run tests (excluding slow ones)"
    echo "  unit             Run unit tests only"
    echo "  integration      Run integration tests only"
    echo "  coverage         Run tests with coverage report"
    echo "  watch            Run tests and watch for changes (requires pytest-watch)"
    echo "  help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./run_tests.sh all"
    echo "  ./run_tests.sh config -v"
    echo "  ./run_tests.sh coverage"
}

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    print_error "pytest is not installed"
    echo "Install with: pip install pytest"
    exit 1
fi

# Parse command
CMD="${1:-all}"

case "$CMD" in
    all)
        print_header "Running All Tests"
        pytest tests/ -v ${@:2}
        print_success "All tests completed"
        ;;

    config)
        print_header "Running Configuration Tests"
        pytest tests/test_core_config.py -v ${@:2}
        print_success "Configuration tests completed"
        ;;

    models)
        print_header "Running Data Model Tests"
        pytest tests/test_core_models.py -v ${@:2}
        print_success "Data model tests completed"
        ;;

    utils)
        print_header "Running Utility Tests"
        pytest tests/test_core_utils.py -v ${@:2}
        print_success "Utility tests completed"
        ;;

    quick)
        print_header "Running Quick Tests (excluding slow)"
        pytest tests/ -v -m "not slow" ${@:2}
        print_success "Quick tests completed"
        ;;

    unit)
        print_header "Running Unit Tests"
        pytest tests/ -v -m "unit" ${@:2}
        print_success "Unit tests completed"
        ;;

    integration)
        print_header "Running Integration Tests"
        pytest tests/ -v -m "integration" ${@:2}
        print_success "Integration tests completed"
        ;;

    coverage)
        print_header "Running Tests with Coverage"
        if ! command -v coverage &> /dev/null; then
            print_info "Installing pytest-cov..."
            pip install -q pytest-cov
        fi
        pytest tests/ -v --cov=core --cov=storage --cov-report=html ${@:2}
        print_success "Coverage report generated in htmlcov/index.html"
        ;;

    watch)
        print_header "Running Tests in Watch Mode"
        if ! command -v ptw &> /dev/null; then
            print_info "Installing pytest-watch..."
            pip install -q pytest-watch
        fi
        ptw tests/ -v ${@:2}
        ;;

    help|--help|-h)
        show_usage
        ;;

    *)
        print_error "Unknown command: $CMD"
        echo ""
        show_usage
        exit 1
        ;;
esac
