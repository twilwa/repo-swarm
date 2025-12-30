# ABOUTME: Comprehensive integration tests for authentication fallback priority
# ABOUTME: Tests all combinations of credential precedence and response equivalence

"""
Comprehensive integration tests for Claude authentication fallback system.

Tests the complete authentication priority chain and credential fallback behavior:
1. CLAUDE_CODE_OAUTH_TOKEN (highest priority)
2. CLAUDE_OAUTH_TOKEN (medium priority)
3. ANTHROPIC_API_KEY (lowest priority, fallback)

Verifies:
- All credential combination scenarios work correctly
- Priority order is enforced
- Client types are selected appropriately
- Response structures are equivalent across auth methods
- Error messages are helpful when credentials missing
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from investigator.core.auth_detector import get_claude_authentication
from investigator.core.claude_cli_client import ClaudeCLIClient
from investigator.core.claude_client_factory import create_claude_client
from investigator.core.claude_sdk_client import ClaudeSDKClient


def is_rate_limit_error(error_msg: str) -> bool:
    """Check if error is due to rate limiting."""
    rate_limit_indicators = [
        "limit",
        "quota",
        "rate",
        "resets",
        "exceeded",
        "too many requests",
    ]
    error_lower = str(error_msg).lower()
    return any(indicator in error_lower for indicator in rate_limit_indicators)


def skip_on_rate_limit(func):
    """Decorator to skip tests when rate limited."""
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if is_rate_limit_error(str(e)):
                pytest.skip(f"Rate limited: {e}")
            raise

    return wrapper


class TestAuthenticationPriorityChain:
    """Test all combinations of credential precedence."""

    def test_all_three_credentials_set_code_oauth_wins(self):
        """Test CODE_OAUTH takes priority when all three credentials present."""
        code_oauth = os.getenv("CLAUDE_CODE_OAUTH_TOKEN")
        oauth = os.getenv("CLAUDE_OAUTH_TOKEN") or "sk-ant-oat01-fake-" + "x" * 50
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not code_oauth:
            pytest.skip("CLAUDE_CODE_OAUTH_TOKEN required for priority test")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY required for priority test")

        # Set all three credentials
        with patch.dict(
            os.environ,
            {
                "CLAUDE_CODE_OAUTH_TOKEN": code_oauth,
                "CLAUDE_OAUTH_TOKEN": oauth,
                "ANTHROPIC_API_KEY": api_key,
            },
            clear=False,
        ):
            # Auth detection should select CODE_OAUTH
            auth_result = get_claude_authentication()
            assert auth_result["method"] == "oauth"
            assert auth_result["token"] == code_oauth
            assert auth_result["use_cli"] is True

            # Factory should create CLI client
            client = create_claude_client()
            assert isinstance(client, ClaudeCLIClient)

    def test_code_oauth_and_api_key_code_oauth_wins(self):
        """Test CODE_OAUTH preferred over API key when both present."""
        code_oauth = os.getenv("CLAUDE_CODE_OAUTH_TOKEN")
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not code_oauth:
            pytest.skip("CLAUDE_CODE_OAUTH_TOKEN required")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY required")

        with patch.dict(
            os.environ,
            {
                "CLAUDE_CODE_OAUTH_TOKEN": code_oauth,
                "CLAUDE_OAUTH_TOKEN": "",
                "ANTHROPIC_API_KEY": api_key,
            },
            clear=False,
        ):
            auth_result = get_claude_authentication()
            assert auth_result["method"] == "oauth"
            assert auth_result["token"] == code_oauth
            assert auth_result["use_cli"] is True

            client = create_claude_client()
            assert isinstance(client, ClaudeCLIClient)

    def test_oauth_and_api_key_oauth_wins(self):
        """Test OAUTH preferred over API key when both present."""
        oauth = os.getenv("CLAUDE_OAUTH_TOKEN")
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not oauth:
            pytest.skip("CLAUDE_OAUTH_TOKEN required")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY required")

        with patch.dict(
            os.environ,
            {
                "CLAUDE_CODE_OAUTH_TOKEN": "",
                "CLAUDE_OAUTH_TOKEN": oauth,
                "ANTHROPIC_API_KEY": api_key,
            },
            clear=False,
        ):
            auth_result = get_claude_authentication()
            assert auth_result["method"] == "oauth"
            assert auth_result["token"] == oauth
            assert auth_result["use_cli"] is True

            client = create_claude_client()
            assert isinstance(client, ClaudeCLIClient)

    def test_only_api_key_uses_api_key(self):
        """Test API key is used when it's the only credential."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY required")

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

            client = create_claude_client()
            assert isinstance(client, ClaudeSDKClient)

    def test_only_code_oauth_uses_code_oauth(self):
        """Test CODE_OAUTH is used when it's the only credential."""
        code_oauth = os.getenv("CLAUDE_CODE_OAUTH_TOKEN")
        if not code_oauth:
            pytest.skip("CLAUDE_CODE_OAUTH_TOKEN required")

        with patch.dict(
            os.environ,
            {
                "CLAUDE_CODE_OAUTH_TOKEN": code_oauth,
                "CLAUDE_OAUTH_TOKEN": "",
                "ANTHROPIC_API_KEY": "",
            },
            clear=False,
        ):
            auth_result = get_claude_authentication()
            assert auth_result["method"] == "oauth"
            assert auth_result["token"] == code_oauth
            assert auth_result["use_cli"] is True

            client = create_claude_client()
            assert isinstance(client, ClaudeCLIClient)

    def test_only_oauth_uses_oauth(self):
        """Test OAUTH is used when it's the only credential."""
        oauth = os.getenv("CLAUDE_OAUTH_TOKEN")
        if not oauth:
            pytest.skip("CLAUDE_OAUTH_TOKEN required")

        with patch.dict(
            os.environ,
            {
                "CLAUDE_CODE_OAUTH_TOKEN": "",
                "CLAUDE_OAUTH_TOKEN": oauth,
                "ANTHROPIC_API_KEY": "",
            },
            clear=False,
        ):
            auth_result = get_claude_authentication()
            assert auth_result["method"] == "oauth"
            assert auth_result["token"] == oauth
            assert auth_result["use_cli"] is True

            client = create_claude_client()
            assert isinstance(client, ClaudeCLIClient)


