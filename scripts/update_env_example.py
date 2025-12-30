#!/usr/bin/env python3
"""
Helper script to update .env.example with OAuth authentication variables.
This script adds the OAuth configuration section to .env.example.
"""

import re
from pathlib import Path

# Path to .env.example
ENV_EXAMPLE_PATH = Path(__file__).parent.parent / ".env.example"

# New content to insert after "# Claude API configuration"
NEW_CONTENT = """# Claude API configuration
# RepoSwarm supports two authentication methods:
# 1. OAuth Token (Claude Max subscription) - Recommended if you have Claude Max
# 2. API Key (Standard Anthropic API) - For standard API tier users
#
# Authentication Priority (checked in order):
# 1. CLAUDE_CODE_OAUTH_TOKEN (highest priority)
# 2. CLAUDE_OAUTH_TOKEN (alternative OAuth variable)
# 3. ANTHROPIC_API_KEY (fallback)
#
# Option 1: OAuth Token (Claude Max)
# Generate OAuth token by running: mise claude-login
# Token format: sk-ant-oat01-... (starts with sk-ant-oat01-)
# Token validity: 1 year
# Use when: You have Claude Max subscription and want access to Max models
CLAUDE_CODE_OAUTH_TOKEN=

# Alternative OAuth token variable (lower priority than CLAUDE_CODE_OAUTH_TOKEN)
# Use this if you prefer a different variable name for OAuth tokens
CLAUDE_OAUTH_TOKEN=

# Option 2: API Key (Standard Anthropic API)
# Get API key from: https://console.anthropic.com/
# Token format: sk-ant-api03-... (starts with sk-ant-api03-)
# Use when: Standard API tier, CI/CD, or production environments
# Note: API key authentication uses direct SDK integration (faster than OAuth)
ANTHROPIC_API_KEY=
"""


def update_env_example():
    """Update .env.example with OAuth authentication variables."""
    if not ENV_EXAMPLE_PATH.exists():
        print(f"Error: {ENV_EXAMPLE_PATH} not found")
        return False

    # Read current content
    content = ENV_EXAMPLE_PATH.read_text()

    # Check if already updated
    if "CLAUDE_CODE_OAUTH_TOKEN" in content:
        print("✅ .env.example already contains OAuth variables")
        return True

    # Find the Claude API configuration section
    pattern = r"(# Claude API configuration\nANTHROPIC_API_KEY=)"
    replacement = NEW_CONTENT.rstrip()

    if re.search(pattern, content):
        # Replace the section
        new_content = re.sub(pattern, replacement, content)
        ENV_EXAMPLE_PATH.write_text(new_content)
        print("✅ Successfully updated .env.example with OAuth variables")
        return True
    else:
        print("⚠️  Could not find exact pattern to replace")
        print("   Please manually update .env.example with the OAuth variables")
        print("\nContent to add:")
        print(NEW_CONTENT)
        return False


if __name__ == "__main__":
    update_env_example()
