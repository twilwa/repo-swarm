"""
ABOUTME: Backward compatibility tests for ClaudeSDKClient
ABOUTME: Proves API key flow unchanged and no breaking changes from OAuth implementation

Comprehensive backward compatibility test suite for ClaudeSDKClient.
Verifies that the introduction of OAuth support (via ClaudeCLIClient) does not
break the existing API key authentication flow.
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


class TestAPIKeyFlowUnchanged(unittest.TestCase):
    """Verify API key authentication flow is identical to pre-OAuth behavior."""

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_api_key_passed_verbatim_to_anthropic_sdk(self, mock_anthropic):
        """Test API key is passed exactly as-is to Anthropic SDK (no transformation)."""
        api_key = "sk-ant-api03-exact-format-no-changes-12345"

        ClaudeSDKClient(api_key=api_key)

        # Verify Anthropic called with exact API key
        mock_anthropic.assert_called_once_with(api_key=api_key)

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_messages_create_forwards_all_parameters_unchanged(self, mock_anthropic):
        """Test messages_create forwards all parameters to SDK without modification."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="test")]
        mock_client.messages.create.return_value = mock_response

        sdk_client = ClaudeSDKClient(api_key="test-key")

        # Exact parameters
        model = "claude-opus-4-5-20251101"
        max_tokens = 4096
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "User message"},
            {"role": "assistant", "content": "Assistant reply"},
            {"role": "user", "content": "Follow-up"},
        ]

        sdk_client.messages_create(
            model=model, max_tokens=max_tokens, messages=messages
        )

        # Verify exact forwarding
        mock_client.messages.create.assert_called_once_with(
            model=model, max_tokens=max_tokens, messages=messages
        )

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_response_structure_unchanged_from_sdk(self, mock_anthropic):
        """Test response object is raw SDK response (no wrapper or transformation)."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        # Create SDK-like response
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "SDK response text"
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response

        sdk_client = ClaudeSDKClient(api_key="test-key")
        response = sdk_client.messages_create(
            model="claude-opus-4-5-20251101",
            max_tokens=2000,
            messages=[{"role": "user", "content": "test"}],
        )

        # Verify response is identical object (not wrapped)
        self.assertIs(response, mock_response)
        # Verify can access SDK attributes
        self.assertEqual(response.content[0].text, "SDK response text")


class TestNoSignatureChanges(unittest.TestCase):
    """Verify no breaking changes to public method signatures."""

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_init_signature_accepts_api_key_and_optional_logger(self, mock_anthropic):
        """Test __init__ signature matches spec: (api_key, logger=None)."""
        # Test positional api_key
        client1 = ClaudeSDKClient("key1")
        self.assertIsNotNone(client1)

        # Test keyword api_key
        client2 = ClaudeSDKClient(api_key="key2")
        self.assertIsNotNone(client2)

        # Test with logger
        mock_logger = Mock()
        client3 = ClaudeSDKClient(api_key="key3", logger=mock_logger)
        self.assertEqual(client3.logger, mock_logger)

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_messages_create_signature_accepts_required_parameters(
        self, mock_anthropic
    ):
        """Test messages_create signature: (model, max_tokens, messages)."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="test")]
        mock_client.messages.create.return_value = mock_response

        sdk_client = ClaudeSDKClient(api_key="test-key")

        # Test positional arguments
        response1 = sdk_client.messages_create(
            "claude-opus-4-5-20251101", 2000, [{"role": "user", "content": "test"}]
        )
        self.assertIsNotNone(response1)

        # Test keyword arguments
        response2 = sdk_client.messages_create(
            model="claude-opus-4-5-20251101",
            max_tokens=2000,
            messages=[{"role": "user", "content": "test"}],
        )
        self.assertIsNotNone(response2)

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_no_new_required_parameters_added(self, mock_anthropic):
        """Test no new required parameters break existing code."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="test")]
        mock_client.messages.create.return_value = mock_response

        sdk_client = ClaudeSDKClient(api_key="test-key")

        # This should work without any OAuth-related parameters
        response = sdk_client.messages_create(
            model="claude-opus-4-5-20251101",
            max_tokens=2000,
            messages=[{"role": "user", "content": "test"}],
        )

        self.assertIsNotNone(response)


class TestErrorHandlingPreserved(unittest.TestCase):
    """Verify error handling behavior is unchanged."""

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_api_errors_wrapped_in_exception(self, mock_anthropic):
        """Test SDK errors are wrapped in Exception with descriptive message."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.side_effect = RuntimeError("Original SDK error")

        sdk_client = ClaudeSDKClient(api_key="test-key")

        with self.assertRaises(Exception) as context:
            sdk_client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=2000,
                messages=[{"role": "user", "content": "test"}],
            )

        # Verify error message format preserved
        self.assertIn("Failed to get analysis from Claude", str(context.exception))
        self.assertIn("Original SDK error", str(context.exception))

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_exception_chain_preserved(self, mock_anthropic):
        """Test exception chain is maintained for debugging."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        original_error = ValueError("Rate limit exceeded")
        mock_client.messages.create.side_effect = original_error

        sdk_client = ClaudeSDKClient(api_key="test-key")

        with self.assertRaises(Exception) as context:
            sdk_client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=2000,
                messages=[{"role": "user", "content": "test"}],
            )

        # Verify __cause__ is set for exception chain
        self.assertIsNotNone(context.exception.__cause__)
        self.assertIs(context.exception.__cause__, original_error)

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_error_logging_behavior_preserved(self, mock_anthropic):
        """Test error logging behavior unchanged (logs if logger, silent if not)."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.side_effect = RuntimeError("Test error")

        # With logger - should log
        mock_logger = Mock()
        sdk_client_with_logger = ClaudeSDKClient(api_key="test-key", logger=mock_logger)

        with self.assertRaises(Exception):  # noqa: B017
            sdk_client_with_logger.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=2000,
                messages=[{"role": "user", "content": "test"}],
            )

        self.assertTrue(mock_logger.error.called)

        # Without logger - should not crash
        sdk_client_no_logger = ClaudeSDKClient(api_key="test-key")

        with self.assertRaises(Exception):  # noqa: B017
            sdk_client_no_logger.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=2000,
                messages=[{"role": "user", "content": "test"}],
            )


