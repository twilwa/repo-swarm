# ABOUTME: Claude authentication method detection and credential resolution
# ABOUTME: Detects OAuth tokens or API keys with priority-based selection

import os
from typing import Any, Dict, TypedDict


class AuthenticationResult(TypedDict):
    """Result of authentication credential detection.

    Attributes:
        method: Authentication method used ('oauth' or 'api_key')
        token: The actual credential token value
        use_cli: Whether to use Claude CLI (True for OAuth, False for API key)
    """

    method: str
    token: str
    use_cli: bool


class ValidationResult(TypedDict):
    """Result of credential validation.

    Attributes:
        valid: Whether the credential is valid
        message: Validation message (success or error with setup instructions)
        method: Authentication method ('oauth' or 'api_key')
        token: The credential token value
    """

    valid: bool
    message: str
    method: str
    token: Any


# Token validation constants
SK_ANT_OAT01_PREFIX = "sk-ant-oat01-"
SK_ANT_API03_PREFIX = "sk-ant-api03-"
MIN_TOKEN_LENGTH = 50
MAX_TOKEN_LENGTH = 200


def get_claude_authentication() -> AuthenticationResult:
    """Detect and return Claude authentication credentials.

    Checks environment variables in priority order:
    1. CLAUDE_CODE_OAUTH_TOKEN (highest priority - Claude Code specific)
    2. CLAUDE_OAUTH_TOKEN (second priority - general Claude OAuth)
    3. ANTHROPIC_API_KEY (fallback - API key authentication)

    Returns:
        Dictionary containing:
        - method: 'oauth' or 'api_key'
        - token: The credential value
        - use_cli: True for OAuth tokens, False for API keys

    Raises:
        ValueError: If no valid credentials are found in any environment variable

    Examples:
        >>> # With OAuth token
        >>> os.environ['CLAUDE_CODE_OAUTH_TOKEN'] = 'oauth-token-123'
        >>> result = get_claude_authentication()
        >>> result['method']
        'oauth'
        >>> result['use_cli']
        True

        >>> # With API key fallback
        >>> os.environ['ANTHROPIC_API_KEY'] = 'sk-ant-key-456'
        >>> result = get_claude_authentication()
        >>> result['method']
        'api_key'
        >>> result['use_cli']
        False
    """
    # Check OAuth tokens in priority order
    claude_code_oauth = os.getenv("CLAUDE_CODE_OAUTH_TOKEN", "").strip()
    if claude_code_oauth:
        return {
            "method": "oauth",
            "token": claude_code_oauth,
            "use_cli": True,
        }

    claude_oauth = os.getenv("CLAUDE_OAUTH_TOKEN", "").strip()
    if claude_oauth:
        return {
            "method": "oauth",
            "token": claude_oauth,
            "use_cli": True,
        }

    # Fallback to API key
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if api_key:
        return {
            "method": "api_key",
            "token": api_key,
            "use_cli": False,
        }

    # No credentials found
    raise ValueError(
        "No Claude authentication credentials found. "
        "Please set one of the following environment variables:\n"
        "  - CLAUDE_CODE_OAUTH_TOKEN (OAuth token from Claude Code)\n"
        "  - CLAUDE_OAUTH_TOKEN (OAuth token from Claude)\n"
        "  - ANTHROPIC_API_KEY (API key from Anthropic Console)"
    )


