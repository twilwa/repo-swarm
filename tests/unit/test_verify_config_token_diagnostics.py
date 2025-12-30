# ABOUTME: Unit tests for verify_config GitHub token diagnostics
# ABOUTME: Ensures token type detection and permission warnings show in output

import sys
from pathlib import Path

import pytest

# Add repo root and src to path
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from investigator.core.github_token_utils import GitHubTokenType
from scripts.verify_config import ConfigVerifier


class DummyGitManager:
    """Test double for GitRepositoryManager to avoid network calls."""

    def __init__(self, token_result, permission_result):
        self._token_result = token_result
        self._permission_result = permission_result

    def validate_github_token(self):
        return self._token_result

    def check_repository_permissions(self, repo_url):
        return self._permission_result


def _capture_table(verifier):
    captured = {}

    def _display_table(title, results):
        captured["title"] = title
        captured["results"] = results

    verifier._display_table = _display_table
    return captured


def _find_row(results, setting):
    return next((row for row in results if row[1] == setting), None)


def test_verify_config_classic_token_diagnostics(monkeypatch):
    token = "ghp_" + "a" * 40
    monkeypatch.setenv("GITHUB_TOKEN", token)

    token_result = {
        "status": "valid",
        "message": "ok",
        "token_type": GitHubTokenType.CLASSIC,
        "format_valid": True,
        "user": "classic-user",
    }
    permission_result = {
        "status": "allowed",
        "message": "ok",
        "permissions": {"push": True},
    }

    verifier = ConfigVerifier()
    verifier.git_manager = DummyGitManager(token_result, permission_result)
    captured = _capture_table(verifier)

    verifier._test_repository_access()

    token_type_row = _find_row(captured["results"], "Token Type")
    assert token_type_row is not None
    assert token_type_row[2] == "Classic PAT (ghp_)"
    assert token_type_row[3] == "Format valid"
    assert not any("fine-grained" in warning for warning in verifier.warnings)


def test_verify_config_fine_grained_user_token_warning(monkeypatch):
    token = "ghu_" + "a" * 10
    monkeypatch.setenv("GITHUB_TOKEN", token)

    token_result = {
        "status": "valid",
        "message": "ok",
        "token_type": GitHubTokenType.FINE_GRAINED_USER,
        "format_valid": True,
        "user": "fg-user",
    }
    permission_result = {
        "status": "denied",
        "message": "no push",
        "permissions": {"push": False},
    }

    verifier = ConfigVerifier()
    verifier.git_manager = DummyGitManager(token_result, permission_result)
    captured = _capture_table(verifier)

    verifier._test_repository_access()

    token_type_row = _find_row(captured["results"], "Token Type")
    assert token_type_row is not None
    assert token_type_row[2] == "Fine-grained user token (ghu_)"

    warning_text = " ".join(verifier.warnings)
    assert "fine-grained user token" in warning_text.lower()
    assert "repo access" in warning_text.lower()


def test_verify_config_fine_grained_pat_token_warning(monkeypatch):
    token = "github_pat_" + "a" * 20
    monkeypatch.setenv("GITHUB_TOKEN", token)

    token_result = {
        "status": "valid",
        "message": "ok",
        "token_type": GitHubTokenType.FINE_GRAINED_PAT,
        "format_valid": True,
        "user": "fg-pat-user",
    }
    permission_result = {
        "status": "allowed",
        "message": "ok",
        "permissions": {"push": True},
    }

    verifier = ConfigVerifier()
    verifier.git_manager = DummyGitManager(token_result, permission_result)
    captured = _capture_table(verifier)

    verifier._test_repository_access()

    token_type_row = _find_row(captured["results"], "Token Type")
    assert token_type_row is not None
    assert token_type_row[2] == "Fine-grained PAT (github_pat_)"

    warning_text = " ".join(verifier.warnings)
    assert "fine-grained pat" in warning_text.lower()
    assert "repo access" in warning_text.lower()
