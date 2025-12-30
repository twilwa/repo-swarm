"""
ABOUTME: Unit tests for ClaudeCLIClient - wrapper around Claude CLI tool
ABOUTME: Tests subprocess execution, JSON parsing, error handling, and OAuth token sanitization

Unit tests for ClaudeCLIClient wrapper around the Claude CLI subprocess.
Verifies subprocess call construction, JSON output parsing, error handling,
and security measures for OAuth token sanitization.
"""

import json
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

# Add the src directory to the path
sys.path.append(
    __import__("os").path.join(
        __import__("os").path.dirname(__file__), "..", "..", "src"
    )
)

from investigator.core.claude_cli_client import (
    ClaudeCLIClient,
    MessageResponse,
    TextContent,
    UsageInfo,
)


class TestClaudeCLIClientInitialization(unittest.TestCase):
    """Test suite for ClaudeCLIClient initialization."""

    def test_init_with_oauth_token_stores_token(self):
        """Test that initialization stores OAuth token."""
        oauth_token = "sk-ant-oat01-test-token-12345"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        self.assertEqual(client.oauth_token, oauth_token)

    def test_init_strips_whitespace_from_token(self):
        """Test that whitespace is stripped from OAuth token."""
        oauth_token = "  sk-ant-oat01-test-token-12345  \n"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        self.assertEqual(client.oauth_token, "sk-ant-oat01-test-token-12345")

    def test_init_with_empty_token_raises_error(self):
        """Test that empty token raises ValueError."""
        with self.assertRaises(ValueError) as context:
            ClaudeCLIClient(oauth_token="")

        self.assertIn("OAuth token cannot be empty", str(context.exception))

    def test_init_with_whitespace_only_token_raises_error(self):
        """Test that whitespace-only token raises ValueError."""
        with self.assertRaises(ValueError) as context:
            ClaudeCLIClient(oauth_token="   \n  ")

        self.assertIn("OAuth token cannot be empty", str(context.exception))

    def test_init_with_none_token_raises_error(self):
        """Test that None token raises ValueError."""
        with self.assertRaises(ValueError) as context:
            ClaudeCLIClient(oauth_token=None)

        self.assertIn("OAuth token cannot be empty", str(context.exception))

    def test_init_with_custom_timeout(self):
        """Test that custom timeout is stored."""
        oauth_token = "sk-ant-oat01-test-token"
        timeout = 600
        client = ClaudeCLIClient(oauth_token=oauth_token, timeout=timeout)

        self.assertEqual(client._timeout, timeout)

    def test_init_with_default_timeout(self):
        """Test that default timeout is used when not specified."""
        oauth_token = "sk-ant-oat01-test-token"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        self.assertEqual(client._timeout, ClaudeCLIClient.DEFAULT_TIMEOUT)

    def test_init_with_logger(self):
        """Test that logger is properly stored."""
        oauth_token = "sk-ant-oat01-test-token"
        mock_logger = Mock()
        client = ClaudeCLIClient(oauth_token=oauth_token, logger=mock_logger)

        self.assertEqual(client.logger, mock_logger)

    def test_init_without_logger(self):
        """Test that initialization works without logger."""
        oauth_token = "sk-ant-oat01-test-token"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        self.assertIsNone(client.logger)


class TestClaudeCLIClientCommandBuilding(unittest.TestCase):
    """Test suite for CLI command construction."""

    def test_build_command_basic_structure(self):
        """Test that command starts with base claude CLI arguments."""
        oauth_token = "sk-ant-oat01-test-token"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        cmd = client._build_command(
            model="claude-opus-4-5-20251101",
            max_tokens=2000,
            messages=[{"role": "user", "content": "test"}],
        )

        # Verify base command structure
        self.assertEqual(cmd[0], "claude")
        self.assertIn("--print", cmd)
        self.assertIn("--output-format", cmd)
        self.assertIn("json", cmd)

    def test_build_command_includes_model(self):
        """Test that command includes model parameter."""
        oauth_token = "sk-ant-oat01-test-token"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        model = "claude-opus-4-5-20251101"
        cmd = client._build_command(
            model=model, max_tokens=2000, messages=[{"role": "user", "content": "test"}]
        )

        self.assertIn("--model", cmd)
        model_index = cmd.index("--model")
        self.assertEqual(cmd[model_index + 1], model)

    def test_build_command_includes_max_tokens(self):
        """Test that command includes max-tokens parameter."""
        oauth_token = "sk-ant-oat01-test-token"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        max_tokens = 4000
        cmd = client._build_command(
            model="claude-opus-4-5-20251101",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": "test"}],
        )

        self.assertIn("--max-tokens", cmd)
        max_tokens_index = cmd.index("--max-tokens")
        self.assertEqual(cmd[max_tokens_index + 1], str(max_tokens))

    def test_build_command_returns_list(self):
        """Test that command is returned as list suitable for subprocess."""
        oauth_token = "sk-ant-oat01-test-token"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        cmd = client._build_command(
            model="claude-opus-4-5-20251101",
            max_tokens=2000,
            messages=[{"role": "user", "content": "test"}],
        )

        self.assertIsInstance(cmd, list)
        self.assertTrue(all(isinstance(item, str) for item in cmd))


