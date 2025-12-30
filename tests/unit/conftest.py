# ABOUTME: Shared pytest fixtures for unit tests
# ABOUTME: Provides token factories and common test utilities for all token types

"""
Shared fixtures for unit test suite.

This module provides fixtures that generate test tokens for all supported GitHub
token types (CLASSIC, FINE_GRAINED_USER, FINE_GRAINED_PAT) to ensure consistent
test data across all test files.
"""

import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from investigator.core.github_token_utils import GitHubTokenType


@pytest.fixture(
    params=[
        GitHubTokenType.CLASSIC,
        GitHubTokenType.FINE_GRAINED_USER,
        GitHubTokenType.FINE_GRAINED_PAT,
    ]
)
def token_factory(request):
    """
    Factory fixture that generates valid tokens for all supported types.

    Parametrized fixture that provides one token type per test run. Enables
    tests to automatically run with all three token types without duplication.

    Yields:
        str: A valid token string for the token type being tested

    Examples:
        Test that works with any token type:
        >>> def test_something(token_factory):
        ...     token = token_factory
        ...     # Test logic that should work with any token type

        When run, pytest will execute this test 3 times:
        - Once with CLASSIC token (ghp_...)
        - Once with FINE_GRAINED_USER token (ghu_...)
        - Once with FINE_GRAINED_PAT token (github_pat_...)
    """
    token_type = request.param

    if token_type == GitHubTokenType.CLASSIC:
        # Classic PAT: ghp_ prefix + exactly 40 alphanumeric characters (44 total)
        return "ghp_" + "a" * 40
    elif token_type == GitHubTokenType.FINE_GRAINED_USER:
        # Fine-grained user token: ghu_ prefix + variable length (minimum ~10 chars)
        return "ghu_" + "a" * 15
    elif token_type == GitHubTokenType.FINE_GRAINED_PAT:
        # Fine-grained PAT: github_pat_ prefix + variable length (minimum ~20 chars)
        return "github_pat_" + "a" * 25
    else:
        pytest.fail(f"Unknown token type: {token_type}")


@pytest.fixture
def classic_token():
    """Provides a valid classic PAT token (ghp_) for testing."""
    return "ghp_" + "a" * 40


@pytest.fixture
def fine_grained_user_token():
    """Provides a valid fine-grained user token (ghu_) for testing."""
    return "ghu_" + "a" * 15


@pytest.fixture
def fine_grained_pat_token():
    """Provides a valid fine-grained PAT token (github_pat_) for testing."""
    return "github_pat_" + "a" * 25


@pytest.fixture
def all_token_types():
    """Provides all three valid token types in a list for comparison tests."""
    return {
        GitHubTokenType.CLASSIC: "ghp_" + "a" * 40,
        GitHubTokenType.FINE_GRAINED_USER: "ghu_" + "a" * 15,
        GitHubTokenType.FINE_GRAINED_PAT: "github_pat_" + "a" * 25,
    }
