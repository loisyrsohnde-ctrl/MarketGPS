# MarketGPS Testing Infrastructure - Quick Index

## Quick Start

```bash
# 1. Install dependencies (one-time)
pip install pytest

# 2. Run all tests
pytest tests/ -v

# 3. Or use the convenient test runner
./run_tests.sh all
```

## Documentation Files

| File | Purpose |
|------|---------|
| **TESTING_GUIDE.md** | Complete testing documentation, best practices, and troubleshooting |
| **TESTING_INFRASTRUCTURE_SUMMARY.md** | Implementation details, architecture, and statistics |
| **TESTING_INDEX.md** | This file - quick reference and navigation |
| **pytest.ini** | Pytest configuration file |
| **run_tests.sh** | Convenient test execution script |

## Test Files

| File | Tests | Coverage |
|------|-------|----------|
| **test_core_config.py** | 33 tests | Configuration management (core.config) |
| **test_core_models.py** | 66 tests | Data models (core.models) |
| **test_core_utils.py** | 50 tests | Utility functions (core.utils) |
| **conftest.py** | Fixtures | Shared test configuration and fixtures |

**Total: 149 tests across 4 files**

## Test Commands

### Using pytest directly
```bash
# All tests
pytest tests/ -v

# Specific file
pytest tests/test_core_config.py -v

# Specific class
pytest tests/test_core_config.py::TestEODHDConfig -v

# Specific test
pytest tests/test_core_config.py::TestEODHDConfig::test_eodhd_config_defaults -v

# With markers
pytest -m unit -v          # Unit tests only
pytest -m integration -v   # Integration tests only
pytest -m "not slow" -v    # Exclude slow tests

# With coverage
pytest tests/ --cov=core --cov-report=html
```

### Using test runner script
```bash
./run_tests.sh all           # All tests
./run_tests.sh config        # Configuration tests
./run_tests.sh models        # Model tests
./run_tests.sh utils         # Utility tests
./run_tests.sh quick         # Exclude slow tests
./run_tests.sh coverage      # With coverage report
./run_tests.sh watch         # Watch mode (auto-rerun)
```

## Test Coverage by Module

### core.config (33 tests)
- **EODHDConfig**: API validation, configuration checking
- **PipelineConfig**: Default values, thresholds
- **ScoringConfig**: Weight distribution, normalization
- **StorageConfig**: Path creation, validation
- **UIConfig**: Application configuration, colors
- **ComplianceConfig**: Compliance settings
- **BillingConfig**: Subscription plans, Stripe integration
- **AppConfig**: Main configuration, singleton pattern
- **SettingsProxy**: Settings access patterns

### core.models (66 tests)
- **AssetType**: Enumeration, conversions, properties
- **Asset**: Creation, defaults, database serialization
- **Score**: Calculation, state management, serialization
- **ScoreBreakdown**: JSON serialization/deserialization
- **GatingStatus**: Eligibility criteria, validation
- **RotationState**: Refresh state, tracking
- **WatchlistItem**: User watchlist management
- **ProQuota**: Usage calculation, tier management
- **StateLabel**: State enumeration, aliases
- **QueueStatus**: Queue status enumeration
- **PaginatedResult**: Pagination logic
- **ProviderHealth**: Provider status tracking

### core.utils (50 tests)
- **safe_divide**: Division with fallback, edge cases
- **clamp**: Value range constraint
- **safe_float**: Type conversion, NaN/Inf handling
- **safe_int**: Integer conversion
- **format_number**: Number formatting, currency
- **format_large_number**: K/M/B suffix formatting
- **parse_datetime**: Multi-format date parsing
- **days_between**: Date difference calculation
- **truncate_string**: String truncation

## Fixtures Available

### Configuration
- `test_config` - Fresh config instance
- `temp_db` - In-memory SQLite database
- `test_repo` - Base repository instance

### Sample Data
- `sample_asset` - Equity asset (AAPL)
- `sample_etf` - ETF asset (SPY)
- `sample_crypto` - Crypto asset (BTC)
- `sample_africa_asset` - African market asset
- `sample_score` - Complete score object
- `sample_gating_status` - Gating status
- `sample_rotation_state` - Rotation state
- `sample_pro_quota` - Pro subscription
- `sample_watchlist_item` - Watchlist item

