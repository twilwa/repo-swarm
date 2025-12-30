"""
ABOUTME: Unit tests for ClaudeSDKClient - wrapper around Anthropic SDK
ABOUTME: Tests API key initialization, message creation, error handling, and backward compatibility

Unit tests for ClaudeSDKClient wrapper around the Anthropic SDK.
Verifies that the wrapper maintains exact backward compatibility with direct SDK usage.
"""

import sys
import unittest
from unittest.mock import MagicMock, Mock, patch

# Add the src directory to the path
sys.path.append(
    __import__("os").path.join(
        __import__("os").path.dirname(__file__), "..", "..", "src"
    )
)

from investigator.core.claude_sdk_client import ClaudeSDKClient


class TestClaudeSDKClientInitialization(unittest.TestCase):
    """Test suite for ClaudeSDKClient initialization."""

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_init_with_api_key_creates_anthropic_client(self, mock_anthropic):
        """Test that initialization creates Anthropic client with API key."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        api_key = "test-api-key-12345"
        sdk_client = ClaudeSDKClient(api_key=api_key)

        # Verify Anthropic was called with correct API key
        mock_anthropic.assert_called_once_with(api_key=api_key)

        # Verify client is stored
        self.assertEqual(sdk_client.client, mock_client)

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_init_with_logger(self, mock_anthropic):
        """Test that logger is properly stored."""
        mock_logger = Mock()
        api_key = "test-api-key"

        sdk_client = ClaudeSDKClient(api_key=api_key, logger=mock_logger)

        self.assertEqual(sdk_client.logger, mock_logger)

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_init_without_logger(self, mock_anthropic):
        """Test that initialization works without logger."""
        api_key = "test-api-key"

        sdk_client = ClaudeSDKClient(api_key=api_key)

        self.assertIsNone(sdk_client.logger)


class TestClaudeSDKClientMessagesCreate(unittest.TestCase):
    """Test suite for messages_create method."""

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_messages_create_calls_api_correctly(self, mock_anthropic):
        """Test that messages_create calls Anthropic API with correct parameters."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Analysis result")]
        mock_client.messages.create.return_value = mock_response

        sdk_client = ClaudeSDKClient(api_key="test-key")

        model = "claude-opus-4-5-20251101"
        max_tokens = 2000
        messages = [{"role": "user", "content": "Analyze this"}]

        response = sdk_client.messages_create(
            model=model, max_tokens=max_tokens, messages=messages
        )

        # Verify API was called with correct parameters
        mock_client.messages.create.assert_called_once_with(
            model=model, max_tokens=max_tokens, messages=messages
        )

        # Verify response is returned (not processed)
        self.assertEqual(response, mock_response)

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_messages_create_returns_raw_anthropic_response(self, mock_anthropic):
        """Test that response structure matches Anthropic SDK (backward compatibility)."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        # Create response matching Anthropic SDK structure
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "Analysis text"
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response

        sdk_client = ClaudeSDKClient(api_key="test-key")
        response = sdk_client.messages_create(
            model="claude-opus-4-5-20251101",
            max_tokens=2000,
            messages=[{"role": "user", "content": "test"}],
        )

        # Verify can access response like Anthropic SDK
        text = response.content[0].text
        self.assertEqual(text, "Analysis text")

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_messages_create_with_logger_logs_request(self, mock_anthropic):
        """Test that logger is used if provided."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="result")]
        mock_client.messages.create.return_value = mock_response

        mock_logger = Mock()
        sdk_client = ClaudeSDKClient(api_key="test-key", logger=mock_logger)

        sdk_client.messages_create(
            model="claude-opus-4-5-20251101",
            max_tokens=2000,
            messages=[{"role": "user", "content": "test"}],
        )

        # Verify debug/info logs were called
        self.assertTrue(mock_logger.debug.called or mock_logger.info.called)

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_messages_create_without_logger_still_works(self, mock_anthropic):
        """Test that messages_create works without logger (no AttributeError)."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="result")]
        mock_client.messages.create.return_value = mock_response

        sdk_client = ClaudeSDKClient(api_key="test-key")  # No logger

        # Should not raise AttributeError
        response = sdk_client.messages_create(
            model="claude-opus-4-5-20251101",
            max_tokens=2000,
            messages=[{"role": "user", "content": "test"}],
        )

        self.assertIsNotNone(response)


class TestClaudeSDKClientErrorHandling(unittest.TestCase):
    """Test suite for error handling."""

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_messages_create_raises_exception_on_api_error(self, mock_anthropic):
        """Test that API errors are wrapped in Exception."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.side_effect = RuntimeError(
            "API rate limit exceeded"
        )

        sdk_client = ClaudeSDKClient(api_key="test-key")

        with self.assertRaises(Exception) as context:
            sdk_client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=2000,
                messages=[{"role": "user", "content": "test"}],
            )

        self.assertIn("Failed to get analysis from Claude", str(context.exception))

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_messages_create_logs_error_if_logger_provided(self, mock_anthropic):
        """Test that errors are logged if logger available."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.side_effect = RuntimeError("API error")

        mock_logger = Mock()
        sdk_client = ClaudeSDKClient(api_key="test-key", logger=mock_logger)

        with self.assertRaises(Exception):  # noqa: B017
            sdk_client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=2000,
                messages=[{"role": "user", "content": "test"}],
            )

        # Verify error was logged
        self.assertTrue(mock_logger.error.called)

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_messages_create_without_logger_still_raises_on_error(self, mock_anthropic):
        """Test that errors raised even without logger."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.side_effect = RuntimeError("API error")

        sdk_client = ClaudeSDKClient(api_key="test-key")  # No logger

        with self.assertRaises(Exception):  # noqa: B017
            sdk_client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=2000,
                messages=[{"role": "user", "content": "test"}],
            )


