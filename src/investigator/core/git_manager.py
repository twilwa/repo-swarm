"""
Git repository management for the Claude Investigator.
"""

import os
import shutil
import subprocess
from urllib.parse import urlparse, urlunparse

from .utils import Utils


class GitRepositoryManager:
    """Handles Git repository operations."""

    def __init__(self, logger):
        self.logger = logger
        self.github_token = os.getenv("GITHUB_TOKEN")
        if self.github_token:
            self.logger.debug("GitHub token found in environment")

    def _sanitize_url_for_logging(self, url: str) -> str:
        """
        Remove sensitive information from URLs for safe logging.

        Args:
            url: URL that may contain authentication tokens or passwords

        Returns:
            Sanitized URL safe for logging
        """
        # If it's not a URL, return as is
        if not url or not url.startswith(("http://", "https://")):
            return url

        parsed = urlparse(url)

        # Remove authentication info from the URL
        if parsed.username or parsed.password:
            # Reconstruct URL without auth
            sanitized_netloc = parsed.hostname or ""
            if parsed.port:
                sanitized_netloc += f":{parsed.port}"

            sanitized_url = urlunparse(
                (
                    parsed.scheme,
                    sanitized_netloc,
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment,
                )
            )

            # Add indication that auth was present
            return f"{sanitized_url} (authentication hidden)"

        # Check if token is embedded in the URL string (e.g., after @)
        if self.github_token and self.github_token in url:
            return url.replace(self.github_token, "***HIDDEN***")

        return url

    def clone_or_update(self, repo_location: str, target_dir: str) -> str:
        """
        Clone a repository or update it if it already exists.

        Args:
            repo_location: URL or path to the repository
            target_dir: Directory to clone/update the repository

        Returns:
            Path to the repository
        """
        # Add authentication to the URL if needed
        auth_repo_location = self._add_authentication(repo_location)

        if self._is_existing_repo(target_dir):
            return self._update_repository(target_dir, auth_repo_location)
        else:
            return self._clone_repository(auth_repo_location, target_dir)

    def _add_authentication(self, repo_location: str) -> str:
        """
        Add GitHub token authentication to repository URL if available.

        Args:
            repo_location: Original repository URL

        Returns:
            Repository URL with authentication added if applicable
        """
        # Only process URLs, not local paths
        if not repo_location.startswith(("http://", "https://")):
            return repo_location

        # Only add token for GitHub repositories
        if "github.com" not in repo_location:
            return repo_location

        # If no token available, return original URL
        if not self.github_token:
            return repo_location

        # Parse the URL
        parsed = urlparse(repo_location)

        # If authentication already exists, don't override
        if parsed.username:
            self.logger.debug("Authentication already present in URL, not overriding")
            return repo_location

        # Add token authentication
        # GitHub accepts the token as username with no password
        auth_netloc = f"{self.github_token}@{parsed.hostname}"
        if parsed.port:
            auth_netloc += f":{parsed.port}"

        # Reconstruct the URL with authentication
        auth_url = urlunparse(
            (
                parsed.scheme,
                auth_netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment,
            )
        )

        self.logger.debug("Added GitHub token authentication to repository URL")
        return auth_url

    def _get_token_type(self):
        """Return detected GitHub token type for diagnostics."""
        from .github_token_utils import GitHubTokenType, detect_github_token_type

        if not self.github_token:
            return GitHubTokenType.UNKNOWN

        try:
            return detect_github_token_type(self.github_token)
        except TypeError:
            return GitHubTokenType.UNKNOWN

    def _token_type_label(self, token_type) -> str:
        """Return human-readable token type label."""
        return token_type.value if hasattr(token_type, "value") else str(token_type)

    def _is_permission_error(self, error_msg: str) -> bool:
        """Detect permission/authentication errors in git output."""
        if not error_msg:
            return False

        error_lower = error_msg.lower()
        indicators = [
            "authentication failed",
            "repository not found",
            "permission denied",
            "permission to",  # Matches "Permission to org/repo denied"
            "access denied",
            "not authorized",
            "forbidden",
            "403",
        ]
        return any(indicator in error_lower for indicator in indicators)

    def _build_permission_error_message(
        self, operation: str, token_type, permission_hint: str | None = None
    ) -> str:
        """Build a permission error message that includes token type context."""
        from .github_token_utils import GitHubTokenType

        token_label = self._token_type_label(token_type)
        if token_type in (
            GitHubTokenType.FINE_GRAINED_USER,
            GitHubTokenType.FINE_GRAINED_PAT,
        ):
            message = f"{operation}: Fine-grained token ({token_label}) lacks repository access permissions."
            if permission_hint:
                message = f"{message} {permission_hint}"
            return message

        if token_type == GitHubTokenType.CLASSIC:
            return (
                f"{operation}: CLASSIC token authentication failed. "
                "Please check your GITHUB_TOKEN."
            )

        return f"{operation}: Authentication failed. Please check your GITHUB_TOKEN."

    def _is_existing_repo(self, repo_dir: str) -> bool:
        """Check if a directory contains a valid Git repository."""
        return os.path.exists(repo_dir) and os.path.exists(
            os.path.join(repo_dir, ".git")
        )

    def _update_repository(self, repo_dir: str, auth_repo_location: str) -> str:
        """Update an existing repository with latest changes."""
        self.logger.info(f"Repository already exists at: {repo_dir}")
        try:
            import git

            repo = git.Repo(repo_dir)
            self.logger.info("Pulling latest changes from remote repository")

            origin = repo.remotes.origin

            # Update remote URL with authentication if needed
            if self.github_token and "github.com" in auth_repo_location:
                current_url = origin.url
                if "github.com" in current_url and "@" not in current_url:
                    self.logger.debug("Updating remote URL with authentication")
                    origin.set_url(auth_repo_location)

            origin.fetch()
            origin.pull()

            self.logger.info(f"Repository successfully updated at: {repo_dir}")
            return repo_dir

        except Exception as e:
            # Import git to check for GitCommandError
            import git

            if isinstance(e, git.exc.GitCommandError):
                self.logger.warning(f"Failed to pull latest changes: {str(e)}")
                self.logger.info("Falling back to cloning the repository")
                shutil.rmtree(repo_dir)
                raise
            else:
                raise

    def _clone_repository(self, repo_location: str, target_dir: str) -> str:
        """Clone a new repository."""
        self._ensure_clean_directory(target_dir)

        try:
            import git

            # Log sanitized URL without exposing sensitive information
            safe_url = self._sanitize_url_for_logging(repo_location)
            self.logger.info(f"Cloning repository from: {safe_url}")

            if self.github_token and self.github_token in repo_location:
                self.logger.info(
                    "Using GitHub token authentication for private repository access"
                )

            git.Repo.clone_from(repo_location, target_dir)
            self.logger.info(f"Repository successfully cloned to: {target_dir}")
            return target_dir

        except Exception as e:
            import git

            if isinstance(e, git.exc.GitCommandError):
                self.logger.error(f"Git clone failed: {str(e)}")

                # Check if it's a resource issue (exit code -9 or similar)
                if "exit code(-9)" in str(e) or "Killed" in str(e):
                    self.logger.warning(
                        "Detected potential resource issue, attempting shallow clone"
                    )
                    # Clean up failed attempt
                    if os.path.exists(target_dir):
                        shutil.rmtree(target_dir, ignore_errors=True)

                    # Try shallow clone as fallback
                    try:
                        return self._shallow_clone_fallback(repo_location, target_dir)
                    except Exception as shallow_error:
                        self.logger.error(
                            f"Shallow clone also failed: {str(shallow_error)}"
                        )
                        raise Exception(
                            f"Failed to clone repository even with shallow clone: {str(shallow_error)}"
                        )

                error_msg = str(e)
                if self._is_permission_error(error_msg):
                    token_type = self._get_token_type()
                    raise Exception(
                        self._build_permission_error_message(
                            "Failed to clone repository",
                            token_type,
                            "Ensure the token includes this repository and has Contents (read) permission.",
                        )
                    )

                # Sanitize error message to remove any tokens
                if self.github_token and self.github_token in error_msg:
                    error_msg = error_msg.replace(self.github_token, "***HIDDEN***")
                raise Exception(f"Failed to clone repository: {error_msg}")
            else:
                raise

    def _shallow_clone_fallback(self, repo_location: str, target_dir: str) -> str:
        """
        Perform a shallow clone as a fallback when normal clone fails due to resource constraints.

        Args:
            repo_location: Repository URL to clone (with authentication if needed)
            target_dir: Target directory for the clone

        Returns:
            Path to the cloned repository
        """
        import subprocess

        self.logger.info("Attempting shallow clone with depth=1 to reduce memory usage")

        # Ensure target directory is clean
        self._ensure_clean_directory(target_dir)

        # Build git clone command with shallow options
        cmd = [
            "git",
            "clone",
            "--depth",
            "1",
            "--single-branch",  # Only clone the default branch
            "--no-tags",  # Don't fetch tags to save space
            repo_location,
            target_dir,
        ]

        # Mask the token in command for logging
        log_cmd = " ".join(cmd)
        if self.github_token and self.github_token in log_cmd:
            log_cmd = log_cmd.replace(self.github_token, "***HIDDEN***")
        # Also sanitize the URL in the command
        safe_url = self._sanitize_url_for_logging(repo_location)
        if repo_location in log_cmd:
            log_cmd = log_cmd.replace(repo_location, safe_url)
        self.logger.debug(f"Shallow clone command: {log_cmd}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
                check=True,
            )

            self.logger.info(f"Repository successfully shallow cloned to: {target_dir}")
            return target_dir

        except subprocess.CalledProcessError as e:
            # Check if it's still a resource issue
            if e.returncode == -9 or "Killed" in e.stderr:
                self.logger.error(
                    "Even shallow clone was killed - severe resource constraints"
                )
                # Try one more time with minimal clone
                return self._minimal_clone_fallback(repo_location, target_dir)

            # Clean up error message to not expose token
            error_msg = e.stderr
            if self._is_permission_error(error_msg):
                token_type = self._get_token_type()
                raise Exception(
                    self._build_permission_error_message(
                        "Shallow clone failed",
                        token_type,
                        "Ensure the token includes this repository and has Contents (read) permission.",
                    )
                )
            if self.github_token and self.github_token in error_msg:
                error_msg = error_msg.replace(self.github_token, "***HIDDEN***")

            raise Exception(f"Shallow clone failed: {error_msg}")
        except subprocess.TimeoutExpired:
            raise Exception("Shallow clone timed out after 10 minutes")

    def _minimal_clone_fallback(self, repo_location: str, target_dir: str) -> str:
        """
        Perform a minimal clone with the most aggressive optimizations for extremely constrained environments.

        Args:
            repo_location: Repository URL to clone (with authentication if needed)
            target_dir: Target directory for the clone

        Returns:
            Path to the cloned repository
        """
        import subprocess

        self.logger.info("Attempting minimal clone with aggressive optimizations")

        # Ensure target directory exists
        os.makedirs(target_dir, exist_ok=True)

        try:
            # Initialize repository
            subprocess.run(["git", "init"], cwd=target_dir, check=True)

            # Add remote (don't log the URL with potential token)
            safe_url = self._sanitize_url_for_logging(repo_location)
            self.logger.debug(f"Adding remote origin: {safe_url}")
            subprocess.run(
                ["git", "remote", "add", "origin", repo_location],
                cwd=target_dir,
                check=True,
            )

            # Configure git to minimize memory usage
            subprocess.run(
                ["git", "config", "core.compression", "0"], cwd=target_dir, check=True
            )
            subprocess.run(
                ["git", "config", "http.postBuffer", "524288000"],
                cwd=target_dir,
                check=True,
            )
            subprocess.run(
                ["git", "config", "pack.windowMemory", "10m"],
                cwd=target_dir,
                check=True,
            )
            subprocess.run(
                ["git", "config", "pack.packSizeLimit", "100m"],
                cwd=target_dir,
                check=True,
            )
            subprocess.run(
                ["git", "config", "core.packedGitLimit", "128m"],
                cwd=target_dir,
                check=True,
            )
            subprocess.run(
                ["git", "config", "core.packedGitWindowSize", "128m"],
                cwd=target_dir,
                check=True,
            )

            # Fetch with minimal data - using blob:none for lazy loading
            fetch_cmd = [
                "git",
                "fetch",
                "--depth=1",
                "--no-tags",
                "--filter=blob:none",  # Lazy fetch blobs only when needed
                "origin",
                "HEAD",
            ]

            result = subprocess.run(
                fetch_cmd,
                cwd=target_dir,
                capture_output=True,
                text=True,
                timeout=600,
                check=True,
            )

            # Checkout the fetched branch
            subprocess.run(
                ["git", "checkout", "FETCH_HEAD"], cwd=target_dir, check=True
            )

            self.logger.info(
                f"Repository successfully cloned with minimal strategy to: {target_dir}"
            )
            return target_dir

        except subprocess.CalledProcessError as e:
            # Clean up error message to not expose token
            error_msg = str(e)
            if self._is_permission_error(error_msg):
                token_type = self._get_token_type()
                raise Exception(
                    self._build_permission_error_message(
                        "Minimal clone failed",
                        token_type,
                        "Ensure the token includes this repository and has Contents (read) permission.",
                    )
                )
            if self.github_token and self.github_token in error_msg:
                error_msg = error_msg.replace(self.github_token, "***HIDDEN***")

            raise Exception(f"Minimal clone failed: {error_msg}")
        except subprocess.TimeoutExpired:
            raise Exception("Minimal clone timed out after 10 minutes")

    def push_with_authentication(self, repo_dir: str, branch: str = "main") -> dict:
        """
        Push changes to remote repository with proper authentication.

        Args:
            repo_dir: Directory containing the git repository
            branch: Branch to push to (default: main)

        Returns:
            Dictionary with push result status and message
        """
        try:
            # Ensure remote URL has authentication for push
            if self.github_token:
                # Get current remote URL
                result = subprocess.run(
                    ["git", "remote", "get-url", "origin"],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    current_url = result.stdout.strip()

                    # Log current remote URL (sanitized)
                    safe_url = self._sanitize_url_for_logging(current_url)
                    self.logger.info(f"Current remote URL: {safe_url}")

                    # Add authentication if not already present
                    auth_url = self._add_authentication(current_url)
                    if auth_url != current_url:
                        self.logger.info(
                            "Updating remote URL with GitHub token for push"
                        )
                        subprocess.run(
                            ["git", "remote", "set-url", "origin", auth_url],
                            cwd=repo_dir,
                            check=True,
                        )
                    else:
                        self.logger.info(
                            "Remote URL already has authentication or is not a GitHub HTTPS URL"
                        )
            else:
                self.logger.warning(
                    "No GitHub token available - push may fail for private repositories"
                )

            # Perform the push
            push_result = subprocess.run(
                ["git", "push", "origin", branch],
                cwd=repo_dir,
                capture_output=True,
                text=True,
            )

            if push_result.returncode != 0:
                # Sanitize error message to avoid exposing tokens
                error_msg = push_result.stderr
                if self._is_permission_error(error_msg):
                    token_type = self._get_token_type()
                    return {
                        "status": "failed",
                        "message": self._build_permission_error_message(
                            "Failed to push changes",
                            token_type,
                            "Ensure the token includes this repository and has Contents (write) permission.",
                        ),
                        "stderr": error_msg,
                    }
                if self.github_token and self.github_token in error_msg:
                    error_msg = error_msg.replace(self.github_token, "***HIDDEN***")

                return {
                    "status": "failed",
                    "message": f"Failed to push changes: {error_msg}",
                    "stderr": error_msg,
                }

            self.logger.info(f"Successfully pushed changes to {branch}")
            return {
                "status": "success",
                "message": f"Successfully pushed changes to {branch}",
                "stdout": push_result.stdout,
            }

        except Exception as e:
            error_msg = str(e)
            if self.github_token and self.github_token in error_msg:
                error_msg = error_msg.replace(self.github_token, "***HIDDEN***")

            return {
                "status": "failed",
                "message": f"Push operation failed: {error_msg}",
                "error": error_msg,
            }

    def validate_github_token(self) -> dict:
        """
        Validate the GitHub token format and authenticity.

        Uses a hybrid approach:
        1. Format validation (fast): Check token format using github_token_utils
        2. API validation (real-time): Verify token works with GitHub API

        Returns:
            Dictionary with validation status, token type, and user info
            {
                'status': 'no_token' | 'valid' | 'invalid' | 'error',
                'message': str,
                'token_type': GitHubTokenType (added in this version),
                'format_valid': bool (added in this version),
                'user': str (if valid),
                'user_info': dict (if valid),
                'status_code': int (if API error),
                'error': str (if exception)
            }
        """
        # Step 1: Format validation using new utility (import first)
        from .github_token_utils import GitHubTokenType
        from .github_token_utils import validate_github_token as util_validate_token

        # Check if token is present in environment
        if self.github_token is None:
            return {
                "status": "no_token",
                "message": "No GitHub token found in environment",
            }

        # Empty string token is treated as invalid format
        if not self.github_token or not self.github_token.strip():
            return {
                "status": "invalid",
                "message": "Token cannot be empty or contain only whitespace",
                "token_type": GitHubTokenType.UNKNOWN,
                "format_valid": False,
            }

        format_result = util_validate_token(self.github_token)
        format_valid = format_result["valid"]
        token_type = format_result["token_type"]

        # If format is invalid, return early without API call
        if not format_valid:
            return {
                "status": "invalid",
                "message": format_result["message"],
                "token_type": token_type,
                "format_valid": False,
            }

        # Step 2: API validation - verify token works with GitHub
        try:
            import requests

            # Use Bearer format for fine-grained tokens, token format for classic
            if token_type == GitHubTokenType.CLASSIC:
                auth_header = f"token {self.github_token}"
            elif token_type in {
                GitHubTokenType.FINE_GRAINED_USER,
                GitHubTokenType.FINE_GRAINED_PAT,
            }:
                auth_header = f"Bearer {self.github_token}"
            else:
                auth_header = f"token {self.github_token}"

            headers = {
                "Authorization": auth_header,
                "Accept": "application/vnd.github.v3+json",
            }

            response = requests.get(
                "https://api.github.com/user", headers=headers, timeout=10
            )

            if response.status_code == 200:
                user_info = response.json()
                return {
                    "status": "valid",
                    "message": f"GitHub token authenticated as user: {user_info.get('login', 'unknown')}",
                    "token_type": token_type,
                    "format_valid": True,
                    "user": user_info.get("login", "unknown"),
                    "user_info": user_info,
                }
            else:
                return {
                    "status": "invalid",
                    "message": f"API validation failed: HTTP {response.status_code}",
                    "token_type": token_type,
                    "format_valid": True,
                    "status_code": response.status_code,
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Could not validate GitHub token: {str(e)}",
                "token_type": token_type,
                "format_valid": True,
                "error": str(e),
            }

    def configure_git_user(
        self, repo_dir: str, user_name: str, user_email: str
    ) -> bool:
        """
        Configure git user for commits in the repository.

        Args:
            repo_dir: Directory containing the git repository
            user_name: Git user name
            user_email: Git user email

        Returns:
            True if configuration was successful, False otherwise
        """
        try:
            subprocess.run(
                ["git", "config", "user.name", user_name], cwd=repo_dir, check=True
            )
            subprocess.run(
                ["git", "config", "user.email", user_email], cwd=repo_dir, check=True
            )

            self.logger.info(f"Git configured with user: {user_name} <{user_email}>")
            return True

        except Exception as e:
            self.logger.error(f"Failed to configure git user: {str(e)}")
            return False

    def check_repository_permissions(self, repo_url: str) -> dict:
        """
        Check if the current GitHub token has push permissions to the repository.

        Args:
            repo_url: Repository URL to check permissions for

        Returns:
            Dictionary with permission check results
        """
        if not self.github_token:
            return {
                "status": "no_token",
                "message": "No GitHub token available to check permissions",
            }

        # Extract owner and repo from URL
        try:
            if "github.com" not in repo_url:
                return {
                    "status": "not_github",
                    "message": "Repository is not hosted on GitHub",
                }

            # Parse GitHub URL to extract owner/repo
            # Handle both https://github.com/owner/repo and https://github.com/owner/repo.git
            url_path = repo_url.replace("https://github.com/", "").replace(".git", "")
            if "/" not in url_path:
                return {
                    "status": "invalid_url",
                    "message": "Could not parse repository owner/name from URL",
                }

            owner, repo = url_path.split("/", 1)

            import requests

            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json",
            }

            # Check repository permissions
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            response = requests.get(api_url, headers=headers, timeout=10)

            if response.status_code == 200:
                repo_data = response.json()
                permissions = repo_data.get("permissions", {})

                can_push = permissions.get("push", False)
                can_admin = permissions.get("admin", False)

                if can_push or can_admin:
                    return {
                        "status": "allowed",
                        "message": f"Token has push permissions to {owner}/{repo}",
                        "permissions": permissions,
                        "owner": owner,
                        "repo": repo,
                    }
                else:
                    return {
                        "status": "denied",
                        "message": f"Token does not have push permissions to {owner}/{repo}",
                        "permissions": permissions,
                        "owner": owner,
                        "repo": repo,
                    }
            elif response.status_code == 404:
                return {
                    "status": "not_found",
                    "message": f"Repository {owner}/{repo} not found or no access",
                    "owner": owner,
                    "repo": repo,
                }
            else:
                return {
                    "status": "error",
                    "message": f"GitHub API returned {response.status_code}",
                    "status_code": response.status_code,
                    "owner": owner,
                    "repo": repo,
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to check repository permissions: {str(e)}",
                "error": str(e),
            }

    def _ensure_clean_directory(self, directory: str):
        """Ensure a directory is clean and ready for use."""
        if os.path.exists(directory):
            self.logger.info(f"Cleaning up existing directory: {directory}")
            shutil.rmtree(directory)
        os.makedirs(directory, exist_ok=True)
