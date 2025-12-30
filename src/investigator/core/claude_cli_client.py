# ABOUTME: Claude CLI client wrapper for OAuth token authentication via subprocess
# ABOUTME: Implements SDK-compatible interface for calling claude CLI with --print --output-format json

"""
Claude CLI client wrapper that calls `claude --print --output-format json`.

Implements a subprocess-based interface for Claude API using OAuth token authentication
through the official Claude CLI tool. Returns responses compatible with the
Anthropic SDK Message type.

Implements: ClaudeClientProtocol
    - Provides messages_create(model, max_tokens, messages) method
    - Returns MessageResponse objects (compatible with Anthropic SDK structure)
"""

import json
import os
import subprocess  # nosec
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class TextContent:
    """Text content block from Claude response."""

    type: str = "text"
    text: str = ""


@dataclass
class UsageInfo:
    """Token usage information from Claude response."""

    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class MessageResponse:
    """Response object compatible with Anthropic SDK Message type."""

    id: str
    type: str = "message"
    role: str = "assistant"
    content: List[TextContent] = None
    model: str = ""
    stop_reason: str = ""
    stop_sequence: Optional[str] = None
    usage: UsageInfo = None

    def __post_init__(self):
        """Initialize default values."""
        if self.content is None:
            self.content = []
        if self.usage is None:
            self.usage = UsageInfo()


