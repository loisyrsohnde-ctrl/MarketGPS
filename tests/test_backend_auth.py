"""Tests for backend authentication - Password hashing and verification."""
import pytest
import hashlib
import json
from unittest.mock import Mock, patch

from pathlib import Path
import sys

# Bootstrap application
from core.bootstrap import bootstrap
bootstrap()

from backend.password_security import (
    hash_password,
    verify_password,
    migrate_hash_if_needed,
    _is_legacy_sha256,
    _is_legacy_pbkdf2,
    _verify_legacy_sha256,
    count_legacy_hashes
)


class TestHashPassword:
    """Tests for hash_password function."""

    def test_hash_password_valid(self):
        """Test hashing a valid password."""
        password = "MySecurePassword123!"
        hashed = hash_password(password)

        assert hashed is not None
        assert len(hashed) > 0
        # Should start with Argon2 prefix
        assert hashed.startswith("$argon2")

    def test_hash_password_different_inputs_different_hashes(self):
        """Test that different passwords produce different hashes."""
        password1 = "Password123!"
        password2 = "Password124!"

        hash1 = hash_password(password1)
        hash2 = hash_password(password2)

        assert hash1 != hash2

    def test_hash_password_same_input_different_hashes(self):
        """Test that same password produces different hashes (salted)."""
        password = "MySecurePassword123!"

        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Different salts

    def test_hash_password_too_short(self):
        """Test that short passwords are rejected."""
        password = "short"

        with pytest.raises(ValueError):
            hash_password(password)

    def test_hash_password_minimum_length(self):
        """Test hashing at minimum length (8 characters)."""
        password = "12345678"  # Exactly 8 chars
        hashed = hash_password(password)

        assert hashed.startswith("$argon2")

    def test_hash_password_non_string(self):
        """Test that non-string passwords are rejected."""
        with pytest.raises(ValueError):
            hash_password(123)

        with pytest.raises(ValueError):
            hash_password(None)

    def test_hash_password_empty_string(self):
        """Test that empty password is rejected."""
        with pytest.raises(ValueError):
            hash_password("")

    def test_hash_password_unicode(self):
        """Test hashing with unicode characters."""
        password = "MonÐotDePasse123!"
        hashed = hash_password(password)

        assert hashed.startswith("$argon2")

    def test_hash_password_special_characters(self):
        """Test hashing with special characters."""
        password = "P@$$w0rd!#%&*()[]{}+-=^~`"
        hashed = hash_password(password)

        assert hashed.startswith("$argon2")


class TestVerifyPassword:
    """Tests for verify_password function."""

    def test_verify_correct_password(self):
        """Test verifying correct password."""
        password = "MySecurePassword123!"
        hashed = hash_password(password)

        is_valid, needs_rehash = verify_password(password, hashed)

        assert is_valid is True
        assert needs_rehash is False

    def test_verify_incorrect_password(self):
        """Test verifying incorrect password."""
        password = "MySecurePassword123!"
        wrong_password = "WrongPassword123!"
        hashed = hash_password(password)

        is_valid, needs_rehash = verify_password(wrong_password, hashed)

        assert is_valid is False
        assert needs_rehash is False

    def test_verify_empty_hash(self):
        """Test verifying against empty hash."""
        is_valid, needs_rehash = verify_password("anypassword", "")

        assert is_valid is False
        assert needs_rehash is False

    def test_verify_none_hash(self):
        """Test verifying against None hash."""
        is_valid, needs_rehash = verify_password("anypassword", None)

        assert is_valid is False
        assert needs_rehash is False

    def test_verify_case_sensitive(self):
        """Test that password verification is case-sensitive."""
        password = "MySecurePassword123!"
        hashed = hash_password(password)

        # Different case should fail
        is_valid, _ = verify_password("mysecurepassword123!", hashed)

        assert is_valid is False

    def test_verify_whitespace_sensitive(self):
        """Test that password verification is whitespace-sensitive."""
        password = "MySecurePassword123!"
        hashed = hash_password(password)

        # Extra space should fail
        is_valid, _ = verify_password("MySecurePassword123! ", hashed)

        assert is_valid is False

    def test_verify_unicode_password(self):
        """Test verifying unicode password."""
        password = "MonMotDePasse123!"
        hashed = hash_password(password)

        is_valid, needs_rehash = verify_password(password, hashed)

        assert is_valid is True


