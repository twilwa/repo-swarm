# ABOUTME: GitHub token type detection and validation utility
# ABOUTME: Detects token types (CLASSIC, FINE_GRAINED_USER, FINE_GRAINED_PAT) based on prefix patterns

from enum import Enum


class GitHubTokenType(Enum):
    """Enumeration of GitHub token types."""

    CLASSIC = "CLASSIC"
    """Classic Personal Access Token (PAT) with ghp_ prefix and exactly 40 characters after."""

    FINE_GRAINED_USER = "FINE_GRAINED_USER"
    """Fine-grained user token with ghu_ prefix and variable length."""

    FINE_GRAINED_PAT = "FINE_GRAINED_PAT"
    """Fine-grained Personal Access Token with github_pat_ prefix and variable length."""

    UNKNOWN = "UNKNOWN"
    """Unknown or invalid token format."""


def detect_github_token_type(token: str) -> GitHubTokenType:
    """Detect the type of GitHub token based on its prefix pattern.

    Token format expectations:
    - CLASSIC: ghp_ prefix followed by exactly 40 alphanumeric characters (total length: 44)
    - FINE_GRAINED_USER: ghu_ prefix followed by variable length alphanumeric characters
    - FINE_GRAINED_PAT: github_pat_ prefix followed by variable length alphanumeric characters
    - UNKNOWN: Any other format or invalid input

    Args:
        token: The GitHub token string to analyze. Must be a non-empty string.

    Returns:
        GitHubTokenType enum value indicating the detected token type.

    Raises:
        TypeError: If token is not a string (e.g., None, int, list).

    Examples:
        >>> detect_github_token_type("ghp_" + "a" * 40)
        <GitHubTokenType.CLASSIC: 'CLASSIC'>

        >>> detect_github_token_type("ghu_abc123")
        <GitHubTokenType.FINE_GRAINED_USER: 'FINE_GRAINED_USER'>

        >>> detect_github_token_type("github_pat_xyz789")
        <GitHubTokenType.FINE_GRAINED_PAT: 'FINE_GRAINED_PAT'>

        >>> detect_github_token_type("invalid_token")
        <GitHubTokenType.UNKNOWN: 'UNKNOWN'>
    """
    # Type validation: ensure token is a string
    if not isinstance(token, str):
        raise TypeError(f"Token must be a string, got {type(token).__name__}")

    # Strip whitespace for validation (but tokens with whitespace are invalid)
    stripped_token = token.strip()

    # Empty string or whitespace-only returns UNKNOWN
    if not stripped_token:
        return GitHubTokenType.UNKNOWN

    # If stripping changed the token, it had leading/trailing whitespace (invalid)
    if stripped_token != token:
        return GitHubTokenType.UNKNOWN

    # Check for fine-grained PAT first (longest prefix, highest priority)
    if token.startswith("github_pat_"):
        # Fine-grained PAT tokens have variable length after prefix
        # Must have at least one character after prefix
        if len(token) > len("github_pat_"):
            return GitHubTokenType.FINE_GRAINED_PAT
        return GitHubTokenType.UNKNOWN

    # Check for fine-grained user token
    if token.startswith("ghu_"):
        # Fine-grained user tokens have variable length after prefix
        # Must have at least one character after prefix
        if len(token) > len("ghu_"):
            return GitHubTokenType.FINE_GRAINED_USER
        return GitHubTokenType.UNKNOWN

    # Check for classic token (must have exactly 40 characters after ghp_)
    if token.startswith("ghp_"):
        # Classic tokens must be exactly: ghp_ (4 chars) + 40 chars = 44 total
        if len(token) == 44:
            return GitHubTokenType.CLASSIC
        return GitHubTokenType.UNKNOWN

    # No matching pattern found
    return GitHubTokenType.UNKNOWN


