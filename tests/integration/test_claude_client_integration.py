"""
Integration tests for Claude client factory integration into ClaudeAnalyzer and ClaudeInvestigator.
Tests verify that both OAuth and API key authentication work end-to-end.
"""

import os
from unittest.mock import patch

import pytest

from src.investigator.core.claude_analyzer import ClaudeAnalyzer
from src.investigator.investigator import ClaudeInvestigator


class TestClaudeAnalyzerIntegration:
    """Test ClaudeAnalyzer uses factory correctly."""

    def test_analyzer_uses_factory_with_api_key(self, tmp_path):
        """Test ClaudeAnalyzer works with API key authentication via factory."""
        # Setup: Set API key in environment
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set - skipping integration test")

        # Clear OAuth tokens to ensure API key is used
        with patch.dict(
            os.environ,
            {
                "CLAUDE_CODE_OAUTH_TOKEN": "",
                "CLAUDE_OAUTH_TOKEN": "",
                "ANTHROPIC_API_KEY": api_key,
            },
            clear=False,
        ):
            import logging

            logger = logging.getLogger(__name__)

            # Should initialize without direct api_key parameter
            analyzer = ClaudeAnalyzer(logger=logger)

            # Test actual analysis with simple prompt
            result = analyzer.analyze_with_context(
                prompt_template="Explain what 'hello world' means in one sentence.",
                repo_structure="",
                previous_context=None,
                config_overrides={"max_tokens": 100},
            )

            assert result is not None
            assert len(result) > 0
            assert "hello" in result.lower() or "world" in result.lower()

    def test_analyzer_uses_factory_with_oauth(self, tmp_path):
        """Test ClaudeAnalyzer works with OAuth authentication via factory."""
        # Setup: Check for OAuth token
        oauth_token = os.getenv("CLAUDE_CODE_OAUTH_TOKEN") or os.getenv(
            "CLAUDE_OAUTH_TOKEN"
        )
        if not oauth_token:
            pytest.skip("No OAuth token set - skipping OAuth integration test")

        # Set OAuth token and clear API key to force OAuth path
        with patch.dict(
            os.environ,
            {
                "CLAUDE_CODE_OAUTH_TOKEN": oauth_token,
                "ANTHROPIC_API_KEY": "",  # Clear API key
            },
            clear=False,
        ):
            import logging

            logger = logging.getLogger(__name__)

            # Should initialize without direct api_key parameter
            analyzer = ClaudeAnalyzer(logger=logger)

            # Test actual analysis with simple prompt
            result = analyzer.analyze_with_context(
                prompt_template="Explain what 'hello world' means in one sentence.",
                repo_structure="",
                previous_context=None,
                config_overrides={"max_tokens": 100},
            )

            assert result is not None
            assert len(result) > 0