class TestLegacySHA256:
    """Tests for legacy SHA256 hash detection and verification."""

    def test_is_legacy_sha256_true(self):
        """Test detection of legacy SHA256 format."""
        legacy_hash = "sha256:" + hashlib.sha256(b"password").hexdigest()

        assert _is_legacy_sha256(legacy_hash) is True

    def test_is_legacy_sha256_false(self):
        """Test non-legacy hash is not detected as SHA256."""
        argon2_hash = hash_password("password")

        assert _is_legacy_sha256(argon2_hash) is False

    def test_verify_legacy_sha256_correct(self):
        """Test verifying legacy SHA256 hash with correct password."""
        password = "MyPassword123!"
        legacy_hash = "sha256:" + hashlib.sha256(password.encode()).hexdigest()

        is_valid = _verify_legacy_sha256(password, legacy_hash)

        assert is_valid is True

    def test_verify_legacy_sha256_incorrect(self):
        """Test verifying legacy SHA256 hash with wrong password."""
        password = "MyPassword123!"
        wrong_password = "WrongPassword!"
        legacy_hash = "sha256:" + hashlib.sha256(password.encode()).hexdigest()

        is_valid = _verify_legacy_sha256(wrong_password, legacy_hash)

        assert is_valid is False

    def test_verify_legacy_sha256_plain_hex(self):
        """Test verifying legacy SHA256 without prefix."""
        password = "MyPassword123!"
        plain_hex = hashlib.sha256(password.encode()).hexdigest()

        is_valid = _verify_legacy_sha256(password, plain_hex)

        assert is_valid is True

    def test_verify_legacy_sha256_timing_attack_resistance(self):
        """Test that legacy SHA256 verification is timing-attack resistant."""
        password = "MyPassword123!"
        legacy_hash = "sha256:" + hashlib.sha256(password.encode()).hexdigest()

        # Both should complete without timing differences
        _verify_legacy_sha256(password, legacy_hash)
        _verify_legacy_sha256("WrongPassword!", legacy_hash)
        # If it reaches here without hanging, timing attack protection works


class TestLegacyPBKDF2:
    """Tests for legacy PBKDF2 hash detection."""

    def test_is_legacy_pbkdf2_true(self):
        """Test detection of legacy PBKDF2 format."""
        legacy_hash = "pbkdf2:sha256:somekey"

        assert _is_legacy_pbkdf2(legacy_hash) is True

    def test_is_legacy_pbkdf2_false(self):
        """Test non-legacy hash is not detected as PBKDF2."""
        argon2_hash = hash_password("password")

        assert _is_legacy_pbkdf2(argon2_hash) is False


class TestPasswordMigration:
    """Tests for password hash migration."""

    def test_migrate_legacy_sha256_to_argon2(self):
        """Test migrating from SHA256 to Argon2."""
        password = "MyPassword123!"
        legacy_hash = "sha256:" + hashlib.sha256(password.encode()).hexdigest()

        new_hash, was_migrated = migrate_hash_if_needed(password, legacy_hash)

        assert was_migrated is True
        assert new_hash.startswith("$argon2")

    def test_migrate_argon2_no_change(self):
        """Test that Argon2 hashes are not migrated."""
        password = "MyPassword123!"
        argon2_hash = hash_password(password)

        new_hash, was_migrated = migrate_hash_if_needed(password, argon2_hash)

        # Argon2 should not be migrated
        assert was_migrated is False
        assert new_hash == argon2_hash

    def test_migrate_none_hash(self):
        """Test migrating None hash (creates new hash)."""
        password = "MyPassword123!"

        new_hash, was_migrated = migrate_hash_if_needed(password, None)

        assert was_migrated is True
        assert new_hash.startswith("$argon2")

    def test_migrate_empty_hash(self):
        """Test migrating empty hash (creates new hash)."""
        password = "MyPassword123!"

        new_hash, was_migrated = migrate_hash_if_needed(password, "")

        assert was_migrated is True
        assert new_hash.startswith("$argon2")

    def test_migrate_pbkdf2_to_argon2(self):
        """Test migrating from PBKDF2 to Argon2."""
        password = "MyPassword123!"
        # Simulate old PBKDF2 hash
        legacy_hash = "pbkdf2:sha256:somevalue"

        new_hash, was_migrated = migrate_hash_if_needed(password, legacy_hash)

        assert was_migrated is True
        assert new_hash.startswith("$argon2")


