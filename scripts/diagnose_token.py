#!/usr/bin/env python3
# ABOUTME: CLI tool for diagnosing GitHub token issues
# ABOUTME: Provides detailed troubleshooting information and actionable recommendations

"""
GitHub Token Diagnostic CLI

Usage:
    python scripts/diagnose_token.py                    # Diagnose token from environment
    python scripts/diagnose_token.py owner/repo         # Include repository access check
    python scripts/diagnose_token.py --token ghp_xxx    # Diagnose specific token
"""

import argparse
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from investigator.core.github_diagnostics import (
    DiagnosticStatus,
    diagnose_github_token,
)


def print_result(result, verbose=False):
    """Print diagnostic result in a user-friendly format."""

    # Status icon and message
    status_icons = {"success": "✅", "warning": "⚠️", "error": "❌"}

    icon = status_icons.get(result.status.value, "?")
    print(f"\n{icon} {result.message}\n")

    # Show issue type if present
    if result.issue_type:
        issue_name = result.issue_type.value.replace("_", " ").title()
        print(f"Issue Type: {issue_name}\n")

    # Show recommendations
    if result.recommendations:
        print("Recommendations:")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"  {i}. {rec}")
        print()

    # Show details if verbose
    if verbose and result.details:
        print("Details:")
        for key, value in result.details.items():
            print(f"  {key}: {value}")
        print()

    # Show troubleshooting link
    if result.troubleshooting_url:
        print(f"For more help, see: {result.troubleshooting_url}\n")

    # Return exit code based on status
    return 0 if result.status == DiagnosticStatus.SUCCESS else 1


def main():
    parser = argparse.ArgumentParser(
        description="Diagnose GitHub token authentication and permission issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Diagnose token from GITHUB_TOKEN environment variable
  python scripts/diagnose_token.py
  
  # Check access to specific repository
  python scripts/diagnose_token.py owner/repo
  
  # Diagnose a specific token
  python scripts/diagnose_token.py --token ghp_your_token_here
  
  # Verbose output with all details
  python scripts/diagnose_token.py --verbose
        """,
    )

    parser.add_argument(
        "repository", nargs="?", help="Repository to check access (format: owner/repo)"
    )

    parser.add_argument(
        "--token", help="GitHub token to diagnose (default: GITHUB_TOKEN env var)"
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show detailed information"
    )

    args = parser.parse_args()

    # Get token
    token = args.token or os.getenv("GITHUB_TOKEN")

    if not token:
        print("❌ Error: No GitHub token provided")
        print("\nPlease either:")
        print("  1. Set GITHUB_TOKEN environment variable")
        print("  2. Use --token flag to specify token")
        print("\nExample:")
        print("  export GITHUB_TOKEN=ghp_your_token_here")
        print("  python scripts/diagnose_token.py")
        return 1

    # Run diagnostics
    print("🔍 Diagnosing GitHub token...")
    if args.repository:
        print(f"📦 Checking access to repository: {args.repository}")

    result = diagnose_github_token(token, args.repository)

    return print_result(result, args.verbose)


if __name__ == "__main__":
    sys.exit(main())
