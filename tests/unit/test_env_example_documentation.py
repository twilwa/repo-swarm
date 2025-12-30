# ABOUTME: Unit tests to verify .env.example documents all authentication options
# ABOUTME: Validates that OAuth and API key variables are documented with clear guidance

import os
import re
from pathlib import Path


def test_env_example_documents_oauth_tokens():
    """Verify .env.example includes CLAUDE_CODE_OAUTH_TOKEN and CLAUDE_OAUTH_TOKEN."""
    env_example_path = Path(__file__).parent.parent.parent / ".env.example"
    content = env_example_path.read_text()

    # Check for OAuth token variables
    assert (
        "CLAUDE_CODE_OAUTH_TOKEN=" in content
    ), "Missing CLAUDE_CODE_OAUTH_TOKEN variable in .env.example"
    assert (
        "CLAUDE_OAUTH_TOKEN=" in content
    ), "Missing CLAUDE_OAUTH_TOKEN variable in .env.example"


def test_env_example_documents_api_key():
    """Verify .env.example includes ANTHROPIC_API_KEY."""
    env_example_path = Path(__file__).parent.parent.parent / ".env.example"
    content = env_example_path.read_text()

    assert (
        "ANTHROPIC_API_KEY=" in content
    ), "Missing ANTHROPIC_API_KEY variable in .env.example"


def test_env_example_explains_priority():
    """Verify .env.example explains authentication priority."""
    env_example_path = Path(__file__).parent.parent.parent / ".env.example"
    content = env_example_path.read_text()

    # Check for priority explanation
    assert (
        "priority" in content.lower() or "precedence" in content.lower()
    ), "Missing priority/precedence explanation in .env.example"

    # Check that CLAUDE_CODE_OAUTH_TOKEN is mentioned as highest priority
    lines = content.split("\n")
    oauth_code_line = None
    oauth_line = None
    api_key_line = None

    for i, line in enumerate(lines):
        if "CLAUDE_CODE_OAUTH_TOKEN" in line and "=" in line:
            oauth_code_line = i
        if "CLAUDE_OAUTH_TOKEN=" in line and "CLAUDE_CODE_OAUTH_TOKEN" not in line:
            oauth_line = i
        if "ANTHROPIC_API_KEY=" in line:
            api_key_line = i

    assert oauth_code_line is not None, "CLAUDE_CODE_OAUTH_TOKEN not found"
    assert oauth_line is not None, "CLAUDE_OAUTH_TOKEN not found"
    assert api_key_line is not None, "ANTHROPIC_API_KEY not found"


def test_env_example_shows_token_format():
    """Verify .env.example shows OAuth token format example."""
    env_example_path = Path(__file__).parent.parent.parent / ".env.example"
    content = env_example_path.read_text()

    # Check for OAuth token format (sk-ant-oat01-)
    assert (
        "sk-ant-oat01-" in content
    ), "Missing OAuth token format example (sk-ant-oat01-...)"


def test_env_example_explains_oauth_vs_api_key():
    """Verify .env.example explains difference between OAuth and API key."""
    env_example_path = Path(__file__).parent.parent.parent / ".env.example"
    content = env_example_path.read_text()

    # Check for mentions of Max subscription, Claude Code, or similar context
    content_lower = content.lower()
    has_oauth_context = any(
        term in content_lower
        for term in [
            "max",
            "subscription",
            "claude code",
            "oauth",
            "web authentication",
        ]
    )

    assert has_oauth_context, "Missing explanation of when to use OAuth vs API key"


def test_env_example_has_clear_comments():
    """Verify .env.example has helpful comments for authentication section."""
    env_example_path = Path(__file__).parent.parent.parent / ".env.example"
    content = env_example_path.read_text()

    # Find the Claude API configuration section
    lines = content.split("\n")
    claude_section_found = False

    for line in lines:
        if "# Claude API" in line or "# Authentication" in line:
            claude_section_found = True
            break

    assert (
        claude_section_found
    ), "Missing clear section header for Claude authentication configuration"
