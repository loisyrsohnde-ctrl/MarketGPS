"""
Password Security Module for MarketGPS

Implements secure password hashing using Argon2 via passlib.
Supports backward compatibility with legacy SHA256 hashes.

MIGRATION NOTES:
- All new passwords are hashed with Argon2
- Legacy SHA256 hashes are recognized but converted on password change
- Users with old hashes will be transparently upgraded on next login
"""

import hashlib
from passlib.context import CryptContext
from typing import Tuple

# Create context with Argon2 as default
# Supports verification of legacy formats during migration
pwd_context = CryptContext(
    schemes=["argon2", "pbkdf2_sha256"],
    deprecated="auto",
    argon2__memory_cost=65536,  # 64 MB
    argon2__time_cost=3,         # 3 iterations
    argon2__parallelism=4,       # 4 parallelism
)

# Legacy schemes for backward compatibility
LEGACY_SHA256_PREFIX = "sha256:"
LEGACY_PBKDF2_PREFIX = "pbkdf2:sha256:"


def _is_legacy_sha256(password_hash: str) -> bool:
    """Check if hash is using legacy SHA256 format."""
    return password_hash.startswith(LEGACY_SHA256_PREFIX)


def _is_legacy_pbkdf2(password_hash: str) -> bool:
    """Check if hash is using legacy PBKDF2-SHA256 format."""
    return password_hash.startswith(LEGACY_PBKDF2_PREFIX)


def _verify_legacy_sha256(password: str, password_hash: str) -> bool:
    """
    Verify password against legacy SHA256 hash.
    SHA256 hashes were stored as 'sha256:hexdigest' or just plain hex.
    """
    try:
        if password_hash.startswith(LEGACY_SHA256_PREFIX):
            # Format: sha256:hexdigest
            stored_hash = password_hash[len(LEGACY_SHA256_PREFIX):]
        else:
            # Plain hex format (older implementation)
            stored_hash = password_hash

        # Hash the provided password using SHA256
        computed_hash = hashlib.sha256(password.encode()).hexdigest()

        # Constant-time comparison to prevent timing attacks
        return len(stored_hash) == len(computed_hash) and all(
            c1 == c2 for c1, c2 in zip(stored_hash, computed_hash)
        )
    except Exception:
        return False


def hash_password(password: str) -> str:
    """
    Hash a password using Argon2.

    Args:
        password: Plain text password to hash

    Returns:
        Hashed password in passlib format

    Example:
        >>> hashed = hash_password("mypassword123")
        >>> verify_password("mypassword123", hashed)
        True
    """
    if not isinstance(password, str):
        raise ValueError("Password must be a string")

    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")

    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> Tuple[bool, bool]:
    """
    Verify a password against a hash.
    Supports both new Argon2 hashes and legacy SHA256/PBKDF2 hashes.

    Args:
        password: Plain text password to verify
        password_hash: Stored password hash (any supported format)

    Returns:
        Tuple of (is_valid, needs_rehash)
        - is_valid: Whether the password matches the hash
        - needs_rehash: Whether the password should be re-hashed (legacy format)

    Example:
        >>> hashed = hash_password("mypassword123")
        >>> is_valid, needs_rehash = verify_password("mypassword123", hashed)
        >>> is_valid
        True
        >>> needs_rehash
        False
    """
    if not password_hash:
        return False, False

    try:
        # Check for legacy SHA256 format
        if _is_legacy_sha256(password_hash):
            is_valid = _verify_legacy_sha256(password, password_hash)
            return is_valid, is_valid  # If valid legacy hash, needs rehash

        # Try to verify with passlib (handles Argon2, PBKDF2, etc.)
        is_valid = pwd_context.verify(password, password_hash)

        # Check if rehash is needed (for non-Argon2 hashes)
        needs_rehash = pwd_context.needs_update(password_hash)

        return is_valid, needs_rehash

    except Exception:
        # Any exception means password doesn't match
        return False, False


def migrate_hash_if_needed(password: str, current_hash: str) -> Tuple[str, bool]:
    """
    Check if a hash needs migration and perform it if necessary.

    Args:
        password: Plain text password (typically just verified)
        current_hash: Current password hash

    Returns:
        Tuple of (new_hash, was_migrated)
        - new_hash: Updated hash (Argon2) or original hash
        - was_migrated: Whether migration occurred

    Example:
        >>> old_hash = "sha256:" + hashlib.sha256(b"test").hexdigest()
        >>> new_hash, migrated = migrate_hash_if_needed("test", old_hash)
        >>> migrated
        True
    """
    if not current_hash:
        return hash_password(password), True

    # Check if it's a legacy format
    if _is_legacy_sha256(current_hash) or _is_legacy_pbkdf2(current_hash):
        return hash_password(password), True

    # Check if passlib says it needs updating
    if pwd_context.needs_update(current_hash):
        return hash_password(password), True

    # Already using Argon2, no migration needed
    return current_hash, False


# ============================================================================
# Migration Helper: Bulk Check for Legacy Hashes
# ============================================================================

def count_legacy_hashes(hash_list: list) -> dict:
    """
    Analyze a list of password hashes and report migration status.

    Args:
        hash_list: List of password hashes from database

    Returns:
        Dictionary with migration statistics:
        {
            'total': int,
            'argon2': int,
            'pbkdf2': int,
            'sha256': int,
            'unknown': int,
        }
    """
    stats = {
        'total': len(hash_list),
        'argon2': 0,
        'pbkdf2': 0,
        'sha256': 0,
        'unknown': 0,
    }

    for h in hash_list:
        if not h:
            stats['unknown'] += 1
        elif _is_legacy_sha256(h):
            stats['sha256'] += 1
        elif _is_legacy_pbkdf2(h):
            stats['pbkdf2'] += 1
        elif h.startswith('$argon2'):
            stats['argon2'] += 1
        else:
            stats['unknown'] += 1

    return stats
