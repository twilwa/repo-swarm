#!/usr/bin/env python3
"""
Manual test script for Claude authentication flows.

Tests all authentication scenarios with mock environment variables:
1. API key detection
2. OAuth token detection
3. Priority order (OAuth > API key)
4. Error messages when no credentials
5. Token validation (format, length, prefix)
"""

import os
import sys
from contextlib import contextmanager
from typing import Any, Dict, Optional

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
)

from investigator.core.auth_detector import (
    MAX_TOKEN_LENGTH,
    MIN_TOKEN_LENGTH,
    SK_ANT_API03_PREFIX,
    SK_ANT_OAT01_PREFIX,
    get_claude_authentication,
    validate_claude_credentials,
)


@contextmanager
def mock_env(**env_vars: Optional[str]):
    """Context manager to temporarily set environment variables."""
    original = {}
    to_delete = []

    env_keys = ["CLAUDE_CODE_OAUTH_TOKEN", "CLAUDE_OAUTH_TOKEN", "ANTHROPIC_API_KEY"]

    for key in env_keys:
        original[key] = os.environ.get(key)
        if key in env_vars:
            if env_vars[key] is None:
                if key in os.environ:
                    del os.environ[key]
                    to_delete.append(key)
            else:
                os.environ[key] = env_vars[key]
        elif key in os.environ:
            del os.environ[key]
            to_delete.append(key)

    try:
        yield
    finally:
        for key in env_keys:
            if original[key] is not None:
                os.environ[key] = original[key]
            elif key in os.environ:
                del os.environ[key]


class TestResult:
    """Stores test results."""

    def __init__(self, name: str, passed: bool, message: str):
        self.name = name
        self.passed = passed
        self.message = message


