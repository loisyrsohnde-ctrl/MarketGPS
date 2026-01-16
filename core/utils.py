"""
MarketGPS Utility Functions.
"""
import logging
import sys
from typing import Optional, TypeVar, Union
from datetime import datetime, date
import math

T = TypeVar("T", int, float)


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Get a configured logger.
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        logger.addHandler(handler)
    
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger


def safe_divide(
    numerator: Optional[T],
    denominator: Optional[T],
    default: T = 0
) -> T:
    """
    Safe division with fallback.
    
    Args:
        numerator: Numerator value
        denominator: Denominator value
        default: Default value if division fails
        
    Returns:
        Division result or default
    """
    if numerator is None or denominator is None:
        return default
    if denominator == 0:
        return default
    try:
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return default


def clamp(value: T, min_val: T, max_val: T) -> T:
    """
    Clamp value to range.
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        Clamped value
    """
    return max(min_val, min(max_val, value))


def safe_float(value: any, default: float = 0.0) -> float:
    """
    Safely convert to float.
    
    Args:
        value: Value to convert
        default: Default if conversion fails
        
    Returns:
        Float value or default
    """
    if value is None:
        return default
    try:
        result = float(value)
        if math.isnan(result) or math.isinf(result):
            return default
        return result
    except (TypeError, ValueError):
        return default


def safe_int(value: any, default: int = 0) -> int:
    """
    Safely convert to int.
    
    Args:
        value: Value to convert
        default: Default if conversion fails
        
    Returns:
        Int value or default
    """
    if value is None:
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def format_number(
    value: Optional[float],
    decimals: int = 2,
    prefix: str = "",
    suffix: str = "",
    na_text: str = "N/A"
) -> str:
    """
    Format number for display.
    
    Args:
        value: Number to format
        decimals: Decimal places
        prefix: Prefix string (e.g., "$")
        suffix: Suffix string (e.g., "%")
        na_text: Text for None/NaN values
        
    Returns:
        Formatted string
    """
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return na_text
    
    try:
        formatted = f"{value:,.{decimals}f}"
        return f"{prefix}{formatted}{suffix}"
    except (TypeError, ValueError):
        return na_text


def format_large_number(value: Optional[float], na_text: str = "N/A") -> str:
    """
    Format large number with K/M/B suffix.
    
    Args:
        value: Number to format
        na_text: Text for None/NaN values
        
    Returns:
        Formatted string (e.g., "1.5M")
    """
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return na_text
    
    try:
        abs_val = abs(value)
        sign = "-" if value < 0 else ""
        
        if abs_val >= 1_000_000_000:
            return f"{sign}{abs_val / 1_000_000_000:.1f}B"
        if abs_val >= 1_000_000:
            return f"{sign}{abs_val / 1_000_000:.1f}M"
        if abs_val >= 1_000:
            return f"{sign}{abs_val / 1_000:.1f}K"
        return f"{sign}{abs_val:.0f}"
    except (TypeError, ValueError):
        return na_text


def parse_datetime(value: Union[str, datetime, date, None]) -> Optional[datetime]:
    """
    Parse various datetime formats.
    
    Args:
        value: Value to parse
        
    Returns:
        Datetime or None
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    if isinstance(value, str):
        try:
            # Try ISO format first
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
        try:
            # Try common formats
            for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y"]:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        except Exception:
            pass
    return None


def days_between(
    date1: Union[str, datetime, date, None],
    date2: Union[str, datetime, date, None] = None
) -> int:
    """
    Calculate days between two dates.
    
    Args:
        date1: First date
        date2: Second date (default: now)
        
    Returns:
        Number of days
    """
    dt1 = parse_datetime(date1)
    dt2 = parse_datetime(date2) if date2 else datetime.now()
    
    if dt1 is None or dt2 is None:
        return 0
    
    return abs((dt2 - dt1).days)


def truncate_string(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate string with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
