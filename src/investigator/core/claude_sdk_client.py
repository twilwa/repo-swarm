"""
ABOUTME: ClaudeSDKClient - Wrapper for Anthropic SDK with unified interface
ABOUTME: Enables dual authentication (API key and OAuth) by providing consistent interface

Wrapper around the Anthropic SDK for Claude API interactions.
Maintains exact backward compatibility with direct SDK usage while enabling
a unified interface for both API key and OAuth authentication methods.
"""

from typing import Any, Optional

from anthropic import Anthropic


class ClaudeSDKClient:
    """
    Wrapper around the Anthropic SDK for Claude API interactions.

    Provides a unified interface for message creation that matches the
    ClaudeCLIClient, enabling seamless switching between API key and
    OAuth authentication methods.

    Attributes:
        client: Anthropic SDK client instance
        logger: Optional logger for debug/info/error messages
    """

    def __init__(self, api_key: str, logger: Optional[Any] = None):
        """
        Initialize the ClaudeSDKClient with an API key.

        Args:
            api_key: Anthropic API key (format: sk-ant-*)
            logger: Optional logger object with debug(), info(), error() methods
                   If not provided, logging is disabled
        """
        self.client = Anthropic(api_key=api_key)
        self.logger = logger

    def messages_create(self, model: str, max_tokens: int, messages: list) -> Any:
        """
        Send a message to Claude and get a response.

        Unified interface for both API key and OAuth authentication methods.
        Returns the raw Anthropic SDK response object for backward compatibility.

        Args:
            model: Claude model identifier (e.g., "claude-opus-4-5-20251101")
            max_tokens: Maximum tokens in the response
            messages: List of message dictionaries with "role" and "content"
                     (format: [{"role": "user|assistant", "content": "text"}])

        Returns:
            Anthropic SDK Message response object with structure:
            - response.content[0].text: The text content of the response

        Raises:
            Exception: If the API call fails, with wrapped error message
        """
        try:
            if self.logger:
                self.logger.debug(
                    f"Preparing Claude API call: model={model}, max_tokens={max_tokens}"
                )

            response = self.client.messages.create(
                model=model, max_tokens=max_tokens, messages=messages
            )

            if self.logger:
                self.logger.info(
                    f"Received response from Claude API ({len(response.content[0].text)} characters)"
                )

            return response

        except Exception as e:
            if self.logger:
                self.logger.error(f"Claude API request failed: {str(e)}")
            raise Exception(f"Failed to get analysis from Claude: {str(e)}") from e
