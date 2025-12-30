# ABOUTME: Unit tests for Claude client factory
# ABOUTME: Tests factory function creates correct client type based on authentication method

"""
Unit tests for claude_client_factory module.

Tests that create_claude_client() correctly selects between ClaudeSDKClient
(for API key authentication) and ClaudeCLIClient (for OAuth authentication).
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

from investigator.core.claude_client_factory import create_claude_client


class TestClaudeClientFactoryOAuthPath(unittest.TestCase):
    """Test suite for OAuth token authentication path."""

    @patch("investigator.core.claude_client_factory.get_claude_authentication")
    @patch("investigator.core.claude_client_factory.ClaudeCLIClient")
    def test_creates_cli_client_when_oauth_token_detected(
        self, mock_cli_client_class, mock_auth_detector
    ):
        """Should create ClaudeCLIClient when OAuth token is detected."""
        # Setup auth detector to return OAuth
        mock_auth_detector.return_value = {
            "method": "oauth",
            "token": "sk-ant-oat01-oauth-token-123",
            "use_cli": True,
        }

        # Setup mock CLI client
        mock_cli_instance = MagicMock()
        mock_cli_client_class.return_value = mock_cli_instance

        # Call factory
        client = create_claude_client()

        # Verify CLI client was created
        mock_cli_client_class.assert_called_once_with(
            oauth_token="sk-ant-oat01-oauth-token-123", logger=None
        )

        # Verify returned client is the CLI client
        self.assertEqual(client, mock_cli_instance)

    @patch("investigator.core.claude_client_factory.get_claude_authentication")
    @patch("investigator.core.claude_client_factory.ClaudeCLIClient")
    def test_cli_client_receives_oauth_token(
        self, mock_cli_client_class, mock_auth_detector
    ):
        """Should pass OAuth token to ClaudeCLIClient constructor."""
        oauth_token = "sk-ant-oat01-test-token-abcdef"
        mock_auth_detector.return_value = {
            "method": "oauth",
            "token": oauth_token,
            "use_cli": True,
        }

        mock_cli_instance = MagicMock()
        mock_cli_client_class.return_value = mock_cli_instance

        create_claude_client()

        # Verify token passed to CLI client
        mock_cli_client_class.assert_called_once()
        call_kwargs = mock_cli_client_class.call_args[1]
        self.assertEqual(call_kwargs["oauth_token"], oauth_token)

    @patch("investigator.core.claude_client_factory.get_claude_authentication")
    @patch("investigator.core.claude_client_factory.ClaudeCLIClient")
    def test_cli_client_receives_logger_when_provided(
        self, mock_cli_client_class, mock_auth_detector
    ):
        """Should pass logger to ClaudeCLIClient when provided."""
        mock_logger = Mock()
        mock_auth_detector.return_value = {
            "method": "oauth",
            "token": "sk-ant-oat01-token",
            "use_cli": True,
        }

        mock_cli_instance = MagicMock()
        mock_cli_client_class.return_value = mock_cli_instance

        create_claude_client(logger=mock_logger)

        # Verify logger passed to CLI client
        mock_cli_client_class.assert_called_once()
        call_kwargs = mock_cli_client_class.call_args[1]
        self.assertEqual(call_kwargs["logger"], mock_logger)

    @patch("investigator.core.claude_client_factory.get_claude_authentication")
    @patch("investigator.core.claude_client_factory.ClaudeCLIClient")
    def test_cli_client_receives_none_logger_by_default(
        self, mock_cli_client_class, mock_auth_detector
    ):
        """Should pass None as logger to ClaudeCLIClient by default."""
        mock_auth_detector.return_value = {
            "method": "oauth",
            "token": "sk-ant-oat01-token",
            "use_cli": True,
        }

        mock_cli_instance = MagicMock()
        mock_cli_client_class.return_value = mock_cli_instance

        create_claude_client()

        # Verify None passed as logger by default
        mock_cli_client_class.assert_called_once()
        call_kwargs = mock_cli_client_class.call_args[1]
        self.assertIsNone(call_kwargs["logger"])


class TestClaudeClientFactoryAPIKeyPath(unittest.TestCase):
    """Test suite for API key authentication path."""

    @patch("investigator.core.claude_client_factory.get_claude_authentication")
    @patch("investigator.core.claude_client_factory.ClaudeSDKClient")
    def test_creates_sdk_client_when_api_key_detected(
        self, mock_sdk_client_class, mock_auth_detector
    ):
        """Should create ClaudeSDKClient when API key is detected."""
        # Setup auth detector to return API key
        mock_auth_detector.return_value = {
            "method": "api_key",
            "token": "sk-ant-api03-api-key-123",
            "use_cli": False,
        }

        # Setup mock SDK client
        mock_sdk_instance = MagicMock()
        mock_sdk_client_class.return_value = mock_sdk_instance

        # Call factory
        client = create_claude_client()

        # Verify SDK client was created
        mock_sdk_client_class.assert_called_once_with(
            api_key="sk-ant-api03-api-key-123", logger=None
        )

        # Verify returned client is the SDK client
        self.assertEqual(client, mock_sdk_instance)

    @patch("investigator.core.claude_client_factory.get_claude_authentication")
    @patch("investigator.core.claude_client_factory.ClaudeSDKClient")
    def test_sdk_client_receives_api_key(
        self, mock_sdk_client_class, mock_auth_detector
    ):
        """Should pass API key to ClaudeSDKClient constructor."""
        api_key = "sk-ant-api03-test-key-xyz789"
        mock_auth_detector.return_value = {
            "method": "api_key",
            "token": api_key,
            "use_cli": False,
        }

        mock_sdk_instance = MagicMock()
        mock_sdk_client_class.return_value = mock_sdk_instance

        create_claude_client()

        # Verify key passed to SDK client
        mock_sdk_client_class.assert_called_once()
        call_kwargs = mock_sdk_client_class.call_args[1]
        self.assertEqual(call_kwargs["api_key"], api_key)

    @patch("investigator.core.claude_client_factory.get_claude_authentication")
    @patch("investigator.core.claude_client_factory.ClaudeSDKClient")
    def test_sdk_client_receives_logger_when_provided(
        self, mock_sdk_client_class, mock_auth_detector
    ):
        """Should pass logger to ClaudeSDKClient when provided."""
        mock_logger = Mock()
        mock_auth_detector.return_value = {
            "method": "api_key",
            "token": "sk-ant-api03-key",
            "use_cli": False,
        }

        mock_sdk_instance = MagicMock()
        mock_sdk_client_class.return_value = mock_sdk_instance

        create_claude_client(logger=mock_logger)

        # Verify logger passed to SDK client
        mock_sdk_client_class.assert_called_once()
        call_kwargs = mock_sdk_client_class.call_args[1]
        self.assertEqual(call_kwargs["logger"], mock_logger)

    @patch("investigator.core.claude_client_factory.get_claude_authentication")
    @patch("investigator.core.claude_client_factory.ClaudeSDKClient")
    def test_sdk_client_receives_none_logger_by_default(
        self, mock_sdk_client_class, mock_auth_detector
    ):
        """Should pass None as logger to ClaudeSDKClient by default."""
        mock_auth_detector.return_value = {
            "method": "api_key",
            "token": "sk-ant-api03-key",
            "use_cli": False,
        }

        mock_sdk_instance = MagicMock()
        mock_sdk_client_class.return_value = mock_sdk_instance

        create_claude_client()

        # Verify None passed as logger by default
        mock_sdk_client_class.assert_called_once()
        call_kwargs = mock_sdk_client_class.call_args[1]
        self.assertIsNone(call_kwargs["logger"])


class TestClaudeClientFactorySelectionLogic(unittest.TestCase):
    """Test suite for client selection logic."""

    @patch("investigator.core.claude_client_factory.get_claude_authentication")
    @patch("investigator.core.claude_client_factory.ClaudeCLIClient")
    @patch("investigator.core.claude_client_factory.ClaudeSDKClient")
    def test_respects_use_cli_true_from_auth_detector(
        self, mock_sdk_class, mock_cli_class, mock_auth_detector
    ):
        """Should use ClaudeCLIClient when use_cli=True in auth result."""
        mock_auth_detector.return_value = {
            "method": "oauth",
            "token": "oauth-token",
            "use_cli": True,
        }
        mock_cli_instance = MagicMock()
        mock_cli_class.return_value = mock_cli_instance

        client = create_claude_client()

        # Verify CLI client created, not SDK
        mock_cli_class.assert_called_once()
        mock_sdk_class.assert_not_called()
        self.assertEqual(client, mock_cli_instance)

    @patch("investigator.core.claude_client_factory.get_claude_authentication")
    @patch("investigator.core.claude_client_factory.ClaudeCLIClient")
    @patch("investigator.core.claude_client_factory.ClaudeSDKClient")
    def test_respects_use_cli_false_from_auth_detector(
        self, mock_sdk_class, mock_cli_class, mock_auth_detector
    ):
        """Should use ClaudeSDKClient when use_cli=False in auth result."""
        mock_auth_detector.return_value = {
            "method": "api_key",
            "token": "api-key",
            "use_cli": False,
        }
        mock_sdk_instance = MagicMock()
        mock_sdk_class.return_value = mock_sdk_instance

        client = create_claude_client()

        # Verify SDK client created, not CLI
        mock_sdk_class.assert_called_once()
        mock_cli_class.assert_not_called()
        self.assertEqual(client, mock_sdk_instance)

    @patch("investigator.core.claude_client_factory.get_claude_authentication")
    def test_only_calls_auth_detector_once(self, mock_auth_detector):
        """Should call auth_detector exactly once."""
        mock_auth_detector.return_value = {
            "method": "api_key",
            "token": "test-token",
            "use_cli": False,
        }

        with patch("investigator.core.claude_client_factory.ClaudeSDKClient"):
            create_claude_client()

        # Verify auth detector called exactly once
        mock_auth_detector.assert_called_once()


class TestClaudeClientFactoryErrorHandling(unittest.TestCase):
    """Test suite for error handling."""

    @patch("investigator.core.claude_client_factory.get_claude_authentication")
    def test_propagates_auth_detector_error_when_no_credentials(
        self, mock_auth_detector
    ):
        """Should propagate ValueError from auth_detector when no credentials found."""
        # Simulate auth detector finding no credentials
        mock_auth_detector.side_effect = ValueError(
            "No Claude authentication credentials found"
        )

        with self.assertRaises(ValueError) as context:
            create_claude_client()

        self.assertIn(
            "No Claude authentication credentials found", str(context.exception)
        )

    @patch("investigator.core.claude_client_factory.get_claude_authentication")
    @patch("investigator.core.claude_client_factory.ClaudeSDKClient")
    def test_propagates_sdk_client_initialization_error(
        self, mock_sdk_class, mock_auth_detector
    ):
        """Should propagate exceptions from ClaudeSDKClient initialization."""
        mock_auth_detector.return_value = {
            "method": "api_key",
            "token": "test-key",
            "use_cli": False,
        }

        # Simulate SDK client initialization error
        mock_sdk_class.side_effect = Exception("Invalid API key format")

        with self.assertRaises(Exception) as context:
            create_claude_client()

        self.assertIn("Invalid API key format", str(context.exception))

    @patch("investigator.core.claude_client_factory.get_claude_authentication")
    @patch("investigator.core.claude_client_factory.ClaudeCLIClient")
    def test_propagates_cli_client_initialization_error(
        self, mock_cli_class, mock_auth_detector
    ):
        """Should propagate exceptions from ClaudeCLIClient initialization."""
        mock_auth_detector.return_value = {
            "method": "oauth",
            "token": "oauth-token",
            "use_cli": True,
        }

        # Simulate CLI client initialization error
        mock_cli_class.side_effect = ValueError("OAuth token cannot be empty")

        with self.assertRaises(ValueError) as context:
            create_claude_client()

        self.assertIn("OAuth token cannot be empty", str(context.exception))


class TestClaudeClientFactoryInterfaceUnification(unittest.TestCase):
    """Test suite for unified client interface."""

    @patch("investigator.core.claude_client_factory.get_claude_authentication")
    @patch("investigator.core.claude_client_factory.ClaudeSDKClient")
    def test_sdk_client_has_messages_create_method(
        self, mock_sdk_class, mock_auth_detector
    ):
        """Should return SDK client with messages_create method."""
        mock_auth_detector.return_value = {
            "method": "api_key",
            "token": "test-key",
            "use_cli": False,
        }

        mock_sdk_instance = MagicMock()
        mock_sdk_instance.messages_create = MagicMock()
        mock_sdk_class.return_value = mock_sdk_instance

        client = create_claude_client()

        # Verify client has messages_create method
        self.assertTrue(hasattr(client, "messages_create"))
        self.assertTrue(callable(client.messages_create))

    @patch("investigator.core.claude_client_factory.get_claude_authentication")
    @patch("investigator.core.claude_client_factory.ClaudeCLIClient")
    def test_cli_client_has_messages_create_method(
        self, mock_cli_class, mock_auth_detector
    ):
        """Should return CLI client with messages_create method."""
        mock_auth_detector.return_value = {
            "method": "oauth",
            "token": "oauth-token",
            "use_cli": True,
        }

        mock_cli_instance = MagicMock()
        mock_cli_instance.messages_create = MagicMock()
        mock_cli_class.return_value = mock_cli_instance

        client = create_claude_client()

        # Verify client has messages_create method
        self.assertTrue(hasattr(client, "messages_create"))
        self.assertTrue(callable(client.messages_create))

    @patch("investigator.core.claude_client_factory.get_claude_authentication")
    @patch("investigator.core.claude_client_factory.ClaudeSDKClient")
    @patch("investigator.core.claude_client_factory.ClaudeCLIClient")
    def test_both_clients_have_consistent_interface(
        self, mock_cli_class, mock_sdk_class, mock_auth_detector
    ):
        """Both SDK and CLI clients should have messages_create with same signature."""
        # Setup both clients
        mock_sdk_instance = MagicMock()
        mock_sdk_instance.messages_create = MagicMock(return_value="sdk_response")
        mock_sdk_class.return_value = mock_sdk_instance

        mock_cli_instance = MagicMock()
        mock_cli_instance.messages_create = MagicMock(return_value="cli_response")
        mock_cli_class.return_value = mock_cli_instance

        # Test SDK client path
        mock_auth_detector.return_value = {
            "method": "api_key",
            "token": "test-key",
            "use_cli": False,
        }
        sdk_client = create_claude_client()

        # Test CLI client path
        mock_auth_detector.return_value = {
            "method": "oauth",
            "token": "oauth-token",
            "use_cli": True,
        }
        cli_client = create_claude_client()

        # Both should have messages_create
        self.assertTrue(hasattr(sdk_client, "messages_create"))
        self.assertTrue(hasattr(cli_client, "messages_create"))


class TestClaudeClientFactoryLogging(unittest.TestCase):
    """Test suite for optional logger parameter."""

    @patch("investigator.core.claude_client_factory.get_claude_authentication")
    @patch("investigator.core.claude_client_factory.ClaudeSDKClient")
    def test_accepts_optional_logger_parameter(
        self, mock_sdk_class, mock_auth_detector
    ):
        """Should accept optional logger parameter."""
        mock_logger = Mock()
        mock_auth_detector.return_value = {
            "method": "api_key",
            "token": "test-key",
            "use_cli": False,
        }
        mock_sdk_instance = MagicMock()
        mock_sdk_class.return_value = mock_sdk_instance

        # Should not raise TypeError with logger parameter
        create_claude_client(logger=mock_logger)

        mock_sdk_class.assert_called_once()

    @patch("investigator.core.claude_client_factory.get_claude_authentication")
    @patch("investigator.core.claude_client_factory.ClaudeSDKClient")
    def test_works_without_logger_parameter(self, mock_sdk_class, mock_auth_detector):
        """Should work correctly when logger parameter not provided."""
        mock_auth_detector.return_value = {
            "method": "api_key",
            "token": "test-key",
            "use_cli": False,
        }
        mock_sdk_instance = MagicMock()
        mock_sdk_class.return_value = mock_sdk_instance

        # Should not raise TypeError without logger parameter
        create_claude_client()

        mock_sdk_class.assert_called_once()

    @patch("investigator.core.claude_client_factory.get_claude_authentication")
    @patch("investigator.core.claude_client_factory.ClaudeSDKClient")
    def test_logger_parameter_defaults_to_none(
        self, mock_sdk_class, mock_auth_detector
    ):
        """Should default logger parameter to None."""
        mock_auth_detector.return_value = {
            "method": "api_key",
            "token": "test-key",
            "use_cli": False,
        }
        mock_sdk_instance = MagicMock()
        mock_sdk_class.return_value = mock_sdk_instance

        create_claude_client()

        # Verify logger=None passed when not specified
        call_kwargs = mock_sdk_class.call_args[1]
        self.assertIsNone(call_kwargs["logger"])


if __name__ == "__main__":
    unittest.main()
