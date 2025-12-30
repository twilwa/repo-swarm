# ABOUTME: Unit tests for auth_detector.py authentication detection logic
# ABOUTME: Tests OAuth and API key detection with priority ordering and error handling

import pytest
import os
from src.investigator.core.auth_detector import (
    get_claude_authentication,
    validate_claude_credentials,
    SK_ANT_OAT01_PREFIX,
    SK_ANT_API03_PREFIX,
    MIN_TOKEN_LENGTH,
    MAX_TOKEN_LENGTH,
)


class TestOAuthTokenDetection:
    """Test OAuth token detection from environment variables."""

    def test_claude_code_oauth_token_detection(self, monkeypatch):
        """Test detection of CLAUDE_CODE_OAUTH_TOKEN (highest priority)."""
        valid_token = "sk-ant-oat01-" + "a" * 50
        monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", valid_token)

        result = get_claude_authentication()

        assert result["method"] == "oauth"
        assert result["token"] == valid_token
        assert result["use_cli"] is True

    def test_claude_oauth_token_detection(self, monkeypatch):
        """Test detection of CLAUDE_OAUTH_TOKEN (second priority)."""
        valid_token = "sk-ant-oat01-" + "b" * 50
        monkeypatch.setenv("CLAUDE_OAUTH_TOKEN", valid_token)
        monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)

        result = get_claude_authentication()

        assert result["method"] == "oauth"
        assert result["token"] == valid_token
        assert result["use_cli"] is True

    def test_oauth_token_with_whitespace_stripped(self, monkeypatch):
        """Test that OAuth tokens are stripped of leading/trailing whitespace."""
        valid_token = "sk-ant-oat01-" + "c" * 50
        monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", f"  {valid_token}  ")

        result = get_claude_authentication()

        assert result["token"] == valid_token  # Should be stripped


class TestAPIKeyDetection:
    """Test API key detection from ANTHROPIC_API_KEY."""

    def test_api_key_detection(self, monkeypatch):
        """Test detection of ANTHROPIC_API_KEY (fallback)."""
        valid_key = "sk-ant-api03-" + "x" * 50
        monkeypatch.setenv("ANTHROPIC_API_KEY", valid_key)
        monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
        monkeypatch.delenv("CLAUDE_OAUTH_TOKEN", raising=False)

        result = get_claude_authentication()

        assert result["method"] == "api_key"
        assert result["token"] == valid_key
        assert result["use_cli"] is False

    def test_api_key_with_whitespace_stripped(self, monkeypatch):
        """Test that API keys are stripped of leading/trailing whitespace."""
        valid_key = "sk-ant-api03-" + "y" * 50
        monkeypatch.setenv("ANTHROPIC_API_KEY", f"\t{valid_key}\n")
        monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
        monkeypatch.delenv("CLAUDE_OAUTH_TOKEN", raising=False)

        result = get_claude_authentication()

        assert result["token"] == valid_key  # Should be stripped


class TestPriorityOrder:
    """Test priority ordering of authentication methods."""

    def test_claude_code_oauth_over_claude_oauth(self, monkeypatch):
        """Test that CLAUDE_CODE_OAUTH_TOKEN takes priority over CLAUDE_OAUTH_TOKEN."""
        code_token = "sk-ant-oat01-" + "a" * 50
        oauth_token = "sk-ant-oat01-" + "b" * 50

        monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", code_token)
        monkeypatch.setenv("CLAUDE_OAUTH_TOKEN", oauth_token)

        result = get_claude_authentication()

        assert result["token"] == code_token
        assert result["method"] == "oauth"

    def test_claude_code_oauth_over_api_key(self, monkeypatch):
        """Test that CLAUDE_CODE_OAUTH_TOKEN takes priority over ANTHROPIC_API_KEY."""
        oauth_token = "sk-ant-oat01-" + "a" * 50
        api_key = "sk-ant-api03-" + "x" * 50

        monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", oauth_token)
        monkeypatch.setenv("ANTHROPIC_API_KEY", api_key)

        result = get_claude_authentication()

        assert result["token"] == oauth_token
        assert result["method"] == "oauth"

    def test_claude_oauth_over_api_key(self, monkeypatch):
        """Test that CLAUDE_OAUTH_TOKEN takes priority over ANTHROPIC_API_KEY."""
        oauth_token = "sk-ant-oat01-" + "b" * 50
        api_key = "sk-ant-api03-" + "y" * 50

        monkeypatch.setenv("CLAUDE_OAUTH_TOKEN", oauth_token)
        monkeypatch.setenv("ANTHROPIC_API_KEY", api_key)
        monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)

        result = get_claude_authentication()

        assert result["token"] == oauth_token
        assert result["method"] == "oauth"

    def test_all_three_credentials_set(self, monkeypatch):
        """Test priority when all three credentials are set."""
        code_token = "sk-ant-oat01-" + "a" * 50
        oauth_token = "sk-ant-oat01-" + "b" * 50
        api_key = "sk-ant-api03-" + "x" * 50

        monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", code_token)
        monkeypatch.setenv("CLAUDE_OAUTH_TOKEN", oauth_token)
        monkeypatch.setenv("ANTHROPIC_API_KEY", api_key)

        result = get_claude_authentication()

        # Should use CLAUDE_CODE_OAUTH_TOKEN (highest priority)
        assert result["token"] == code_token
        assert result["method"] == "oauth"


