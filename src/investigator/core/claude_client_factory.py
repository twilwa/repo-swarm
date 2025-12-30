# ABOUTME: Claude client factory for creating appropriate client based on authentication method
# ABOUTME: Routes to ClaudeSDKClient for API keys or ClaudeCLIClient for OAuth tokens

"""
Factory module for creating Claude clients with automatic authentication detection.

This module provides a single factory function that detects available credentials
(OAuth token or API key) and creates the appropriate client type:
- ClaudeCLIClient for OAuth token authentication (via CLI)
- ClaudeSDKClient for API key authentication (direct SDK)

The factory automatically passes optional logger to both client types.
"""

from typing import Any, Optional

from investigator.core.auth_detector import get_claude_authentication
from investigator.core.claude_cli_client import ClaudeCLIClient
from investigator.core.claude_sdk_client import ClaudeSDKClient


def create_claude_client(logger: Optional[Any] = None) -> Any:
    """
    Create a Claude client with automatic authentication method detection.

    Detects available credentials using get_claude_authentication() and creates
    the appropriate client type:
    - Returns ClaudeCLIClient if OAuth token is detected (use_cli=True)
    - Returns ClaudeSDKClient if API key is detected (use_cli=False)

    Both client types implement the same messages_create() interface, enabling
    seamless switching between authentication methods without code changes.

    Args:
        logger: Optional logger object with debug(), info(), error() methods.
               If provided, passed to both client types for request/response logging.
               Defaults to None (logging disabled).

    Returns:
        Either ClaudeCLIClient or ClaudeSDKClient instance, depending on
        which credentials were detected. Both implement the unified interface:
        - messages_create(model: str, max_tokens: int, messages: list) -> response

    Raises:
        ValueError: If no credentials found in environment (from get_claude_authentication)
        ValueError: If OAuth token is invalid or empty (from ClaudeCLIClient init)
        Exception: If SDK client initialization fails or credentials are invalid

    Examples:
        >>> # With OAuth token (uses CLI)
        >>> import os
        >>> os.environ['CLAUDE_CODE_OAUTH_TOKEN'] = 'sk-ant-oat01-...'
        >>> client = create_claude_client()
        >>> # client is ClaudeCLIClient instance

        >>> # With API key (uses SDK)
        >>> os.environ['ANTHROPIC_API_KEY'] = 'sk-ant-api03-...'
        >>> client = create_claude_client(logger=logging_instance)
        >>> # client is ClaudeSDKClient instance

        >>> # With logger for request tracking
        >>> import logging
        >>> logger = logging.getLogger(__name__)
        >>> client = create_claude_client(logger=logger)
    """
    # Detect which credentials are available
    auth_result = get_claude_authentication()

    # Route to appropriate client based on use_cli flag
    if auth_result["use_cli"]:
        # OAuth token detected - use Claude CLI client
        return ClaudeCLIClient(oauth_token=auth_result["token"], logger=logger)
    else:
        # API key detected - use SDK client
        return ClaudeSDKClient(api_key=auth_result["token"], logger=logger)