class AuthFlowTester:
    """Tests all authentication flow scenarios."""

    def __init__(self):
        self.results: list[TestResult] = []
        self.valid_oauth = SK_ANT_OAT01_PREFIX + "a" * 50
        self.valid_api_key = SK_ANT_API03_PREFIX + "b" * 50

    def _record(self, name: str, passed: bool, message: str = ""):
        self.results.append(TestResult(name, passed, message))
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")
        if message and not passed:
            print(f"         {message}")

    def test_api_key_detection(self):
        """Test API key detection when only ANTHROPIC_API_KEY is set."""
        print("\n📋 Testing API Key Detection...")

        with mock_env(ANTHROPIC_API_KEY=self.valid_api_key):
            try:
                result = get_claude_authentication()
                self._record(
                    "API key detected",
                    result["method"] == "api_key",
                    f"Expected 'api_key', got '{result['method']}'",
                )
                self._record(
                    "Token matches",
                    result["token"] == self.valid_api_key,
                    "Token mismatch",
                )
                self._record(
                    "use_cli=False for API key",
                    result["use_cli"] == False,
                    f"Expected False, got {result['use_cli']}",
                )
            except Exception as e:
                self._record("API key detection", False, str(e))

    def test_oauth_detection(self):
        """Test OAuth token detection."""
        print("\n📋 Testing OAuth Token Detection...")

        # Test CLAUDE_CODE_OAUTH_TOKEN
        with mock_env(CLAUDE_CODE_OAUTH_TOKEN=self.valid_oauth):
            try:
                result = get_claude_authentication()
                self._record(
                    "CLAUDE_CODE_OAUTH_TOKEN detected",
                    result["method"] == "oauth",
                    f"Expected 'oauth', got '{result['method']}'",
                )
                self._record(
                    "use_cli=True for OAuth",
                    result["use_cli"] == True,
                    f"Expected True, got {result['use_cli']}",
                )
            except Exception as e:
                self._record("CLAUDE_CODE_OAUTH_TOKEN detection", False, str(e))

        # Test CLAUDE_OAUTH_TOKEN
        with mock_env(CLAUDE_OAUTH_TOKEN=self.valid_oauth):
            try:
                result = get_claude_authentication()
                self._record(
                    "CLAUDE_OAUTH_TOKEN detected",
                    result["method"] == "oauth",
                    f"Expected 'oauth', got '{result['method']}'",
                )
            except Exception as e:
                self._record("CLAUDE_OAUTH_TOKEN detection", False, str(e))

    def test_priority_order(self):
        """Test that OAuth has priority over API key."""
        print("\n📋 Testing Priority Order (OAuth > API Key)...")

        # CLAUDE_CODE_OAUTH_TOKEN > ANTHROPIC_API_KEY
        with mock_env(
            CLAUDE_CODE_OAUTH_TOKEN=self.valid_oauth,
            ANTHROPIC_API_KEY=self.valid_api_key,
        ):
            try:
                result = get_claude_authentication()
                self._record(
                    "CLAUDE_CODE_OAUTH_TOKEN has priority over ANTHROPIC_API_KEY",
                    result["method"] == "oauth" and result["token"] == self.valid_oauth,
                    f"Expected OAuth, got {result['method']}",
                )
            except Exception as e:
                self._record("Priority check (CODE_OAUTH > API)", False, str(e))

        # CLAUDE_CODE_OAUTH_TOKEN > CLAUDE_OAUTH_TOKEN
        other_oauth = SK_ANT_OAT01_PREFIX + "c" * 50
        with mock_env(
            CLAUDE_CODE_OAUTH_TOKEN=self.valid_oauth, CLAUDE_OAUTH_TOKEN=other_oauth
        ):
            try:
                result = get_claude_authentication()
                self._record(
                    "CLAUDE_CODE_OAUTH_TOKEN has priority over CLAUDE_OAUTH_TOKEN",
                    result["token"] == self.valid_oauth,
                    "Wrong token selected",
                )
            except Exception as e:
                self._record("Priority check (CODE > OAUTH)", False, str(e))

        # CLAUDE_OAUTH_TOKEN > ANTHROPIC_API_KEY
        with mock_env(
            CLAUDE_OAUTH_TOKEN=self.valid_oauth, ANTHROPIC_API_KEY=self.valid_api_key
        ):
            try:
                result = get_claude_authentication()
                self._record(
                    "CLAUDE_OAUTH_TOKEN has priority over ANTHROPIC_API_KEY",
                    result["method"] == "oauth",
                    f"Expected OAuth, got {result['method']}",
                )
            except Exception as e:
                self._record("Priority check (OAUTH > API)", False, str(e))

    def test_no_credentials_error(self):
        """Test error message when no credentials are set."""
        print("\n📋 Testing Missing Credentials Error...")

        with mock_env():
            try:
                get_claude_authentication()
                self._record(
                    "No credentials raises ValueError", False, "No exception raised"
                )
            except ValueError as e:
                error_msg = str(e)
                self._record("ValueError raised with no credentials", True, "")
                self._record(
                    "Error mentions CLAUDE_CODE_OAUTH_TOKEN",
                    "CLAUDE_CODE_OAUTH_TOKEN" in error_msg,
                    "Missing env var in error message",
                )
                self._record(
                    "Error mentions ANTHROPIC_API_KEY",
                    "ANTHROPIC_API_KEY" in error_msg,
                    "Missing env var in error message",
                )
            except Exception as e:
                self._record(
                    "No credentials error", False, f"Wrong exception: {type(e)}"
                )

    def test_token_validation_valid(self):
        """Test validation of correctly formatted tokens."""
        print("\n📋 Testing Token Validation (Valid Tokens)...")

        # Valid OAuth token
        result = validate_claude_credentials(
            {"method": "oauth", "token": self.valid_oauth}
        )
        self._record(
            "Valid OAuth token passes validation",
            result["valid"] == True,
            result.get("message", ""),
        )

        # Valid API key
        result = validate_claude_credentials(
            {"method": "api_key", "token": self.valid_api_key}
        )
        self._record(
            "Valid API key passes validation",
            result["valid"] == True,
            result.get("message", ""),
        )

    def test_token_validation_invalid_prefix(self):
        """Test validation rejects wrong prefixes."""
        print("\n📋 Testing Token Validation (Invalid Prefix)...")

        # OAuth with API key prefix
        result = validate_claude_credentials(
            {"method": "oauth", "token": self.valid_api_key}
        )
        self._record(
            "OAuth with API key prefix fails",
            result["valid"] == False,
            result.get("message", ""),
        )
        self._record(
            "Error mentions 'claude setup-token'",
            "setup-token" in result.get("message", "").lower(),
            f"Message: {result.get('message', '')}",
        )

        # API key with OAuth prefix
        result = validate_claude_credentials(
            {"method": "api_key", "token": self.valid_oauth}
        )
        self._record(
            "API key with OAuth prefix fails",
            result["valid"] == False,
            result.get("message", ""),
        )
        self._record(
            "Error mentions console.anthropic.com",
            "console.anthropic.com" in result.get("message", ""),
            f"Message: {result.get('message', '')}",
        )

    def test_token_validation_length(self):
        """Test validation checks token length."""
        print("\n📋 Testing Token Validation (Length)...")

        # Too short
        short_token = SK_ANT_OAT01_PREFIX + "a" * 10
        result = validate_claude_credentials({"method": "oauth", "token": short_token})
        self._record(
            f"Token < {MIN_TOKEN_LENGTH} chars fails",
            result["valid"] == False and "length" in result.get("message", "").lower(),
            result.get("message", ""),
        )

        # Too long
        long_token = SK_ANT_OAT01_PREFIX + "a" * 250
        result = validate_claude_credentials({"method": "oauth", "token": long_token})
        self._record(
            f"Token > {MAX_TOKEN_LENGTH} chars fails",
            result["valid"] == False and "length" in result.get("message", "").lower(),
            result.get("message", ""),
        )

    def test_token_validation_edge_cases(self):
        """Test validation handles edge cases."""
        print("\n📋 Testing Token Validation (Edge Cases)...")

        # Empty token
        result = validate_claude_credentials({"method": "oauth", "token": ""})
        self._record(
            "Empty token fails validation",
            result["valid"] == False,
            result.get("message", ""),
        )

        # None token
        result = validate_claude_credentials({"method": "oauth", "token": None})
        self._record(
            "None token fails validation",
            result["valid"] == False,
            result.get("message", ""),
        )

        # Missing method
        result = validate_claude_credentials({"token": self.valid_oauth})
        self._record(
            "Missing method fails validation",
            result["valid"] == False,
            result.get("message", ""),
        )

        # Missing token
        result = validate_claude_credentials({"method": "oauth"})
        self._record(
            "Missing token field fails validation",
            result["valid"] == False,
            result.get("message", ""),
        )

    def run_all_tests(self):
        """Run all test scenarios."""
        print("=" * 60)
        print("🧪 Claude Authentication Flow Tests")
        print("=" * 60)

        self.test_api_key_detection()
        self.test_oauth_detection()
        self.test_priority_order()
        self.test_no_credentials_error()
        self.test_token_validation_valid()
        self.test_token_validation_invalid_prefix()
        self.test_token_validation_length()
        self.test_token_validation_edge_cases()

        self.print_summary()

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)

        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)

        print(f"\nTotal: {total} | Passed: {passed} | Failed: {failed}")

        if failed > 0:
            print("\n❌ Failed Tests:")
            for r in self.results:
                if not r.passed:
                    print(f"  - {r.name}")
                    if r.message:
                        print(f"    {r.message}")
            print()
            return 1
        else:
            print("\n✅ All tests passed!")
            return 0


def main():
    """Main entry point."""
    tester = AuthFlowTester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
