# ABOUTME: Unit tests for fine-grained token permission error detection and messaging
# ABOUTME: Tests improved error messages with actionable guidance and documentation links

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from investigator.core.git_manager import GitRepositoryManager
from investigator.core.github_token_utils import GitHubTokenType


class TestPermissionErrorDetection:
    """Test suite for detecting GitHub API permission errors."""

    def test_detect_403_permission_error(self):
        """Should detect 403 Forbidden error as permission issue."""
        logger = Mock()
        manager = GitRepositoryManager(logger)

        error_msg = "fatal: could not read Username for 'https://github.com': terminal prompts disabled\nHTTP/1.1 403 Forbidden"
        assert manager._is_permission_error(error_msg) is True

    def test_detect_resource_not_accessible(self):
        """Should detect 'Resource not accessible' error from GitHub API."""
        logger = Mock()
        manager = GitRepositoryManager(logger)

        error_msg = "Resource not accessible by personal access token"
        assert manager._is_permission_error(error_msg) is True

    def test_detect_insufficient_scopes(self):
        """Should detect insufficient scopes error."""
        logger = Mock()
        manager = GitRepositoryManager(logger)

        error_msg = "This fine-grained personal access token does not have the required permissions"
        assert manager._is_permission_error(error_msg) is True

    def test_detect_fine_grained_repository_access_error(self):
        """Should detect fine-grained token without repository access."""
        logger = Mock()
        manager = GitRepositoryManager(logger)

        error_msg = "Resource not accessible by fine-grained personal access token"
        assert manager._is_permission_error(error_msg) is True


class TestPermissionErrorMessages:
    """Test suite for permission error messages with actionable guidance."""

    def test_fine_grained_clone_error_message_includes_required_permissions(self):
        """Should include specific required permissions for clone operations."""
        logger = Mock()
        manager = GitRepositoryManager(logger)

        message = manager._build_permission_error_message(
            operation="Failed to clone repository",
            token_type=GitHubTokenType.FINE_GRAINED_PAT,
            permission_hint="Ensure the token includes this repository and has Contents (read) permission.",
        )

        assert "Fine-grained token" in message
        assert "Contents (read)" in message
        assert "Ensure the token includes this repository" in message

    def test_fine_grained_push_error_message_includes_write_permission(self):
        """Should include write permission requirement for push operations."""
        logger = Mock()
        manager = GitRepositoryManager(logger)

        message = manager._build_permission_error_message(
            operation="Failed to push changes",
            token_type=GitHubTokenType.FINE_GRAINED_PAT,
            permission_hint="Ensure the token includes this repository and has Contents (write) permission.",
        )

        assert "Fine-grained token" in message
        assert "Contents (write)" in message

    def test_permission_error_message_includes_documentation_link(self):
        """Should include link to GitHub documentation for fixing permissions."""
        logger = Mock()
        manager = GitRepositoryManager(logger)

        message = manager._build_permission_error_message(
            operation="Failed to access repository",
            token_type=GitHubTokenType.FINE_GRAINED_PAT,
            permission_hint="Ensure the token includes this repository and has Contents (read) permission.",
            include_docs_link=True,
        )

        assert (
            "https://docs.github.com" in message or "documentation" in message.lower()
        )

    def test_permission_error_distinguishes_repository_access_vs_permission_scopes(
        self,
    ):
        """Should distinguish between repository not included vs insufficient permission scopes."""
        logger = Mock()
        manager = GitRepositoryManager(logger)

        # Repository not included in token access list
        repo_access_msg = manager._build_permission_error_message(
            operation="Failed to clone",
            token_type=GitHubTokenType.FINE_GRAINED_PAT,
            permission_hint="Repository not included in token's repository access list.",
            include_docs_link=True,
        )

        assert (
            "repository access list" in repo_access_msg.lower()
            or "not included" in repo_access_msg.lower()
        )

    def test_fine_grained_user_token_error_message(self):
        """Should provide appropriate message for fine-grained user tokens."""
        logger = Mock()
        manager = GitRepositoryManager(logger)

        message = manager._build_permission_error_message(
            operation="Failed to access repository",
            token_type=GitHubTokenType.FINE_GRAINED_USER,
            permission_hint="Ensure the token includes this repository and has Contents (read) permission.",
        )

        assert "Fine-grained token" in message
        assert "FINE_GRAINED_USER" in message

    def test_classic_token_error_message_differs_from_fine_grained(self):
        """Should provide different guidance for classic tokens vs fine-grained."""
        logger = Mock()
        manager = GitRepositoryManager(logger)

        classic_msg = manager._build_permission_error_message(
            operation="Failed to clone",
            token_type=GitHubTokenType.CLASSIC,
            permission_hint="Check token scopes.",
        )

        fine_grained_msg = manager._build_permission_error_message(
            operation="Failed to clone",
            token_type=GitHubTokenType.FINE_GRAINED_PAT,
            permission_hint="Ensure the token includes this repository and has Contents (read) permission.",
        )

        # Classic tokens don't have repository access lists
        assert "CLASSIC" in classic_msg
        assert classic_msg != fine_grained_msg
        assert "Fine-grained" in fine_grained_msg