class TestResponseStructureEquivalence:
    """Test SDK and CLI clients return equivalent response structures."""

    @skip_on_rate_limit
    def test_response_content_structure_matches(self):
        """Test both clients return same content structure."""
        oauth = os.getenv("CLAUDE_CODE_OAUTH_TOKEN") or os.getenv("CLAUDE_OAUTH_TOKEN")
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not oauth or not api_key:
            pytest.skip("Both OAuth and API key required")

        test_messages = [{"role": "user", "content": "Say exactly: test response"}]

        # Get OAuth response
        with patch.dict(
            os.environ,
            {"CLAUDE_CODE_OAUTH_TOKEN": oauth, "ANTHROPIC_API_KEY": ""},
            clear=False,
        ):
            oauth_client = create_claude_client()
            oauth_response = oauth_client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=50,
                messages=test_messages,
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
                messages=test_messages,
            )

        # Both should have content list
        assert hasattr(oauth_response, "content")
        assert hasattr(sdk_response, "content")
        assert isinstance(oauth_response.content, list)
        assert isinstance(sdk_response.content, list)

        # Both should have at least one content block
        assert len(oauth_response.content) > 0
        assert len(sdk_response.content) > 0

        # Both content blocks should have text
        assert hasattr(oauth_response.content[0], "text")
        assert hasattr(sdk_response.content[0], "text")
        assert isinstance(oauth_response.content[0].text, str)
        assert isinstance(sdk_response.content[0].text, str)

    @skip_on_rate_limit
    def test_response_metadata_structure_matches(self):
        """Test both clients return same metadata fields."""
        oauth = os.getenv("CLAUDE_CODE_OAUTH_TOKEN") or os.getenv("CLAUDE_OAUTH_TOKEN")
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not oauth or not api_key:
            pytest.skip("Both OAuth and API key required")

        test_messages = [{"role": "user", "content": "Hi"}]

        # Get OAuth response
        with patch.dict(
            os.environ,
            {"CLAUDE_CODE_OAUTH_TOKEN": oauth, "ANTHROPIC_API_KEY": ""},
            clear=False,
        ):
            oauth_client = create_claude_client()
            oauth_response = oauth_client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=50,
                messages=test_messages,
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
                messages=test_messages,
            )

        # Check all expected metadata fields exist
        required_fields = ["role", "model"]
        for field in required_fields:
            assert hasattr(oauth_response, field), f"OAuth response missing {field}"
            assert hasattr(sdk_response, field), f"SDK response missing {field}"

        # Verify field values are same type
        assert type(oauth_response.role) == type(sdk_response.role)
        assert type(oauth_response.model) == type(sdk_response.model)

    @skip_on_rate_limit
    def test_both_clients_handle_same_prompts(self):
        """Test both clients successfully process identical prompts."""
        oauth = os.getenv("CLAUDE_CODE_OAUTH_TOKEN") or os.getenv("CLAUDE_OAUTH_TOKEN")
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not oauth or not api_key:
            pytest.skip("Both OAuth and API key required")

        # Test various prompt types
        test_prompts = [
            "Count to 3",
            "What is 2+2?",
            "Say hello",
        ]

        for prompt in test_prompts:
            messages = [{"role": "user", "content": prompt}]

            # OAuth client
            with patch.dict(
                os.environ,
                {"CLAUDE_CODE_OAUTH_TOKEN": oauth, "ANTHROPIC_API_KEY": ""},
                clear=False,
            ):
                oauth_client = create_claude_client()
                oauth_response = oauth_client.messages_create(
                    model="claude-opus-4-5-20251101",
                    max_tokens=100,
                    messages=messages,
                )

            # SDK client
            with patch.dict(
                os.environ,
                {"CLAUDE_CODE_OAUTH_TOKEN": "", "ANTHROPIC_API_KEY": api_key},
                clear=False,
            ):
                sdk_client = create_claude_client()
                sdk_response = sdk_client.messages_create(
                    model="claude-opus-4-5-20251101",
                    max_tokens=100,
                    messages=messages,
                )

            # Both should return valid responses
            assert len(oauth_response.content) > 0
            assert len(sdk_response.content) > 0
            assert len(oauth_response.content[0].text) > 0
            assert len(sdk_response.content[0].text) > 0