class TestClaudeCLIClientEnvironmentPreparation(unittest.TestCase):
    """Test suite for subprocess environment preparation."""

    @patch.dict("os.environ", {"EXISTING_VAR": "value"}, clear=True)
    def test_prepare_environment_sets_oauth_token(self):
        """Test that environment includes OAuth token."""
        oauth_token = "sk-ant-oat01-test-token-12345"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        env = client._prepare_environment()

        self.assertEqual(env["CLAUDE_CODE_OAUTH_TOKEN"], oauth_token)

    @patch.dict("os.environ", {}, clear=True)
    def test_prepare_environment_sets_subscription_mode(self):
        """Test that environment forces subscription mode."""
        oauth_token = "sk-ant-oat01-test-token"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        env = client._prepare_environment()

        self.assertEqual(env["CLAUDE_USE_SUBSCRIPTION"], "true")

    @patch.dict(
        "os.environ",
        {"ANTHROPIC_API_KEY": "sk-ant-api03-should-be-removed"},
        clear=True,
    )
    def test_prepare_environment_removes_api_key(self):
        """Test that ANTHROPIC_API_KEY is removed (OAuth takes precedence)."""
        oauth_token = "sk-ant-oat01-test-token"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        env = client._prepare_environment()

        self.assertNotIn("ANTHROPIC_API_KEY", env)

    @patch.dict("os.environ", {"PATH": "/usr/bin", "HOME": "/home/user"}, clear=True)
    def test_prepare_environment_preserves_existing_vars(self):
        """Test that other environment variables are preserved."""
        oauth_token = "sk-ant-oat01-test-token"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        env = client._prepare_environment()

        self.assertEqual(env["PATH"], "/usr/bin")
        self.assertEqual(env["HOME"], "/home/user")


class TestClaudeCLIClientJSONParsing(unittest.TestCase):
    """Test suite for JSON response parsing."""

    def test_parse_response_extracts_basic_fields(self):
        """Test that basic response fields are extracted correctly."""
        oauth_token = "sk-ant-oat01-test-token"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        response_data = {
            "id": "msg_12345",
            "type": "message",
            "role": "assistant",
            "model": "claude-opus-4-5-20251101",
            "stop_reason": "end_turn",
            "content": [{"type": "text", "text": "Analysis result"}],
            "usage": {"input_tokens": 100, "output_tokens": 200},
        }

        response = client._parse_response(response_data)

        self.assertEqual(response.id, "msg_12345")
        self.assertEqual(response.type, "message")
        self.assertEqual(response.role, "assistant")
        self.assertEqual(response.model, "claude-opus-4-5-20251101")
        self.assertEqual(response.stop_reason, "end_turn")

    def test_parse_response_extracts_text_content(self):
        """Test that text content is extracted from content blocks."""
        oauth_token = "sk-ant-oat01-test-token"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        response_data = {
            "id": "msg_12345",
            "content": [
                {"type": "text", "text": "First text block"},
                {"type": "text", "text": "Second text block"},
            ],
            "usage": {},
        }

        response = client._parse_response(response_data)

        self.assertEqual(len(response.content), 2)
        self.assertEqual(response.content[0].text, "First text block")
        self.assertEqual(response.content[1].text, "Second text block")
        self.assertEqual(response.content[0].type, "text")

    def test_parse_response_extracts_usage_info(self):
        """Test that token usage information is extracted."""
        oauth_token = "sk-ant-oat01-test-token"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        response_data = {
            "id": "msg_12345",
            "content": [],
            "usage": {"input_tokens": 150, "output_tokens": 300},
        }

        response = client._parse_response(response_data)

        self.assertEqual(response.usage.input_tokens, 150)
        self.assertEqual(response.usage.output_tokens, 300)

    def test_parse_response_handles_missing_fields(self):
        """Test that parsing works with minimal response data."""
        oauth_token = "sk-ant-oat01-test-token"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        response_data = {"id": "msg_12345"}

        response = client._parse_response(response_data)

        self.assertEqual(response.id, "msg_12345")
        self.assertEqual(response.content, [])
        self.assertEqual(response.usage.input_tokens, 0)
        self.assertEqual(response.usage.output_tokens, 0)

    def test_parse_response_handles_empty_content(self):
        """Test that parsing handles empty content array."""
        oauth_token = "sk-ant-oat01-test-token"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        response_data = {"id": "msg_12345", "content": []}

        response = client._parse_response(response_data)

        self.assertEqual(response.content, [])

    def test_parse_response_returns_message_response_type(self):
        """Test that parsed response is MessageResponse instance."""
        oauth_token = "sk-ant-oat01-test-token"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        response_data = {
            "id": "msg_12345",
            "content": [{"type": "text", "text": "result"}],
            "usage": {},
        }

        response = client._parse_response(response_data)

        self.assertIsInstance(response, MessageResponse)