class ClaudeCLIClient:
    """
    Claude CLI client wrapper that calls `claude --print --output-format json`.

    Implements a subprocess-based interface for Claude API using OAuth token authentication
    through the official Claude CLI tool. Returns responses compatible with the
    Anthropic SDK Message type.

    Implements: ClaudeClientProtocol
        - messages_create(model: str, max_tokens: int, messages: list) -> MessageResponse

    Attributes:
        oauth_token: OAuth token for Claude authentication (sk-ant-oat01-...)
        timeout: Subprocess timeout in seconds (default: 300)
        logger: Optional logger for debug/info/error messages
    """

    DEFAULT_TIMEOUT = 300

    def __init__(
        self,
        oauth_token: str,
        timeout: Optional[int] = None,
        logger: Optional[Any] = None,
    ):
        """
        Initialize ClaudeCLIClient.

        Args:
            oauth_token: OAuth token from `claude setup-token` (format: sk-ant-oat01-...)
            timeout: Subprocess timeout in seconds (default: 300 seconds)
            logger: Optional logger object with debug(), info(), error() methods.
                   If not provided, logging is disabled.

        Raises:
            ValueError: If oauth_token is empty or None
        """
        if not oauth_token or not oauth_token.strip():
            raise ValueError("OAuth token cannot be empty")

        self.oauth_token = oauth_token.strip()
        self._timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT
        self.logger = logger

    def messages_create(
        self, model: str, max_tokens: int, messages: List[Dict[str, str]]
    ) -> MessageResponse:
        """
        Create a message using Claude CLI with OAuth authentication.

        Compatible with Anthropic SDK interface: messages.create(model, max_tokens, messages).

        Implements: ClaudeClientProtocol.messages_create()

        Args:
            model: Claude model identifier (e.g., "claude-opus-4-5-20251101")
            max_tokens: Maximum tokens in response
            messages: List of message dicts with "role" and "content" keys

        Returns:
            MessageResponse object with SDK-compatible attributes

        Raises:
            TimeoutError: If subprocess times out
            Exception: If CLI returns non-zero exit code, invalid JSON, or other errors

        Example:
            >>> client = ClaudeCLIClient(oauth_token="sk-ant-oat01-...")
            >>> response = client.messages_create(
            ...     model="claude-opus-4-5-20251101",
            ...     max_tokens=1024,
            ...     messages=[{"role": "user", "content": "Hello"}]
            ... )
            >>> print(response.content[0].text)
        """
        if self.logger:
            self.logger.debug(
                f"Preparing Claude CLI call: model={model}, max_tokens={max_tokens}"
            )

        # Build environment for subprocess
        env = self._prepare_environment()

        # Build CLI command
        cmd = self._build_command(model, max_tokens, messages)

        try:
            # Execute Claude CLI subprocess
            result = subprocess.run(  # nosec - fixed command list
                cmd,
                env=env,
                input=messages[0]["content"] if messages else "",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self._timeout,
                text=True,
            )

            # Check for non-zero exit code
            # Note: CLI may return exit code 1 with valid JSON output (e.g., rate limits)
            # We try to parse the output first to get a better error message
            if result.returncode != 0:
                # Try to extract error from JSON output if available
                error_msg = self._extract_error_from_output(
                    result.stdout, result.stderr
                )
                # Sanitize OAuth token from error message
                error_msg = self._sanitize_token_from_error(error_msg)
                msg = (
                    f"Claude CLI failed with exit code {result.returncode}: {error_msg}"
                )
                if self.logger:
                    self.logger.error(f"Claude CLI request failed: {msg}")
                raise Exception(msg) from None

            # Parse JSON response
            if not result.stdout or not result.stdout.strip():
                error_msg = "Claude CLI returned empty output"
                if self.logger:
                    self.logger.error(f"Claude CLI request failed: {error_msg}")
                raise Exception(error_msg) from None

            try:
                response_data = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                msg = f"Failed to parse Claude CLI JSON output: {str(e)}"
                if self.logger:
                    self.logger.error(f"Claude CLI request failed: {msg}")
                raise Exception(msg) from e

            # Convert JSON to SDK-compatible response object
            response = self._parse_response(response_data)

            if self.logger:
                response_length = (
                    len(response.content[0].text) if response.content else 0
                )
                self.logger.info(
                    f"Received response from Claude CLI ({response_length} characters)"
                )

            return response

        except subprocess.TimeoutExpired as e:
            msg = f"Claude CLI subprocess timed out after {self._timeout} seconds"
            if self.logger:
                self.logger.error(f"Claude CLI request failed: {msg}")
            raise TimeoutError(msg) from e

    def _prepare_environment(self) -> Dict[str, str]:
        """
        Prepare environment variables for subprocess.

        Sets:
        - CLAUDE_CODE_OAUTH_TOKEN: OAuth token for authentication
        - CLAUDE_USE_SUBSCRIPTION: "true" to force subscription mode
        - Removes ANTHROPIC_API_KEY if present (OAuth takes precedence)
        - Passes through other relevant environment variables

        Returns:
            Dictionary with prepared environment variables
        """
        env = os.environ.copy()

        # Set OAuth token
        env["CLAUDE_CODE_OAUTH_TOKEN"] = self.oauth_token

        # Force subscription mode
        env["CLAUDE_USE_SUBSCRIPTION"] = "true"

        # Remove API key if present (OAuth takes precedence)
        env.pop("ANTHROPIC_API_KEY", None)

        return env

    def _build_command(
        self, model: str, max_tokens: int, messages: List[Dict[str, str]]
    ) -> List[str]:
        """
        Build claude CLI command with parameters.

        Constructs: claude --print --output-format json [additional args]

        Args:
            model: Claude model identifier
            max_tokens: Maximum tokens in response
            messages: List of messages to send

        Returns:
            Command as list suitable for subprocess.run()
        """
        # Start with base command
        cmd = ["claude", "--print", "--output-format", "json"]

        # Add model parameter if not default
        if model:
            cmd.extend(["--model", model])

        # Note: max_tokens parameter not supported by Claude CLI
        # The CLI will use model defaults for response length

        # Note: Messages are passed via stdin as prompt
        # The claude CLI will read from stdin if no file is specified

        return cmd

    def _parse_response(self, response_data: Any) -> MessageResponse:
        """
        Parse Claude CLI JSON response into SDK-compatible MessageResponse.

        The CLI returns a list of events when using --output-format json.
        We need to find the event with type="assistant" which contains the message.

        Args:
            response_data: JSON response from Claude CLI (list or dict)

        Returns:
            MessageResponse object with SDK-compatible attributes

        Raises:
            Exception: If no assistant message found in response
        """
        # Handle list response format from CLI
        message_data = None
        if isinstance(response_data, list):
            # Find the assistant message in the event stream
            for event in response_data:
                if isinstance(event, dict) and event.get("type") == "assistant":
                    message_data = event.get("message", {})
                    break

            if not message_data:
                raise Exception("No assistant message found in Claude CLI response")
        else:
            # Handle dict format (direct message)
            message_data = response_data

        # Parse content blocks
        content_list = []
        if "content" in message_data:
            for content_item in message_data["content"]:
                if content_item.get("type") == "text":
                    content_list.append(
                        TextContent(type="text", text=content_item.get("text", ""))
                    )

        # Parse usage information
        usage_data = message_data.get("usage", {})
        usage = UsageInfo(
            input_tokens=usage_data.get("input_tokens", 0),
            output_tokens=usage_data.get("output_tokens", 0),
        )

        # Create response object
        return MessageResponse(
            id=message_data.get("id", ""),
            type=message_data.get("type", "message"),
            role=message_data.get("role", "assistant"),
            content=content_list,
            model=message_data.get("model", ""),
            stop_reason=message_data.get("stop_reason", ""),
            stop_sequence=message_data.get("stop_sequence"),
            usage=usage,
        )

    def _extract_error_from_output(self, stdout: str, stderr: str) -> str:
        """
        Extract error message from CLI output.

        Tries to parse JSON output to find error details, falls back to stderr.

        Args:
            stdout: Standard output from CLI (may contain JSON with error info)
            stderr: Standard error from CLI

        Returns:
            Human-readable error message
        """
        # Try to parse JSON output for better error messages
        if stdout and stdout.strip():
            try:
                response_data = json.loads(stdout)
                if isinstance(response_data, list):
                    # Look for result event with is_error=True
                    for event in response_data:
                        if isinstance(event, dict):
                            if event.get("type") == "result" and event.get("is_error"):
                                return event.get("result", "Unknown error")
                            # Also check assistant message for error content
                            if event.get("type") == "assistant":
                                msg = event.get("message", {})
                                content = msg.get("content", [])
                                if content and content[0].get("type") == "text":
                                    text = content[0].get("text", "")
                                    # Check for rate limit or error messages
                                    if (
                                        "limit" in text.lower()
                                        or "error" in text.lower()
                                    ):
                                        return text
            except json.JSONDecodeError:
                pass

        # Fall back to stderr or unknown error
        return stderr.strip() if stderr and stderr.strip() else "Unknown error"

    def _sanitize_token_from_error(self, error_msg: str) -> str:
        """
        Remove OAuth token from error message for security.

        Sanitizes sensitive token data from error messages before they are
        logged or displayed to users.

        Args:
            error_msg: Error message that may contain token

        Returns:
            Sanitized error message with token removed
        """
        # Replace actual token with placeholder
        if self.oauth_token in error_msg:
            error_msg = error_msg.replace(self.oauth_token, "[REDACTED_OAUTH_TOKEN]")

        # Also replace common patterns of the token (first and last few chars visible)
        token_prefix = (
            self.oauth_token[:20] if len(self.oauth_token) > 20 else self.oauth_token
        )
        if token_prefix in error_msg:
            error_msg = error_msg.replace(token_prefix, "[REDACTED_OAUTH_TOKEN]")

        return error_msg
