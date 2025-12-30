# ABOUTME: Integration tests for Claude authentication - OAuth and API key flows
# ABOUTME: Tests end-to-end authentication fallback and compatibility between methods

"""
Integration tests for Claude authentication methods.

Tests both OAuth token and API key authentication flows end-to-end:
1. API key authentication (existing flow compatibility)
2. OAuth token authentication (new flow)
3. Authentication fallback (OAuth -> API key)
4. Response compatibility between both methods
5. Mock fallback when credentials unavailable
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from investigator.core.auth_detector import get_claude_authentication
from investigator.core.claude_client_factory import create_claude_client
from investigator.core.claude_cli_client import ClaudeCLIClient, MessageResponse
from investigator.core.claude_sdk_client import ClaudeSDKClient


class TestAPIKeyAuthentication:
    """Test API key authentication flow (backward compatibility)."""

    def test_api_key_real_request(self):
        """Test real API key authentication produces valid response."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set - skipping real API test")

        # Clear OAuth tokens to ensure API key is used
        with patch.dict(
            os.environ,
            {
                "CLAUDE_CODE_OAUTH_TOKEN": "",
                "CLAUDE_OAUTH_TOKEN": "",
                "ANTHROPIC_API_KEY": api_key,
            },
            clear=False,
        ):
            # Create client via factory
            client = create_claude_client()

            # Verify it's an SDK client
            assert isinstance(
                client, ClaudeSDKClient
            ), "Should create ClaudeSDKClient for API key"

            # Make real request
            response = client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=100,
                messages=[{"role": "user", "content": "Say 'hello world' briefly."}],
            )

            # Verify response structure
            assert response is not None
            assert hasattr(response, "content")
            assert len(response.content) > 0
            assert hasattr(response.content[0], "text")

            # Verify content
            text = response.content[0].text.lower()
            assert len(text) > 0
            assert "hello" in text or "world" in text

    def test_api_key_auth_detection(self):
        """Test auth detector correctly identifies API key."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        with patch.dict(
            os.environ,
            {
                "CLAUDE_CODE_OAUTH_TOKEN": "",
                "CLAUDE_OAUTH_TOKEN": "",
                "ANTHROPIC_API_KEY": api_key,
            },
            clear=False,
        ):
            auth_result = get_claude_authentication()

            assert auth_result["method"] == "api_key"
            assert auth_result["token"] == api_key
            assert auth_result["use_cli"] is False


class TestOAuthAuthentication:
    """Test OAuth token authentication flow (new functionality)."""

    def test_oauth_real_request(self):
        """Test real OAuth authentication produces valid response."""
        oauth_token = os.getenv("CLAUDE_CODE_OAUTH_TOKEN") or os.getenv(
            "CLAUDE_OAUTH_TOKEN"
        )
        if not oauth_token:
            pytest.skip("No OAuth token set - skipping real OAuth test")

        # Set OAuth and clear API key
        with patch.dict(
            os.environ,
            {
                "CLAUDE_CODE_OAUTH_TOKEN": oauth_token,
                "ANTHROPIC_API_KEY": "",
            },
            clear=False,
        ):
            # Create client via factory
            client = create_claude_client()

            # Verify it's a CLI client
            assert isinstance(
                client, ClaudeCLIClient
            ), "Should create ClaudeCLIClient for OAuth"

            # Make real request
            response = client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=100,
                messages=[{"role": "user", "content": "Say 'hello world' briefly."}],
            )

            # Verify response structure
            assert isinstance(response, MessageResponse)
            assert len(response.content) > 0
            assert hasattr(response.content[0], "text")

            # Verify content
            text = response.content[0].text.lower()
            assert len(text) > 0
            assert "hello" in text or "world" in text

    def test_oauth_auth_detection_claude_code(self):
        """Test auth detector prioritizes CLAUDE_CODE_OAUTH_TOKEN."""
        oauth_token = os.getenv("CLAUDE_CODE_OAUTH_TOKEN")
        if not oauth_token:
            pytest.skip("CLAUDE_CODE_OAUTH_TOKEN not set")

        with patch.dict(
            os.environ,
            {
                "CLAUDE_CODE_OAUTH_TOKEN": oauth_token,
                "CLAUDE_OAUTH_TOKEN": "other-token",  # Should be ignored
                "ANTHROPIC_API_KEY": "api-key",  # Should be ignored
            },
            clear=False,
        ):
            auth_result = get_claude_authentication()

            assert auth_result["method"] == "oauth"
            assert auth_result["token"] == oauth_token
            assert auth_result["use_cli"] is True

    def test_oauth_auth_detection_fallback(self):
        """Test auth detector falls back to CLAUDE_OAUTH_TOKEN."""
        oauth_token = os.getenv("CLAUDE_OAUTH_TOKEN")
        if not oauth_token:
            pytest.skip("CLAUDE_OAUTH_TOKEN not set")

        with patch.dict(
            os.environ,
            {
                "CLAUDE_CODE_OAUTH_TOKEN": "",
                "CLAUDE_OAUTH_TOKEN": oauth_token,
                "ANTHROPIC_API_KEY": "api-key",  # Should be ignored
            },
            clear=False,
        ):
            auth_result = get_claude_authentication()

            assert auth_result["method"] == "oauth"
            assert auth_result["token"] == oauth_token
            assert auth_result["use_cli"] is True


class TestAuthenticationFallback:
    """Test authentication fallback priority (OAuth -> API key)."""

    def test_oauth_takes_priority_over_api_key(self):
        """Test OAuth is preferred when both credentials available."""
        oauth_token = os.getenv("CLAUDE_CODE_OAUTH_TOKEN") or os.getenv(
            "CLAUDE_OAUTH_TOKEN"
        )
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not oauth_token or not api_key:
            pytest.skip("Both OAuth and API key required for priority test")

        with patch.dict(
            os.environ,
            {
                "CLAUDE_CODE_OAUTH_TOKEN": oauth_token,
                "ANTHROPIC_API_KEY": api_key,
            },
            clear=False,
        ):
            # Auth detection should prefer OAuth
            auth_result = get_claude_authentication()
            assert auth_result["method"] == "oauth"
            assert auth_result["use_cli"] is True

            # Factory should create CLI client
            client = create_claude_client()
            assert isinstance(client, ClaudeCLIClient)

    def test_api_key_used_when_oauth_unavailable(self):
        """Test API key is used when OAuth not available."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY required for fallback test")

        with patch.dict(
            os.environ,
            {
                "CLAUDE_CODE_OAUTH_TOKEN": "",
                "CLAUDE_OAUTH_TOKEN": "",
                "ANTHROPIC_API_KEY": api_key,
            },
            clear=False,
        ):
            # Auth detection should fall back to API key
            auth_result = get_claude_authentication()
            assert auth_result["method"] == "api_key"
            assert auth_result["use_cli"] is False

            # Factory should create SDK client
            client = create_claude_client()
            assert isinstance(client, ClaudeSDKClient)

    def test_error_when_no_credentials(self):
        """Test error raised when neither OAuth nor API key available."""
        with patch.dict(
            os.environ,
            {
                "CLAUDE_CODE_OAUTH_TOKEN": "",
                "CLAUDE_OAUTH_TOKEN": "",
                "ANTHROPIC_API_KEY": "",
            },
            clear=False,
        ):
            with pytest.raises(ValueError) as exc_info:
                get_claude_authentication()

            error_msg = str(exc_info.value)
            assert "No Claude authentication credentials found" in error_msg
            assert "CLAUDE_CODE_OAUTH_TOKEN" in error_msg
            assert "ANTHROPIC_API_KEY" in error_msg