class TestClaudeCLIClientTokenSanitization(unittest.TestCase):
    """Test suite for OAuth token sanitization in error messages."""

    def test_sanitize_token_removes_full_token(self):
        """Test that full OAuth token is removed from error message."""
        oauth_token = "sk-ant-oat01-test-token-12345-full"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        error_msg = f"Authentication failed with token {oauth_token}"
        sanitized = client._sanitize_token_from_error(error_msg)

        self.assertNotIn(oauth_token, sanitized)
        self.assertIn("[REDACTED_OAUTH_TOKEN]", sanitized)

    def test_sanitize_token_removes_token_prefix(self):
        """Test that token prefix (first 20 chars) is also sanitized."""
        oauth_token = "sk-ant-oat01-very-long-token-that-exceeds-twenty-characters"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        token_prefix = oauth_token[:20]
        error_msg = f"Invalid token starting with {token_prefix}..."
        sanitized = client._sanitize_token_from_error(error_msg)

        self.assertNotIn(token_prefix, sanitized)
        self.assertIn("[REDACTED_OAUTH_TOKEN]", sanitized)

    def test_sanitize_token_handles_no_token_in_message(self):
        """Test that messages without token are unchanged."""
        oauth_token = "sk-ant-oat01-test-token"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        error_msg = "Generic error message with no sensitive data"
        sanitized = client._sanitize_token_from_error(error_msg)

        self.assertEqual(sanitized, error_msg)

    def test_sanitize_token_handles_empty_message(self):
        """Test that empty error message is handled."""
        oauth_token = "sk-ant-oat01-test-token"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        error_msg = ""
        sanitized = client._sanitize_token_from_error(error_msg)

        self.assertEqual(sanitized, "")