def validate_github_token(token: str) -> dict:
    """Validate GitHub token format and return detailed validation result.

    Validates token format according to GitHub token type specifications:
    - CLASSIC (ghp_*): Must be exactly 40 characters after 'ghp_' prefix (44 total)
    - FINE_GRAINED_USER (ghu_*): Must have minimum 10 characters after 'ghu_' prefix
    - FINE_GRAINED_PAT (github_pat_*): Must have minimum 20 characters after 'github_pat_' prefix

    Args:
        token: The GitHub token string to validate. Can be any type, but must be a string for valid tokens.

    Returns:
        Dictionary with validation result:
        {
            'valid': bool,           # True if token passes format validation
            'token_type': GitHubTokenType,  # Detected token type (may be UNKNOWN)
            'message': str           # Human-readable success or error message
        }

    Examples:
        >>> validate_github_token("ghp_" + "a" * 40)
        {'valid': True, 'token_type': <GitHubTokenType.CLASSIC: 'CLASSIC'>,
         'message': 'Valid CLASSIC token'}

        >>> validate_github_token("ghp_" + "a" * 39)
        {'valid': False, 'token_type': <GitHubTokenType.UNKNOWN: 'UNKNOWN'>,
         'message': 'CLASSIC tokens must have exactly 40 characters after prefix'}

        >>> validate_github_token("ghu_" + "a" * 10)
        {'valid': True, 'token_type': <GitHubTokenType.FINE_GRAINED_USER: 'FINE_GRAINED_USER'},
         'message': 'Valid FINE_GRAINED_USER token'}

        >>> validate_github_token(None)
        {'valid': False, 'token_type': <GitHubTokenType.UNKNOWN: 'UNKNOWN'},
         'message': 'Token must be a string, got NoneType'}
    """
    # Type validation: handle non-string input gracefully
    if not isinstance(token, str):
        token_type_name = type(token).__name__
        return {
            "valid": False,
            "token_type": GitHubTokenType.UNKNOWN,
            "message": f"Token must be a string, got {token_type_name}",
        }

    # Handle empty or whitespace-only strings
    if not token or not token.strip():
        return {
            "valid": False,
            "token_type": GitHubTokenType.UNKNOWN,
            "message": "Token cannot be empty or contain only whitespace",
        }

    # Check for leading/trailing whitespace (invalid tokens)
    if token != token.strip():
        return {
            "valid": False,
            "token_type": GitHubTokenType.UNKNOWN,
            "message": "Token cannot contain leading or trailing whitespace",
        }

    # Check for classic token pattern before calling detect_github_token_type
    # This allows us to provide specific error messages for malformed classic tokens
    if token.startswith("ghp_"):
        if len(token) == 44:
            return {
                "valid": True,
                "token_type": GitHubTokenType.CLASSIC,
                "message": "Valid CLASSIC token",
            }
        else:
            return {
                "valid": False,
                "token_type": GitHubTokenType.UNKNOWN,
                "message": "CLASSIC tokens must have exactly 40 characters after prefix (ghp_)",
            }

    # Check for fine-grained user token pattern
    if token.startswith("ghu_"):
        suffix_length = len(token) - len("ghu_")
        if suffix_length >= 10:
            return {
                "valid": True,
                "token_type": GitHubTokenType.FINE_GRAINED_USER,
                "message": "Valid FINE_GRAINED_USER token",
            }
        else:
            return {
                "valid": False,
                "token_type": GitHubTokenType.UNKNOWN,
                "message": f"FINE_GRAINED_USER tokens must have minimum 10 characters after prefix (ghu_), got {suffix_length}",
            }

    # Check for fine-grained PAT pattern
    if token.startswith("github_pat_"):
        suffix_length = len(token) - len("github_pat_")
        if suffix_length >= 20:
            return {
                "valid": True,
                "token_type": GitHubTokenType.FINE_GRAINED_PAT,
                "message": "Valid FINE_GRAINED_PAT token",
            }
        else:
            return {
                "valid": False,
                "token_type": GitHubTokenType.UNKNOWN,
                "message": f"FINE_GRAINED_PAT tokens must have minimum 20 characters after prefix (github_pat_), got {suffix_length}",
            }

    # No recognized pattern - return UNKNOWN
    return {
        "valid": False,
        "token_type": GitHubTokenType.UNKNOWN,
        "message": "Invalid or unknown GitHub token format",
    }
