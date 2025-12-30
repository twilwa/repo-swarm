# ABOUTME: Tests for GitRepositoryManager validate_github_token() method
# ABOUTME: Validates token detection, validation, and backward compatibility

import os
import subprocess
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

from investigator.core.git_manager import GitRepositoryManager
from investigator.core.github_token_utils import GitHubTokenType


class TestValidateGitHubToken:
    """Test validate_github_token() method with new token utilities."""

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        return Mock()

    @pytest.fixture
    def git_manager(self, mock_logger):
        """Create GitRepositoryManager instance with mocked logger."""
        return GitRepositoryManager(mock_logger)

    def test_no_token_in_environment(self, git_manager):
        """Test when GITHUB_TOKEN environment variable is not set."""
        git_manager.github_token = None
        result = git_manager.validate_github_token()

        assert result["status"] == "no_token"
        assert "No GitHub token" in result["message"]

    def test_classic_token_format_invalid(self, git_manager):
        """Test CLASSIC token with invalid format (wrong length)."""
        git_manager.github_token = "ghp_" + "a" * 39  # Too short
        result = git_manager.validate_github_token()

        assert result["status"] == "invalid"
        assert result["format_valid"] is False
        assert "exactly 40 characters" in result["message"]
        assert result["token_type"] == GitHubTokenType.UNKNOWN

    def test_classic_token_format_valid_api_call(self, git_manager):
        """Test CLASSIC token with valid format, successful API call."""
        valid_classic_token = "ghp_" + "a" * 40
        git_manager.github_token = valid_classic_token

        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"login": "testuser"}
            mock_get.return_value = mock_response

            result = git_manager.validate_github_token()

        assert result["status"] == "valid"
        assert result["format_valid"] is True
        assert result["token_type"] == GitHubTokenType.CLASSIC
        assert result["user"] == "testuser"
        assert "testuser" in result["message"]

    def test_fine_grained_user_token_format_valid(self, git_manager):
        """Test FINE_GRAINED_USER token with valid format."""
        valid_user_token = "ghu_" + "a" * 15
        git_manager.github_token = valid_user_token

        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"login": "usertoken"}
            mock_get.return_value = mock_response

            result = git_manager.validate_github_token()

        assert result["status"] == "valid"
        assert result["format_valid"] is True
        assert result["token_type"] == GitHubTokenType.FINE_GRAINED_USER
        assert result["user"] == "usertoken"

    def test_fine_grained_user_token_format_invalid(self, git_manager):
        """Test FINE_GRAINED_USER token with invalid format (too short)."""
        git_manager.github_token = "ghu_" + "a" * 5  # Too short
        result = git_manager.validate_github_token()

        assert result["status"] == "invalid"
        assert result["format_valid"] is False
        assert "minimum 10 characters" in result["message"]
        assert result["token_type"] == GitHubTokenType.UNKNOWN

    def test_fine_grained_pat_token_format_valid(self, git_manager):
        """Test FINE_GRAINED_PAT token with valid format."""
        valid_pat_token = "github_pat_" + "a" * 25
        git_manager.github_token = valid_pat_token

        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"login": "patuser"}
            mock_get.return_value = mock_response

            result = git_manager.validate_github_token()

        assert result["status"] == "valid"
        assert result["format_valid"] is True
        assert result["token_type"] == GitHubTokenType.FINE_GRAINED_PAT
        assert result["user"] == "patuser"

    def test_fine_grained_pat_token_format_invalid(self, git_manager):
        """Test FINE_GRAINED_PAT token with invalid format (too short)."""
        git_manager.github_token = "github_pat_" + "a" * 10  # Too short
        result = git_manager.validate_github_token()

        assert result["status"] == "invalid"
        assert result["format_valid"] is False
        assert "minimum 20 characters" in result["message"]
        assert result["token_type"] == GitHubTokenType.UNKNOWN

    def test_api_call_fails_with_http_401(self, git_manager):
        """Test API call returns 401 (invalid token)."""
        valid_classic_token = "ghp_" + "a" * 40
        git_manager.github_token = valid_classic_token

        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_get.return_value = mock_response

            result = git_manager.validate_github_token()

        assert result["status"] == "invalid"
        assert result["format_valid"] is True  # Format was OK
        assert result["token_type"] == GitHubTokenType.CLASSIC
        assert (
            "API validation failed" in result["message"] or "401" in result["message"]
        )

    def test_api_call_fails_with_http_403(self, git_manager):
        """Test API call returns 403 (forbidden/no permission)."""
        valid_classic_token = "ghp_" + "a" * 40
        git_manager.github_token = valid_classic_token

        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 403
            mock_get.return_value = mock_response

            result = git_manager.validate_github_token()

        assert result["status"] == "invalid"
        assert result["format_valid"] is True
        assert result["token_type"] == GitHubTokenType.CLASSIC
        assert "403" in str(result.get("status_code", ""))

    def test_api_call_network_error(self, git_manager):
        """Test API call raises network exception."""
        valid_classic_token = "ghp_" + "a" * 40
        git_manager.github_token = valid_classic_token

        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception("Network error")

            result = git_manager.validate_github_token()

        assert result["status"] == "error"
        assert result["format_valid"] is True  # Format was valid
        assert result["token_type"] == GitHubTokenType.CLASSIC
        assert "error" in result["message"].lower()

    def test_backward_compatibility_valid_token(self, git_manager):
        """Test backward compatibility: all old fields still present for valid token."""
        valid_classic_token = "ghp_" + "a" * 40
        git_manager.github_token = valid_classic_token

        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "login": "backcompat_user",
                "id": 12345,
                "type": "User",
            }
            mock_get.return_value = mock_response

            result = git_manager.validate_github_token()

        # Old fields (backward compatibility)
        assert "status" in result
        assert "message" in result
        assert "user" in result
        assert "user_info" in result

        # New fields (enhancements)
        assert "token_type" in result
        assert "format_valid" in result

        # Values
        assert result["status"] == "valid"
        assert result["user"] == "backcompat_user"
        assert result["user_info"]["login"] == "backcompat_user"
        assert result["token_type"] == GitHubTokenType.CLASSIC
        assert result["format_valid"] is True

    def test_backward_compatibility_no_token(self, git_manager):
        """Test backward compatibility: handles no token case."""
        git_manager.github_token = None
        result = git_manager.validate_github_token()

        assert result["status"] == "no_token"
        assert "message" in result
        assert "No GitHub token" in result["message"]

    def test_bearer_format_in_api_call(self, git_manager):
        """Test that API call uses Bearer format for fine-grained tokens."""
        valid_user_token = "ghu_" + "a" * 15
        git_manager.github_token = valid_user_token

        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"login": "testuser"}
            mock_get.return_value = mock_response

            git_manager.validate_github_token()

            # Check that Bearer format is used
            call_args = mock_get.call_args
            headers = call_args.kwargs.get("headers") or call_args[1].get("headers")

            # Should use Bearer format for fine-grained tokens
            auth_header = headers.get("Authorization", "")
            assert auth_header == f"Bearer {valid_user_token}"

    def test_classic_token_format_in_api_call(self, git_manager):
        """Test that API call uses token format for classic tokens."""
        valid_classic_token = "ghp_" + "a" * 40
        git_manager.github_token = valid_classic_token

        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"login": "testuser"}
            mock_get.return_value = mock_response

            git_manager.validate_github_token()

            call_args = mock_get.call_args
            headers = call_args.kwargs.get("headers") or call_args[1].get("headers")

            auth_header = headers.get("Authorization", "")
            assert auth_header == f"token {valid_classic_token}"

    def test_token_type_detection_priority(self, git_manager):
        """Test that github_pat_ prefix has priority over ghu_."""
        # This tests the priority of token detection