class TestResponseCompatibility:
    """Test both auth methods produce compatible responses."""

    def test_api_key_and_oauth_responses_compatible(self):
        """Test API key and OAuth produce compatible response structures."""
        oauth_token = os.getenv("CLAUDE_CODE_OAUTH_TOKEN") or os.getenv(
            "CLAUDE_OAUTH_TOKEN"
        )
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not oauth_token or not api_key:
            pytest.skip("Both OAuth and API key required for compatibility test")

        test_prompt = "Respond with exactly: 'compatibility test successful'"

        # Test OAuth response
        with patch.dict(
            os.environ,
            {"CLAUDE_CODE_OAUTH_TOKEN": oauth_token, "ANTHROPIC_API_KEY": ""},
            clear=False,
        ):
            oauth_client = create_claude_client()
            oauth_response = oauth_client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=50,
                messages=[{"role": "user", "content": test_prompt}],
            )

        # Test API key response
        with patch.dict(
            os.environ,
            {"CLAUDE_CODE_OAUTH_TOKEN": "", "ANTHROPIC_API_KEY": api_key},
            clear=False,
        ):
            sdk_client = create_claude_client()
            sdk_response = sdk_client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=50,
                messages=[{"role": "user", "content": test_prompt}],
            )

        # Both responses should have same structure
        assert hasattr(oauth_response, "content")
        assert hasattr(sdk_response, "content")

        assert len(oauth_response.content) > 0
        assert len(sdk_response.content) > 0

        assert hasattr(oauth_response.content[0], "text")
        assert hasattr(sdk_response.content[0], "text")

        # Both should have non-empty text
        assert len(oauth_response.content[0].text) > 0
        assert len(sdk_response.content[0].text) > 0

    def test_response_attributes_match(self):
        """Test both response types have same essential attributes."""
        oauth_token = os.getenv("CLAUDE_CODE_OAUTH_TOKEN") or os.getenv(
            "CLAUDE_OAUTH_TOKEN"
        )
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not oauth_token or not api_key:
            pytest.skip("Both credentials required")

        # Get OAuth response
        with patch.dict(
            os.environ,
            {"CLAUDE_CODE_OAUTH_TOKEN": oauth_token, "ANTHROPIC_API_KEY": ""},
            clear=False,
        ):
            oauth_client = create_claude_client()
            oauth_response = oauth_client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=50,
                messages=[{"role": "user", "content": "Hi"}],
            )

        # Get API key response
        with patch.dict(
            os.environ,
            {"CLAUDE_CODE_OAUTH_TOKEN": "", "ANTHROPIC_API_KEY": api_key},
            clear=False,
        ):
            sdk_client = create_claude_client()
            sdk_response = sdk_client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=50,
                messages=[{"role": "user", "content": "Hi"}],
            )

        # Check common attributes exist in both
        common_attrs = ["content", "role", "model"]
        for attr in common_attrs:
            assert hasattr(oauth_response, attr), f"OAuth response missing {attr}"
            assert hasattr(sdk_response, attr), f"SDK response missing {attr}"


