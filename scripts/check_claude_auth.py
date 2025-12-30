#!/usr/bin/env python3
"""
Claude authentication status checker for RepoSwarm.

This script displays the current Claude authentication method (OAuth or API key),
token validation status, and which environment variables are configured.
"""

import os
import sys

# Add src to path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from investigator.core.auth_detector import (
    get_claude_authentication,
    validate_claude_credentials,
)

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class ClaudeAuthChecker:
    """Checks and displays Claude authentication status."""

    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None

    def _print_header(self):
        """Print script header."""
        if self.console:
            self.console.print(
                "\n[bold cyan]Claude Authentication Status[/bold cyan]\n"
            )
        else:
            print("\nClaude Authentication Status\n")

    def _sanitize_token(self, token: str, show_length: int = 8) -> str:
        """Sanitize token for display (show only prefix)."""
        if not token:
            return "Not set"
        if len(token) <= show_length:
            return "***"
        return f"{token[:show_length]}...***"

    def _check_env_vars(self) -> dict:
        """Check which environment variables are set."""
        env_vars = {
            "CLAUDE_CODE_OAUTH_TOKEN": os.getenv("CLAUDE_CODE_OAUTH_TOKEN", ""),
            "CLAUDE_OAUTH_TOKEN": os.getenv("CLAUDE_OAUTH_TOKEN", ""),
            "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", ""),
        }
        return env_vars

    def check(self):
        """Run authentication check and display results."""
        self._print_header()

        # Check environment variables
        env_vars = self._check_env_vars()

        # Try to detect authentication
        try:
            auth_result = get_claude_authentication()
            validation_result = validate_claude_credentials(auth_result)

            # Display results
            if self.console:
                self._display_rich_results(auth_result, validation_result, env_vars)
            else:
                self._display_plain_results(auth_result, validation_result, env_vars)

        except ValueError as e:
            # No credentials found
            if self.console:
                self.console.print(
                    Panel(
                        f"[red]❌ No Claude authentication credentials found[/red]\n\n"
                        f"[yellow]{str(e)}[/yellow]\n\n"
                        f"[bold]Setup Instructions:[/bold]\n"
                        f"1. For OAuth (Claude Max): Run [cyan]mise claude-login[/cyan]\n"
                        f"2. For API Key: Get key from https://console.anthropic.com/\n"
                        f"3. Add to .env.local:\n"
                        f"   - CLAUDE_CODE_OAUTH_TOKEN=your-token (for OAuth)\n"
                        f"   - ANTHROPIC_API_KEY=your-key (for API key)",
                        title="[bold red]Authentication Required[/bold red]",
                        border_style="red",
                    )
                )
            else:
                print("❌ No Claude authentication credentials found")
                print(f"\n{str(e)}")
                print("\nSetup Instructions:")
                print("1. For OAuth (Claude Max): Run 'mise claude-login'")
                print("2. For API Key: Get key from https://console.anthropic.com/")
                print("3. Add to .env.local:")
                print("   - CLAUDE_CODE_OAUTH_TOKEN=your-token (for OAuth)")
                print("   - ANTHROPIC_API_KEY=your-key (for API key)")

            sys.exit(1)

    def _display_rich_results(
        self, auth_result: dict, validation_result: dict, env_vars: dict
    ):
        """Display results using rich formatting."""
        # Create status table
        table = Table(
            title="Authentication Status", show_header=True, header_style="bold cyan"
        )
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        # Authentication method
        method_display = (
            "[bold green]OAuth[/bold green] (Claude Max)"
            if auth_result["method"] == "oauth"
            else "[bold blue]API Key[/bold blue]"
        )
        table.add_row("Authentication Method", method_display)

        # Token status
        if validation_result["valid"]:
            status_display = "[bold green]✅ Valid[/bold green]"
        else:
            status_display = (
                f"[bold red]❌ Invalid[/bold red]: {validation_result['message']}"
            )
        table.add_row("Token Status", status_display)

        # Token preview
        token_preview = self._sanitize_token(auth_result["token"])
        table.add_row("Token Preview", token_preview)

        # Client type
        client_type = (
            "Claude CLI (subprocess)" if auth_result["use_cli"] else "Anthropic SDK"
        )
        table.add_row("Client Type", client_type)

        self.console.print(table)

        # Environment variables table
        env_table = Table(
            title="Environment Variables", show_header=True, header_style="bold yellow"
        )
        env_table.add_column("Variable", style="yellow")
        env_table.add_column("Status", style="green")

        for var_name, var_value in env_vars.items():
            if var_value:
                status = f"[green]✅ Set[/green] ({self._sanitize_token(var_value)})"
            else:
                status = "[dim]Not set[/dim]"
            env_table.add_row(var_name, status)

        self.console.print("\n")
        self.console.print(env_table)

        # Priority information
        if env_vars["CLAUDE_CODE_OAUTH_TOKEN"]:
            priority_note = (
                "[dim]Note: CLAUDE_CODE_OAUTH_TOKEN has highest priority[/dim]"
            )
        elif env_vars["CLAUDE_OAUTH_TOKEN"]:
            priority_note = "[dim]Note: CLAUDE_OAUTH_TOKEN has second priority[/dim]"
        elif env_vars["ANTHROPIC_API_KEY"]:
            priority_note = "[dim]Note: ANTHROPIC_API_KEY is used as fallback[/dim]"

        if env_vars["CLAUDE_CODE_OAUTH_TOKEN"] or env_vars["CLAUDE_OAUTH_TOKEN"]:
            self.console.print(f"\n{priority_note}")

        # Success message
        if validation_result["valid"]:
            self.console.print(
                "\n[bold green]✅ Claude authentication is configured correctly![/bold green]"
            )
        else:
            self.console.print(
                "\n[bold red]❌ Authentication credentials are invalid. Please check your configuration.[/bold red]"
            )

    def _display_plain_results(
        self, auth_result: dict, validation_result: dict, env_vars: dict
    ):
        """Display results using plain text formatting."""
        print("\n=== Authentication Status ===")
        print(f"Authentication Method: {auth_result['method'].upper()}")
        if auth_result["method"] == "oauth":
            print("  Type: OAuth (Claude Max)")
        else:
            print("  Type: API Key")

        print(
            f"\nToken Status: {'✅ Valid' if validation_result['valid'] else '❌ Invalid'}"
        )
        if not validation_result["valid"]:
            print(f"  Error: {validation_result['message']}")

        print(f"\nToken Preview: {self._sanitize_token(auth_result['token'])}")
        print(
            f"Client Type: {'Claude CLI (subprocess)' if auth_result['use_cli'] else 'Anthropic SDK'}"
        )

        print("\n=== Environment Variables ===")
        for var_name, var_value in env_vars.items():
            status = (
                f"✅ Set ({self._sanitize_token(var_value)})"
                if var_value
                else "Not set"
            )
            print(f"{var_name}: {status}")

        # Priority information
        if env_vars["CLAUDE_CODE_OAUTH_TOKEN"]:
            print("\nNote: CLAUDE_CODE_OAUTH_TOKEN has highest priority")
        elif env_vars["CLAUDE_OAUTH_TOKEN"]:
            print("\nNote: CLAUDE_OAUTH_TOKEN has second priority")
        elif env_vars["ANTHROPIC_API_KEY"]:
            print("\nNote: ANTHROPIC_API_KEY is used as fallback")

        # Success message
        if validation_result["valid"]:
            print("\n✅ Claude authentication is configured correctly!")
        else:
            print(
                "\n❌ Authentication credentials are invalid. Please check your configuration."
            )


def main():
    """Main entry point."""
    checker = ClaudeAuthChecker()
    checker.check()


if __name__ == "__main__":
    main()