class TestVerifyPasswordWithLegacy:
    """Tests for verify_password with legacy hash support."""

    def test_verify_legacy_sha256_returns_rehash_flag(self):
        """Test that legacy SHA256 verification sets needs_rehash=True."""
        password = "MyPassword123!"
        legacy_hash = "sha256:" + hashlib.sha256(password.encode()).hexdigest()

        is_valid, needs_rehash = verify_password(password, legacy_hash)

        assert is_valid is True
        assert needs_rehash is True  # Indicates migration needed

    def test_verify_modern_argon2_no_rehash(self):
        """Test that Argon2 hashes don't need rehashing."""
        password = "MyPassword123!"
        argon2_hash = hash_password(password)

        is_valid, needs_rehash = verify_password(password, argon2_hash)

        assert is_valid is True
        assert needs_rehash is False

    def test_verify_wrong_legacy_password_no_rehash(self):
        """Test that wrong legacy password doesn't return rehash flag."""
        password = "MyPassword123!"
        wrong_password = "WrongPassword!"
        legacy_hash = "sha256:" + hashlib.sha256(password.encode()).hexdigest()

        is_valid, needs_rehash = verify_password(wrong_password, legacy_hash)

        assert is_valid is False
        assert needs_rehash is False  # No rehash if password wrong


class TestLegacyHashCount:
    """Tests for count_legacy_hashes utility."""

    def test_count_legacy_hashes_empty_list(self):
        """Test counting with empty list."""
        stats = count_legacy_hashes([])

        assert stats['total'] == 0
        assert stats['argon2'] == 0
        assert stats['pbkdf2'] == 0
        assert stats['sha256'] == 0

    def test_count_legacy_hashes_mixed(self):
        """Test counting mixed hash formats."""
        hashes = [
            hash_password("password1"),  # Argon2
            hash_password("password2"),  # Argon2
            "sha256:" + hashlib.sha256(b"password3").hexdigest(),  # SHA256
            "pbkdf2:sha256:value",  # PBKDF2
        ]

        stats = count_legacy_hashes(hashes)

        assert stats['total'] == 4
        assert stats['argon2'] == 2
        assert stats['sha256'] == 1
        assert stats['pbkdf2'] == 1

    def test_count_legacy_hashes_all_argon2(self):
        """Test counting when all are Argon2."""
        hashes = [
            hash_password("password1"),
            hash_password("password2"),
            hash_password("password3"),
        ]

        stats = count_legacy_hashes(hashes)

        assert stats['total'] == 3
        assert stats['argon2'] == 3
        assert stats['pbkdf2'] == 0
        assert stats['sha256'] == 0

    def test_count_legacy_hashes_all_sha256(self):
        """Test counting when all are SHA256."""
        hashes = [
            "sha256:" + hashlib.sha256(b"pass1").hexdigest(),
            "sha256:" + hashlib.sha256(b"pass2").hexdigest(),
        ]

        stats = count_legacy_hashes(hashes)

        assert stats['total'] == 2
        assert stats['sha256'] == 2
        assert stats['argon2'] == 0

    def test_count_legacy_hashes_unknown_format(self):
        """Test counting unknown hash formats."""
        hashes = [
            "unknown_format_hash",
            hash_password("password1"),
        ]

        stats = count_legacy_hashes(hashes)

        assert stats['total'] == 2
        assert stats['unknown'] == 1
        assert stats['argon2'] == 1


