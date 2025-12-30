# ABOUTME: Unit tests for GitHub token type detection utility
# ABOUTME: Tests detection logic for CLASSIC, FINE_GRAINED_USER, FINE_GRAINED_PAT token types

import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from investigator.core.github_token_utils import (
    GitHubTokenType,
    detect_github_token_type,
    validate_github_token,
)


class TestGitHubTokenTypeDetection:
    """Test suite for GitHub token type detection."""

    def test_classic_token_detection(self):
        """Should detect CLASSIC token with ghp_ prefix and exactly 40 characters after."""
        # Valid classic token: ghp_ + 40 chars
        token = "ghp_" + "a" * 40
        result = detect_github_token_type(token)
        assert result == GitHubTokenType.CLASSIC

    def test_classic_token_exact_length(self):
        """Should detect CLASSIC token with exactly 44 characters total (ghp_ + 40)."""
        token = "ghp_" + "1" * 40
        result = detect_github_token_type(token)
        assert result == GitHubTokenType.CLASSIC

    def test_classic_token_various_characters(self):
        """Should detect CLASSIC token with various alphanumeric characters."""
        token = "ghp_" + "AbCdEf1234567890XyZ9876543210abcdefghijk"
        assert len(token) == 44
        result = detect_github_token_type(token)
        assert result == GitHubTokenType.CLASSIC

    def test_fine_grained_user_token_detection(self):
        """Should detect FINE_GRAINED_USER token with ghu_ prefix."""
        # Fine-grained user tokens have variable length after ghu_
        token = "ghu_" + "a" * 20
        result = detect_github_token_type(token)
        assert result == GitHubTokenType.FINE_GRAINED_USER

    def test_fine_grained_user_token_short(self):
        """Should detect FINE_GRAINED_USER token with minimal length."""
        token = "ghu_abc123"
        result = detect_github_token_type(token)
        assert result == GitHubTokenType.FINE_GRAINED_USER

    def test_fine_grained_user_token_long(self):
        """Should detect FINE_GRAINED_USER token with longer length."""
        token = "ghu_" + "x" * 100
        result = detect_github_token_type(token)
        assert result == GitHubTokenType.FINE_GRAINED_USER

    def test_fine_grained_pat_token_detection(self):
        """Should detect FINE_GRAINED_PAT token with github_pat_ prefix."""
        # Fine-grained PAT tokens have variable length after github_pat_
        token = "github_pat_" + "a" * 20
        result = detect_github_token_type(token)
        assert result == GitHubTokenType.FINE_GRAINED_PAT

    def test_fine_grained_pat_token_short(self):
        """Should detect FINE_GRAINED_PAT token with minimal length."""
        token = "github_pat_abc123"
        result = detect_github_token_type(token)
        assert result == GitHubTokenType.FINE_GRAINED_PAT

    def test_fine_grained_pat_token_long(self):
        """Should detect FINE_GRAINED_PAT token with longer length."""
        token = "github_pat_" + "y" * 100
        result = detect_github_token_type(token)
        assert result == GitHubTokenType.FINE_GRAINED_PAT

    def test_unknown_token_random_string(self):
        """Should return UNKNOWN for random string that doesn't match any pattern."""
        token = "random_token_string_12345"
        result = detect_github_token_type(token)
        assert result == GitHubTokenType.UNKNOWN

    def test_unknown_token_wrong_prefix(self):
        """Should return UNKNOWN for token with wrong prefix."""
        token = "ghx_" + "a" * 40
        result = detect_github_token_type(token)
        assert result == GitHubTokenType.UNKNOWN

    def test_unknown_token_partial_match(self):
        """Should return UNKNOWN for token that partially matches but doesn't meet criteria."""
        # ghp_ but not 40 chars after
        token = "ghp_" + "a" * 39
        result = detect_github_token_type(token)
        assert result == GitHubTokenType.UNKNOWN

    def test_unknown_token_classic_too_short(self):
        """Should return UNKNOWN for ghp_ token with less than 40 characters after."""
        token = "ghp_" + "a" * 39
        result = detect_github_token_type(token)
        assert result == GitHubTokenType.UNKNOWN

    def test_unknown_token_classic_too_long(self):
        """Should return UNKNOWN for ghp_ token with more than 40 characters after."""
        token = "ghp_" + "a" * 41
        result = detect_github_token_type(token)
        assert result == GitHubTokenType.UNKNOWN

    def test_empty_string(self):
        """Should return UNKNOWN for empty string."""
        token = ""
        result = detect_github_token_type(token)
        assert result == GitHubTokenType.UNKNOWN

    def test_whitespace_only(self):
        """Should return UNKNOWN for whitespace-only string."""
        token = "   "
        result = detect_github_token_type(token)
        assert result == GitHubTokenType.UNKNOWN

    def test_whitespace_before_token(self):
        """Should return UNKNOWN for token with leading whitespace."""
        token = "   ghp_" + "a" * 40
        result = detect_github_token_type(token)
        assert result == GitHubTokenType.UNKNOWN

    def test_whitespace_after_token(self):
        """Should return UNKNOWN for token with trailing whitespace."""
        token = "ghp_" + "a" * 40 + "   "
        result = detect_github_token_type(token)
        assert result == GitHubTokenType.UNKNOWN

    def test_whitespace_in_middle(self):
        """Should return UNKNOWN for token with whitespace in middle."""
        token = "ghp_" + "a" * 20 + " " + "a" * 20
        result = detect_github_token_type(token)
        assert result == GitHubTokenType.UNKNOWN

    def test_none_value(self):
        """Should raise TypeError for None value."""
        with pytest.raises(TypeError):
            detect_github_token_type(None)

    def test_non_string_type(self):
        """Should raise TypeError for non-string types."""
        with pytest.raises(TypeError):
            detect_github_token_type(12345)

        with pytest.raises(TypeError):
            detect_github_token_type([])

        with pytest.raises(TypeError):
            detect_github_token_type({})

    def test_short_token(self):
        """Should return UNKNOWN for very short token."""
        token = "ghp"
        result = detect_github_token_type(token)
        assert result == GitHubTokenType.UNKNOWN

    def test_just_prefix_classic(self):
        """Should return UNKNOWN for just the prefix without suffix."""
        token = "ghp_"
        result = detect_github_token_type(token)
        assert result == GitHubTokenType.UNKNOWN

    def test_just_prefix_fine_grained_user(self):
        """Should return UNKNOWN for just ghu_ prefix without suffix."""
        token = "ghu_"
        result = detect_github_token_type(token)
        assert result == GitHubTokenType.UNKNOWN

    def test_just_prefix_fine_grained_pat(self):
        """Should return UNKNOWN for just github_pat_ prefix without suffix."""
        token = "github_pat_"
        result = detect_github_token_type(token)
        assert result == GitHubTokenType.UNKNOWN

    def test_case_sensitivity_classic(self):
        """Should return UNKNOWN for uppercase prefix (case sensitive)."""
        token = "GHP_" + "a" * 40
        result = detect_github_token_type(token)
        assert result == GitHubTokenType.UNKNOWN

    def test_case_sensitivity_fine_grained_user(self):
        """Should return UNKNOWN for uppercase ghu_ prefix."""
        token = "GHU_" + "a" * 20
        result = detect_github_token_type(token)
        assert result == GitHubTokenType.UNKNOWN

    def test_case_sensitivity_fine_grained_pat(self):
        """Should return UNKNOWN for uppercase github_pat_ prefix."""
        token = "GITHUB_PAT_" + "a" * 20
        result = detect_github_token_type(token)
        assert result == GitHubTokenType.UNKNOWN

    def test_priority_fine_grained_pat_over_user(self):
        """Should detect FINE_GRAINED_PAT even if it contains ghu_ substring."""
        # github_pat_ should take priority
        token = "github_pat_ghu_something"
        result = detect_github_token_type(token)
        assert result == GitHubTokenType.FINE_GRAINED_PAT

    def test_priority_fine_grained_pat_over_classic(self):
        """Should detect FINE_GRAINED_PAT even if it contains ghp_ substring."""
        token = "github_pat_ghp_something"
        result = detect_github_token_type(token)
        assert result == GitHubTokenType.FINE_GRAINED_PAT

    def test_enum_values(self):
        """Should have correct enum values."""
        assert GitHubTokenType.CLASSIC.value == "CLASSIC"
        assert GitHubTokenType.FINE_GRAINED_USER.value == "FINE_GRAINED_USER"
        assert GitHubTokenType.FINE_GRAINED_PAT.value == "FINE_GRAINED_PAT"
        assert GitHubTokenType.UNKNOWN.value == "UNKNOWN"