class TestClaudeSDKClientBackwardCompatibility(unittest.TestCase):
    """Test suite for backward compatibility with direct SDK usage."""

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_response_can_be_used_like_direct_sdk_response(self, mock_anthropic):
        """Test that response from wrapper works identically to direct SDK response."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        # Create realistic response structure
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "Detailed analysis of repository structure"
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response

        sdk_client = ClaudeSDKClient(api_key="test-key")
        response = sdk_client.messages_create(
            model="claude-opus-4-5-20251101",
            max_tokens=2000,
            messages=[{"role": "user", "content": "Analyze repo"}],
        )

        # This is how claude_analyzer.py uses the response (line 98)
        analysis_text = response.content[0].text
        self.assertEqual(analysis_text, "Detailed analysis of repository structure")

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_messages_create_method_signature_matches_spec(self, mock_anthropic):
        """Test that method signature matches specification."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="result")]
        mock_client.messages.create.return_value = mock_response

        sdk_client = ClaudeSDKClient(api_key="test-key")

        # Verify can call with exact signature specified
        response = sdk_client.messages_create(
            model="claude-opus-4-5-20251101",
            max_tokens=2000,
            messages=[{"role": "user", "content": "test"}],
        )

        self.assertIsNotNone(response)

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_init_maintains_api_key_format_compatibility(self, mock_anthropic):
        """Test that API key is passed to Anthropic exactly as received."""
        api_key = "sk-ant-api03-real-key-format-12345"

        ClaudeSDKClient(api_key=api_key)

        # Verify API key passed exactly as-is
        mock_anthropic.assert_called_once_with(api_key=api_key)


class TestClaudeSDKClientInterfaceUnification(unittest.TestCase):
    """Test suite for unified interface with ClaudeCLIClient."""

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_messages_create_has_unified_signature(self, mock_anthropic):
        """Test that messages_create signature matches CLI client spec."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="result")]
        mock_client.messages.create.return_value = mock_response

        sdk_client = ClaudeSDKClient(api_key="test-key")

        # Standard parameters all implementations must support
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Test prompt"},
        ]

        response = sdk_client.messages_create(
            model="claude-opus-4-5-20251101", max_tokens=2000, messages=messages
        )

        # Response must have content structure for unified interface
        self.assertTrue(hasattr(response, "content"))


if __name__ == "__main__":
    unittest.main()