class TestMockedAuthentication:
    """Test authentication with mocked responses when credentials unavailable."""

    def test_api_key_mocked_when_unavailable(self):
        """Test API key flow with mocked client when credentials not available."""
        # Mock the Anthropic client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="mocked response")]

        with patch("investigator.core.claude_sdk_client.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            # Create SDK client with fake key
            client = ClaudeSDKClient(api_key="sk-ant-api03-fake-key-" + "x" * 50)

            # Should work with mocked response
            response = client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=100,
                messages=[{"role": "user", "content": "test"}],
            )

            assert response.content[0].text == "mocked response"
            mock_client.messages.create.assert_called_once()

    def test_oauth_mocked_when_unavailable(self):
        """Test OAuth flow with mocked subprocess when credentials not available."""
        mock_response_json = {
            "id": "msg_123",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "mocked oauth response"}],
            "model": "claude-opus-4-5-20251101",
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = str(mock_response_json).replace("'", '"')
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            # Create CLI client with fake token
            client = ClaudeCLIClient(oauth_token="sk-ant-oat01-fake-token-" + "x" * 50)

            # Should work with mocked subprocess
            response = client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=100,
                messages=[{"role": "user", "content": "test"}],
            )

            assert len(response.content) > 0
            assert response.content[0].text == "mocked oauth response"

    def test_factory_with_mocked_auth_detection(self):
        """Test factory with mocked authentication detection."""
        # Mock auth detection to return API key
        mock_auth_result = {
            "method": "api_key",
            "token": "sk-ant-api03-mocked-key-" + "x" * 50,
            "use_cli": False,
        }

        with patch(
            "investigator.core.claude_client_factory.get_claude_authentication",
            return_value=mock_auth_result,
        ):
            with patch(
                "investigator.core.claude_sdk_client.Anthropic"
            ) as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.return_value = mock_client

                # Factory should create SDK client
                client = create_claude_client()
                assert isinstance(client, ClaudeSDKClient)