class TestGitHubTokenValidation:
    """Test suite for GitHub token validation."""

    # Valid token tests
    def test_validate_classic_token_valid(self):
        """Should validate CLASSIC token with correct format."""
        token = "ghp_" + "a" * 40
        result = validate_github_token(token)
        assert result["valid"] is True
        assert result["token_type"] == GitHubTokenType.CLASSIC
        assert "valid" in result["message"].lower()

    def test_validate_classic_token_with_mixed_chars(self):
        """Should validate CLASSIC token with mixed alphanumeric characters."""
        token = "ghp_" + "AbCdEf1234567890XyZ9876543210abcdefghijk"
        result = validate_github_token(token)
        assert result["valid"] is True
        assert result["token_type"] == GitHubTokenType.CLASSIC

    def test_validate_fine_grained_user_token_min_length(self):
        """Should validate FINE_GRAINED_USER token with minimum length (10 chars after prefix)."""
        token = "ghu_" + "a" * 10
        result = validate_github_token(token)
        assert result["valid"] is True
        assert result["token_type"] == GitHubTokenType.FINE_GRAINED_USER
        assert "valid" in result["message"].lower()

    def test_validate_fine_grained_user_token_longer(self):
        """Should validate FINE_GRAINED_USER token with longer length."""
        token = "ghu_" + "x" * 50
        result = validate_github_token(token)
        assert result["valid"] is True
        assert result["token_type"] == GitHubTokenType.FINE_GRAINED_USER

    def test_validate_fine_grained_pat_token_min_length(self):
        """Should validate FINE_GRAINED_PAT token with minimum length (20 chars after prefix)."""
        token = "github_pat_" + "a" * 20
        result = validate_github_token(token)
        assert result["valid"] is True
        assert result["token_type"] == GitHubTokenType.FINE_GRAINED_PAT
        assert "valid" in result["message"].lower()

    def test_validate_fine_grained_pat_token_longer(self):
        """Should validate FINE_GRAINED_PAT token with longer length."""
        token = "github_pat_" + "y" * 100
        result = validate_github_token(token)
        assert result["valid"] is True
        assert result["token_type"] == GitHubTokenType.FINE_GRAINED_PAT

    # Invalid token tests - CLASSIC
    def test_validate_classic_token_too_short(self):
        """Should invalidate CLASSIC token with less than 40 characters after prefix."""
        token = "ghp_" + "a" * 39
        result = validate_github_token(token)
        assert result["valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN
        assert "40 characters" in result["message"]

    def test_validate_classic_token_too_long(self):
        """Should invalidate CLASSIC token with more than 40 characters after prefix."""
        token = "ghp_" + "a" * 41
        result = validate_github_token(token)
        assert result["valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN
        assert "40 characters" in result["message"]

    def test_validate_classic_token_just_prefix(self):
        """Should invalidate CLASSIC token with just prefix."""
        token = "ghp_"
        result = validate_github_token(token)
        assert result["valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN

    # Invalid token tests - FINE_GRAINED_USER
    def test_validate_fine_grained_user_token_too_short(self):
        """Should invalidate FINE_GRAINED_USER token with less than 10 chars after prefix."""
        token = "ghu_" + "a" * 9
        result = validate_github_token(token)
        assert result["valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN
        assert "minimum 10 characters" in result["message"]

    def test_validate_fine_grained_user_token_just_prefix(self):
        """Should invalidate FINE_GRAINED_USER token with just prefix."""
        token = "ghu_"
        result = validate_github_token(token)
        assert result["valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN

    # Invalid token tests - FINE_GRAINED_PAT
    def test_validate_fine_grained_pat_token_too_short(self):
        """Should invalidate FINE_GRAINED_PAT token with less than 20 chars after prefix."""
        token = "github_pat_" + "a" * 19
        result = validate_github_token(token)
        assert result["valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN
        assert "minimum 20 characters" in result["message"]

    def test_validate_fine_grained_pat_token_just_prefix(self):
        """Should invalidate FINE_GRAINED_PAT token with just prefix."""
        token = "github_pat_"
        result = validate_github_token(token)
        assert result["valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN

    # Edge cases
    def test_validate_empty_string(self):
        """Should invalidate empty string."""
        token = ""
        result = validate_github_token(token)
        assert result["valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN
        assert "empty" in result["message"].lower()

    def test_validate_none_value(self):
        """Should handle None value gracefully."""
        result = validate_github_token(None)
        assert result["valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN
        assert "must be a string" in result["message"].lower()

    def test_validate_whitespace_only(self):
        """Should invalidate whitespace-only string."""
        token = "   "
        result = validate_github_token(token)
        assert result["valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN
        assert (
            "empty" in result["message"].lower()
            or "whitespace" in result["message"].lower()
        )

    def test_validate_token_with_leading_whitespace(self):
        """Should invalidate token with leading whitespace."""
        token = "   ghp_" + "a" * 40
        result = validate_github_token(token)
        assert result["valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN
        assert "whitespace" in result["message"].lower()

    def test_validate_token_with_trailing_whitespace(self):
        """Should invalidate token with trailing whitespace."""
        token = "ghp_" + "a" * 40 + "   "
        result = validate_github_token(token)
        assert result["valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN
        assert "whitespace" in result["message"].lower()

    def test_validate_token_with_embedded_whitespace(self):
        """Should invalidate token with embedded whitespace."""
        token = "ghp_" + "a" * 20 + " " + "a" * 20
        result = validate_github_token(token)
        assert result["valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN

    def test_validate_unknown_prefix(self):
        """Should invalidate token with unknown prefix."""
        token = "ghx_" + "a" * 40
        result = validate_github_token(token)
        assert result["valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN
        assert (
            "unknown" in result["message"].lower()
            or "invalid" in result["message"].lower()
        )

    def test_validate_random_string(self):
        """Should invalidate random string that doesn't match any pattern."""
        token = "random_token_string_12345"
        result = validate_github_token(token)
        assert result["valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN

    def test_validate_non_string_type_int(self):
        """Should handle non-string types (integer)."""
        result = validate_github_token(12345)
        assert result["valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN
        assert "must be a string" in result["message"].lower()

    def test_validate_non_string_type_list(self):
        """Should handle non-string types (list)."""
        result = validate_github_token([])
        assert result["valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN
        assert "must be a string" in result["message"].lower()

    def test_validate_non_string_type_dict(self):
        """Should handle non-string types (dict)."""
        result = validate_github_token({})
        assert result["valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN
        assert "must be a string" in result["message"].lower()

    # Response structure tests
    def test_validate_response_structure_valid(self):
        """Should return correct structure for valid token."""
        token = "ghp_" + "a" * 40
        result = validate_github_token(token)
        assert "valid" in result
        assert "token_type" in result
        assert "message" in result
        assert isinstance(result["valid"], bool)
        assert isinstance(result["token_type"], GitHubTokenType)
        assert isinstance(result["message"], str)

    def test_validate_response_structure_invalid(self):
        """Should return correct structure for invalid token."""
        token = "invalid"
        result = validate_github_token(token)
        assert "valid" in result
        assert "token_type" in result
        assert "message" in result
        assert isinstance(result["valid"], bool)
        assert isinstance(result["token_type"], GitHubTokenType)
        assert isinstance(result["message"], str)

    # Case sensitivity tests
    def test_validate_case_sensitivity_classic(self):
        """Should invalidate uppercase prefix (case sensitive)."""
        token = "GHP_" + "a" * 40
        result = validate_github_token(token)
        assert result["valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN

    def test_validate_case_sensitivity_fine_grained_user(self):
        """Should invalidate uppercase ghu_ prefix."""
        token = "GHU_" + "a" * 20
        result = validate_github_token(token)
        assert result["valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN

    def test_validate_case_sensitivity_fine_grained_pat(self):
        """Should invalidate uppercase github_pat_ prefix."""
        token = "GITHUB_PAT_" + "a" * 20
        result = validate_github_token(token)
        assert result["valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN
