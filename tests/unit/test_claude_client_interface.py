# ABOUTME: Protocol conformance tests for ClaudeClient interface
# ABOUTME: Validates that both SDK and CLI clients implement the common interface correctly

"""
Tests for ClaudeClient interface conformance and type safety.

Validates that:
1. Both ClaudeSDKClient and ClaudeCLIClient implement the interface
2. The interface definition is correct (typing.Protocol)
3. Type checking passes (mypy/typing validation)
4. Both clients have compatible signatures and return types
"""

import sys
import unittest
from typing import Any, List, Protocol, runtime_checkable
from unittest.mock import MagicMock, Mock, patch

# Add the src directory to the path
sys.path.append(
    __import__("os").path.join(
        __import__("os").path.dirname(__file__), "..", "..", "src"
    )
)

from investigator.core.claude_cli_client import ClaudeCLIClient
from investigator.core.claude_sdk_client import ClaudeSDKClient


@runtime_checkable
class ClaudeClientProtocol(Protocol):
    """
    Protocol defining the interface for Claude client implementations.

    All Claude client implementations (SDK-based, CLI-based, etc.) must
    provide this interface for seamless substitution.

    Methods:
        messages_create: Send a message to Claude and receive a response.
    """

    def messages_create(self, model: str, max_tokens: int, messages: List[dict]) -> Any:
        """
        Send a message to Claude and get a response.

        Args:
            model: Claude model identifier (e.g., "claude-opus-4-5-20251101")
            max_tokens: Maximum tokens in the response
            messages: List of message dicts with "role" and "content" keys

        Returns:
            Response object with structure: {content: [{text: str}]}
        """
        ...