class TestGitAuthentication:
    """Test Git URL authentication and permission error handling."""

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        return Mock()

    @pytest.fixture
    def git_manager(self, mock_logger):
        """Create GitRepositoryManager instance with mocked logger."""
        return GitRepositoryManager(mock_logger)

    def test_add_authentication_classic_token(self, git_manager):
        """Test ghp_ token gets embedded in GitHub HTTPS URL."""
        token = "ghp_" + "a" * 40
        git_manager.github_token = token

        url = "https://github.com/org/repo.git"
        auth_url = git_manager._add_authentication(url)

        assert auth_url == f"https://{token}@github.com/org/repo.git"

    def test_add_authentication_fine_grained_pat(self, git_manager):
        """Test github_pat_ token gets embedded in GitHub HTTPS URL."""
        token = "github_pat_" + "a" * 25
        git_manager.github_token = token

        url = "https://github.com/org/repo.git"
        auth_url = git_manager._add_authentication(url)

        assert auth_url == f"https://{token}@github.com/org/repo.git"

    def test_add_authentication_fine_grained_user(self, git_manager):
        """Test ghu_ token gets embedded in GitHub HTTPS URL."""
        token = "ghu_" + "a" * 15
        git_manager.github_token = token

        url = "https://github.com/org/repo.git"
        auth_url = git_manager._add_authentication(url)

        assert auth_url == f"https://{token}@github.com/org/repo.git"

    def test_clone_permission_error_fine_grained_pat(self, git_manager):
        """Test clone permission error includes fine-grained token type."""
        token = "github_pat_" + "a" * 25
        git_manager.github_token = token

        auth_url = git_manager._add_authentication("https://github.com/org/repo.git")

        with patch.object(git_manager, "_ensure_clean_directory"), patch(
            "git.Repo.clone_from"
        ) as mock_clone:
            import git

            mock_clone.side_effect = git.exc.GitCommandError(
                "clone",
                128,
                stderr="remote: Repository not found.\nfatal: repository not found",
            )

            with pytest.raises(Exception) as exc_info:
                git_manager._clone_repository(auth_url, "/tmp/repo")

        error_message = str(exc_info.value)
        assert "Fine-grained token" in error_message
        assert "FINE_GRAINED_PAT" in error_message

    def test_push_permission_error_fine_grained_user(self, git_manager):
        """Test push permission error includes fine-grained token type."""
        token = "ghu_" + "a" * 15
        git_manager.github_token = token

        def run_side_effect(cmd, *args, **kwargs):
            if cmd[:3] == ["git", "remote", "get-url"]:
                return subprocess.CompletedProcess(
                    cmd, 0, stdout="https://github.com/org/repo.git\n", stderr=""
                )
            if cmd[:3] == ["git", "remote", "set-url"]:
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
            if cmd[:2] == ["git", "push"]:
                return subprocess.CompletedProcess(
                    cmd,
                    1,
                    stdout="",
                    stderr="remote: Permission to org/repo denied",
                )
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        with patch("investigator.core.git_manager.subprocess.run") as mock_run:
            mock_run.side_effect = run_side_effect
            result = git_manager.push_with_authentication("/tmp/repo", branch="main")

        assert result["status"] == "failed"
        assert "Fine-grained token" in result["message"]
        assert "FINE_GRAINED_USER" in result["message"]
        valid_pat_token = "github_pat_" + "a" * 25
        git_manager.github_token = valid_pat_token

        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"login": "testuser"}
            mock_get.return_value = mock_response

            result = git_manager.validate_github_token()

        # Must be detected as PAT, not USER
        assert result["token_type"] == GitHubTokenType.FINE_GRAINED_PAT

    def test_unknown_token_format(self, git_manager):
        """Test with completely invalid token format."""
        git_manager.github_token = "invalid_token_xyz"
        result = git_manager.validate_github_token()

        assert result["status"] == "invalid"
        assert result["format_valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN

    def test_empty_token_string(self, git_manager):
        """Test with empty token string."""
        git_manager.github_token = ""
        result = git_manager.validate_github_token()

        assert result["status"] == "invalid"
        assert result["format_valid"] is False
        assert "empty" in result["message"].lower()

    def test_token_with_whitespace(self, git_manager):
        """Test that tokens with whitespace are detected as invalid."""
        git_manager.github_token = "  ghp_" + "a" * 40
        result = git_manager.validate_github_token()

        assert result["status"] == "invalid"
        assert result["format_valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN


class TestTokenDetectionIntegration:
    """Integration tests for token detection with git_manager."""

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        return Mock()

    @pytest.fixture
    def git_manager(self, mock_logger):
        """Create GitRepositoryManager instance."""
        return GitRepositoryManager(mock_logger)

    def test_all_token_types_detected_correctly(self, git_manager):
        """Test that all token types are correctly identified."""
        test_cases = [
            ("ghp_" + "a" * 40, GitHubTokenType.CLASSIC),
            ("ghu_" + "a" * 15, GitHubTokenType.FINE_GRAINED_USER),
            ("github_pat_" + "a" * 25, GitHubTokenType.FINE_GRAINED_PAT),
        ]

        for token, expected_type in test_cases:
            git_manager.github_token = token

            with patch("requests.get") as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"login": "testuser"}
                mock_get.return_value = mock_response

                result = git_manager.validate_github_token()

            assert (
                result["token_type"] == expected_type
            ), f"Token {token[:10]}... should be {expected_type}, got {result['token_type']}"
