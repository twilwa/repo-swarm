# ABOUTME: Tests GitHub auth header selection in update_repos script
# ABOUTME: Ensures classic vs fine-grained tokens use correct Authorization format

import os
import sys
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../scripts"))

import update_repos


def _mock_response(status_code=200, json_data=None, headers=None):
    response = Mock()
    response.status_code = status_code
    response.json.return_value = json_data if json_data is not None else []
    response.headers = headers or {}
    response.raise_for_status = Mock()
    return response


@pytest.mark.parametrize(
    "token,expected_header",
    [
        ("ghp_" + "a" * 40, "token ghp_" + "a" * 40),
        ("ghu_" + "a" * 15, "Bearer ghu_" + "a" * 15),
    ],
)
def test_fetch_all_organization_repos_uses_expected_auth_header(token, expected_header):
    with patch.object(update_repos, "_detect_account_type", return_value="user"):
        with patch.object(update_repos.requests, "get") as mock_get:
            mock_get.return_value = _mock_response(json_data=[])

            update_repos.fetch_all_organization_repos("example-org", token)

            call_args = mock_get.call_args
            headers = call_args.kwargs.get("headers") or call_args[1].get("headers")
            assert headers["Authorization"] == expected_header


@pytest.mark.parametrize(
    "token,expected_header",
    [
        ("ghp_" + "a" * 40, "token ghp_" + "a" * 40),
        ("github_pat_" + "a" * 25, "Bearer github_pat_" + "a" * 25),
    ],
)
def test_has_recent_activity_uses_expected_auth_header(token, expected_header):
    repo = {"name": "example-repo"}

    with patch.object(update_repos.requests, "get") as mock_get:
        mock_get.return_value = _mock_response(json_data=[])

        update_repos.has_recent_activity(repo, "example-org", token=token, years=1)

        call_args = mock_get.call_args
        headers = call_args.kwargs.get("headers") or call_args[1].get("headers")
        assert headers["Authorization"] == expected_header
