# ABOUTME: Unit tests for Claude CLI client wrapper for OAuth token authentication
# ABOUTME: Tests subprocess integration, JSON parsing, error handling, and SDK compatibility

import json
import subprocess
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.investigator.core.claude_cli_client import ClaudeCLIClient


class TestClaudeCLIClientMessages:
    """Test suite for ClaudeCLIClient.messages_create() method."""

    def test_messages_create_basic_call(self):
        """Should construct and execute claude CLI command with correct parameters."""
        client = ClaudeCLIClient(oauth_token="sk-ant-oat01-test-token-123")

        mock_response = {
            "id": "msg_123",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "Test response"}],
            "model": "claude-opus-4-5-20251101",
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0, stdout=json.dumps(mock_response), stderr=""
            )

            response = client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=1024,
                messages=[{"role": "user", "content": "Hello"}],
            )

            # Verify subprocess was called
            assert mock_run.called

            # Verify response object has expected attributes
            assert hasattr(response, "id")
            assert hasattr(response, "content")
            assert hasattr(response, "model")
            assert hasattr(response, "usage")

    def test_messages_create_with_logger_logs_request(self):
        """Should log request/response when logger is provided."""
        mock_logger = Mock()
        client = ClaudeCLIClient(
            oauth_token="sk-ant-oat01-test-token-123", logger=mock_logger
        )

        mock_response = {
            "id": "msg_123",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "Test response"}],
            "model": "claude-opus-4-5-20251101",
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0, stdout=json.dumps(mock_response), stderr=""
            )

            client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=1024,
                messages=[{"role": "user", "content": "Hello"}],
            )

            # Verify logger was called
            assert mock_logger.debug.called or mock_logger.info.called

    def test_messages_create_without_logger_still_works(self):
        """Should work without logger (backward compatible)."""
        client = ClaudeCLIClient(oauth_token="sk-ant-oat01-test-token-123")

        mock_response = {
            "id": "msg_123",
            "content": [{"type": "text", "text": "response"}],
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0, stdout=json.dumps(mock_response), stderr=""
            )

            response = client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=1024,
                messages=[{"role": "user", "content": "Test"}],
            )

            assert response is not None

    def test_messages_create_subprocess_command_structure(self):
        """Should call subprocess with correct claude CLI command."""
        client = ClaudeCLIClient(oauth_token="sk-ant-oat01-test-token-123")

        mock_response = {
            "id": "msg_123",
            "content": [{"type": "text", "text": "response"}],
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0, stdout=json.dumps(mock_response), stderr=""
            )

            client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=1024,
                messages=[{"role": "user", "content": "Test"}],
            )

            # Check that subprocess.run was called with list command
            assert mock_run.called
            call_args = mock_run.call_args
            assert call_args is not None

            # First argument should be a list starting with 'claude'
            cmd = call_args[0][0]
            assert isinstance(cmd, list)
            assert cmd[0] == "claude"
            assert "--print" in cmd
            assert "--output-format" in cmd
            assert "json" in cmd

    def test_messages_create_json_parsing(self):
        """Should parse JSON output from CLI stdout correctly."""
        client = ClaudeCLIClient(oauth_token="sk-ant-oat01-test-token-123")

        mock_response = {
            "id": "msg_456",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "Parsed response"}],
            "model": "claude-opus-4-5-20251101",
            "stop_reason": "end_turn",
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0, stdout=json.dumps(mock_response), stderr=""
            )

            response = client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=1024,
                messages=[{"role": "user", "content": "Test"}],
            )

            assert response.id == "msg_456"
            assert response.content[0].text == "Parsed response"

    def test_messages_create_with_timeout(self):
        """Should pass timeout parameter to subprocess.run()."""
        client = ClaudeCLIClient(oauth_token="sk-ant-oat01-test-token-123", timeout=60)

        mock_response = {
            "id": "msg_123",
            "content": [{"type": "text", "text": "response"}],
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0, stdout=json.dumps(mock_response), stderr=""
            )

            client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=1024,
                messages=[{"role": "user", "content": "Test"}],
            )

            # Verify timeout was passed
            call_kwargs = mock_run.call_args[1]
            assert "timeout" in call_kwargs
            assert call_kwargs["timeout"] == 60

    def test_messages_create_default_timeout(self):
        """Should use default 300 second timeout if not specified."""
        client = ClaudeCLIClient(oauth_token="sk-ant-oat01-test-token-123")

        mock_response = {
            "id": "msg_123",
            "content": [{"type": "text", "text": "response"}],
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0, stdout=json.dumps(mock_response), stderr=""
            )

            client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=1024,
                messages=[{"role": "user", "content": "Test"}],
            )

            # Verify default timeout was used
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["timeout"] == 300