class TestErrorCases:
    """Test error handling for missing or invalid credentials."""

    def test_no_credentials_set(self, monkeypatch):
        """Test error when no credentials are available."""
        monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
        monkeypatch.delenv("CLAUDE_OAUTH_TOKEN", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with pytest.raises(ValueError) as exc_info:
            get_claude_authentication()

        error_msg = str(exc_info.value)
        assert "No Claude authentication credentials found" in error_msg
        assert "CLAUDE_CODE_OAUTH_TOKEN" in error_msg
        assert "CLAUDE_OAUTH_TOKEN" in error_msg
        assert "ANTHROPIC_API_KEY" in error_msg

    def test_empty_string_credentials(self, monkeypatch):
        """Test that empty string credentials are treated as not set."""
        monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "")
        monkeypatch.setenv("CLAUDE_OAUTH_TOKEN", "   ")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "\t\n")

        with pytest.raises(ValueError) as exc_info:
            get_claude_authentication()

        assert "No Claude authentication credentials found" in str(exc_info.value)

    def test_whitespace_only_credentials(self, monkeypatch):
        """Test that whitespace-only credentials are treated as not set."""
        monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "   ")
        monkeypatch.delenv("CLAUDE_OAUTH_TOKEN", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with pytest.raises(ValueError) as exc_info:
            get_claude_authentication()

        assert "No Claude authentication credentials found" in str(exc_info.value)


class TestValidateClaudeCredentials:
    """Test validation of authentication credentials."""

    def test_valid_oauth_token(self):
        """Test validation of a valid OAuth token."""
        auth_result = {
            "method": "oauth",
            "token": "sk-ant-oat01-" + "a" * 50,
        }

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is True
        assert result["message"] == "Valid oauth credential."
        assert result["method"] == "oauth"
        assert result["token"] == auth_result["token"]

    def test_valid_api_key(self):
        """Test validation of a valid API key."""
        auth_result = {
            "method": "api_key",
            "token": "sk-ant-api03-" + "x" * 50,
        }

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is True
        assert result["message"] == "Valid api_key credential."
        assert result["method"] == "api_key"
        assert result["token"] == auth_result["token"]

    def test_oauth_token_at_minimum_length(self):
        """Test OAuth token at minimum valid length (50 chars)."""
        auth_result = {
            "method": "oauth",
            "token": "sk-ant-oat01-" + "b" * 37,  # 13 + 37 = 50
        }

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is True

    def test_oauth_token_at_maximum_length(self):
        """Test OAuth token at maximum valid length (200 chars)."""
        auth_result = {
            "method": "oauth",
            "token": "sk-ant-oat01-" + "c" * 187,  # 13 + 187 = 200
        }

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is True


class TestValidationErrorCases:
    """Test validation error handling."""

    def test_missing_method_field(self):
        """Test validation when 'method' field is missing."""
        auth_result = {"token": "sk-ant-oat01-" + "a" * 50}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert "Missing 'method' field" in result["message"]

    def test_missing_token_field(self):
        """Test validation when 'token' field is missing."""
        auth_result = {"method": "oauth"}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert "Missing 'token' field" in result["message"]

    def test_invalid_method_value(self):
        """Test validation with invalid method value."""
        auth_result = {
            "method": "invalid_method",
            "token": "sk-ant-oat01-" + "a" * 50,
        }

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert "Invalid method 'invalid_method'" in result["message"]
        assert "Expected 'oauth' or 'api_key'" in result["message"]

    def test_oauth_token_none(self):
        """Test validation when OAuth token is None."""
        auth_result = {"method": "oauth", "token": None}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert "OAuth token is None" in result["message"]
        assert "claude setup-token" in result["message"]

    def test_api_key_none(self):
        """Test validation when API key is None."""
        auth_result = {"method": "api_key", "token": None}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert "API key is None" in result["message"]
        assert "console.anthropic.com" in result["message"]

    def test_token_not_string(self):
        """Test validation when token is not a string."""
        auth_result = {"method": "oauth", "token": 12345}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert "Token must be a string" in result["message"]

    def test_oauth_token_empty_string(self):
        """Test validation when OAuth token is empty string."""
        auth_result = {"method": "oauth", "token": ""}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert "OAuth token is empty" in result["message"]
        assert "claude setup-token" in result["message"]

    def test_api_key_empty_string(self):
        """Test validation when API key is empty string."""
        auth_result = {"method": "api_key", "token": "   "}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert "API key is empty" in result["message"]
        assert "console.anthropic.com" in result["message"]


class TestValidationFormatChecks:
    """Test format validation for OAuth tokens and API keys."""

    def test_oauth_token_wrong_prefix(self):
        """Test OAuth token with wrong prefix (API key prefix)."""
        auth_result = {
            "method": "oauth",
            "token": "sk-ant-api03-" + "a" * 50,  # Wrong prefix
        }

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert "sk-ant-oat01-" in result["message"]
        assert "claude setup-token" in result["message"]

    def test_api_key_wrong_prefix(self):
        """Test API key with wrong prefix (OAuth prefix)."""
        auth_result = {
            "method": "api_key",
            "token": "sk-ant-oat01-" + "x" * 50,  # Wrong prefix
        }

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert "sk-ant-api03-" in result["message"]
        assert "console.anthropic.com" in result["message"]

    def test_oauth_token_too_short(self):
        """Test OAuth token shorter than minimum length."""
        auth_result = {
            "method": "oauth",
            "token": "sk-ant-oat01-short",  # Only ~20 chars
        }

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert f"at least {MIN_TOKEN_LENGTH} characters" in result["message"]
        assert "claude setup-token" in result["message"]

    def test_api_key_too_short(self):
        """Test API key shorter than minimum length."""
        auth_result = {
            "method": "api_key",
            "token": "sk-ant-api03-short",
        }

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert f"at least {MIN_TOKEN_LENGTH} characters" in result["message"]
        assert "console.anthropic.com" in result["message"]

    def test_oauth_token_too_long(self):
        """Test OAuth token longer than maximum length."""
        auth_result = {
            "method": "oauth",
            "token": "sk-ant-oat01-" + "x" * 250,  # ~260 chars
        }

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert f"at most {MAX_TOKEN_LENGTH} characters" in result["message"]

    def test_api_key_too_long(self):
        """Test API key longer than maximum length."""
        auth_result = {
            "method": "api_key",
            "token": "sk-ant-api03-" + "y" * 250,
        }

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert f"at most {MAX_TOKEN_LENGTH} characters" in result["message"]


class TestHelpfulErrorMessages:
    """Test that error messages provide helpful setup instructions."""

    def test_oauth_error_includes_setup_command(self):
        """Test that OAuth errors mention the setup command."""
        auth_result = {"method": "oauth", "token": "invalid"}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert "claude setup-token" in result["message"].lower()

    def test_api_key_error_includes_console_link(self):
        """Test that API key errors mention the console URL."""
        auth_result = {"method": "api_key", "token": "invalid"}

        result = validate_claude_credentials(auth_result)

        assert result["valid"] is False
        assert "console.anthropic.com" in result["message"]

    def test_no_credentials_error_mentions_all_options(self, monkeypatch):
        """Test that no credentials error mentions all available options."""
        monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
        monkeypatch.delenv("CLAUDE_OAUTH_TOKEN", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with pytest.raises(ValueError) as exc_info:
            get_claude_authentication()

        error_msg = str(exc_info.value)
        # Should list all three options
        assert "CLAUDE_CODE_OAUTH_TOKEN" in error_msg
        assert "CLAUDE_OAUTH_TOKEN" in error_msg
        assert "ANTHROPIC_API_KEY" in error_msg
        # Should explain what each is for
        assert "OAuth token from Claude Code" in error_msg
        assert "OAuth token from Claude" in error_msg
        assert "API key from Anthropic Console" in error_msg


class TestConstants:
    """Test that constants are properly defined."""

    def test_oauth_prefix_constant(self):
        """Test that OAuth token prefix constant is correct."""
        assert SK_ANT_OAT01_PREFIX == "sk-ant-oat01-"

    def test_api_key_prefix_constant(self):
        """Test that API key prefix constant is correct."""
        assert SK_ANT_API03_PREFIX == "sk-ant-api03-"

    def test_min_token_length_constant(self):
        """Test that minimum token length is 50."""
        assert MIN_TOKEN_LENGTH == 50

    def test_max_token_length_constant(self):
        """Test that maximum token length is 200."""
        assert MAX_TOKEN_LENGTH == 200
