"""
Configuration constants for the Claude Investigator.
"""

import os
from typing import Any, Dict, Optional


class Config:
    """Configuration constants for the investigator."""

    # Claude API settings
    CLAUDE_MODEL = "claude-opus-4-5-20251101"
    MAX_TOKENS = 6000

    # Valid Claude model names for validation (4.x models only)
    # See: https://platform.claude.com/docs/en/about-claude/models/overview
    VALID_CLAUDE_MODELS = [
        # Claude 4.5 (current)
        "claude-sonnet-4-5-20250929",
        "claude-haiku-4-5-20251001",
        "claude-opus-4-5-20251101",  # current default
        "claude-opus-4-1-20250805",
        # Claude 4.0 (legacy)
        "claude-sonnet-4-20250514",
        "claude-opus-4-20250514",
    ]

    # File settings
    ANALYSIS_FILE = "arch.md"

    # Logging format
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    # Directory names
    TEMP_DIR = "temp"
    PROMPTS_DIR = "prompts"

    # Repository structure icons
    DIR_ICON = "📁"
    FILE_ICON = "📄"

    # Size units for human-readable format
    SIZE_UNITS = ["B", "KB", "MB", "GB", "TB"]

    # Architecture Hub configuration
    # These values are read from environment variables with sensible defaults
    ARCH_HUB_REPO_NAME = os.getenv("ARCH_HUB_REPO_NAME", "architecture-hub")
    ARCH_HUB_BASE_URL = os.getenv("ARCH_HUB_BASE_URL", "https://github.com/your-org")
    ARCH_HUB_FILES_DIR = os.getenv(
        "ARCH_HUB_FILES_DIR", ""
    )  # Empty string means root directory

    # Repository scanning configuration
    # DEFAULT_ORG_NAME supports both GitHub organizations and individual user accounts
    DEFAULT_ORG_NAME = os.getenv("DEFAULT_ORG_NAME", "your-org")
    DEFAULT_REPO_URL = os.getenv(
        "DEFAULT_REPO_URL", "https://github.com/facebook/react"
    )

    # Git configuration for commits
    GIT_USER_NAME = os.getenv("GIT_USER_NAME", "Architecture Bot")
    GIT_USER_EMAIL = os.getenv("GIT_USER_EMAIL", "architecture-bot@your-org.com")

    # Authentication token format constants
    SK_ANT_OAT01_PREFIX = "sk-ant-oat01-"  # OAuth Access Token v1
    SK_ANT_API03_PREFIX = "sk-ant-api03-"  # API Key v3
    MIN_TOKEN_LENGTH = 50
    MAX_TOKEN_LENGTH = 200

    @staticmethod
    def get_arch_hub_repo_url() -> str:
        """Get the full repository URL for the architecture hub."""
        return f"{Config.ARCH_HUB_BASE_URL}/{Config.ARCH_HUB_REPO_NAME}.git"

    @staticmethod
    def get_arch_hub_web_url() -> str:
        """Get the web URL for the architecture hub (without .git extension)."""
        return f"{Config.ARCH_HUB_BASE_URL}/{Config.ARCH_HUB_REPO_NAME}"

    @staticmethod
    def get_default_org_github_url() -> str:
        """Get the GitHub URL for the default organization."""
        return f"https://github.com/{Config.DEFAULT_ORG_NAME}"

    # Workflow configuration
    WORKFLOW_CHUNK_SIZE = 8  # Number of sub-workflows to run in parallel
    WORKFLOW_SLEEP_HOURS = 6  # Hours to sleep between workflow executions

    @staticmethod
    def validate_claude_model(model_name: str) -> str:
        """Validate and return claude model name.

        Args:
            model_name: The model name to validate

        Returns:
            The validated model name

        Raises:
            ValueError: If model name is not in VALID_CLAUDE_MODELS
        """
        if model_name not in Config.VALID_CLAUDE_MODELS:
            valid_models_str = ", ".join(Config.VALID_CLAUDE_MODELS)
            raise ValueError(
                f"Invalid Claude model '{model_name}'. Valid models: {valid_models_str}"
            )
        return model_name

    @staticmethod
    def validate_max_tokens(tokens: int) -> int:
        """Validate and return max tokens value.

        Args:
            tokens: The max tokens value to validate

        Returns:
            The validated max tokens value

        Raises:
            ValueError: If tokens is not in valid range (100-100000)
        """
        if not isinstance(tokens, int) or tokens < 100 or tokens > 100000:
            raise ValueError(
                f"Invalid max_tokens '{tokens}'. Must be integer between 100 and 100000"
            )
        return tokens

    @staticmethod
    def validate_sleep_hours(hours: float) -> float:
        """Validate and return sleep hours value.

        Args:
            hours: The sleep hours value to validate (supports fractional hours)

        Returns:
            The validated sleep hours value

        Raises:
            ValueError: If hours is not in valid range (0.01-168)
        """
        if not isinstance(hours, (int, float)) or hours < 0.01 or hours > 168:
            raise ValueError(
                f"Invalid sleep_hours '{hours}'. Must be number between 0.01 and 168 (36 seconds to 1 week)"
            )
        return float(hours)

    @staticmethod
    def validate_chunk_size(size: int) -> int:
        """Validate and return chunk size value.

        Args:
            size: The chunk size value to validate

        Returns:
            The validated chunk size value

        Raises:
            ValueError: If size is not in valid range (1-20)
        """
        if not isinstance(size, int) or size < 1 or size > 20:
            raise ValueError(
                f"Invalid chunk_size '{size}'. Must be integer between 1 and 20"
            )
        return size

    @staticmethod
    def validate_oauth_token(token: Any) -> str:
        """Validate OAuth token format.

        Validates that OAuth tokens match expected format:
        - Must start with 'sk-ant-oat01-' (OAuth Access Token v1)
        - Must be between 50-200 characters total
        - Must be a non-empty string

        Args:
            token: The OAuth token to validate

        Returns:
            The validated OAuth token

        Raises:
            ValueError: If token format is invalid with setup instructions

        Examples:
            >>> Config.validate_oauth_token("sk-ant-oat01-" + "a" * 50)
            'sk-ant-oat01-aaa...'

            >>> Config.validate_oauth_token("invalid")
            Traceback (most recent call last):
                ...
            ValueError: Invalid OAuth token format...
        """
        # Check for None
        if token is None:
            raise ValueError(
                "OAuth token is None. To generate an OAuth token:\n"
                "  1. Run: claude setup-token\n"
                "  2. Set CLAUDE_CODE_OAUTH_TOKEN or CLAUDE_OAUTH_TOKEN in .env.local"
            )

        # Check for non-string
        if not isinstance(token, str):
            raise ValueError(
                f"OAuth token must be a string, got {type(token).__name__}. "
                "Run `claude setup-token` to generate a valid OAuth token."
            )

        # Check for empty string
        if not token.strip():
            raise ValueError(
                "OAuth token is empty. To generate an OAuth token:\n"
                "  1. Run: claude setup-token\n"
                "  2. Set CLAUDE_CODE_OAUTH_TOKEN or CLAUDE_OAUTH_TOKEN in .env.local"
            )

        # Check prefix
        if not token.startswith(Config.SK_ANT_OAT01_PREFIX):
            raise ValueError(
                f"Invalid OAuth token format. Expected token to start with '{Config.SK_ANT_OAT01_PREFIX}'. "
                "To generate a valid OAuth token:\n"
                "  1. Run: claude setup-token\n"
                "  2. Set CLAUDE_CODE_OAUTH_TOKEN or CLAUDE_OAUTH_TOKEN in .env.local"
            )

        # Check length
        token_length = len(token)
        if token_length < Config.MIN_TOKEN_LENGTH:
            raise ValueError(
                f"Invalid OAuth token length. Token must be at least {Config.MIN_TOKEN_LENGTH} characters "
                f"(got {token_length}). Run `claude setup-token` to generate a valid OAuth token."
            )

        if token_length > Config.MAX_TOKEN_LENGTH:
            raise ValueError(
                f"Invalid OAuth token length. Token must be at most {Config.MAX_TOKEN_LENGTH} characters "
                f"(got {token_length}). Run `claude setup-token` to generate a valid OAuth token."
            )

        return token

    @staticmethod
    def validate_api_key(api_key: Any) -> str:
        """Validate API key format.

        Validates that API keys match expected format:
        - Must start with 'sk-ant-api03-' (API Key v3)
        - Must be between 50-200 characters total
        - Must be a non-empty string

        Args:
            api_key: The API key to validate

        Returns:
            The validated API key

        Raises:
            ValueError: If API key format is invalid with setup instructions

        Examples:
            >>> Config.validate_api_key("sk-ant-api03-" + "a" * 50)
            'sk-ant-api03-aaa...'

            >>> Config.validate_api_key("invalid")
            Traceback (most recent call last):
                ...
            ValueError: Invalid API key format...
        """
        # Check for None
        if api_key is None:
            raise ValueError(
                "API key is None. To get an API key:\n"
                "  1. Visit: https://console.anthropic.com/\n"
                "  2. Generate an API key\n"
                "  3. Set ANTHROPIC_API_KEY in .env.local"
            )

        # Check for non-string
        if not isinstance(api_key, str):
            raise ValueError(
                f"API key must be a string, got {type(api_key).__name__}. "
                "Get API key from https://console.anthropic.com/"
            )

        # Check for empty string
        if not api_key.strip():
            raise ValueError(
                "API key is empty. To get an API key:\n"
                "  1. Visit: https://console.anthropic.com/\n"
                "  2. Generate an API key\n"
                "  3. Set ANTHROPIC_API_KEY in .env.local"
            )

        # Check prefix
        if not api_key.startswith(Config.SK_ANT_API03_PREFIX):
            raise ValueError(
                f"Invalid API key format. Expected key to start with '{Config.SK_ANT_API03_PREFIX}'. "
                "Get API key from https://console.anthropic.com/"
            )

        # Check length
        key_length = len(api_key)
        if key_length < Config.MIN_TOKEN_LENGTH:
            raise ValueError(
                f"Invalid API key length. Key must be at least {Config.MIN_TOKEN_LENGTH} characters "
                f"(got {key_length}). Get API key from https://console.anthropic.com/"
            )

        if key_length > Config.MAX_TOKEN_LENGTH:
            raise ValueError(
                f"Invalid API key length. Key must be at most {Config.MAX_TOKEN_LENGTH} characters "
                f"(got {key_length}). Get API key from https://console.anthropic.com/"
            )

        return api_key

    @staticmethod
    def validate_oauth_from_env() -> Optional[Dict[str, Any]]:
        """Validate OAuth tokens from environment variables.

        Checks environment variables in priority order:
        1. CLAUDE_CODE_OAUTH_TOKEN (highest priority)
        2. CLAUDE_OAUTH_TOKEN (second priority)

        Returns:
            Dictionary containing validation result:
            - method: 'oauth'
            - token: The OAuth token value
            - valid: True if token is valid, False otherwise
            - message: Validation message

            Returns None if no OAuth token is set in environment

        Examples:
            >>> os.environ['CLAUDE_CODE_OAUTH_TOKEN'] = 'sk-ant-oat01-' + 'a' * 50
            >>> result = Config.validate_oauth_from_env()
            >>> result['valid']
            True
            >>> result['method']
            'oauth'
        """
        # Check OAuth tokens in priority order
        claude_code_oauth = os.getenv("CLAUDE_CODE_OAUTH_TOKEN", "").strip()
        claude_oauth = os.getenv("CLAUDE_OAUTH_TOKEN", "").strip()

        # Determine which token to use
        token = None
        source = None
        if claude_code_oauth:
            token = claude_code_oauth
            source = "CLAUDE_CODE_OAUTH_TOKEN"
        elif claude_oauth:
            token = claude_oauth
            source = "CLAUDE_OAUTH_TOKEN"

        # No OAuth token set
        if not token:
            return None

        # Validate the token
        try:
            validated_token = Config.validate_oauth_token(token)
            return {
                "method": "oauth",
                "token": validated_token,
                "valid": True,
                "message": f"Valid OAuth token from {source}",
                "source": source,
            }
        except ValueError as e:
            return {
                "method": "oauth",
                "token": token,
                "valid": False,
                "message": str(e),
                "source": source,
            }

    @staticmethod
    def get_authentication_setup_message() -> str:
        """Get helpful message about authentication setup options.

        Returns:
            Multi-line string with authentication setup instructions

        Examples:
            >>> msg = Config.get_authentication_setup_message()
            >>> "CLAUDE_CODE_OAUTH_TOKEN" in msg
            True
            >>> "claude setup-token" in msg.lower()
            True
        """
        return """
Claude Authentication Setup
============================

RepoSwarm supports two authentication methods:

1. OAuth Token (Recommended for Claude Code users)
   Environment variables (in priority order):
   - CLAUDE_CODE_OAUTH_TOKEN (Claude Code specific)
   - CLAUDE_OAUTH_TOKEN (General Claude OAuth)
   
   Setup:
   1. Run: claude setup-token
   2. Copy the generated OAuth token
   3. Add to .env.local: CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-...

2. API Key (For Anthropic Console users)
   Environment variable:
   - ANTHROPIC_API_KEY
   
   Setup:
   1. Visit: https://console.anthropic.com/
   2. Generate an API key
   3. Add to .env.local: ANTHROPIC_API_KEY=sk-ant-api03-...

Token Format Requirements:
- OAuth tokens: Must start with 'sk-ant-oat01-'
- API keys: Must start with 'sk-ant-api03-'
- Length: 50-200 characters

For more information, see the authentication documentation.
""".strip()