class TestClaudeCLIClientMessagesCreate(unittest.TestCase):
    """Test suite for messages_create method with subprocess mocking."""

    @patch("investigator.core.claude_cli_client.subprocess.run")
    def test_messages_create_success_returns_message_response(self, mock_run):
        """Test that successful CLI call returns MessageResponse."""
        oauth_token = "sk-ant-oat01-test-token"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        # Mock successful subprocess response
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(
            {
                "id": "msg_12345",
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": "Analysis complete"}],
                "model": "claude-opus-4-5-20251101",
                "usage": {"input_tokens": 100, "output_tokens": 200},
            }
        )
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        response = client.messages_create(
            model="claude-opus-4-5-20251101",
            max_tokens=2000,
            messages=[{"role": "user", "content": "Analyze this"}],
        )

        self.assertIsInstance(response, MessageResponse)
        self.assertEqual(response.id, "msg_12345")
        self.assertEqual(response.content[0].text, "Analysis complete")

    @patch("investigator.core.claude_cli_client.subprocess.run")
    def test_messages_create_calls_subprocess_with_correct_command(self, mock_run):
        """Test that subprocess.run is called with correct command structure."""
        oauth_token = "sk-ant-oat01-test-token"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(
            {"id": "msg_12345", "content": [{"type": "text", "text": "result"}]}
        )
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        client.messages_create(
            model="claude-opus-4-5-20251101",
            max_tokens=2000,
            messages=[{"role": "user", "content": "test"}],
        )

        # Verify subprocess.run was called
        self.assertTrue(mock_run.called)
        call_args = mock_run.call_args

        # Verify command structure
        cmd = call_args[0][0]
        self.assertEqual(cmd[0], "claude")
        self.assertIn("--print", cmd)
        self.assertIn("--output-format", cmd)
        self.assertIn("json", cmd)

    @patch("investigator.core.claude_cli_client.subprocess.run")
    def test_messages_create_sets_correct_environment(self, mock_run):
        """Test that subprocess is called with correct environment variables."""
        oauth_token = "sk-ant-oat01-test-token-12345"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(
            {"id": "msg_12345", "content": [{"type": "text", "text": "result"}]}
        )
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        client.messages_create(
            model="claude-opus-4-5-20251101",
            max_tokens=2000,
            messages=[{"role": "user", "content": "test"}],
        )

        # Verify environment was set
        call_args = mock_run.call_args
        env = call_args[1]["env"]

        self.assertEqual(env["CLAUDE_CODE_OAUTH_TOKEN"], oauth_token)
        self.assertEqual(env["CLAUDE_USE_SUBSCRIPTION"], "true")
        self.assertNotIn("ANTHROPIC_API_KEY", env)

    @patch("investigator.core.claude_cli_client.subprocess.run")
    def test_messages_create_uses_correct_timeout(self, mock_run):
        """Test that subprocess uses specified timeout."""
        oauth_token = "sk-ant-oat01-test-token"
        timeout = 600
        client = ClaudeCLIClient(oauth_token=oauth_token, timeout=timeout)

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(
            {"id": "msg_12345", "content": [{"type": "text", "text": "result"}]}
        )
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        client.messages_create(
            model="claude-opus-4-5-20251101",
            max_tokens=2000,
            messages=[{"role": "user", "content": "test"}],
        )

        # Verify timeout was passed to subprocess.run
        call_args = mock_run.call_args
        self.assertEqual(call_args[1]["timeout"], timeout)

    @patch("investigator.core.claude_cli_client.subprocess.run")
    def test_messages_create_with_logger_logs_debug(self, mock_run):
        """Test that debug logging occurs when logger is provided."""
        oauth_token = "sk-ant-oat01-test-token"
        mock_logger = Mock()
        client = ClaudeCLIClient(oauth_token=oauth_token, logger=mock_logger)

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(
            {"id": "msg_12345", "content": [{"type": "text", "text": "result"}]}
        )
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        client.messages_create(
            model="claude-opus-4-5-20251101",
            max_tokens=2000,
            messages=[{"role": "user", "content": "test"}],
        )

        # Verify debug and info logs were called
        self.assertTrue(mock_logger.debug.called)
        self.assertTrue(mock_logger.info.called)


class TestClaudeCLIClientErrorHandling(unittest.TestCase):
    """Test suite for error handling during subprocess execution."""

    @patch("investigator.core.claude_cli_client.subprocess.run")
    def test_messages_create_raises_on_non_zero_exit_code(self, mock_run):
        """Test that non-zero exit code raises Exception."""
        oauth_token = "sk-ant-oat01-test-token"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Authentication failed"
        mock_run.return_value = mock_result

        with self.assertRaises(Exception) as context:
            client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=2000,
                messages=[{"role": "user", "content": "test"}],
            )

        self.assertIn("Claude CLI failed with exit code 1", str(context.exception))
        self.assertIn("Authentication failed", str(context.exception))

    @patch("investigator.core.claude_cli_client.subprocess.run")
    def test_messages_create_sanitizes_token_in_error(self, mock_run):
        """Test that OAuth token is sanitized from error messages."""
        oauth_token = "sk-ant-oat01-test-token-secret"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = f"Invalid token: {oauth_token}"
        mock_run.return_value = mock_result

        with self.assertRaises(Exception) as context:
            client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=2000,
                messages=[{"role": "user", "content": "test"}],
            )

        error_message = str(context.exception)
        self.assertNotIn(oauth_token, error_message)
        self.assertIn("[REDACTED_OAUTH_TOKEN]", error_message)

    @patch("investigator.core.claude_cli_client.subprocess.run")
    def test_messages_create_raises_on_empty_output(self, mock_run):
        """Test that empty stdout raises Exception."""
        oauth_token = "sk-ant-oat01-test-token"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        with self.assertRaises(Exception) as context:
            client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=2000,
                messages=[{"role": "user", "content": "test"}],
            )

        self.assertIn("empty output", str(context.exception))

    @patch("investigator.core.claude_cli_client.subprocess.run")
    def test_messages_create_raises_on_invalid_json(self, mock_run):
        """Test that invalid JSON in stdout raises Exception."""
        oauth_token = "sk-ant-oat01-test-token"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Not valid JSON at all"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        with self.assertRaises(Exception) as context:
            client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=2000,
                messages=[{"role": "user", "content": "test"}],
            )

        self.assertIn("Failed to parse Claude CLI JSON output", str(context.exception))

    @patch("investigator.core.claude_cli_client.subprocess.run")
    def test_messages_create_raises_timeout_error(self, mock_run):
        """Test that subprocess timeout raises TimeoutError."""
        oauth_token = "sk-ant-oat01-test-token"
        client = ClaudeCLIClient(oauth_token=oauth_token, timeout=10)

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=10)

        with self.assertRaises(TimeoutError) as context:
            client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=2000,
                messages=[{"role": "user", "content": "test"}],
            )

        self.assertIn("timed out after 10 seconds", str(context.exception))

    @patch("investigator.core.claude_cli_client.subprocess.run")
    def test_messages_create_logs_error_with_logger(self, mock_run):
        """Test that errors are logged when logger is available."""
        oauth_token = "sk-ant-oat01-test-token"
        mock_logger = Mock()
        client = ClaudeCLIClient(oauth_token=oauth_token, logger=mock_logger)

        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "CLI error"
        mock_run.return_value = mock_result

        with self.assertRaises(Exception):  # noqa: B017
            client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=2000,
                messages=[{"role": "user", "content": "test"}],
            )

        # Verify error was logged
        self.assertTrue(mock_logger.error.called)

    @patch("investigator.core.claude_cli_client.subprocess.run")
    def test_messages_create_without_logger_still_raises(self, mock_run):
        """Test that errors are raised even without logger."""
        oauth_token = "sk-ant-oat01-test-token"
        client = ClaudeCLIClient(oauth_token=oauth_token)  # No logger

        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error"
        mock_run.return_value = mock_result

        with self.assertRaises(Exception):  # noqa: B017
            client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=2000,
                messages=[{"role": "user", "content": "test"}],
            )


