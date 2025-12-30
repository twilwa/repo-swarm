# ABOUTME: GitHub token diagnostic utilities for troubleshooting permission issues
# ABOUTME: Detects expired tokens, insufficient scopes, rate limits, and repository access issues

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional

import requests

from .github_token_utils import GitHubTokenType, detect_github_token_type

logger = logging.getLogger(__name__)


class DiagnosticStatus(Enum):
    """Status of diagnostic check"""

    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class TokenIssueType(Enum):
    """Types of token issues that can be detected"""

    EXPIRED_OR_INVALID = "expired_or_invalid"
    INSUFFICIENT_SCOPES = "insufficient_scopes"
    REPOSITORY_NOT_SELECTED = "repository_not_selected"
    RATE_LIMITED = "rate_limited"
    INVALID_FORMAT = "invalid_format"
    NO_PUSH_PERMISSION = "no_push_permission"
    NETWORK_ERROR = "network_error"


@dataclass
class DiagnosticResult:
    """Result of token diagnostic check"""

    status: DiagnosticStatus
    message: str
    issue_type: Optional[TokenIssueType] = None
    recommendations: List[str] = None
    troubleshooting_url: Optional[str] = None
    details: dict = None

    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []
        if self.details is None:
            self.details = {}


def diagnose_github_token(
    token: str, repository: Optional[str] = None
) -> DiagnosticResult:
    """
    Diagnose GitHub token issues and provide actionable recommendations.

    Args:
        token: GitHub token to diagnose
        repository: Optional repository in format 'owner/repo' to check access

    Returns:
        DiagnosticResult with status, issue type, and recommendations
    """
    troubleshooting_url = "https://github.com/your-org/repo-swarm/blob/main/docs/GITHUB_TOKEN_TROUBLESHOOTING.md"

    # Step 1: Validate token format
    try:
        token_type = detect_github_token_type(token)

        # If token type is UNKNOWN, treat as invalid format
        if token_type == GitHubTokenType.UNKNOWN:
            return DiagnosticResult(
                status=DiagnosticStatus.ERROR,
                message="Token has invalid format - doesn't match any known GitHub token pattern",
                issue_type=TokenIssueType.INVALID_FORMAT,
                recommendations=[
                    "Verify you copied the complete token without extra spaces",
                    "Classic tokens should start with 'ghp_'",
                    "Fine-grained tokens should start with 'github_pat_'",
                    "Check the troubleshooting guide for token format details",
                ],
                troubleshooting_url=troubleshooting_url,
            )

    except (ValueError, TypeError) as e:
        return DiagnosticResult(
            status=DiagnosticStatus.ERROR,
            message=f"Token has invalid format: {str(e)}",
            issue_type=TokenIssueType.INVALID_FORMAT,
            recommendations=[
                "Verify you copied the complete token without extra spaces",
                "Classic tokens should start with 'ghp_'",
                "Fine-grained tokens should start with 'github_pat_'",
                "Check the troubleshooting guide for token format details",
            ],
            troubleshooting_url=troubleshooting_url,
        )

    # Step 2: Check token validity and permissions via API
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        # Check user endpoint to validate token
        user_response = requests.get(
            "https://api.github.com/user", headers=headers, timeout=10
        )

        # Handle rate limiting
        if user_response.status_code == 429:
            reset_time = user_response.headers.get("X-RateLimit-Reset", "unknown")
            if reset_time != "unknown":
                reset_dt = datetime.fromtimestamp(int(reset_time))
                reset_str = reset_dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                reset_str = "unknown"

            return DiagnosticResult(
                status=DiagnosticStatus.ERROR,
                message=f"GitHub API rate limit exceeded. Resets at {reset_str}",
                issue_type=TokenIssueType.RATE_LIMITED,
                recommendations=[
                    "Wait until rate limit reset time",
                    "Use a different token if available",
                    "Check rate limit status: https://api.github.com/rate_limit",
                    "Consider upgrading to GitHub Pro for higher limits",
                ],
                troubleshooting_url=troubleshooting_url,
                details={
                    "reset_time": reset_str,
                    "remaining": user_response.headers.get(
                        "X-RateLimit-Remaining", "0"
                    ),
                },
            )

        # Handle authentication errors
        if user_response.status_code == 401:
            return DiagnosticResult(
                status=DiagnosticStatus.ERROR,
                message="Token is expired or invalid",
                issue_type=TokenIssueType.EXPIRED_OR_INVALID,
                recommendations=[
                    "Generate a new token at https://github.com/settings/tokens",
                    "For fine-grained tokens, check expiration date in token settings",
                    "Verify the token was copied completely without truncation",
                    "Update GITHUB_TOKEN in your .env.local file",
                ],
                troubleshooting_url=troubleshooting_url,
            )

        # Handle permission errors at user level
        if user_response.status_code == 403:
            return DiagnosticResult(
                status=DiagnosticStatus.ERROR,
                message="Token lacks required permissions",
                issue_type=TokenIssueType.INSUFFICIENT_SCOPES,
                recommendations=[
                    "Classic tokens: Verify 'repo' scope is selected",
                    "Fine-grained tokens: Verify 'Contents' permission is set to 'Read and write'",
                    "Regenerate token with correct scopes at https://github.com/settings/tokens",
                    "See troubleshooting guide for detailed permission requirements",
                ],
                troubleshooting_url=troubleshooting_url,
            )

        # Check for successful user validation
        if user_response.status_code != 200:
            return DiagnosticResult(
                status=DiagnosticStatus.ERROR,
                message=f"Unexpected response from GitHub API: {user_response.status_code}",
                issue_type=TokenIssueType.NETWORK_ERROR,
                recommendations=[
                    "Check network connectivity",
                    "Verify GitHub API is accessible",
                    f"Review response: {user_response.text[:200]}",
                ],
                troubleshooting_url=troubleshooting_url,
            )

        user_data = user_response.json()
        username = user_data.get("login", "unknown")
        scopes = user_response.headers.get("X-OAuth-Scopes", "")

        # Step 3: Check repository access if repository specified
        if repository:
            repo_response = requests.get(
                f"https://api.github.com/repos/{repository}",
                headers=headers,
                timeout=10,
            )

            # Repository not found - could be private or not selected for fine-grained token
            if repo_response.status_code == 404:
                if token_type == GitHubTokenType.FINE_GRAINED_PAT:
                    return DiagnosticResult(
                        status=DiagnosticStatus.ERROR,
                        message=f"Repository '{repository}' is not selected in fine-grained token settings",
                        issue_type=TokenIssueType.REPOSITORY_NOT_SELECTED,
                        recommendations=[
                            "Edit your token at https://github.com/settings/tokens",
                            f"In 'Repository access', select '{repository}'",
                            "Save changes and wait a few minutes for propagation",
                            "Alternatively, select 'All repositories' if appropriate",
                        ],
                        troubleshooting_url=troubleshooting_url,
                        details={
                            "repository": repository,
                            "token_type": token_type.value,
                        },
                    )
                else:
                    return DiagnosticResult(
                        status=DiagnosticStatus.ERROR,
                        message=f"Repository '{repository}' not found or token lacks access",
                        issue_type=TokenIssueType.INSUFFICIENT_SCOPES,
                        recommendations=[
                            "Verify repository name is correct (case-sensitive)",
                            "Verify token has 'repo' scope for private repositories",
                            f"Check repository exists: https://github.com/{repository}",
                            "Ensure token owner has access to the repository",
                        ],
                        troubleshooting_url=troubleshooting_url,
                        details={"repository": repository},
                    )

            # Permission denied
            if repo_response.status_code == 403:
                return DiagnosticResult(
                    status=DiagnosticStatus.ERROR,
                    message=f"Token has insufficient permissions for repository '{repository}'",
                    issue_type=TokenIssueType.INSUFFICIENT_SCOPES,
                    recommendations=[
                        "Classic tokens: Ensure 'repo' scope is selected",
                        "Fine-grained tokens: Ensure 'Contents' permission is 'Read and write'",
                        "Verify repository is selected in token settings",
                        "Check token hasn't been revoked by repository owner",
                    ],
                    troubleshooting_url=troubleshooting_url,
                    details={"repository": repository, "scopes": scopes},
                )

            # Check push permissions
            if repo_response.status_code == 200:
                repo_data = repo_response.json()
                permissions = repo_data.get("permissions", {})

                if not permissions.get("push", False):
                    return DiagnosticResult(
                        status=DiagnosticStatus.WARNING,
                        message=f"Token has read-only access to '{repository}' - push operations will fail",
                        issue_type=TokenIssueType.NO_PUSH_PERMISSION,
                        recommendations=[
                            "Token can read repository but cannot write/push",
                            "For architecture hub commits, you need write access",
                            "Classic tokens: Verify 'repo' scope (not just 'public_repo')",
                            "Fine-grained tokens: Change 'Contents' permission to 'Read and write'",
                        ],
                        troubleshooting_url=troubleshooting_url,
                        details={
                            "repository": repository,
                            "permissions": permissions,
                            "can_pull": permissions.get("pull", False),
                            "can_push": permissions.get("push", False),
                        },
                    )

        # Success case
        rate_remaining = user_response.headers.get("X-RateLimit-Remaining", "unknown")
        rate_limit = user_response.headers.get("X-RateLimit-Limit", "unknown")

        success_message = f"Token successfully validated for user '{username}'"
        if repository:
            success_message += f" with push access to '{repository}'"

        return DiagnosticResult(
            status=DiagnosticStatus.SUCCESS,
            message=success_message,
            details={
                "username": username,
                "token_type": token_type.value,
                "scopes": scopes,
                "rate_limit_remaining": rate_remaining,
                "rate_limit_total": rate_limit,
            },
        )

    except requests.exceptions.Timeout:
        return DiagnosticResult(
            status=DiagnosticStatus.ERROR,
            message="GitHub API request timed out",
            issue_type=TokenIssueType.NETWORK_ERROR,
            recommendations=[
                "Check network connectivity",
                "Verify GitHub API is accessible (https://www.githubstatus.com)",
                "Try again in a few moments",
            ],
            troubleshooting_url=troubleshooting_url,
        )

    except requests.exceptions.RequestException as e:
        return DiagnosticResult(
            status=DiagnosticStatus.ERROR,
            message=f"Network error while validating token: {str(e)}",
            issue_type=TokenIssueType.NETWORK_ERROR,
            recommendations=[
                "Check network connectivity",
                "Verify proxy settings if applicable",
                "Check firewall rules for api.github.com access",
            ],
            troubleshooting_url=troubleshooting_url,
        )
