"""
Unit Tests: Core Utilities
Tests for core.utils module utility functions.
"""

import pytest
import math
from datetime import datetime, date, timedelta

from core.utils import (
    safe_divide, clamp, safe_float, safe_int, format_number,
    format_large_number, parse_datetime, days_between, truncate_string
)


class TestSafeDivide:
    """Tests for safe_divide utility function."""

    def test_safe_divide_normal(self):
        """Test normal division."""
        assert safe_divide(10, 2) == 5.0

    def test_safe_divide_floats(self):
        """Test division with floats."""
        assert safe_divide(10.5, 2.0) == 5.25

    def test_safe_divide_by_zero(self):
        """Test division by zero returns default."""
        assert safe_divide(10, 0) == 0

    def test_safe_divide_by_zero_custom_default(self):
        """Test division by zero with custom default."""
        assert safe_divide(10, 0, default=99) == 99

    def test_safe_divide_none_numerator(self):
        """Test None numerator returns default."""
        assert safe_divide(None, 2) == 0

    def test_safe_divide_none_denominator(self):
        """Test None denominator returns default."""
        assert safe_divide(10, None) == 0

    def test_safe_divide_both_none(self):
        """Test both None returns default."""
        assert safe_divide(None, None) == 0

    def test_safe_divide_type_error(self):
        """Test type error returns default."""
        assert safe_divide("string", 2) == 0


class TestClamp:
    """Tests for clamp utility function."""

    def test_clamp_within_range(self):
        """Test clamping value within range returns value."""
        assert clamp(5, 0, 10) == 5

    def test_clamp_below_range(self):
        """Test clamping value below range."""
        assert clamp(-5, 0, 10) == 0

    def test_clamp_above_range(self):
        """Test clamping value above range."""
        assert clamp(15, 0, 10) == 10

    def test_clamp_at_min(self):
        """Test clamping at minimum."""
        assert clamp(0, 0, 10) == 0

    def test_clamp_at_max(self):
        """Test clamping at maximum."""
        assert clamp(10, 0, 10) == 10

    def test_clamp_floats(self):
        """Test clamping with floats."""
        assert clamp(5.5, 0.0, 10.0) == 5.5


class TestSafeFloat:
    """Tests for safe_float utility function."""

    def test_safe_float_valid_int(self):
        """Test converting valid int."""
        assert safe_float(42) == 42.0

    def test_safe_float_valid_float(self):
        """Test converting valid float."""
        assert safe_float(3.14) == 3.14

    def test_safe_float_valid_string(self):
        """Test converting valid string."""
        assert safe_float("3.14") == 3.14

    def test_safe_float_none(self):
        """Test None returns default."""
        assert safe_float(None) == 0.0

    def test_safe_float_none_custom_default(self):
        """Test None with custom default."""
        assert safe_float(None, default=-1.0) == -1.0

    def test_safe_float_invalid_string(self):
        """Test invalid string returns default."""
        assert safe_float("invalid") == 0.0

    def test_safe_float_nan(self):
        """Test NaN returns default."""
        assert safe_float(float("nan")) == 0.0

    def test_safe_float_inf(self):
        """Test infinity returns default."""
        assert safe_float(float("inf")) == 0.0

    def test_safe_float_negative_inf(self):
        """Test negative infinity returns default."""
        assert safe_float(float("-inf")) == 0.0


class TestSafeInt:
    """Tests for safe_int utility function."""

    def test_safe_int_valid_int(self):
        """Test converting valid int."""
        assert safe_int(42) == 42

    def test_safe_int_valid_float(self):
        """Test converting valid float."""
        assert safe_int(3.9) == 3

    def test_safe_int_valid_string(self):
        """Test converting valid string."""
        assert safe_int("42") == 42

    def test_safe_int_float_string(self):
        """Test converting float string."""
        assert safe_int("3.14") == 3

    def test_safe_int_none(self):
        """Test None returns default."""
        assert safe_int(None) == 0

    def test_safe_int_none_custom_default(self):
        """Test None with custom default."""
        assert safe_int(None, default=-1) == -1

    def test_safe_int_invalid_string(self):
        """Test invalid string returns default."""
        assert safe_int("invalid") == 0


class TestFormatNumber:
    """Tests for format_number utility function."""

    def test_format_number_basic(self):
        """Test basic number formatting."""
        assert format_number(123.456, decimals=2) == "123.46"

    def test_format_number_with_prefix(self):
        """Test formatting with prefix."""
        assert format_number(100, prefix="$") == "$100.00"

    def test_format_number_with_suffix(self):
        """Test formatting with suffix."""
        assert format_number(50, suffix="%") == "50.00%"

    def test_format_number_thousands_separator(self):
        """Test formatting includes thousands separator."""
        assert format_number(1000.50, decimals=2) == "1,000.50"

    def test_format_number_zero_decimals(self):
        """Test formatting with zero decimals."""
        assert format_number(123.456, decimals=0) == "123"

    def test_format_number_none(self):
        """Test None returns N/A."""
        assert format_number(None) == "N/A"

    def test_format_number_none_custom_na_text(self):
        """Test None with custom N/A text."""
        assert format_number(None, na_text="-") == "-"

    def test_format_number_nan(self):
        """Test NaN returns N/A."""
        assert format_number(float("nan")) == "N/A"