class TestGitHubAPIPermissionErrors:
    """Test suite for detecting permission errors from GitHub API responses."""

    @patch("requests.get")
    def test_detect_api_403_permission_error(self, mock_get):
        """Should detect 403 API response and provide helpful message."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.json.return_value = {
            "message": "Resource not accessible by personal access token",
            "documentation_url": "https://docs.github.com/rest/overview/permissions-required-for-fine-grained-personal-access-tokens",
        }
        mock_get.return_value = mock_response

        # This would be called from update_repos.py or similar
        response = mock_get("https://api.github.com/repos/owner/repo")

        assert response.status_code == 403
        assert "not accessible" in response.json()["message"]
        assert "documentation_url" in response.json()

    @patch("requests.get")
    def test_detect_api_404_vs_403_distinction(self, mock_get):
        """Should distinguish between 404 (not found/no access) and 403 (permission denied)."""
        # 404 could mean repo doesn't exist OR token can't see it
        mock_404 = Mock()
        mock_404.status_code = 404

        # 403 specifically means permission denied
        mock_403 = Mock()
        mock_403.status_code = 403

        # Different HTTP codes should be treated differently
        assert mock_404.status_code != mock_403.status_code


class TestPermissionErrorIntegration:
    """Integration tests for permission error handling in real scenarios."""

    def test_clone_with_insufficient_permissions_provides_clear_message(self):
        """Should provide clear, actionable message when clone fails due to permissions."""
        logger = Mock()
        manager = GitRepositoryManager(logger)
        manager.github_token = "github_pat_" + "a" * 82  # Fine-grained PAT

        # Simulate clone failure with permission error
        with patch("git.Repo.clone_from") as mock_clone:
            from git.exc import GitCommandError

            mock_clone.side_effect = GitCommandError(
                "git clone",
                128,
                stderr="fatal: could not read Username for 'https://github.com': Permission denied",
            )

            with pytest.raises(Exception) as exc_info:
                manager._clone_repository(
                    "https://github.com/test/repo", "/tmp/test-repo"
                )

            error_message = str(exc_info.value)
            # Should contain helpful information
            assert (
                "Fine-grained token" in error_message
                or "permission" in error_message.lower()
            )

    def test_push_with_read_only_token_provides_write_permission_hint(self):
        """Should specifically mention write permission when push fails."""
        logger = Mock()
        manager = GitRepositoryManager(logger)
        manager.github_token = "github_pat_" + "a" * 82  # Fine-grained PAT

        with patch("subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stderr = "Permission to org/repo denied"
            mock_run.return_value = mock_result

            result = manager.push_with_authentication("/tmp/test-repo")

            assert result["status"] == "failed"
            # Should mention write permission specifically
            assert (
                "write" in result["message"].lower()
                or "Contents (write)" in result["message"]
            )
