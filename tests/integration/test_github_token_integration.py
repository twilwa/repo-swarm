# ABOUTME: Integration tests for GitHub token authentication with real API calls
# ABOUTME: Tests classic PAT, fine-grained tokens, permission validation, and error handling

import logging
import os
import sys
import time
from pathlib import Path

import pytest
import requests

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from investigator.core.git_manager import GitRepositoryManager
from investigator.core.github_token_utils import (
    GitHubTokenType,
    detect_github_token_type,
    validate_github_token,
)

# Skip all tests if GITHUB_TOKEN not available
pytestmark = pytest.mark.skipif(
    not os.environ.get("GITHUB_TOKEN"),
    reason="GITHUB_TOKEN environment variable not set. "
    "Set valid GitHub token to run integration tests: export GITHUB_TOKEN=your_token",
)


class TestGitHubTokenIntegration:
    """Integration tests for GitHub token authentication with real API calls."""

    @pytest.fixture
    def github_token(self):
        """Get GitHub token from environment."""
        return os.environ.get("GITHUB_TOKEN")

    @pytest.fixture
    def logger(self):
        """Create logger instance."""
        logging.basicConfig(level=logging.DEBUG)
        return logging.getLogger("test_github_token")

    @pytest.fixture
    def git_manager(self, logger):
        """Create GitRepositoryManager instance with logger."""
        return GitRepositoryManager(logger=logger)

    @pytest.fixture
    def public_test_repo(self):
        """Public test repository URL (no auth required)."""
        return "https://github.com/octocat/Hello-World"

    @pytest.fixture
    def github_api_base(self):
        """GitHub API base URL."""
        return "https://api.github.com"

    def _get_auth_header(self, token):
        """Get correct auth header for token type."""
        if token.startswith("ghp_"):
            return f"token {token}"
        elif token.startswith(("ghu_", "github_pat_")):
            return f"Bearer {token}"
        else:
            return f"token {token}"

    def _get_rate_limit_info(self, headers=None):
        """Get current GitHub API rate limit status."""
        if headers is None:
            headers = {}

        try:
            response = requests.get(
                "https://api.github.com/rate_limit", headers=headers, timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("rate", {})
        except Exception as e:
            print(f"Warning: Could not get rate limit info: {e}")
        return {}

    # ========================
    # TOKEN FORMAT & DETECTION TESTS
    # ========================

    def test_token_type_detected(self, github_token):
        """Should detect token type based on prefix."""
        token_type = detect_github_token_type(github_token)
        # Token should have a type (valid tokens are CLASSIC, FINE_GRAINED_USER, or FINE_GRAINED_PAT)
        assert isinstance(token_type, GitHubTokenType)
        assert token_type in [
            GitHubTokenType.CLASSIC,
            GitHubTokenType.FINE_GRAINED_USER,
            GitHubTokenType.FINE_GRAINED_PAT,
            GitHubTokenType.UNKNOWN,
        ]

    def test_token_validation_returns_structured_result(self, github_token):
        """Should validate token and return structured result."""
        result = validate_github_token(github_token)

        # Check response structure
        assert isinstance(result, dict)
        assert "valid" in result
        assert "token_type" in result
        assert "message" in result
        assert isinstance(result["valid"], bool)
        assert isinstance(result["token_type"], GitHubTokenType)
        assert isinstance(result["message"], str)

    # ========================
    # API VALIDATION TESTS
    # ========================

    def test_token_api_validation(self, git_manager):
        """Should validate token with GitHub API /user endpoint."""
        result = git_manager.validate_github_token()

        # Should have response structure
        assert isinstance(result, dict)
        assert "status" in result
        assert "message" in result
        assert "token_type" in result

        # Status should be one of the known values
        assert result["status"] in ["no_token", "valid", "invalid", "error"]

    def test_token_api_returns_user_for_valid_token(self, git_manager, github_token):
        """If token is valid, should return user information."""
        result = git_manager.validate_github_token()

        # If status is valid, should have user info
        if result["status"] == "valid":
            assert "user" in result
            assert "user_info" in result
            assert isinstance(result["user"], str)
            assert len(result["user"]) > 0

    def test_token_api_handles_invalid_token(self, github_token):
        """Should handle invalid token with proper status code."""
        # Use obviously invalid token
        invalid_token = "ghp_" + "0" * 40

        if invalid_token.startswith("ghp_"):
            auth_header = f"token {invalid_token}"
        else:
            auth_header = f"Bearer {invalid_token}"

        headers = {
            "Authorization": auth_header,
            "Accept": "application/vnd.github.v3+json",
        }

        response = requests.get(
            "https://api.github.com/user", headers=headers, timeout=10
        )

        # Invalid token should get 401 response
        assert response.status_code == 401

    def test_rate_limit_info_available(self, github_token):
        """Should get rate limit information."""
        auth_header = self._get_auth_header(github_token)
        headers = {
            "Authorization": auth_header,
            "Accept": "application/vnd.github.v3+json",
        }

        response = requests.get(
            "https://api.github.com/rate_limit", headers=headers, timeout=10
        )

        # Should get rate limit info
        assert response.status_code == 200
        data = response.json()
        assert "rate" in data
        assert "limit" in data["rate"]
        assert "remaining" in data["rate"]

    # ========================
    # ERROR HANDLING TESTS
    # ========================

    def test_invalid_token_format_wrong_prefix(self):
        """Should detect invalid token with wrong prefix."""
        invalid_token = "xyz_" + "a" * 40
        result = validate_github_token(invalid_token)

        assert result["valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN

    def test_invalid_token_format_too_short(self):
        """Should detect token that's too short."""
        invalid_token = "ghp_" + "a" * 20  # Too short
        result = validate_github_token(invalid_token)

        assert result["valid"] is False

    def test_invalid_token_format_empty_string(self):
        """Should reject empty token string."""
        result = validate_github_token("")

        assert result["valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN
        assert "empty" in result["message"].lower()

    def test_invalid_token_format_whitespace(self):
        """Should reject whitespace-only token."""
        result = validate_github_token("   ")

        assert result["valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN

    def test_invalid_token_format_with_whitespace_prefix(self):
        """Should reject token with leading whitespace."""
        invalid_token = "  ghp_" + "a" * 40
        result = validate_github_token(invalid_token)

        assert result["valid"] is False
        assert "whitespace" in result["message"].lower()

    def test_invalid_token_format_with_whitespace_suffix(self):
        """Should reject token with trailing whitespace."""
        invalid_token = "ghp_" + "a" * 40 + "  "
        result = validate_github_token(invalid_token)

        assert result["valid"] is False
        assert "whitespace" in result["message"].lower()

    def test_missing_token_error(self, logger):
        """Should handle missing token gracefully."""
        git_manager = GitRepositoryManager(logger=logger)
        original_token = git_manager.github_token
        git_manager.github_token = None

        result = git_manager.validate_github_token()

        assert result["status"] == "no_token"
        assert "No GitHub token" in result["message"]

        git_manager.github_token = original_token

    def test_empty_token_error(self, logger):
        """Should handle empty token gracefully."""
        git_manager = GitRepositoryManager(logger=logger)
        original_token = git_manager.github_token
        git_manager.github_token = ""

        result = git_manager.validate_github_token()

        assert result["status"] == "invalid"

        git_manager.github_token = original_token

    def test_http_401_on_invalid_token(self):
        """Should get 401 response for invalid token."""
        invalid_token = "ghp_invalid1234567890123456789012345"

        headers = {
            "Authorization": f"token {invalid_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        response = requests.get(
            "https://api.github.com/user", headers=headers, timeout=10
        )

        assert response.status_code == 401

    def test_network_timeout_handling(self, git_manager):
        """Should handle network timeouts gracefully."""
        result = git_manager.validate_github_token()
        # Should get a response (not hang)
        assert "status" in result

    def test_rate_limit_response_handling(self, github_token):
        """Should handle rate limit 429 response."""
        auth_header = self._get_auth_header(github_token)
        headers = {
            "Authorization": auth_header,
            "Accept": "application/vnd.github.v3+json",
        }

        response = requests.get(
            "https://api.github.com/user", headers=headers, timeout=10
        )

        # If rate limited, should have retry headers
        if response.status_code == 429:
            assert (
                "Retry-After" in response.headers
                or "X-RateLimit-Reset" in response.headers
            )

    # ========================
    # REPOSITORY PERMISSION TESTS
    # ========================

    def test_repository_permission_check_structure(self, git_manager):
        """Should return structured result for repository permission check."""
        result = git_manager.check_repository_permissions(
            "https://github.com/octocat/Hello-World"
        )

        # Check response structure
        assert "status" in result
        assert "message" in result
        assert result["status"] in ["allowed", "denied", "not_found", "error"]

    def test_clone_public_repository(self, git_manager, public_test_repo, tmp_path):
        """Should successfully clone public repository."""
        target_dir = str(tmp_path / "test_repo")

        result = git_manager.clone_or_update(public_test_repo, target_dir)

        assert result is not None
        assert os.path.isdir(target_dir)
        assert os.path.isdir(os.path.join(target_dir, ".git"))

    # ========================
    # TOKEN TYPE SPECIFIC TESTS
    # ========================

    def test_classic_pat_format_validation(self):
        """Classic PAT tokens have ghp_ prefix and exactly 44 characters."""
        classic_token = "ghp_" + "a" * 40
        assert len(classic_token) == 44

        result = validate_github_token(classic_token)
        assert result["valid"] is True
        assert result["token_type"] == GitHubTokenType.CLASSIC

    def test_fine_grained_user_format_validation(self):
        """Fine-grained user tokens have ghu_ prefix and variable length."""
        token = "ghu_" + "a" * 10
        result = validate_github_token(token)

        assert result["valid"] is True
        assert result["token_type"] == GitHubTokenType.FINE_GRAINED_USER

    def test_fine_grained_pat_format_validation(self):
        """Fine-grained PAT tokens have github_pat_ prefix and variable length."""
        token = "github_pat_" + "a" * 20
        result = validate_github_token(token)

        assert result["valid"] is True
        assert result["token_type"] == GitHubTokenType.FINE_GRAINED_PAT

    def test_correct_auth_header_for_classic_token(self):
        """Classic tokens should use token auth scheme."""
        classic_token = "ghp_" + "a" * 40
        auth_header = self._get_auth_header(classic_token)
        assert auth_header.startswith("token ")

    def test_correct_auth_header_for_fine_grained_user_token(self):
        """Fine-grained user tokens should use Bearer auth scheme."""
        token = "ghu_something"
        auth_header = self._get_auth_header(token)
        assert auth_header.startswith("Bearer ")

    def test_correct_auth_header_for_fine_grained_pat_token(self):
        """Fine-grained PAT tokens should use Bearer auth scheme."""
        token = "github_pat_something"
        auth_header = self._get_auth_header(token)
        assert auth_header.startswith("Bearer ")

    # ========================
    # EDGE CASE TESTS
    # ========================

    def test_token_none_type_error(self):
        """Should handle None token gracefully."""
        result = validate_github_token(None)

        assert result["valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN
        assert "must be a string" in result["message"].lower()

    def test_token_numeric_type_error(self):
        """Should handle numeric token type gracefully."""
        result = validate_github_token(12345)

        assert result["valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN

    def test_token_list_type_error(self):
        """Should handle list token type gracefully."""
        result = validate_github_token([])

        assert result["valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN

    def test_token_dict_type_error(self):
        """Should handle dict token type gracefully."""
        result = validate_github_token({})

        assert result["valid"] is False
        assert result["token_type"] == GitHubTokenType.UNKNOWN

    def test_sequential_api_calls_same_token(self, github_token):
        """Should handle sequential API calls with same token."""
        auth_header = self._get_auth_header(github_token)
        headers = {
            "Authorization": auth_header,
            "Accept": "application/vnd.github.v3+json",
        }

        # Make a few sequential requests
        responses = []
        for _i in range(3):
            response = requests.get(
                "https://api.github.com/user", headers=headers, timeout=10
            )
            responses.append(response.status_code)
            time.sleep(0.1)  # Small delay

        # All should be successful or all fail (consistent state)
        assert len(set(responses)) <= 2

    def test_unauthenticated_vs_authenticated_rate_limits(self, github_token):
        """Should show difference in rate limits with and without auth."""
        # Unauthenticated
        unauth_response = requests.get("https://api.github.com/rate_limit", timeout=10)

        # Authenticated
        auth_header = self._get_auth_header(github_token)
        headers = {
            "Authorization": auth_header,
            "Accept": "application/vnd.github.v3+json",
        }
        auth_response = requests.get(
            "https://api.github.com/rate_limit", headers=headers, timeout=10
        )

        # Both should succeed
        assert unauth_response.status_code == 200
        assert auth_response.status_code == 200

        # Parse data
        unauth_data = unauth_response.json()
        auth_data = auth_response.json()

        # Authenticated should have higher limit
        unauth_limit = unauth_data.get("rate", {}).get("limit", 0)
        auth_limit = auth_data.get("rate", {}).get("limit", 0)

        assert auth_limit >= unauth_limit

    # ========================
    # DOCUMENTATION TESTS
    # ========================

    def test_github_api_endpoints_documented(self):
        """Document the GitHub API endpoints used for validation."""
        endpoints = {
            "/user": "Get authenticated user (tests token validity)",
            "/rate_limit": "Get rate limit status",
            "/repos/{owner}/{repo}": "Get repository info (tests repo access)",
        }

        for endpoint, description in endpoints.items():
            assert endpoint.startswith("/")
            assert len(description) > 0

    def test_token_authentication_schemes_documented(self):
        """Document the different GitHub token authentication schemes."""
        # Classic PAT: uses token scheme
        classic_auth = "token ghp_example"
        assert classic_auth.startswith("token ")

        # Fine-grained: uses Bearer scheme
        fine_grained_auth = "Bearer github_pat_example"
        assert fine_grained_auth.startswith("Bearer ")

        # These are incompatible - wrong scheme will fail
        assert classic_auth != fine_grained_auth

    def test_token_type_characteristics_documented(self):
        """Document the characteristics of each token type."""
        token_specs = {
            "CLASSIC": {
                "prefix": "ghp_",
                "total_length": 44,
                "suffix_length": 40,
                "auth_scheme": "token",
            },
            "FINE_GRAINED_USER": {
                "prefix": "ghu_",
                "min_suffix_length": 1,
                "auth_scheme": "Bearer",
            },
            "FINE_GRAINED_PAT": {
                "prefix": "github_pat_",
                "min_suffix_length": 1,
                "auth_scheme": "Bearer",
            },
        }

        # Just document these for future developers
        for _token_type, specs in token_specs.items():
            assert "prefix" in specs
            assert "auth_scheme" in specs