class TestClaudeInvestigatorIntegration:
    """Test ClaudeInvestigator initialization without api_key parameter."""

    def test_investigator_initializes_with_api_key_in_env(self):
        """Test ClaudeInvestigator initializes when ANTHROPIC_API_KEY is in environment."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set - skipping integration test")

        # Clear OAuth to ensure API key path
        with patch.dict(
            os.environ,
            {
                "CLAUDE_CODE_OAUTH_TOKEN": "",
                "CLAUDE_OAUTH_TOKEN": "",
                "ANTHROPIC_API_KEY": api_key,
            },
            clear=False,
        ):
            # Should initialize without api_key parameter
            investigator = ClaudeInvestigator(log_level="INFO")

            assert investigator is not None
            assert investigator.claude_analyzer is not None

    def test_investigator_initializes_with_oauth_in_env(self):
        """Test ClaudeInvestigator initializes when OAuth token is in environment."""
        oauth_token = os.getenv("CLAUDE_CODE_OAUTH_TOKEN") or os.getenv(
            "CLAUDE_OAUTH_TOKEN"
        )
        if not oauth_token:
            pytest.skip("No OAuth token set - skipping OAuth integration test")

        # Set OAuth and clear API key to force OAuth path
        with patch.dict(
            os.environ,
            {
                "CLAUDE_CODE_OAUTH_TOKEN": oauth_token,
                "ANTHROPIC_API_KEY": "",  # Clear API key
            },
            clear=False,
        ):
            # Should initialize without api_key parameter
            investigator = ClaudeInvestigator(log_level="INFO")

            assert investigator is not None
            assert investigator.claude_analyzer is not None

    def test_investigator_fails_without_credentials(self):
        """Test ClaudeInvestigator raises error when no credentials available."""
        # Clear both OAuth and API key
        with patch.dict(
            os.environ,
            {
                "CLAUDE_CODE_OAUTH_TOKEN": "",
                "CLAUDE_OAUTH_TOKEN": "",
                "ANTHROPIC_API_KEY": "",
            },
            clear=False,
        ):
            with pytest.raises(
                ValueError, match="Claude.*required|authentication.*required"
            ):
                ClaudeInvestigator(log_level="INFO")


class TestWorkerValidationIntegration:
    """Test worker validation accepts either OAuth or API key."""

    def test_worker_validation_passes_with_api_key(self):
        """Test worker validation passes when ANTHROPIC_API_KEY is set."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set - skipping test")

        from src.worker import validate_environment

        with patch.dict(
            os.environ,
            {
                "CLAUDE_CODE_OAUTH_TOKEN": "",
                "CLAUDE_OAUTH_TOKEN": "",
                "ANTHROPIC_API_KEY": api_key,
                "GITHUB_TOKEN": "dummy",
                "AWS_ACCESS_KEY_ID": "dummy",
                "AWS_SECRET_ACCESS_KEY": "dummy",
            },
            clear=False,
        ):
            errors, warnings = validate_environment()

            # Should not have authentication errors
            auth_errors = [
                e
                for e in errors
                if "ANTHROPIC_API_KEY" in e
                or "OAuth" in e
                or "authentication" in e.lower()
            ]
            assert (
                len(auth_errors) == 0
            ), f"Should accept API key auth, but got: {auth_errors}"

    def test_worker_validation_passes_with_oauth(self):
        """Test worker validation passes when OAuth token is set."""
        oauth_token = os.getenv("CLAUDE_CODE_OAUTH_TOKEN") or os.getenv(
            "CLAUDE_OAUTH_TOKEN"
        )
        if not oauth_token:
            pytest.skip("No OAuth token set - skipping OAuth test")

        from src.worker import validate_environment

        with patch.dict(
            os.environ,
            {
                "CLAUDE_CODE_OAUTH_TOKEN": oauth_token,
                "ANTHROPIC_API_KEY": "",  # Clear API key
                "GITHUB_TOKEN": "dummy",
                "AWS_ACCESS_KEY_ID": "dummy",
                "AWS_SECRET_ACCESS_KEY": "dummy",
            },
            clear=False,
        ):
            errors, warnings = validate_environment()

            # Should not have authentication errors
            auth_errors = [
                e
                for e in errors
                if "ANTHROPIC_API_KEY" in e
                or "OAuth" in e
                or "authentication" in e.lower()
            ]
            assert (
                len(auth_errors) == 0
            ), f"Should accept OAuth auth, but got: {auth_errors}"

    def test_worker_validation_fails_without_credentials(self):
        """Test worker validation fails when neither OAuth nor API key is set."""
        from src.worker import validate_environment

        with patch.dict(
            os.environ,
            {
                "CLAUDE_CODE_OAUTH_TOKEN": "",
                "CLAUDE_OAUTH_TOKEN": "",
                "ANTHROPIC_API_KEY": "",
                "GITHUB_TOKEN": "dummy",
                "AWS_ACCESS_KEY_ID": "dummy",
                "AWS_SECRET_ACCESS_KEY": "dummy",
            },
            clear=False,
        ):
            errors, warnings = validate_environment()

            # Should have authentication error
            auth_errors = [
                e
                for e in errors
                if "ANTHROPIC_API_KEY" in e
                or "OAuth" in e
                or "Claude" in e
                or "authentication" in e.lower()
            ]
            assert len(auth_errors) > 0, "Should require either OAuth or API key"
