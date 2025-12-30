# ABOUTME: Unit tests for Claude authentication detection utility
# ABOUTME: Tests credential priority, detection logic, and error handling

import pytest

from src.investigator.core.auth_detector import (
    get_claude_authentication,
    validate_claude_credentials,
)


class TestClaudeAuthenticationDetection:
    """Test suite for Claude authentication credential detection."""

    def test_oauth_token_from_claude_code_env_var(self, monkeypatch):
        """Should detect OAuth token from CLAUDE_CODE_OAUTH_TOKEN (highest priority)."""
        monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "test-oauth-token-123")

        result = get_claude_authentication()

        assert result["method"] == "oauth"
        assert result["token"] == "test-oauth-token-123"
        assert result["use_cli"] is True

    def test_oauth_token_from_claude_env_var(self, monkeypatch):
        """Should detect OAuth token from CLAUDE_OAUTH_TOKEN (second priority)."""
        monkeypatch.setenv("CLAUDE_OAUTH_TOKEN", "test-oauth-token-456")

        result = get_claude_authentication()

        assert result["method"] == "oauth"
        assert result["token"] == "test-oauth-token-456"
        assert result["use_cli"] is True

    def test_api_key_fallback(self, monkeypatch):
        """Should fall back to ANTHROPIC_API_KEY when no OAuth token present."""
        monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
        monkeypatch.delenv("CLAUDE_OAUTH_TOKEN", raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-api-key-789")

        result = get_claude_authentication()

        assert result["method"] == "api_key"
        assert result["token"] == "sk-ant-api-key-789"
        assert result["use_cli"] is False

    def test_oauth_priority_over_api_key(self, monkeypatch):
        """Should prefer CLAUDE_CODE_OAUTH_TOKEN over API key when both present."""
        monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "oauth-wins")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "api-key-loses")

        result = get_claude_authentication()

        assert result["method"] == "oauth"
        assert result["token"] == "oauth-wins"
        assert result["use_cli"] is True

    def test_claude_oauth_priority_over_api_key(self, monkeypatch):
        """Should prefer CLAUDE_OAUTH_TOKEN over API key when both present."""
        monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
        monkeypatch.setenv("CLAUDE_OAUTH_TOKEN", "oauth-second-priority")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "api-key-loses-again")

        result = get_claude_authentication()

        assert result["method"] == "oauth"
        assert result["token"] == "oauth-second-priority"
        assert result["use_cli"] is True

    def test_claude_code_oauth_priority_over_claude_oauth(self, monkeypatch):
        """Should prefer CLAUDE_CODE_OAUTH_TOKEN over CLAUDE_OAUTH_TOKEN."""
        monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "code-oauth-wins")
        monkeypatch.setenv("CLAUDE_OAUTH_TOKEN", "claude-oauth-loses")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "api-key-also-loses")

        result = get_claude_authentication()

        assert result["method"] == "oauth"
        assert result["token"] == "code-oauth-wins"
        assert result["use_cli"] is True

    def test_no_credentials_raises_error(self, monkeypatch):
        """Should raise clear error when no credentials found."""
        monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
        monkeypatch.delenv("CLAUDE_OAUTH_TOKEN", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with pytest.raises(ValueError) as exc_info:
            get_claude_authentication()

        error_message = str(exc_info.value)
        assert "No Claude authentication credentials found" in error_message
        assert "CLAUDE_CODE_OAUTH_TOKEN" in error_message
        assert "CLAUDE_OAUTH_TOKEN" in error_message
        assert "ANTHROPIC_API_KEY" in error_message

    def test_empty_oauth_token_falls_through(self, monkeypatch):
        """Should treat empty OAuth token as missing and check next priority."""
        monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "")
        monkeypatch.setenv("CLAUDE_OAUTH_TOKEN", "")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fallback")

        result = get_claude_authentication()

        assert result["method"] == "api_key"
        assert result["token"] == "sk-ant-fallback"

    def test_whitespace_only_token_treated_as_empty(self, monkeypatch):
        """Should treat whitespace-only tokens as missing."""
        monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "   ")
        monkeypatch.delenv("CLAUDE_OAUTH_TOKEN", raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-valid")

        result = get_claude_authentication()

        assert result["method"] == "api_key"
        assert result["token"] == "sk-ant-valid"

    def test_return_type_structure(self, monkeypatch):
        """Should return dict with correct keys and types."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")

        result = get_claude_authentication()

        assert isinstance(result, dict)
        assert set(result.keys()) == {"method", "token", "use_cli"}
        assert isinstance(result["method"], str)
        assert isinstance(result["token"], str)
        assert isinstance(result["use_cli"], bool)


class TestClaudeCredentialsValidation:
    """Test suite for Claude credential validation."""

    def test_valid_oauth_token_min_length(self):
        """Should validate OAuth token with minimum valid length (50 chars)."""
        token = "sk-ant-oat01-" + "a" * (50 - len("sk-ant-oat01-"))
        auth_result = {"method": "oauth", "token": token}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is True
        assert result["method"] == "oauth"
        assert result["token"] == token
        assert (
            "valid" in result["message"].lower()
            or "success" in result["message"].lower()
        )

    def test_valid_oauth_token_max_length(self):
        """Should validate OAuth token with maximum valid length (200 chars)."""
        token = "sk-ant-oat01-" + "a" * (200 - len("sk-ant-oat01-"))
        auth_result = {"method": "oauth", "token": token}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is True
        assert result["method"] == "oauth"
        assert result["token"] == token

    def test_valid_oauth_token_mid_length(self):
        """Should validate OAuth token with mid-range length."""
        token = "sk-ant-oat01-" + "a" * 100
        auth_result = {"method": "oauth", "token": token}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is True
        assert result["method"] == "oauth"
        assert result["token"] == token

    def test_valid_api_key_min_length(self):
        """Should validate API key with minimum valid length (50 chars)."""
        token = "sk-ant-api03-" + "a" * (50 - len("sk-ant-api03-"))
        auth_result = {"method": "api_key", "token": token}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is True
        assert result["method"] == "api_key"
        assert result["token"] == token

    def test_valid_api_key_max_length(self):
        """Should validate API key with maximum valid length (200 chars)."""
        token = "sk-ant-api03-" + "a" * (200 - len("sk-ant-api03-"))
        auth_result = {"method": "api_key", "token": token}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is True
        assert result["method"] == "api_key"
        assert result["token"] == token

    def test_valid_api_key_mid_length(self):
        """Should validate API key with mid-range length."""
        token = "sk-ant-api03-" + "a" * 100
        auth_result = {"method": "api_key", "token": token}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is True
        assert result["method"] == "api_key"
        assert result["token"] == token

    def test_invalid_oauth_wrong_prefix(self):
        """Should reject OAuth token with wrong prefix."""
        token = "sk-ant-api03-" + "a" * 50
        auth_result = {"method": "oauth", "token": token}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert result["method"] == "oauth"
        assert result["token"] == token
        assert "sk-ant-oat01-" in result["message"]
        assert "claude setup-token" in result["message"].lower()

    def test_invalid_api_key_wrong_prefix(self):
        """Should reject API key with wrong prefix."""
        token = "sk-ant-oat01-" + "a" * 50
        auth_result = {"method": "api_key", "token": token}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert result["method"] == "api_key"
        assert result["token"] == token
        assert "sk-ant-api03-" in result["message"]
        assert "console.anthropic.com" in result["message"]

    def test_invalid_oauth_too_short(self):
        """Should reject OAuth token that is too short (< 50 chars)."""
        token = "sk-ant-oat01-short"
        auth_result = {"method": "oauth", "token": token}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert result["method"] == "oauth"
        assert result["token"] == token
        assert "50" in result["message"] or "length" in result["message"].lower()
        assert "claude setup-token" in result["message"].lower()

    def test_invalid_oauth_too_long(self):
        """Should reject OAuth token that is too long (> 200 chars)."""
        token = "sk-ant-oat01-" + "a" * 200
        auth_result = {"method": "oauth", "token": token}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert result["method"] == "oauth"
        assert result["token"] == token
        assert "200" in result["message"] or "length" in result["message"].lower()

    def test_invalid_api_key_too_short(self):
        """Should reject API key that is too short (< 50 chars)."""
        token = "sk-ant-api03-short"
        auth_result = {"method": "api_key", "token": token}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert result["method"] == "api_key"
        assert result["token"] == token
        assert "50" in result["message"] or "length" in result["message"].lower()
        assert "console.anthropic.com" in result["message"]

    def test_invalid_api_key_too_long(self):
        """Should reject API key that is too long (> 200 chars)."""
        token = "sk-ant-api03-" + "a" * 200
        auth_result = {"method": "api_key", "token": token}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert result["method"] == "api_key"
        assert result["token"] == token
        assert "200" in result["message"] or "length" in result["message"].lower()

    def test_invalid_oauth_empty_string(self):
        """Should reject empty OAuth token."""
        auth_result = {"method": "oauth", "token": ""}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert result["method"] == "oauth"
        assert result["token"] == ""
        assert "claude setup-token" in result["message"].lower()

    def test_invalid_api_key_empty_string(self):
        """Should reject empty API key."""
        auth_result = {"method": "api_key", "token": ""}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert result["method"] == "api_key"
        assert result["token"] == ""
        assert "console.anthropic.com" in result["message"]

    def test_invalid_oauth_none_token(self):
        """Should reject OAuth token that is None."""
        auth_result = {"method": "oauth", "token": None}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert result["method"] == "oauth"
        assert result["token"] is None
        assert "claude setup-token" in result["message"].lower()

    def test_invalid_api_key_none_token(self):
        """Should reject API key that is None."""
        auth_result = {"method": "api_key", "token": None}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert result["method"] == "api_key"
        assert result["token"] is None
        assert "console.anthropic.com" in result["message"]

    def test_missing_method_field(self):
        """Should handle missing 'method' field gracefully."""
        auth_result = {"token": "sk-ant-oat01-" + "a" * 50}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert (
            "method" in result["message"].lower()
            or "missing" in result["message"].lower()
        )

    def test_missing_token_field(self):
        """Should handle missing 'token' field gracefully."""
        auth_result = {"method": "oauth"}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert (
            "token" in result["message"].lower()
            or "missing" in result["message"].lower()
        )

    def test_invalid_method_value(self):
        """Should reject invalid method value."""
        auth_result = {"method": "invalid_method", "token": "sk-ant-oat01-" + "a" * 50}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert result["method"] == "invalid_method"
        assert (
            "oauth" in result["message"].lower()
            or "api_key" in result["message"].lower()
        )

    def test_non_string_token(self):
        """Should handle non-string token gracefully."""
        auth_result = {"method": "oauth", "token": 12345}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert result["method"] == "oauth"
        assert result["token"] == 12345

    def test_return_structure(self):
        """Should return dict with correct structure."""
        token = "sk-ant-oat01-" + "a" * 50
        auth_result = {"method": "oauth", "token": token}

        result = validate_claude_credentials(auth_result)

        assert isinstance(result, dict)
        assert set(result.keys()) == {"valid", "message", "method", "token"}
        assert isinstance(result["valid"], bool)
        assert isinstance(result["message"], str)
        assert isinstance(result["method"], str)
        assert isinstance(result["token"], str)

    def test_oauth_token_with_special_chars(self):
        """Should validate OAuth token containing alphanumeric, hyphens, underscores."""
        token = "sk-ant-oat01-" + "a" * 20 + "-" + "b" * 10 + "_" + "c" * 10
        auth_result = {"method": "oauth", "token": token}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is True
        assert result["method"] == "oauth"
        assert result["token"] == token

    def test_api_key_with_special_chars(self):
        """Should validate API key containing alphanumeric, hyphens, underscores."""
        token = "sk-ant-api03-" + "a" * 20 + "-" + "b" * 10 + "_" + "c" * 10
        auth_result = {"method": "api_key", "token": token}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is True
        assert result["method"] == "api_key"
        assert result["token"] == token
