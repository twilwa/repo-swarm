# ABOUTME: Unit tests for config.py validation methods
# ABOUTME: Tests OAuth token validation and configuration validation logic

import pytest
import os
from src.investigator.core.config import Config


class TestOAuthTokenValidation:
    """Test suite for OAuth token format validation in Config."""

    def test_valid_oauth_token_format(self):
        """Test that valid OAuth tokens pass validation."""
        # Valid OAuth token format: sk-ant-oat01- followed by sufficient characters
        valid_token = "sk-ant-oat01-" + "a" * 50

        # Should not raise ValueError
        result = Config.validate_oauth_token(valid_token)
        assert result == valid_token

    def test_valid_oauth_token_at_min_length(self):
        """Test OAuth token at minimum valid length (50 chars total)."""
        # Exactly 50 characters total
        valid_token = "sk-ant-oat01-" + "b" * 37  # 13 + 37 = 50
        result = Config.validate_oauth_token(valid_token)
        assert result == valid_token

    def test_valid_oauth_token_at_max_length(self):
        """Test OAuth token at maximum valid length (200 chars total)."""
        # Exactly 200 characters total
        valid_token = "sk-ant-oat01-" + "c" * 187  # 13 + 187 = 200
        result = Config.validate_oauth_token(valid_token)
        assert result == valid_token

    def test_invalid_oauth_token_wrong_prefix(self):
        """Test that tokens with wrong prefix are rejected."""
        # Wrong prefix (API key format instead of OAuth)
        invalid_token = "sk-ant-api03-" + "a" * 50

        with pytest.raises(ValueError) as exc_info:
            Config.validate_oauth_token(invalid_token)

        assert "sk-ant-oat01-" in str(exc_info.value)
        assert "claude setup-token" in str(exc_info.value).lower()

    def test_invalid_oauth_token_too_short(self):
        """Test that tokens shorter than 50 chars are rejected."""
        # Only 40 characters total (too short)
        invalid_token = "sk-ant-oat01-short"

        with pytest.raises(ValueError) as exc_info:
            Config.validate_oauth_token(invalid_token)

        assert "50 characters" in str(exc_info.value)
        assert "claude setup-token" in str(exc_info.value).lower()

    def test_invalid_oauth_token_too_long(self):
        """Test that tokens longer than 200 chars are rejected."""
        # 250 characters total (too long)
        invalid_token = "sk-ant-oat01-" + "x" * 237

        with pytest.raises(ValueError) as exc_info:
            Config.validate_oauth_token(invalid_token)

        assert "200 characters" in str(exc_info.value)

    def test_invalid_oauth_token_empty_string(self):
        """Test that empty strings are rejected."""
        with pytest.raises(ValueError) as exc_info:
            Config.validate_oauth_token("")

        assert "empty" in str(exc_info.value).lower()

    def test_invalid_oauth_token_none(self):
        """Test that None values are rejected."""
        with pytest.raises(ValueError) as exc_info:
            Config.validate_oauth_token(None)

        assert "None" in str(exc_info.value)

    def test_invalid_oauth_token_not_string(self):
        """Test that non-string values are rejected."""
        with pytest.raises(ValueError) as exc_info:
            Config.validate_oauth_token(12345)

        assert "string" in str(exc_info.value).lower()


class TestAPIKeyValidation:
    """Test suite for API key format validation in Config."""

    def test_valid_api_key_format(self):
        """Test that valid API keys pass validation."""
        # Valid API key format: sk-ant-api03- followed by sufficient characters
        valid_key = "sk-ant-api03-" + "a" * 50

        result = Config.validate_api_key(valid_key)
        assert result == valid_key

    def test_invalid_api_key_wrong_prefix(self):
        """Test that API keys with wrong prefix are rejected."""
        # Wrong prefix (OAuth format instead of API key)
        invalid_key = "sk-ant-oat01-" + "a" * 50

        with pytest.raises(ValueError) as exc_info:
            Config.validate_api_key(invalid_key)

        assert "sk-ant-api03-" in str(exc_info.value)
        assert "console.anthropic.com" in str(exc_info.value)

    def test_invalid_api_key_too_short(self):
        """Test that API keys shorter than 50 chars are rejected."""
        invalid_key = "sk-ant-api03-short"

        with pytest.raises(ValueError) as exc_info:
            Config.validate_api_key(invalid_key)

        assert "50 characters" in str(exc_info.value)


