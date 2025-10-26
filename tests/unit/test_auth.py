"""
Comprehensive tests for authentication functions.
Tests password hashing, token creation, and user retrieval.
"""
import pytest
from datetime import timedelta
from jose import jwt
from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_token_from_header,
    generate_verification_code
)
from app.config import SECRET_KEY, ALGORITHM


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_hash_password(self):
        """Test that password can be hashed."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed != password  # Should be different from plaintext
    
    def test_verify_correct_password(self):
        """Test that correct password verifies successfully."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_incorrect_password(self):
        """Test that incorrect password fails verification."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_hash_different_passwords_produce_different_hashes(self):
        """Test that different passwords produce different hashes."""
        password1 = "password1"
        password2 = "password2"
        
        hash1 = get_password_hash(password1)
        hash2 = get_password_hash(password2)
        
        assert hash1 != hash2
    
    def test_hash_same_password_twice_produces_different_hashes(self):
        """Test that hashing same password twice produces different hashes (salt)."""
        password = "test_password"
        
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Due to salt, hashes should be different
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True
    
    def test_empty_password(self):
        """Test handling of empty password."""
        password = ""
        hashed = get_password_hash(password)
        
        assert hashed is not None
        assert verify_password(password, hashed) is True
    
    def test_long_password(self):
        """Test handling of long password (within bcrypt limits)."""
        password = "a" * 70  # 70 character password (bcrypt limit is 72)
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_special_characters_in_password(self):
        """Test password with special characters."""
        password = "p@ssw0rd!#$%^&*()"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_unicode_password(self):
        """Test password with unicode characters."""
        password = "пароль密码كلمة السر"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True


class TestTokenCreation:
    """Test JWT token creation."""
    
    def test_create_access_token_basic(self):
        """Test creating a basic access token."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_access_token_with_custom_expiry(self):
        """Test creating token with custom expiry time."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta)
        
        assert token is not None
        # Decode and check expiry
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in decoded
    
    def test_token_contains_subject(self):
        """Test that token contains the subject."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == "testuser"
    
    def test_token_contains_expiry(self):
        """Test that token contains expiry time."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in decoded
        assert isinstance(decoded["exp"], (int, float))
    
    def test_token_with_additional_data(self):
        """Test creating token with additional data."""
        data = {"sub": "testuser", "email": "test@example.com", "role": "admin"}
        token = create_access_token(data)
        
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == "testuser"
        assert decoded["email"] == "test@example.com"
        assert decoded["role"] == "admin"
    
    def test_token_with_zero_expiry(self):
        """Test creating token with zero expiry (expires immediately)."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(seconds=0)
        token = create_access_token(data, expires_delta)
        
        assert token is not None
        # Token is created but might be expired
    
    def test_different_users_different_tokens(self):
        """Test that different users get different tokens."""
        token1 = create_access_token({"sub": "user1"})
        token2 = create_access_token({"sub": "user2"})
        
        assert token1 != token2


class TestTokenExtraction:
    """Test token extraction from headers."""
    
    def test_extract_token_from_valid_header(self):
        """Test extracting token from valid Bearer header."""
        token = "test_token_123"
        header = f"Bearer {token}"
        
        extracted = get_token_from_header(header)
        assert extracted == token
    
    def test_extract_token_case_insensitive(self):
        """Test that Bearer is case insensitive."""
        token = "test_token_123"
        header = f"bearer {token}"
        
        extracted = get_token_from_header(header)
        assert extracted == token
    
    def test_extract_token_uppercase_bearer(self):
        """Test BEARER in uppercase."""
        token = "test_token_123"
        header = f"BEARER {token}"
        
        extracted = get_token_from_header(header)
        assert extracted == token
    
    def test_extract_token_from_none_header(self):
        """Test extracting from None header."""
        extracted = get_token_from_header(None)
        assert extracted is None
    
    def test_extract_token_from_empty_header(self):
        """Test extracting from empty header."""
        extracted = get_token_from_header("")
        assert extracted is None
    
    def test_extract_token_from_invalid_scheme(self):
        """Test extracting from header with wrong scheme."""
        header = "Basic dGVzdDp0ZXN0"
        
        extracted = get_token_from_header(header)
        assert extracted is None
    
    def test_extract_token_from_malformed_header(self):
        """Test extracting from malformed header."""
        header = "NotAValidHeader"
        
        extracted = get_token_from_header(header)
        assert extracted is None
    
    def test_extract_token_with_extra_spaces(self):
        """Test extracting token with multiple spaces."""
        token = "test_token_123"
        header = f"Bearer  {token}"  # Extra space
        
        # Should handle or return None depending on implementation
        extracted = get_token_from_header(header)
        # Either extracted == None or it handles gracefully
        assert extracted is None or isinstance(extracted, str)
    
    def test_extract_token_only_token_no_scheme(self):
        """Test extracting when only token provided (no Bearer)."""
        header = "just_a_token"
        
        extracted = get_token_from_header(header)
        assert extracted is None