class TestClaudeCLIClientEnvironmentSetup:
    """Test suite for environment variable handling in subprocess."""

    def test_oauth_token_passed_to_subprocess(self):
        """Should set CLAUDE_CODE_OAUTH_TOKEN in subprocess environment."""
        oauth_token = "sk-ant-oat01-test-token-456"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        mock_response = {
            "id": "msg_123",
            "content": [{"type": "text", "text": "response"}],
        }

        with patch.dict("os.environ", {"PATH": "/usr/bin", "HOME": "/tmp"}, clear=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(
                    returncode=0, stdout=json.dumps(mock_response), stderr=""
                )

                client.messages_create(
                    model="claude-opus-4-5-20251101",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": "Test"}],
                )

                # Check environment passed to subprocess
                call_kwargs = mock_run.call_args[1]
                assert "env" in call_kwargs
                env = call_kwargs["env"]
                assert env.get("CLAUDE_CODE_OAUTH_TOKEN") == oauth_token

    def test_subscription_mode_enabled(self):
        """Should set CLAUDE_USE_SUBSCRIPTION=true in subprocess environment."""
        client = ClaudeCLIClient(oauth_token="sk-ant-oat01-test-token-123")

        mock_response = {
            "id": "msg_123",
            "content": [{"type": "text", "text": "response"}],
        }

        with patch.dict("os.environ", {"PATH": "/usr/bin", "HOME": "/tmp"}, clear=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(
                    returncode=0, stdout=json.dumps(mock_response), stderr=""
                )

                client.messages_create(
                    model="claude-opus-4-5-20251101",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": "Test"}],
                )

                # Check environment
                call_kwargs = mock_run.call_args[1]
                env = call_kwargs["env"]
                assert env.get("CLAUDE_USE_SUBSCRIPTION") == "true"

    def test_anthropic_api_key_removed_from_env(self):
        """Should remove ANTHROPIC_API_KEY from subprocess environment if present."""
        client = ClaudeCLIClient(oauth_token="sk-ant-oat01-test-token-123")

        mock_response = {
            "id": "msg_123",
            "content": [{"type": "text", "text": "response"}],
        }

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-api03-key"}):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(
                    returncode=0, stdout=json.dumps(mock_response), stderr=""
                )

                client.messages_create(
                    model="claude-opus-4-5-20251101",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": "Test"}],
                )

                # Check that API key was not passed
                call_kwargs = mock_run.call_args[1]
                env = call_kwargs["env"]
                assert (
                    "ANTHROPIC_API_KEY" not in env
                    or env.get("ANTHROPIC_API_KEY") is None
                )

    def test_other_env_vars_passed_through(self):
        """Should pass through other relevant environment variables."""
        client = ClaudeCLIClient(oauth_token="sk-ant-oat01-test-token-123")

        mock_response = {
            "id": "msg_123",
            "content": [{"type": "text", "text": "response"}],
        }

        with patch.dict(
            "os.environ",
            {"PATH": "/usr/bin", "HOME": "/home/user", "CUSTOM_VAR": "custom_value"},
        ):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(
                    returncode=0, stdout=json.dumps(mock_response), stderr=""
                )

                client.messages_create(
                    model="claude-opus-4-5-20251101",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": "Test"}],
                )

                # Check that standard env vars are passed
                call_kwargs = mock_run.call_args[1]
                env = call_kwargs["env"]
                assert "PATH" in env
                assert "HOME" in env


class TestClaudeCLIClientErrorHandling:
    """Test suite for error handling and edge cases."""

    def test_non_zero_exit_code_raises_error(self):
        """Should raise exception when subprocess returns non-zero exit code."""
        client = ClaudeCLIClient(oauth_token="sk-ant-oat01-test-token-123")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1, stdout="", stderr="Claude CLI error: Invalid token"
            )

            with pytest.raises(Exception) as exc_info:
                client.messages_create(
                    model="claude-opus-4-5-20251101",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": "Test"}],
                )

            error_message = str(exc_info.value)
            assert "exit code" in error_message or "failed" in error_message.lower()

    def test_timeout_raises_timeout_error(self):
        """Should raise TimeoutError when subprocess times out."""
        client = ClaudeCLIClient(oauth_token="sk-ant-oat01-test-token-123", timeout=1)

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("claude", 1)

            with pytest.raises(TimeoutError):
                client.messages_create(
                    model="claude-opus-4-5-20251101",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": "Test"}],
                )

    def test_invalid_json_output_raises_error(self):
        """Should raise exception when CLI output is not valid JSON."""
        client = ClaudeCLIClient(oauth_token="sk-ant-oat01-test-token-123")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0, stdout="This is not valid JSON", stderr=""
            )

            with pytest.raises(Exception) as exc_info:
                client.messages_create(
                    model="claude-opus-4-5-20251101",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": "Test"}],
                )

            error_message = str(exc_info.value)
            assert "json" in error_message.lower() or "parse" in error_message.lower()

    def test_oauth_token_sanitized_in_error(self):
        """Should remove OAuth token from error messages (security)."""
        oauth_token = "sk-ant-oat01-super-secret-token-789"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1, stdout="", stderr=f"Error with token {oauth_token}"
            )

            with pytest.raises(Exception) as exc_info:
                client.messages_create(
                    model="claude-opus-4-5-20251101",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": "Test"}],
                )

            error_message = str(exc_info.value)
            # Token should be sanitized/removed from error message
            assert oauth_token not in error_message

    def test_empty_stdout_with_zero_exit_code_raises_error(self):
        """Should raise error when stdout is empty even with zero exit code."""
        client = ClaudeCLIClient(oauth_token="sk-ant-oat01-test-token-123")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            with pytest.raises(Exception):
                client.messages_create(
                    model="claude-opus-4-5-20251101",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": "Test"}],
                )


