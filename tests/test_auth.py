"""
DataPulse Authentication Tests

Unit tests for user authentication, JWT tokens, and email validation.
Tests for A4 (JWT Cross-Platform), A5 (Email Validation) fixes.
"""

import os
import sys

import pytest

# Add project path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.auth import (
    MIN_PASSWORD_LENGTH,
    create_access_token,
    hash_password,
    validate_email,
    verify_access_token,
    verify_password,
)


class TestEmailValidation:
    """Test per validazione email (A5 fix)."""

    def test_valid_email(self):
        """Email valide devono passare."""
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.com",
            "user123@example.co.uk",
            "a@b.co",
        ]
        for email in valid_emails:
            is_valid, msg = validate_email(email)
            assert is_valid == True, f"{email} should be valid: {msg}"

    def test_invalid_email_format(self):
        """Email con formato non valido devono essere rifiutate."""
        invalid_emails = [
            "notanemail",
            "missing@domain",
            "@nodomain.com",
            "no@.com",
            "spaces in@email.com",
            "double..dots@email.com",
            ".startswith@dot.com",
            "endswith.@dot.com",
        ]
        for email in invalid_emails:
            is_valid, msg = validate_email(email)
            assert is_valid == False, f"{email} should be invalid"

    def test_empty_email(self):
        """Email vuota deve essere rifiutata."""
        is_valid, msg = validate_email("")
        assert is_valid == False
        assert "required" in msg.lower()

    def test_none_email(self):
        """Email None deve essere rifiutata."""
        is_valid, msg = validate_email(None)
        assert is_valid == False

    def test_email_too_short(self):
        """Email troppo corta deve essere rifiutata."""
        is_valid, msg = validate_email("a@b")
        assert is_valid == False

    def test_email_too_long(self):
        """Email troppo lunga (>254 chars) deve essere rifiutata."""
        long_email = "a" * 250 + "@example.com"
        is_valid, msg = validate_email(long_email)
        assert is_valid == False
        assert "long" in msg.lower()

    def test_email_consecutive_dots(self):
        """Email con punti consecutivi deve essere rifiutata."""
        is_valid, msg = validate_email("user..name@example.com")
        assert is_valid == False
        assert "dots" in msg.lower() or "consecutive" in msg.lower()

    def test_email_case_insensitive(self):
        """Email deve essere case-insensitive."""
        is_valid1, _ = validate_email("User@Example.COM")
        is_valid2, _ = validate_email("user@example.com")
        assert is_valid1 == is_valid2 == True


class TestPasswordHashing:
    """Test per hashing password."""

    def test_hash_password(self):
        """Password deve essere hashata correttamente."""
        password = "SecurePassword123"
        hashed = hash_password(password)

        assert hashed != password
        assert "$" in hashed  # Format: salt$hash
        assert len(hashed) > 50  # Salt + hash

    def test_verify_correct_password(self):
        """Password corretta deve essere verificata."""
        password = "SecurePassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) == True

    def test_verify_wrong_password(self):
        """Password errata deve fallire verifica."""
        hashed = hash_password("CorrectPassword")

        assert verify_password("WrongPassword", hashed) == False

    def test_verify_empty_password(self):
        """Password vuota deve fallire verifica."""
        hashed = hash_password("SomePassword")

        assert verify_password("", hashed) == False

    def test_verify_invalid_hash(self):
        """Hash non valido deve fallire verifica."""
        assert verify_password("password", "invalid_hash") == False
        assert verify_password("password", "") == False
        assert verify_password("password", None) == False

    def test_hash_uniqueness(self):
        """Ogni hash deve essere unico (salt diverso)."""
        password = "SamePassword"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Different salts


class TestJWTTokens:
    """Test per JWT token generation e validation."""

    def test_create_access_token(self):
        """Token deve essere creato correttamente."""
        token = create_access_token(user_id=1, email="test@example.com")

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are long

    def test_verify_valid_token(self):
        """Token valido deve essere verificato."""
        token = create_access_token(user_id=42, email="user@test.com")
        payload = verify_access_token(token)

        assert payload is not None
        assert payload["sub"] == "42"
        assert payload["email"] == "user@test.com"
        assert payload["type"] == "access"

    def test_verify_invalid_token(self):
        """Token non valido deve fallire."""
        result = verify_access_token("invalid.token.here")
        assert result is None

    def test_verify_empty_token(self):
        """Token vuoto deve fallire."""
        result = verify_access_token("")
        assert result is None

    def test_verify_modified_token(self):
        """Token modificato deve fallire."""
        token = create_access_token(user_id=1, email="test@example.com")
        # Modify the token
        modified = token[:-5] + "XXXXX"

        result = verify_access_token(modified)
        assert result is None


class TestPasswordRequirements:
    """Test per requisiti password."""

    def test_min_password_length_defined(self):
        """MIN_PASSWORD_LENGTH deve essere definito."""
        assert MIN_PASSWORD_LENGTH >= 8  # Security minimum


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