class TestEnvironmentVariableValidation:
    """Test validation of OAuth tokens from environment variables."""

    def test_validate_oauth_from_env_claude_code(self, monkeypatch):
        """Test validation of CLAUDE_CODE_OAUTH_TOKEN from environment."""
        valid_token = "sk-ant-oat01-" + "a" * 50
        monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", valid_token)

        result = Config.validate_oauth_from_env()
        assert result["method"] == "oauth"
        assert result["token"] == valid_token
        assert result["valid"] is True

    def test_validate_oauth_from_env_claude_oauth(self, monkeypatch):
        """Test validation of CLAUDE_OAUTH_TOKEN from environment (second priority)."""
        valid_token = "sk-ant-oat01-" + "b" * 50
        monkeypatch.setenv("CLAUDE_OAUTH_TOKEN", valid_token)
        # Ensure CLAUDE_CODE_OAUTH_TOKEN is not set
        monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)

        result = Config.validate_oauth_from_env()
        assert result["method"] == "oauth"
        assert result["token"] == valid_token
        assert result["valid"] is True

    def test_validate_oauth_from_env_priority(self, monkeypatch):
        """Test that CLAUDE_CODE_OAUTH_TOKEN takes priority over CLAUDE_OAUTH_TOKEN."""
        code_token = "sk-ant-oat01-" + "a" * 50
        oauth_token = "sk-ant-oat01-" + "b" * 50

        monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", code_token)
        monkeypatch.setenv("CLAUDE_OAUTH_TOKEN", oauth_token)

        result = Config.validate_oauth_from_env()
        assert result["token"] == code_token  # Should use CLAUDE_CODE_OAUTH_TOKEN

    def test_validate_oauth_from_env_no_token(self, monkeypatch):
        """Test validation when no OAuth token is set (should return None or skip)."""
        monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
        monkeypatch.delenv("CLAUDE_OAUTH_TOKEN", raising=False)

        result = Config.validate_oauth_from_env()
        # Should return a result indicating no OAuth token set (not an error)
        assert result is None or result["valid"] is False

    def test_validate_oauth_from_env_invalid_format(self, monkeypatch):
        """Test validation of invalid OAuth token from environment."""
        invalid_token = "sk-ant-api03-wrong"  # Wrong prefix
        monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", invalid_token)

        result = Config.validate_oauth_from_env()
        assert result["valid"] is False
        assert "sk-ant-oat01-" in result["message"]
        assert "claude setup-token" in result["message"].lower()


class TestConfigurationHelpers:
    """Test configuration helper methods."""

    def test_get_authentication_setup_message(self):
        """Test that helpful setup message is generated."""
        message = Config.get_authentication_setup_message()

        # Should mention both OAuth and API key options
        assert "CLAUDE_CODE_OAUTH_TOKEN" in message
        assert "CLAUDE_OAUTH_TOKEN" in message
        assert "ANTHROPIC_API_KEY" in message

        # Should mention setup commands
        assert "claude setup-token" in message.lower()
        assert "console.anthropic.com" in message

    def test_error_message_references_docs(self):
        """Test that error messages reference documentation."""
        # Test with invalid OAuth token
        invalid_token = "sk-ant-oat01-short"

        with pytest.raises(ValueError) as exc_info:
            Config.validate_oauth_token(invalid_token)

        error_msg = str(exc_info.value)
        # Should provide helpful guidance similar to GitHub token migration guide
        assert "claude setup-token" in error_msg.lower()


class TestBackwardCompatibility:
    """Test that existing code continues to work."""

    def test_existing_validation_methods_unchanged(self):
        """Test that existing validation methods still work."""
        # These should continue to work as before
        assert (
            Config.validate_claude_model("claude-opus-4-5-20251101")
            == "claude-opus-4-5-20251101"
        )
        assert Config.validate_max_tokens(5000) == 5000
        assert Config.validate_sleep_hours(2.5) == 2.5
        assert Config.validate_chunk_size(5) == 5

    def test_no_breaking_changes_to_config_class(self):
        """Test that Config class structure is preserved."""
        # Existing constants should still exist
        assert hasattr(Config, "CLAUDE_MODEL")
        assert hasattr(Config, "MAX_TOKENS")
        assert hasattr(Config, "VALID_CLAUDE_MODELS")

        # Existing methods should still exist
        assert hasattr(Config, "validate_claude_model")
        assert hasattr(Config, "validate_max_tokens")
        assert hasattr(Config, "validate_sleep_hours")
        assert hasattr(Config, "validate_chunk_size")