class TestUsagePatternCompatibility(unittest.TestCase):
    """Test real-world usage patterns remain compatible."""

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_claude_analyzer_usage_pattern_preserved(self, mock_anthropic):
        """Test usage pattern from claude_analyzer.py still works."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        # Simulate realistic response structure
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "## Analysis\n\nThis is the analysis text."
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response

        sdk_client = ClaudeSDKClient(api_key="test-key")

        # This mirrors claude_analyzer.py line 95-98
        response = sdk_client.messages_create(
            model="claude-opus-4-5-20251101",
            max_tokens=4000,
            messages=[
                {"role": "system", "content": "You are an expert code analyst."},
                {"role": "user", "content": "Analyze this repository..."},
            ],
        )

        # Extract text like claude_analyzer does
        analysis_text = response.content[0].text

        self.assertEqual(analysis_text, "## Analysis\n\nThis is the analysis text.")

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_multi_turn_conversation_pattern(self, mock_anthropic):
        """Test multi-turn conversation pattern still works."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "Response text"
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response

        sdk_client = ClaudeSDKClient(api_key="test-key")

        # Multi-turn conversation
        messages = [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "First response"},
            {"role": "user", "content": "Follow-up message"},
        ]

        response = sdk_client.messages_create(
            model="claude-opus-4-5-20251101", max_tokens=2000, messages=messages
        )

        # Verify all messages passed through
        call_args = mock_client.messages.create.call_args
        self.assertEqual(call_args[1]["messages"], messages)

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_logger_optional_behavior_preserved(self, mock_anthropic):
        """Test logger is truly optional (no breaking change)."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="test")]
        mock_client.messages.create.return_value = mock_response

        # Without logger - should work
        sdk_client_no_log = ClaudeSDKClient(api_key="test-key")
        response1 = sdk_client_no_log.messages_create(
            model="claude-opus-4-5-20251101",
            max_tokens=2000,
            messages=[{"role": "user", "content": "test"}],
        )
        self.assertIsNotNone(response1)

        # With logger - should also work
        mock_logger = Mock()
        sdk_client_with_log = ClaudeSDKClient(api_key="test-key", logger=mock_logger)
        response2 = sdk_client_with_log.messages_create(
            model="claude-opus-4-5-20251101",
            max_tokens=2000,
            messages=[{"role": "user", "content": "test"}],
        )
        self.assertIsNotNone(response2)


class TestNoOAuthInterference(unittest.TestCase):
    """Verify OAuth implementation doesn't affect API key flow."""

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_no_oauth_token_parameter_required(self, mock_anthropic):
        """Test ClaudeSDKClient doesn't require OAuth tokens."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="test")]
        mock_client.messages.create.return_value = mock_response

        # Should work with only API key (no OAuth params)
        sdk_client = ClaudeSDKClient(api_key="sk-ant-api-key")
        response = sdk_client.messages_create(
            model="claude-opus-4-5-20251101",
            max_tokens=2000,
            messages=[{"role": "user", "content": "test"}],
        )

        self.assertIsNotNone(response)

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_no_oauth_environment_variable_dependency(self, mock_anthropic):
        """Test SDK client doesn't check OAuth environment variables."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="test")]
        mock_client.messages.create.return_value = mock_response

        # Even if OAuth env vars are set, SDK client uses API key
        import os

        original_env = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
        try:
            os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = "fake-oauth-token"

            sdk_client = ClaudeSDKClient(api_key="sk-ant-api-key")
            response = sdk_client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=2000,
                messages=[{"role": "user", "content": "test"}],
            )

            # Verify Anthropic still called with API key, not OAuth
            mock_anthropic.assert_called_with(api_key="sk-ant-api-key")
            self.assertIsNotNone(response)
        finally:
            if original_env:
                os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = original_env
            else:
                os.environ.pop("CLAUDE_CODE_OAUTH_TOKEN", None)


if __name__ == "__main__":
    unittest.main()
