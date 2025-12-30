# ABOUTME: ClaudeClient Protocol - Common interface for Claude client implementations
# ABOUTME: Defines the contract that all Claude clients must implement (SDK, CLI, etc.)

"""
Protocol definition for Claude client implementations.

Provides a common interface that all Claude client implementations must satisfy:
- ClaudeSDKClient (API key authentication)
- ClaudeCLIClient (OAuth token authentication)
- Future implementations (custom, cached, wrapped, etc.)

This enables seamless substitution of different client implementations while
maintaining type safety and interface consistency.

Protocol:
    ClaudeClientProtocol: Common interface for all Claude clients
        - messages_create(model, max_tokens, messages) -> response

Usage:
    >>> from investigator.core.claude_client_interface import ClaudeClientProtocol
    >>> from investigator.core.claude_sdk_client import ClaudeSDKClient
    >>>
    >>> client: ClaudeClientProtocol = ClaudeSDKClient(api_key="sk-ant-...")
    >>> response = client.messages_create(
    ...     model="claude-opus-4-5-20251101",
    ...     max_tokens=2000,
    ...     messages=[{"role": "user", "content": "Analyze this code"}]
    ... )
    >>> print(response.content[0].text)
"""

from typing import Any, List, Protocol, runtime_checkable


@runtime_checkable
class ClaudeClientProtocol(Protocol):
    """
    Protocol defining the interface for Claude client implementations.

    All Claude client implementations (SDK-based, CLI-based, etc.) must
    provide this interface for seamless substitution and type safety.

    Any class that implements messages_create() with this signature will
    automatically conform to this protocol (structural typing).

    Methods:
        messages_create: Send a message to Claude and receive a response.
            Required parameters:
                - model: Claude model identifier string
                - max_tokens: Maximum tokens in response (int)
                - messages: List of message dictionaries
            Required return:
                - Response object with .content attribute (list of content blocks)
                - Each content block must have .text attribute
    """

    def messages_create(self, model: str, max_tokens: int, messages: List[dict]) -> Any:
        """
        Send a message to Claude and get a response.

        Unified interface for both API key and OAuth authentication methods.
        Implementations may return different response object types, but all
        must have the structure: response.content[0].text

        Args:
            model: Claude model identifier (e.g., "claude-opus-4-5-20251101")
            max_tokens: Maximum tokens in the response (e.g., 2000)
            messages: List of message dictionaries with keys:
                - "role": "user" | "assistant" | "system"
                - "content": Text content of the message
                Example: [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there!"},
                ]

        Returns:
            Response object. All implementations must provide:
            - response.content: List of content blocks
            - response.content[0]: First content block
            - response.content[0].text: Text content as string

        Raises:
            Exception: If the API call fails (timeout, invalid auth, API error, etc.)
        """
        ...
