# Change: Add Fine-Grained GitHub Token Support

## Why

RepoSwarm currently only supports classic GitHub Personal Access Tokens (PATs) with the `ghp_` prefix. GitHub is actively promoting fine-grained personal access tokens (with `ghu_` and `github_pat_` prefixes) as a more secure alternative that follows the principle of least privilege by allowing granular repository-specific permissions and automatic expiration.

Users with fine-grained tokens cannot currently use RepoSwarm, forcing them to either:

1. Create less secure classic PATs against GitHub's security recommendations
2. Abandon fine-grained tokens they've already configured for other tools

This creates a security and usability barrier for modern GitHub workflows.

## What Changes

- **Add fine-grained token format recognition** - Support `ghu_*` and `github_pat_*` token formats alongside existing `ghp_*` classic tokens
- **Implement token type detection** - Automatically detect whether a token is classic or fine-grained based on prefix
- **Update token validation logic** - Modify GitHub API validation to handle both token types correctly
- **Update authorization headers** - Ensure both token types work correctly with GitHub REST API (both accept `Bearer` format, but classic also accepts `token` format)
- **Update documentation** - Add instructions for generating and using fine-grained tokens
- **Add token type diagnostics** - Display detected token type during configuration verification
- **Maintain backward compatibility** - Classic tokens continue to work without any changes

**BREAKING CHANGES**: None - this is fully backward compatible

## Impact

### Affected Specs

- **github-authentication** (NEW) - Token format validation, type detection, API authentication

### Affected Code

- **Core Authentication**:
  - `src/investigator/core/git_manager.py:433-596` - Token validation and API calls
  - `src/investigator/core/git_manager.py:81-128` - Git URL authentication

- **Configuration & Validation**:
  - `scripts/verify_config.py:195-313` - Token format validation
  - `scripts/update_repos.py:80-86, 176-180` - GitHub API authentication

- **Documentation**:
  - `src/investigator/README.md:36-40` - Token generation instructions
  - `src/investigator/example_private_repo.py:76` - Example code comments
  - `.env.example:20` - Configuration documentation

- **Testing**:
  - New unit tests for token type detection
  - New integration tests with fine-grained token format
  - Update existing tests to cover both token types

### User Benefits

- **Improved Security**: Users can follow GitHub's best practices with fine-grained tokens
- **Better Compliance**: Organizations enforcing fine-grained token policies can use RepoSwarm
- **Granular Permissions**: Fine-grained tokens can be scoped to specific repositories
- **Automatic Expiration**: Fine-grained tokens support automatic expiration dates
- **Zero Migration Cost**: Existing users with classic tokens experience no disruption

### Risk Assessment

- **Low Risk**: Token format detection is straightforward (prefix-based)
- **Backward Compatible**: Classic tokens continue to work unchanged
- **No API Changes**: GitHub REST API accepts both token types with `Bearer` authentication
- **Testable**: Easy to verify with both real classic and fine-grained tokens