class TestClaudeSDKClientConformance(unittest.TestCase):
    """Test that ClaudeSDKClient conforms to ClaudeClient interface."""

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_claude_sdk_client_has_messages_create_method(self, mock_anthropic):
        """Test that ClaudeSDKClient has messages_create method."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        sdk_client = ClaudeSDKClient(api_key="test-key")

        # Verify method exists
        self.assertTrue(hasattr(sdk_client, "messages_create"))
        self.assertTrue(callable(sdk_client.messages_create))

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_claude_sdk_client_messages_create_signature(self, mock_anthropic):
        """Test that messages_create has correct signature."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="result")]
        mock_client.messages.create.return_value = mock_response

        sdk_client = ClaudeSDKClient(api_key="test-key")

        # Verify can call with protocol signature
        response = sdk_client.messages_create(
            model="claude-opus-4-5-20251101",
            max_tokens=2000,
            messages=[{"role": "user", "content": "test"}],
        )

        self.assertIsNotNone(response)

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_claude_sdk_client_returns_response_with_content(self, mock_anthropic):
        """Test that response has content attribute."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "Analysis result"
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response

        sdk_client = ClaudeSDKClient(api_key="test-key")

        response = sdk_client.messages_create(
            model="claude-opus-4-5-20251101",
            max_tokens=2000,
            messages=[{"role": "user", "content": "test"}],
        )

        # Response must have content
        self.assertTrue(hasattr(response, "content"))
        self.assertIsInstance(response.content, list)
        self.assertTrue(len(response.content) > 0)

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_claude_sdk_client_conforms_to_protocol(self, mock_anthropic):
        """Test that ClaudeSDKClient conforms to ClaudeClientProtocol."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        sdk_client = ClaudeSDKClient(api_key="test-key")

        # Check if instance conforms to protocol
        # (runtime check for Protocol implementation)
        self.assertTrue(
            isinstance(sdk_client, ClaudeClientProtocol),
            "ClaudeSDKClient should conform to ClaudeClientProtocol",
        )

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_claude_sdk_client_method_callable_with_protocol_args(self, mock_anthropic):
        """Test that messages_create accepts protocol-defined arguments."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="result")]
        mock_client.messages.create.return_value = mock_response

        sdk_client = ClaudeSDKClient(api_key="test-key")

        # Should accept all protocol-defined arguments
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Analyze this repo"},
        ]

        # Call with protocol signature
        response = sdk_client.messages_create(
            model="claude-opus-4-5-20251101", max_tokens=4000, messages=messages
        )

        self.assertIsNotNone(response)


class TestClaudeCLIClientConformance(unittest.TestCase):
    """Test that ClaudeCLIClient conforms to ClaudeClient interface."""

    def test_claude_cli_client_has_messages_create_method(self):
        """Test that ClaudeCLIClient has messages_create method."""
        cli_client = ClaudeCLIClient(oauth_token="sk-ant-oat01-test-token")

        # Verify method exists
        self.assertTrue(hasattr(cli_client, "messages_create"))
        self.assertTrue(callable(cli_client.messages_create))

    def test_claude_cli_client_messages_create_signature(self):
        """Test that messages_create has correct signature."""
        cli_client = ClaudeCLIClient(oauth_token="sk-ant-oat01-test-token")

        mock_response_data = {
            "id": "msg_123",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "result"}],
            "model": "claude-opus-4-5-20251101",
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout=__import__("json").dumps(mock_response_data),
                stderr="",
            )

            # Verify can call with protocol signature
            response = cli_client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=2000,
                messages=[{"role": "user", "content": "test"}],
            )

            self.assertIsNotNone(response)

    def test_claude_cli_client_returns_response_with_content(self):
        """Test that response has content attribute."""
        cli_client = ClaudeCLIClient(oauth_token="sk-ant-oat01-test-token")

        mock_response_data = {
            "id": "msg_456",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "Analysis result"}],
            "model": "claude-opus-4-5-20251101",
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout=__import__("json").dumps(mock_response_data),
                stderr="",
            )

            response = cli_client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=2000,
                messages=[{"role": "user", "content": "test"}],
            )

            # Response must have content
            self.assertTrue(hasattr(response, "content"))
            self.assertIsInstance(response.content, list)
            self.assertTrue(len(response.content) > 0)

    def test_claude_cli_client_conforms_to_protocol(self):
        """Test that ClaudeCLIClient conforms to ClaudeClientProtocol."""
        cli_client = ClaudeCLIClient(oauth_token="sk-ant-oat01-test-token")

        # Check if instance conforms to protocol
        # (runtime check for Protocol implementation)
        self.assertTrue(
            isinstance(cli_client, ClaudeClientProtocol),
            "ClaudeCLIClient should conform to ClaudeClientProtocol",
        )

    def test_claude_cli_client_method_callable_with_protocol_args(self):
        """Test that messages_create accepts protocol-defined arguments."""
        cli_client = ClaudeCLIClient(oauth_token="sk-ant-oat01-test-token")

        mock_response_data = {
            "id": "msg_789",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "result"}],
            "model": "claude-opus-4-5-20251101",
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout=__import__("json").dumps(mock_response_data),
                stderr="",
            )

            # Should accept all protocol-defined arguments
            messages = [
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "Analyze this repo"},
            ]

            # Call with protocol signature
            response = cli_client.messages_create(
                model="claude-opus-4-5-20251101", max_tokens=4000, messages=messages
            )

            self.assertIsNotNone(response)


class TestClientInterfaceCompatibility(unittest.TestCase):
    """Test that both clients are compatible with the common interface."""

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_both_clients_accept_same_arguments(self, mock_anthropic):
        """Test that both clients accept same method arguments."""
        # Setup SDK client
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="result")]
        mock_client.messages.create.return_value = mock_response

        sdk_client = ClaudeSDKClient(api_key="test-key")

        # Setup CLI client
        cli_client = ClaudeCLIClient(oauth_token="sk-ant-oat01-test-token")

        # Common arguments
        model = "claude-opus-4-5-20251101"
        max_tokens = 2000
        messages = [{"role": "user", "content": "test"}]

        # Both should accept same arguments
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout=__import__("json").dumps(
                    {
                        "id": "msg_123",
                        "content": [{"type": "text", "text": "result"}],
                    }
                ),
                stderr="",
            )

            sdk_response = sdk_client.messages_create(
                model=model, max_tokens=max_tokens, messages=messages
            )
            cli_response = cli_client.messages_create(
                model=model, max_tokens=max_tokens, messages=messages
            )

            self.assertIsNotNone(sdk_response)
            self.assertIsNotNone(cli_response)

    @patch("investigator.core.claude_sdk_client.Anthropic")
    def test_both_clients_return_compatible_responses(self, mock_anthropic):
        """Test that both clients return compatible response structures."""
        # Setup SDK client
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "SDK response"
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response

        sdk_client = ClaudeSDKClient(api_key="test-key")

        # Setup CLI client
        cli_client = ClaudeCLIClient(oauth_token="sk-ant-oat01-test-token")

        # Call both clients
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout=__import__("json").dumps(
                    {
                        "id": "msg_123",
                        "content": [{"type": "text", "text": "CLI response"}],
                    }
                ),
                stderr="",
            )

            sdk_response = sdk_client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=2000,
                messages=[{"role": "user", "content": "test"}],
            )
            cli_response = cli_client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=2000,
                messages=[{"role": "user", "content": "test"}],
            )

            # Both should have content
            self.assertTrue(hasattr(sdk_response, "content"))
            self.assertTrue(hasattr(cli_response, "content"))

            # Content should be iterable
            self.assertIsInstance(sdk_response.content, list)
            self.assertIsInstance(cli_response.content, list)

            # Content should have text
            self.assertTrue(hasattr(sdk_response.content[0], "text"))
            self.assertTrue(hasattr(cli_response.content[0], "text"))


class TestClientProtocolDefinition(unittest.TestCase):
    """Test that the protocol definition is correct and usable."""

    def test_protocol_is_runtime_checkable(self):
        """Test that protocol has @runtime_checkable decorator."""
        # Protocol should support isinstance() checks
        from investigator.core.claude_client_interface import (
            ClaudeClientProtocol as IfaceProtocol,
        )

        self.assertTrue(hasattr(IfaceProtocol, "__protocol_attrs__"))

    def test_protocol_defines_messages_create_method(self):
        """Test that protocol defines messages_create method."""
        from investigator.core.claude_client_interface import (
            ClaudeClientProtocol as IfaceProtocol,
        )

        # Check if protocol has the method
        self.assertIn("messages_create", dir(IfaceProtocol))

    def test_protocol_method_has_correct_annotations(self):
        """Test that protocol method has type hints."""
        from investigator.core.claude_client_interface import (
            ClaudeClientProtocol as IfaceProtocol,
        )

        # Get the method
        method = getattr(IfaceProtocol, "messages_create")

        # Should have __annotations__
        self.assertTrue(hasattr(method, "__annotations__"))


if __name__ == "__main__":
    unittest.main()