def validate_claude_credentials(auth_result: Dict[str, Any]) -> ValidationResult:
    """Validate Claude authentication credentials format.

    Validates that OAuth tokens and API keys match expected format:
    - OAuth tokens: Must start with 'sk-ant-oat01-' and be 50-200 characters
    - API keys: Must start with 'sk-ant-api03-' and be 50-200 characters

    Args:
        auth_result: Dictionary containing:
            - method: 'oauth' or 'api_key'
            - token: The credential token value

    Returns:
        Dictionary containing:
            - valid: True if credential is valid, False otherwise
            - message: Validation message with success confirmation or error with setup instructions
            - method: The authentication method ('oauth' or 'api_key')
            - token: The credential token value

    Examples:
        >>> # Valid OAuth token
        >>> result = validate_claude_credentials({"method": "oauth", "token": "sk-ant-oat01-" + "a" * 50})
        >>> result["valid"]
        True

        >>> # Invalid OAuth token (wrong prefix)
        >>> result = validate_claude_credentials({"method": "oauth", "token": "sk-ant-api03-" + "a" * 50})
        >>> result["valid"]
        False
        >>> "claude setup-token" in result["message"].lower()
        True

        >>> # Invalid API key (too short)
        >>> result = validate_claude_credentials({"method": "api_key", "token": "sk-ant-api03-short"})
        >>> result["valid"]
        False
        >>> "console.anthropic.com" in result["message"]
        True
    """
    # Check for required fields
    if "method" not in auth_result:
        return {
            "valid": False,
            "message": "Missing 'method' field in auth_result. Expected 'oauth' or 'api_key'.",
            "method": "",
            "token": auth_result.get("token", ""),
        }

    if "token" not in auth_result:
        return {
            "valid": False,
            "message": "Missing 'token' field in auth_result.",
            "method": auth_result.get("method", ""),
            "token": "",
        }

    method = auth_result["method"]
    token = auth_result["token"]

    # Validate method value
    if method not in ("oauth", "api_key"):
        return {
            "valid": False,
            "message": f"Invalid method '{method}'. Expected 'oauth' or 'api_key'.",
            "method": method,
            "token": token,
        }

    # Check if token is None or not a string
    if token is None:
        if method == "oauth":
            return {
                "valid": False,
                "message": "OAuth token is None. Run `claude setup-token` to generate OAuth token.",
                "method": method,
                "token": None,
            }
        else:
            return {
                "valid": False,
                "message": "API key is None. Get API key from https://console.anthropic.com/",
                "method": method,
                "token": None,
            }

    if not isinstance(token, str):
        return {
            "valid": False,
            "message": f"Token must be a string, got {type(token).__name__}.",
            "method": method,
            "token": token,
        }

    # Check for empty string
    if not token.strip():
        if method == "oauth":
            return {
                "valid": False,
                "message": "OAuth token is empty. Run `claude setup-token` to generate OAuth token.",
                "method": method,
                "token": token,
            }
        else:
            return {
                "valid": False,
                "message": "API key is empty. Get API key from https://console.anthropic.com/",
                "method": method,
                "token": token,
            }

    # Validate based on method
    if method == "oauth":
        expected_prefix = SK_ANT_OAT01_PREFIX
        setup_instruction = "Run `claude setup-token` to generate OAuth token"
    else:  # api_key
        expected_prefix = SK_ANT_API03_PREFIX
        setup_instruction = "Get API key from https://console.anthropic.com/"

    # Check prefix
    if not token.startswith(expected_prefix):
        return {
            "valid": False,
            "message": (
                f"Invalid {method} format. Expected token to start with '{expected_prefix}'. "
                f"{setup_instruction}."
            ),
            "method": method,
            "token": token,
        }

    # Check length
    token_length = len(token)
    if token_length < MIN_TOKEN_LENGTH:
        return {
            "valid": False,
            "message": (
                f"Invalid {method} length. Token must be at least {MIN_TOKEN_LENGTH} characters "
                f"(got {token_length}). {setup_instruction}."
            ),
            "method": method,
            "token": token,
        }

    if token_length > MAX_TOKEN_LENGTH:
        return {
            "valid": False,
            "message": (
                f"Invalid {method} length. Token must be at most {MAX_TOKEN_LENGTH} characters "
                f"(got {token_length}). {setup_instruction}."
            ),
            "method": method,
            "token": token,
        }

    # Token is valid
    return {
        "valid": True,
        "message": f"Valid {method} credential.",
        "method": method,
        "token": token,
    }