class TestErrorHandling:
    """Test error handling for invalid or missing credentials."""

    def test_error_message_includes_all_credential_types(self):
        """Test error message lists all credential options."""
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

            # Error should mention all three credential types
            assert "CLAUDE_CODE_OAUTH_TOKEN" in error_msg
            assert "CLAUDE_OAUTH_TOKEN" in error_msg
            assert "ANTHROPIC_API_KEY" in error_msg

            # Error should be helpful
            assert "No Claude authentication credentials found" in error_msg

    def test_empty_string_credentials_treated_as_missing(self):
        """Test empty string credentials are treated as missing."""
        with patch.dict(
            os.environ,
            {
                "CLAUDE_CODE_OAUTH_TOKEN": "   ",  # Whitespace only
                "CLAUDE_OAUTH_TOKEN": "",
                "ANTHROPIC_API_KEY": "",
            },
            clear=False,
        ):
            with pytest.raises(ValueError) as exc_info:
                get_claude_authentication()

            # Should raise error for missing credentials
            assert "No Claude authentication credentials found" in str(exc_info.value)

    def test_whitespace_stripped_from_credentials(self):
        """Test whitespace is stripped from credential values."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY required")

        # Add whitespace around API key
        with patch.dict(
            os.environ,
            {
                "CLAUDE_CODE_OAUTH_TOKEN": "",
                "CLAUDE_OAUTH_TOKEN": "",
                "ANTHROPIC_API_KEY": f"  {api_key}  ",
            },
            clear=False,
        ):
            auth_result = get_claude_authentication()

            # Should strip whitespace
            assert auth_result["token"] == api_key
            assert not auth_result["token"].startswith(" ")
            assert not auth_result["token"].endswith(" ")


class TestClientMethodCompatibility:
    """Test both client types implement same interface."""

    def test_both_clients_have_messages_create_method(self):
        """Test both clients implement messages_create()."""
        oauth = os.getenv("CLAUDE_CODE_OAUTH_TOKEN") or os.getenv("CLAUDE_OAUTH_TOKEN")
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not oauth:
            oauth = "sk-ant-oat01-fake-" + "x" * 50
        if not api_key:
            api_key = "sk-ant-api03-fake-" + "x" * 50

        # Create both client types
        cli_client = ClaudeCLIClient(oauth_token=oauth)
        sdk_client = ClaudeSDKClient(api_key=api_key)

        # Both should have messages_create method
        assert hasattr(cli_client, "messages_create")
        assert hasattr(sdk_client, "messages_create")
        assert callable(cli_client.messages_create)
        assert callable(sdk_client.messages_create)

    @skip_on_rate_limit
    def test_both_clients_accept_same_parameters(self):
        """Test both clients accept same messages_create() parameters."""
        oauth = os.getenv("CLAUDE_CODE_OAUTH_TOKEN") or os.getenv("CLAUDE_OAUTH_TOKEN")
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not oauth or not api_key:
            pytest.skip("Both credentials required")

        # Same parameters for both clients
        params = {
            "model": "claude-opus-4-5-20251101",
            "max_tokens": 50,
            "messages": [{"role": "user", "content": "Hi"}],
        }

        # OAuth client should accept parameters
        with patch.dict(
            os.environ,
            {"CLAUDE_CODE_OAUTH_TOKEN": oauth, "ANTHROPIC_API_KEY": ""},
            clear=False,
        ):
            oauth_client = create_claude_client()
            oauth_response = oauth_client.messages_create(**params)
            assert oauth_response is not None

        # SDK client should accept same parameters
        with patch.dict(
            os.environ,
            {"CLAUDE_CODE_OAUTH_TOKEN": "", "ANTHROPIC_API_KEY": api_key},
            clear=False,
        ):
            sdk_client = create_claude_client()
            sdk_response = sdk_client.messages_create(**params)
            assert sdk_response is not None


class TestFactoryBehavior:
    """Test factory correctly routes to appropriate client."""

    def test_factory_creates_cli_client_for_oauth(self):
        """Test factory creates ClaudeCLIClient when OAuth detected."""
        oauth = os.getenv("CLAUDE_CODE_OAUTH_TOKEN") or os.getenv("CLAUDE_OAUTH_TOKEN")
        if not oauth:
            pytest.skip("OAuth token required")

        with patch.dict(
            os.environ,
            {"CLAUDE_CODE_OAUTH_TOKEN": oauth, "ANTHROPIC_API_KEY": ""},
            clear=False,
        ):
            client = create_claude_client()
            assert isinstance(client, ClaudeCLIClient)
            assert not isinstance(client, ClaudeSDKClient)

    def test_factory_creates_sdk_client_for_api_key(self):
        """Test factory creates ClaudeSDKClient when API key detected."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("API key required")

        with patch.dict(
            os.environ,
            {
                "CLAUDE_CODE_OAUTH_TOKEN": "",
                "CLAUDE_OAUTH_TOKEN": "",
                "ANTHROPIC_API_KEY": api_key,
            },
            clear=False,
        ):
            client = create_claude_client()
            assert isinstance(client, ClaudeSDKClient)
            assert not isinstance(client, ClaudeCLIClient)

    def test_factory_passes_logger_to_both_clients(self):
        """Test factory passes optional logger to both client types."""

        class MockLogger:
            """Mock logger for testing."""

            def __init__(self):
                self.messages = []

            def debug(self, msg):
                self.messages.append(("debug", msg))

            def info(self, msg):
                self.messages.append(("info", msg))

            def error(self, msg):
                self.messages.append(("error", msg))

        oauth = os.getenv("CLAUDE_CODE_OAUTH_TOKEN") or os.getenv("CLAUDE_OAUTH_TOKEN")
        api_key = os.getenv("ANTHROPIC_API_KEY")

        # Test with OAuth
        if oauth:
            logger = MockLogger()
            with patch.dict(
                os.environ,
                {"CLAUDE_CODE_OAUTH_TOKEN": oauth, "ANTHROPIC_API_KEY": ""},
                clear=False,
            ):
                client = create_claude_client(logger=logger)
                assert client.logger is logger

        # Test with API key
        if api_key:
            logger = MockLogger()
            with patch.dict(
                os.environ,
                {"CLAUDE_CODE_OAUTH_TOKEN": "", "ANTHROPIC_API_KEY": api_key},
                clear=False,
            ):
                client = create_claude_client(logger=logger)
                assert client.logger is logger