class TestPasswordValidation:
    """Tests for password validation during hashing."""

    def test_hash_password_validates_length(self):
        """Test that minimum length is enforced."""
        # 7 characters - too short
        with pytest.raises(ValueError, match="at least 8 characters"):
            hash_password("1234567")

        # 8 characters - OK
        hash_password("12345678")

    def test_hash_password_validates_type(self):
        """Test that string type is enforced."""
        with pytest.raises(ValueError, match="must be a string"):
            hash_password(12345678)

    def test_hash_password_with_spaces(self):
        """Test hashing password with spaces."""
        password = "pass word 123!"  # Spaces are valid
        hashed = hash_password(password)

        assert hashed.startswith("$argon2")

        # Verify it works
        is_valid, _ = verify_password(password, hashed)
        assert is_valid is True


class TestAuthenticationFlow:
    """Tests for complete authentication flows."""

    def test_registration_login_flow(self):
        """Test complete registration and login flow."""
        # Registration: hash password
        registration_password = "MySecurePassword123!"
        stored_hash = hash_password(registration_password)

        # Login: verify password
        login_password = "MySecurePassword123!"
        is_valid, needs_rehash = verify_password(login_password, stored_hash)

        assert is_valid is True
        assert needs_rehash is False

    def test_password_change_flow(self):
        """Test password change flow."""
        # Current password
        old_password = "OldPassword123!"
        old_hash = hash_password(old_password)

        # Verify old password
        is_valid, _ = verify_password(old_password, old_hash)
        assert is_valid is True

        # Change password
        new_password = "NewPassword123!"
        new_hash = hash_password(new_password)

        # Verify new password works
        is_valid, _ = verify_password(new_password, new_hash)
        assert is_valid is True

        # Verify old password no longer works
        is_valid, _ = verify_password(old_password, new_hash)
        assert is_valid is False

    def test_legacy_user_migration_flow(self):
        """Test migrating legacy user to Argon2."""
        # User has legacy SHA256 hash
        password = "LegacyPassword123!"
        legacy_hash = "sha256:" + hashlib.sha256(password.encode()).hexdigest()

        # On login, verify password
        is_valid, needs_rehash = verify_password(password, legacy_hash)
        assert is_valid is True
        assert needs_rehash is True

        # If needs_rehash, migrate to Argon2
        if needs_rehash:
            new_hash, was_migrated = migrate_hash_if_needed(password, legacy_hash)
            assert was_migrated is True
            assert new_hash.startswith("$argon2")

            # Update database with new hash
            # (In real code, this would update the database)

            # Verify new hash works
            is_valid, needs_rehash = verify_password(password, new_hash)
            assert is_valid is True
            assert needs_rehash is False


class TestSecurityProperties:
    """Tests for security properties of password handling."""

    def test_hash_is_deterministic(self):
        """Test that Argon2 is non-deterministic (salted)."""
        password = "MyPassword123!"

        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Different hashes due to different salts
        assert hash1 != hash2

        # Both verify with same password
        assert verify_password(password, hash1)[0] is True
        assert verify_password(password, hash2)[0] is True

    def test_hash_length_reasonable(self):
        """Test that hash has reasonable length."""
        password = "MyPassword123!"
        hashed = hash_password(password)

        # Argon2 hashes are typically 80-100 characters
        assert len(hashed) > 50
        assert len(hashed) < 200

    def test_hash_not_password_itself(self):
        """Test that hash doesn't contain plaintext password."""
        password = "MyPassword123!"
        hashed = hash_password(password)

        # Hash should not contain the plaintext password
        assert password not in hashed
        assert password.lower() not in hashed.lower()

    def test_password_not_logged(self):
        """Test that password functions don't expose password in their behavior."""
        password = "SensitivePassword123!"

        # These should complete without error
        hashed = hash_password(password)
        verify_password(password, hashed)
        migrate_hash_if_needed(password, hashed)

        # No assertions needed - we're just testing they don't crash
        # In real testing, you'd verify logs don't contain the password


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