class TestClaudeCLIClientSDKCompatibility:
    """Test suite for SDK interface compatibility."""

    def test_response_object_has_required_attributes(self):
        """Should return response object with SDK-compatible attributes."""
        client = ClaudeCLIClient(oauth_token="sk-ant-oat01-test-token-123")

        mock_response = {
            "id": "msg_789",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "Test response"}],
            "model": "claude-opus-4-5-20251101",
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {"input_tokens": 15, "output_tokens": 8},
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0, stdout=json.dumps(mock_response), stderr=""
            )

            response = client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=1024,
                messages=[{"role": "user", "content": "Test"}],
            )

            # Check SDK-compatible attributes
            assert response.id == "msg_789"
            assert response.model == "claude-opus-4-5-20251101"
            assert response.content is not None
            assert len(response.content) > 0
            assert response.content[0].text == "Test response"
            assert response.usage is not None
            assert response.usage.input_tokens == 15
            assert response.usage.output_tokens == 8

    def test_response_content_is_list_of_text_blocks(self):
        """Should return content as list of text objects (SDK compatible)."""
        client = ClaudeCLIClient(oauth_token="sk-ant-oat01-test-token-123")

        mock_response = {
            "id": "msg_123",
            "content": [
                {"type": "text", "text": "First paragraph"},
                {"type": "text", "text": "Second paragraph"},
            ],
            "model": "claude-opus-4-5-20251101",
            "usage": {"input_tokens": 10, "output_tokens": 20},
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0, stdout=json.dumps(mock_response), stderr=""
            )

            response = client.messages_create(
                model="claude-opus-4-5-20251101",
                max_tokens=1024,
                messages=[{"role": "user", "content": "Test"}],
            )

            assert len(response.content) == 2
            assert response.content[0].text == "First paragraph"
            assert response.content[1].text == "Second paragraph"

    def test_messages_parameter_format(self):
        """Should accept messages in SDK format (role + content)."""
        client = ClaudeCLIClient(oauth_token="sk-ant-oat01-test-token-123")

        mock_response = {
            "id": "msg_123",
            "content": [{"type": "text", "text": "response"}],
        }

        messages = [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "Second message"},
            {"role": "user", "content": "Third message"},
        ]

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0, stdout=json.dumps(mock_response), stderr=""
            )

            # Should not raise any error with SDK-format messages
            client.messages_create(
                model="claude-opus-4-5-20251101", max_tokens=1024, messages=messages
            )

            assert mock_run.called


class TestClaudeCLIClientInitialization:
    """Test suite for ClaudeCLIClient initialization."""

    def test_initialization_with_oauth_token(self):
        """Should initialize with OAuth token."""
        oauth_token = "sk-ant-oat01-init-test-token"
        client = ClaudeCLIClient(oauth_token=oauth_token)

        assert client is not None
        assert hasattr(client, "messages_create")

    def test_initialization_with_timeout(self):
        """Should initialize with custom timeout value."""
        client = ClaudeCLIClient(oauth_token="sk-ant-oat01-test-token", timeout=120)

        assert client is not None

    def test_initialization_default_timeout(self):
        """Should use default timeout if not specified."""
        client = ClaudeCLIClient(oauth_token="sk-ant-oat01-test-token")

        assert client is not None
        # Default should be 300 seconds
        assert hasattr(client, "_timeout")

    def test_initialization_with_logger(self):
        """Should initialize with logger parameter."""
        mock_logger = Mock()
        client = ClaudeCLIClient(
            oauth_token="sk-ant-oat01-test-token", logger=mock_logger
        )

        assert client is not None
        assert client.logger == mock_logger

    def test_initialization_without_logger(self):
        """Should initialize without logger (backward compatible)."""
        client = ClaudeCLIClient(oauth_token="sk-ant-oat01-test-token")

        assert client is not None
        assert client.logger is None