class TestFormatLargeNumber:
    """Tests for format_large_number utility function."""

    def test_format_large_number_thousands(self):
        """Test formatting thousands."""
        assert format_large_number(1500) == "1.5K"

    def test_format_large_number_millions(self):
        """Test formatting millions."""
        assert format_large_number(1_500_000) == "1.5M"

    def test_format_large_number_billions(self):
        """Test formatting billions."""
        assert format_large_number(1_500_000_000) == "1.5B"

    def test_format_large_number_small(self):
        """Test formatting small numbers."""
        assert format_large_number(500) == "500"

    def test_format_large_number_negative(self):
        """Test formatting negative numbers."""
        result = format_large_number(-1_500_000)
        assert "-" in result
        assert "1.5M" in result

    def test_format_large_number_none(self):
        """Test None returns N/A."""
        assert format_large_number(None) == "N/A"

    def test_format_large_number_nan(self):
        """Test NaN returns N/A."""
        assert format_large_number(float("nan")) == "N/A"


class TestParseDatetime:
    """Tests for parse_datetime utility function."""

    def test_parse_datetime_with_datetime(self):
        """Test parsing datetime object."""
        dt = datetime(2026, 1, 15, 10, 30, 0)
        result = parse_datetime(dt)
        assert result == dt

    def test_parse_datetime_with_date(self):
        """Test parsing date object."""
        d = date(2026, 1, 15)
        result = parse_datetime(d)
        assert isinstance(result, datetime)
        assert result.year == 2026
        assert result.month == 1
        assert result.day == 15

    def test_parse_datetime_iso_format(self):
        """Test parsing ISO format string."""
        result = parse_datetime("2026-01-15T10:30:00")
        assert isinstance(result, datetime)

    def test_parse_datetime_iso_format_with_z(self):
        """Test parsing ISO format with Z suffix."""
        result = parse_datetime("2026-01-15T10:30:00Z")
        assert isinstance(result, datetime)

    def test_parse_datetime_date_format(self):
        """Test parsing date format string."""
        result = parse_datetime("2026-01-15")
        assert isinstance(result, datetime)
        assert result.year == 2026

    def test_parse_datetime_european_format(self):
        """Test parsing European date format."""
        result = parse_datetime("15/01/2026")
        assert isinstance(result, datetime)

    def test_parse_datetime_none(self):
        """Test parsing None returns None."""
        assert parse_datetime(None) is None

    def test_parse_datetime_invalid_string(self):
        """Test parsing invalid string returns None."""
        assert parse_datetime("invalid date") is None


class TestDaysBetween:
    """Tests for days_between utility function."""

    def test_days_between_same_day(self):
        """Test days between same day is 0."""
        today = datetime.now()
        assert days_between(today, today) == 0

    def test_days_between_one_day(self):
        """Test days between consecutive days."""
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        assert days_between(today, tomorrow) == 1

    def test_days_between_multiple_days(self):
        """Test days between multiple days."""
        date1 = datetime(2026, 1, 1)
        date2 = datetime(2026, 1, 11)
        assert days_between(date1, date2) == 10

    def test_days_between_reverse_order(self):
        """Test days between works regardless of order."""
        date1 = datetime(2026, 1, 11)
        date2 = datetime(2026, 1, 1)
        assert days_between(date1, date2) == 10

    def test_days_between_with_now_default(self):
        """Test days between with now as default."""
        past = datetime.now() - timedelta(days=5)
        result = days_between(past)
        # Should be approximately 5 days (allow 1 day margin for test execution)
        assert 4 <= result <= 6

    def test_days_between_string_dates(self):
        """Test days between with string dates."""
        result = days_between("2026-01-01", "2026-01-11")
        assert result == 10

    def test_days_between_invalid_dates(self):
        """Test days between with invalid dates returns 0."""
        assert days_between("invalid", "also invalid") == 0


class TestTruncateString:
    """Tests for truncate_string utility function."""

    def test_truncate_string_no_truncation_needed(self):
        """Test string shorter than limit."""
        result = truncate_string("hello", max_length=10)
        assert result == "hello"

    def test_truncate_string_exact_length(self):
        """Test string exactly at limit."""
        result = truncate_string("hello", max_length=5)
        assert result == "hello"

    def test_truncate_string_needs_truncation(self):
        """Test string longer than limit."""
        result = truncate_string("hello world", max_length=8)
        assert len(result) <= 8
        assert result.endswith("...")

    def test_truncate_string_custom_suffix(self):
        """Test truncation with custom suffix."""
        result = truncate_string("hello world", max_length=8, suffix=">>")
        assert result.endswith(">>")

    def test_truncate_string_long_text(self):
        """Test truncating long text."""
        long_text = "This is a very long string that needs to be truncated"
        result = truncate_string(long_text, max_length=20)
        assert len(result) <= 20

    def test_truncate_string_empty(self):
        """Test truncating empty string."""
        result = truncate_string("", max_length=10)
        assert result == ""

    def test_truncate_string_single_char(self):
        """Test truncating single character."""
        result = truncate_string("a", max_length=5)
        assert result == "a"

    def test_truncate_string_longer_suffix_than_max(self):
        """Test when suffix is longer than max_length."""
        # This is an edge case - suffix longer than max_length
        # The function should still work but produce weird results
        result = truncate_string("hello", max_length=3, suffix=">>>>")
        # Result will be negative length, Python handles it gracefully
        assert isinstance(result, str)