### Utilities
- `seed_database` - Pre-populated database
- `mock_logger` - Log capture helper

## Common Test Patterns

### Testing a function
```python
def test_my_function():
    """Test basic functionality."""
    result = my_function(input)
    assert result == expected
```

### Testing a class
```python
class TestMyClass:
    def test_creation(self, sample_object):
        """Test object creation."""
        assert sample_object.field == expected_value

    def test_from_row(self):
        """Test database deserialization."""
        row = {"field": "value"}
        obj = MyClass.from_row(row)
        assert obj.field == "value"
```

### Using fixtures
```python
def test_with_config(test_config):
    """Test with fresh configuration."""
    assert test_config.eodhd.timeout == 30

def test_with_database(temp_db, test_repo):
    """Test with database."""
    # test_repo has database at temp_db
    pass

def test_with_sample_data(sample_asset, sample_score):
    """Test with sample data."""
    assert sample_asset.symbol == "AAPL"
    assert sample_score.is_calculated
```

## Performance

- **Total Tests**: 149
- **Execution Time**: ~0.1 seconds (in-memory databases)
- **Test Classes**: 31
- **Coverage Target**: Core modules, models, utilities

## Project Structure

```
/sessions/funny-exciting-einstein/mnt/MarketGPS/
├── tests/
│   ├── conftest.py
│   ├── test_core_config.py
│   ├── test_core_models.py
│   ├── test_core_utils.py
│   └── ... (existing tests)
├── pytest.ini
├── run_tests.sh
├── TESTING_GUIDE.md
├── TESTING_INFRASTRUCTURE_SUMMARY.md
└── TESTING_INDEX.md
```

## Tips & Tricks

### Run tests in quiet mode
```bash
pytest tests/ -q
```

### Show slowest tests
```bash
pytest tests/ --durations=10
```

### Stop on first failure
```bash
pytest tests/ -x
```

### Show local variables on failure
```bash
pytest tests/ -l
```

### Detailed failure info
```bash
pytest tests/ -vv --tb=long
```

### Run tests that match a pattern
```bash
pytest tests/ -k "config"  # Tests with "config" in name
pytest tests/ -k "not slow"  # Tests without "slow" in name
```

### Parallel execution (requires pytest-xdist)
```bash
pip install pytest-xdist
pytest tests/ -n auto  # Use all CPU cores
```

## Troubleshooting

### ModuleNotFoundError
Make sure you're in the project root and have installed dependencies:
```bash
cd /sessions/funny-exciting-einstein/mnt/MarketGPS
pip install -r requirements.txt
pip install pytest
```

### pytest not found
Add to PATH or use python module:
```bash
export PATH="/sessions/funny-exciting-einstein/.local/bin:$PATH"
python -m pytest tests/ -v
```

### Database locked
Tests use in-memory SQLite to avoid this issue. If you still encounter it:
```bash
rm -rf .pytest_cache
rm -rf __pycache__
pytest tests/ -v
```

## Next Steps

1. **Read Documentation**
   - Start with [TESTING_GUIDE.md](TESTING_GUIDE.md)
   - Review [TESTING_INFRASTRUCTURE_SUMMARY.md](TESTING_INFRASTRUCTURE_SUMMARY.md)

2. **Run Tests**
   ```bash
   pytest tests/ -v
   # or
   ./run_tests.sh all
   ```

3. **Explore Test Files**
   - Open `tests/test_core_config.py` for configuration tests
   - Open `tests/test_core_models.py` for model tests
   - Open `tests/test_core_utils.py` for utility tests

4. **Extend Tests**
   - Add tests for new functions/classes
   - Follow patterns in existing tests
   - Use conftest.py fixtures

5. **Integrate with CI/CD**
   - Use pytest configuration in CI pipeline
   - Generate coverage reports
   - Monitor test metrics

## Contact & Support

For questions about the testing infrastructure:
- Review TESTING_GUIDE.md for detailed documentation
- Check test files for examples and patterns
- Look at conftest.py for available fixtures
- Run tests with -vv for debugging information

## References

- Pytest Docs: https://docs.pytest.org/
- MarketGPS Docs: See PROJECT_STRUCTURE.md
- Test Best Practices: See TESTING_GUIDE.md

---

**Last Updated**: 2026-02-02
**Total Tests**: 149 (All Passing)
**Status**: Production Ready