class TestClaudeCLIClientBackwardCompatibility(unittest.TestCase):
    """Test suite for backward compatibility with SDK interface."""

    @patch("investigator.core.claude_cli_client.subprocess.run")
    def test_response_structure_matches_sdk(self, mock_run):
        """Test that response structure is compatible with SDK response."""
        oauth_token = "sk-ant-oat01-test-token"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(
            {
                "id": "msg_12345",
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": "Analysis result"}],
                "model": "claude-opus-4-5-20251101",
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 100, "output_tokens": 200},
            }
        )
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        response = client.messages_create(
            model="claude-opus-4-5-20251101",
            max_tokens=2000,
            messages=[{"role": "user", "content": "Analyze repo"}],
        )

        # Verify can access response like SDK (same as claude_analyzer.py line 98)
        analysis_text = response.content[0].text
        self.assertEqual(analysis_text, "Analysis result")

    @patch("investigator.core.claude_cli_client.subprocess.run")
    def test_messages_create_signature_matches_sdk_client(self, mock_run):
        """Test that method signature matches SDK client interface."""
        oauth_token = "sk-ant-oat01-test-token"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(
            {"id": "msg_12345", "content": [{"type": "text", "text": "result"}]}
        )
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # Verify can call with exact same signature as SDK client
        response = client.messages_create(
            model="claude-opus-4-5-20251101",
            max_tokens=2000,
            messages=[{"role": "user", "content": "test"}],
        )

        self.assertIsNotNone(response)


class TestMessageResponseDataClass(unittest.TestCase):
    """Test suite for MessageResponse dataclass."""

    def test_message_response_post_init_defaults(self):
        """Test that __post_init__ sets default values correctly."""
        response = MessageResponse(id="msg_12345")

        self.assertEqual(response.content, [])
        self.assertIsInstance(response.usage, UsageInfo)
        self.assertEqual(response.usage.input_tokens, 0)

    def test_message_response_with_content(self):
        """Test MessageResponse with content."""
        content = [TextContent(type="text", text="Test content")]
        response = MessageResponse(id="msg_12345", content=content)

        self.assertEqual(len(response.content), 1)
        self.assertEqual(response.content[0].text, "Test content")

    def test_text_content_defaults(self):
        """Test TextContent default values."""
        content = TextContent()

        self.assertEqual(content.type, "text")
        self.assertEqual(content.text, "")

    def test_usage_info_defaults(self):
        """Test UsageInfo default values."""
        usage = UsageInfo()

        self.assertEqual(usage.input_tokens, 0)
        self.assertEqual(usage.output_tokens, 0)


if __name__ == "__main__":
    unittest.main()