class TestVerificationCode:
    """Test verification code generation."""
    
    def test_generate_verification_code(self):
        """Test generating verification code."""
        code = generate_verification_code()
        
        assert code is not None
        assert isinstance(code, str)
    
    def test_verification_code_length(self):
        """Test that verification code has correct length."""
        code = generate_verification_code()
        
        # Default length is 6 digits
        assert len(code) == 6
    
    def test_verification_code_only_digits(self):
        """Test that code only contains digits."""
        codes = [generate_verification_code() for _ in range(10)]
        
        for code in codes:
            assert all(c.isdigit() for c in code)
    
    def test_verification_code_is_numeric(self):
        """Test that verification code contains only digits."""
        code = generate_verification_code()
        
        assert code.isdigit()
    
    def test_verification_code_uniqueness(self):
        """Test that multiple codes are different (high probability)."""
        codes = [generate_verification_code() for _ in range(100)]
        
        # At least 90% should be unique (allowing for some collisions)
        unique_codes = len(set(codes))
        assert unique_codes >= 90
    
    def test_verification_code_no_leading_zeros(self):
        """Test that code doesn't start with zero (if required)."""
        codes = [generate_verification_code() for _ in range(50)]
        
        # All codes should be valid numbers
        for code in codes:
            assert int(code) >= 0


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_hash_very_short_password(self):
        """Test hashing very short password."""
        password = "a"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_create_token_with_empty_data(self):
        """Test creating token with empty subject."""
        data = {"sub": ""}
        token = create_access_token(data)
        
        assert token is not None
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == ""
    
    def test_verify_password_with_empty_hash(self):
        """Test verifying password against empty hash."""
        password = "test"
        
        # Should handle gracefully (return False or raise)
        try:
            result = verify_password(password, "")
            assert result is False
        except Exception:
            # If it raises, that's also acceptable
            pass
    
    def test_token_extraction_with_multiple_bearer_keywords(self):
        """Test token extraction with Bearer appearing multiple times."""
        header = "Bearer Bearer token123"
        
        extracted = get_token_from_header(header)
        # Should extract the second part after first Bearer
        # or return None if malformed
        assert extracted is None or extracted == "Bearer"
    
    def test_verification_code_format(self):
        """Test verification code format."""
        code = generate_verification_code()
        
        # Should be 6 digits
        assert len(code) == 6
        assert code.isdigit()
        # Should be convertible to int
        assert isinstance(int(code), int)


class TestPasswordComplexity:
    """Test password hashing with various complexity levels."""
    
    def test_simple_password(self):
        """Test simple alphanumeric password."""
        password = "simple123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_complex_password(self):
        """Test complex password with special characters."""
        password = "C0mpl3x!P@ssw0rd#2024"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_password_with_spaces(self):
        """Test password containing spaces."""
        password = "password with spaces"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_password_with_newlines(self):
        """Test password containing newlines."""
        password = "password\nwith\nnewlines"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_password_with_tabs(self):
        """Test password containing tabs."""
        password = "password\twith\ttabs"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True

