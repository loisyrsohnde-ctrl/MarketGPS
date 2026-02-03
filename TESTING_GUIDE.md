# MarketGPS Testing Infrastructure

Complete test infrastructure for the MarketGPS project with comprehensive coverage of core modules.

## Overview

The testing framework is built on **pytest** with well-organized test suites for:
- Configuration management (`core.config`)
- Data models (`core.models`)
- Utility functions (`core.utils`)
- Database operations (via fixtures)

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and pytest configuration
├── pytest.ini               # Pytest configuration
├── test_core_config.py      # Configuration tests (33 tests)
├── test_core_models.py      # Data model tests (66 tests)
├── test_core_utils.py       # Utility function tests (50 tests)
└── ... (existing tests)
```

## Installation

Pytest dependencies are included in `requirements.txt`. Install them:

```bash
pip install -r requirements.txt
pip install pytest
```

## Running Tests

### Run all tests
```bash
pytest tests/ -v
```

### Run specific test file
```bash
pytest tests/test_core_config.py -v
```

### Run specific test class
```bash
pytest tests/test_core_config.py::TestEODHDConfig -v
```

### Run specific test
```bash
pytest tests/test_core_config.py::TestEODHDConfig::test_eodhd_config_defaults -v
```

### Run tests with markers
```bash
# Run only unit tests
pytest -m unit -v

# Run only integration tests
pytest -m integration -v

# Skip slow tests
pytest -m "not slow" -v
```

### Run with coverage (install pytest-cov first)
```bash
pip install pytest-cov
pytest tests/ --cov=core --cov=storage --cov-report=html
```

## Test Coverage

### Configuration Tests (test_core_config.py)
Tests for all configuration components:

- **TestEODHDConfig** (6 tests)
  - API key validation
  - Configuration checking
  - Startup validation

- **TestPipelineConfig** (2 tests)
  - Default values
  - Africa-specific thresholds

- **TestScoringConfig** (4 tests)
  - Weight distribution
  - Optimal ranges

- **TestStorageConfig** (3 tests)
  - Path creation
  - Path validity

- **TestUIConfig** (3 tests)
  - App configuration
  - Color definitions

- **TestComplianceConfig** (3 tests)
  - Compliance settings

- **TestBillingConfig** (4 tests)
  - Subscription plans
  - Stripe configuration

- **TestAppConfig** (4 tests)
  - Main app config
  - Singleton pattern

- **TestSettingsProxy** (5 tests)
  - Settings access

### Data Model Tests (test_core_models.py)
Tests for all dataclass models:

- **TestAssetType** (7 tests)
  - Enum values
  - String conversion
  - Display names
  - Asset properties

- **TestAsset** (4 tests)
  - Creation and defaults
  - Database serialization

- **TestScore** (6 tests)
  - Score calculation
  - Database serialization

- **TestScoreBreakdown** (5 tests)
  - JSON serialization/deserialization

- **TestGatingStatus** (3 tests)
  - Gating criteria
  - Database operations

- **TestRotationState** (2 tests)
  - Refresh state tracking

- **TestWatchlistItem** (2 tests)
  - User watchlist management

- **TestProQuota** (7 tests)
  - Usage calculation
  - Tier management

- **TestStateLabel** (2 tests)
  - State enumeration

- **TestQueueStatus** (1 test)
  - Queue status values

- **TestPaginatedResult** (5 tests)
  - Pagination logic

- **TestProviderHealth** (3 tests)
  - Provider status

### Utility Tests (test_core_utils.py)
Tests for utility functions:

- **TestSafeDivide** (8 tests)
  - Safe division handling
  - Edge cases

- **TestClamp** (6 tests)
  - Value clamping

- **TestSafeFloat** (9 tests)
  - Type conversion
  - NaN/Inf handling

- **TestSafeInt** (7 tests)
  - Integer conversion

- **TestFormatNumber** (8 tests)
  - Number formatting
  - Currency formatting

- **TestFormatLargeNumber** (7 tests)
  - K/M/B formatting

- **TestParseDatetime** (8 tests)
  - Date/time parsing

- **TestDaysBetween** (7 tests)
  - Date calculations

- **TestTruncateString** (8 tests)
  - String truncation

## Fixtures

### Configuration Fixtures
- `test_config`: Fresh config instance for each test
- `temp_db`: Temporary SQLite database with schema

### Data Fixtures
- `sample_asset`: Equity asset (AAPL)
- `sample_etf`: ETF asset (SPY)
- `sample_crypto`: Crypto asset (BTC)
- `sample_africa_asset`: African market asset
- `sample_score`: Complete score object
- `sample_gating_status`: Gating status
- `sample_rotation_state`: Rotation state
- `sample_pro_quota`: Pro subscription quota
- `sample_watchlist_item`: Watchlist item

### Utility Fixtures
- `test_repo`: Base repository instance
- `seed_database`: Pre-populated database
- `mock_logger`: Log capture helper

## Configuration (pytest.ini)

The `pytest.ini` file provides:
- Test discovery patterns
- Output formatting
- Test markers (unit, integration, slow)
- Doctest configuration
- Logging setup

## Best Practices

1. **Test Organization**
   - One test class per main class/function
   - Descriptive test names
   - Clear test purposes

2. **Fixtures**
   - Use fixtures for common setup
   - Share via conftest.py
   - Minimize test coupling

3. **Assertions**
   - Use pytest assertions
   - One assertion focus per test
   - Clear assertion messages

4. **Markers**
   - Use `@pytest.mark.unit` for fast tests
   - Use `@pytest.mark.integration` for slow tests
   - Use `@pytest.mark.slow` for very slow tests

5. **Database Testing**
   - Use in-memory SQLite (`temp_db` fixture)
   - No external dependencies
   - Fast and isolated

## Adding New Tests

### For new functions
```python
def test_my_function_basic():
    """Test basic functionality."""
    result = my_function(input)
    assert result == expected

def test_my_function_edge_case():
    """Test edge case handling."""
    result = my_function(None)
    assert result == default
```

### For new models
```python
class TestMyModel:
    """Tests for MyModel dataclass."""

    def test_creation(self):
        """Test creating model."""
        obj = MyModel(field="value")
        assert obj.field == "value"

    def test_from_row(self):
        """Test creating from database row."""
        row = {"field": "value"}
        obj = MyModel.from_row(row)
        assert obj.field == "value"
```

## Continuous Integration

To integrate with CI/CD:

```bash
# Run tests with coverage report
pytest tests/ -v --cov=core --cov=storage --cov-report=xml

# Generate JUnit XML for CI tools
pytest tests/ -v --junit-xml=test-results.xml
```

## Troubleshooting

### Import Errors
Make sure bootstrap is called:
```python
from core.bootstrap import bootstrap
bootstrap()
```

### Database Locked
Tests use in-memory databases to avoid locking issues.

### Missing Dependencies
Install all requirements:
```bash
pip install -r requirements.txt
pip install pytest pytest-cov
```

## Test Statistics

- **Total Tests**: 149
- **Test Classes**: 31
- **Coverage Target**: Core modules, models, utilities
- **Average Execution Time**: < 1 second

## Future Enhancements

- Add integration tests for pipeline modules
- Add performance benchmarks
- Add tests for storage layer
- Add tests for providers
- Add E2E tests for API endpoints
- Add security/compliance tests

## References

- Pytest Documentation: https://docs.pytest.org/
- Python Testing Best Practices: https://docs.python-guide.org/writing/tests/
- MarketGPS Architecture: /sessions/funny-exciting-einstein/mnt/MarketGPS/PROJECT_STRUCTURE.md
