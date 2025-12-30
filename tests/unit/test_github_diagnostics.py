# ABOUTME: Unit tests for GitHub token diagnostic utilities
# ABOUTME: Tests detection of common token permission and configuration issues

from unittest.mock import Mock, patch

import pytest

from src.investigator.core.github_diagnostics import (
    DiagnosticResult,
    DiagnosticStatus,
    TokenIssueType,
    diagnose_github_token,
)

# Valid test tokens matching GitHub's actual format
VALID_CLASSIC_TOKEN = "ghp_" + "a" * 40  # Classic token format
VALID_FINEGRAINED_USER_TOKEN = "ghu_" + "a" * 15  # Fine-grained user token format
VALID_FINEGRAINED_PAT_TOKEN = "github_pat_" + "a" * 30  # Fine-grained PAT token format


class TestGitHubDiagnostics:
    """Test GitHub token diagnostic utilities"""

    def test_diagnose_valid_token(self):
        """Should return success for valid token with proper permissions"""
        with patch("src.investigator.core.github_diagnostics.requests.get") as mock_get:
            # Mock successful user endpoint
            user_response = Mock()
            user_response.status_code = 200
            user_response.json.return_value = {"login": "testuser"}
            user_response.headers = {
                "X-OAuth-Scopes": "repo, user",
                "X-RateLimit-Remaining": "5000",
                "X-RateLimit-Limit": "5000",
            }

            # Mock successful repo endpoint
            repo_response = Mock()
            repo_response.status_code = 200
            repo_response.json.return_value = {"permissions": {"push": True}}

            mock_get.side_effect = [user_response, repo_response]

            result = diagnose_github_token(VALID_CLASSIC_TOKEN, "owner/repo")

            assert result.status == DiagnosticStatus.SUCCESS
            assert result.issue_type is None
            assert "successfully validated" in result.message.lower()

    def test_diagnose_expired_token(self):
        """Should detect expired token"""
        with patch("src.investigator.core.github_diagnostics.requests.get") as mock_get:
            response = Mock()
            response.status_code = 401
            response.json.return_value = {
                "message": "Bad credentials",
                "documentation_url": "https://docs.github.com/rest",
            }
            mock_get.return_value = response

            result = diagnose_github_token(VALID_CLASSIC_TOKEN)

            assert result.status == DiagnosticStatus.ERROR
            assert result.issue_type == TokenIssueType.EXPIRED_OR_INVALID
            assert "expired or invalid" in result.message.lower()
            assert len(result.recommendations) > 0

    def test_diagnose_insufficient_scopes(self):
        """Should detect insufficient scopes"""
        with patch("src.investigator.core.github_diagnostics.requests.get") as mock_get:
            # User endpoint succeeds but with limited scopes
            user_response = Mock()
            user_response.status_code = 200
            user_response.json.return_value = {"login": "testuser"}
            user_response.headers = {
                "X-OAuth-Scopes": "public_repo",  # Missing 'repo' scope
                "X-RateLimit-Remaining": "5000",
            }

            # Repo endpoint fails with 403
            repo_response = Mock()
            repo_response.status_code = 403
            repo_response.json.return_value = {
                "message": "Resource not accessible by personal access token"
            }

            mock_get.side_effect = [user_response, repo_response]

            result = diagnose_github_token(VALID_CLASSIC_TOKEN, "owner/private-repo")

            assert result.status == DiagnosticStatus.ERROR
            assert result.issue_type == TokenIssueType.INSUFFICIENT_SCOPES
            assert "insufficient permissions" in result.message.lower()

    def test_diagnose_repository_not_selected(self):
        """Should detect when fine-grained token doesn't have repository selected"""
        with patch("src.investigator.core.github_diagnostics.requests.get") as mock_get:
            # User endpoint succeeds
            user_response = Mock()
            user_response.status_code = 200
            user_response.json.return_value = {"login": "testuser"}
            user_response.headers = {"X-RateLimit-Remaining": "5000"}

            # Repo endpoint returns 404 (repo not selected)
            repo_response = Mock()
            repo_response.status_code = 404
            repo_response.json.return_value = {"message": "Not Found"}

            mock_get.side_effect = [user_response, repo_response]

            result = diagnose_github_token(VALID_FINEGRAINED_PAT_TOKEN, "owner/repo")

            assert result.status == DiagnosticStatus.ERROR
            assert result.issue_type == TokenIssueType.REPOSITORY_NOT_SELECTED
            assert "not selected" in result.message.lower()

    def test_diagnose_rate_limited(self):
        """Should detect rate limiting"""
        with patch("src.investigator.core.github_diagnostics.requests.get") as mock_get:
            response = Mock()
            response.status_code = 429
            response.headers = {
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": "1640000000",
            }
            response.json.return_value = {"message": "API rate limit exceeded"}
            mock_get.return_value = response

            result = diagnose_github_token(VALID_CLASSIC_TOKEN)

            assert result.status == DiagnosticStatus.ERROR
            assert result.issue_type == TokenIssueType.RATE_LIMITED
            assert "rate limit" in result.message.lower()

    def test_diagnose_invalid_token_format(self):
        """Should detect invalid token format before making API calls"""
        # Test with a token that doesn't match any known pattern
        result = diagnose_github_token("invalid_token_123")

        assert result.status == DiagnosticStatus.ERROR
        assert result.issue_type == TokenIssueType.INVALID_FORMAT
        assert "invalid format" in result.message.lower()

    def test_diagnose_no_push_permission(self):
        """Should detect when token has read but not write permission"""
        with patch("src.investigator.core.github_diagnostics.requests.get") as mock_get:
            # User endpoint succeeds
            user_response = Mock()
            user_response.status_code = 200
            user_response.json.return_value = {"login": "testuser"}
            user_response.headers = {
                "X-OAuth-Scopes": "repo",
                "X-RateLimit-Remaining": "5000",
            }

            # Repo endpoint succeeds but no push permission
            repo_response = Mock()
            repo_response.status_code = 200
            repo_response.json.return_value = {
                "permissions": {"pull": True, "push": False}
            }

            mock_get.side_effect = [user_response, repo_response]

            result = diagnose_github_token(VALID_CLASSIC_TOKEN, "owner/repo")

            assert result.status == DiagnosticStatus.WARNING
            assert result.issue_type == TokenIssueType.NO_PUSH_PERMISSION
            assert "read-only" in result.message.lower()

    def test_diagnostic_result_includes_recommendations(self):
        """Should include actionable recommendations for each issue type"""
        with patch("src.investigator.core.github_diagnostics.requests.get") as mock_get:
            response = Mock()
            response.status_code = 401
            response.json.return_value = {"message": "Bad credentials"}
            mock_get.return_value = response

            result = diagnose_github_token(VALID_CLASSIC_TOKEN)

            assert len(result.recommendations) >= 2
            # Check for "generate" in recommendations
            assert any("generate" in rec.lower() for rec in result.recommendations)

    def test_diagnostic_result_includes_troubleshooting_url(self):
        """Should include link to troubleshooting guide"""
        with patch("src.investigator.core.github_diagnostics.requests.get") as mock_get:
            response = Mock()
            response.status_code = 403
            response.json.return_value = {"message": "Resource not accessible"}
            mock_get.return_value = response

            result = diagnose_github_token(VALID_CLASSIC_TOKEN)

            assert result.troubleshooting_url is not None
            assert "troubleshooting" in result.troubleshooting_url.lower()
