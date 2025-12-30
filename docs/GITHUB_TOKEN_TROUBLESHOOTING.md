# GitHub Token Troubleshooting Guide

This guide helps you diagnose and resolve common GitHub token authentication and permission issues in RepoSwarm.

## Table of Contents

1. [Quick Diagnostic](#quick-diagnostic)
2. [Common Issues](#common-issues)
   - [Invalid Token Format](#1-invalid-token-format)
   - [Expired or Invalid Token](#2-expired-or-invalid-token)
   - [Insufficient Scopes/Permissions](#3-insufficient-scopespermissions)
   - [Repository Not Selected (Fine-Grained Tokens)](#4-repository-not-selected-fine-grained-tokens)
   - [No Push Permission](#5-no-push-permission)
   - [Rate Limiting](#6-rate-limiting)
   - [Network Errors](#7-network-errors)
3. [Token Types](#token-types)
4. [Required Permissions](#required-permissions)
5. [Best Practices](#best-practices)

## Quick Diagnostic

RepoSwarm includes built-in diagnostic tools to help identify token issues:

```bash
# Verify your GitHub token configuration
mise verify-config

# Run diagnostic on your current token
python -c "from src.investigator.core.github_diagnostics import diagnose_github_token; \
import os; \
result = diagnose_github_token(os.getenv('GITHUB_TOKEN')); \
print(f'Status: {result.status.value}'); \
print(f'Message: {result.message}'); \
[print(f'- {rec}') for rec in result.recommendations] if result.recommendations else None"
```

## Common Issues

### 1. Invalid Token Format

**Symptoms:**

- Error: "Token has invalid format"
- Token doesn't start with `ghp_` or `github_pat_`

**Causes:**

- Token was copied incorrectly (extra spaces, truncation)
- Using an old token format
- Using a different type of credential (password, OAuth app token)

**Solutions:**

1. **Verify token format:**
   - Classic tokens: Must start with `ghp_` followed by exactly 40 characters
   - Fine-grained tokens: Must start with `github_pat_` followed by additional characters

2. **Copy token correctly:**

   ```bash
   # When copying from GitHub, ensure no trailing spaces
   export GITHUB_TOKEN="ghp_YourActualTokenHere"
   ```

3. **Regenerate if needed:**
   - Go to https://github.com/settings/tokens
   - Delete the problematic token
   - Create a new one following the [Token Creation Guide](#token-types)

### 2. Expired or Invalid Token

**Symptoms:**

- HTTP 401 Unauthorized errors
- Error: "Token is expired or invalid"
- Token worked before but stopped working

**Causes:**

- Token has expired (check expiration date in GitHub settings)
- Token was revoked by you or an organization admin
- Token was regenerated but `.env.local` wasn't updated

**Solutions:**

1. **Check token expiration:**
   - Go to https://github.com/settings/tokens
   - Look for your token in the list
   - Check the "Expires" column

2. **Generate a new token:**

   ```bash
   # For Classic tokens:
   # 1. Go to https://github.com/settings/tokens
   # 2. Click "Generate new token" → "Generate new token (classic)"
   # 3. Select scopes: ✅ repo (all), ✅ user:email
   # 4. Set expiration (recommended: 90 days or No expiration)
   # 5. Click "Generate token"
   # 6. Copy the token immediately (shown only once!)

   # Update .env.local
   nano .env.local  # or your preferred editor
   # Set: GITHUB_TOKEN=ghp_YourNewTokenHere
   ```

3. **For fine-grained tokens:**
   - Go to https://github.com/settings/tokens?type=beta
   - Check expiration and regenerate if needed
   - Update `GITHUB_TOKEN` in `.env.local`

### 3. Insufficient Scopes/Permissions

**Symptoms:**

- HTTP 403 Forbidden errors
- Error: "Resource not accessible by personal access token"
- Can read repositories but cannot perform operations

**Causes:**

- Classic token missing `repo` scope
- Fine-grained token missing required permissions
- Token has wrong permission level (read when write is needed)

**Solutions:**

#### For Classic Tokens:

1. **Required scopes:**
   - ✅ **repo** (Full control of private repositories)
     - Includes: repo:status, repo_deployment, public_repo, repo:invite, security_events
   - ✅ **user:email** (Access user email addresses)

2. **Update token scopes:**
   - Go to https://github.com/settings/tokens
   - Click your token name
   - Scroll to "Select scopes"
   - Check ✅ **repo** and ✅ **user:email**
   - Click "Update token"
   - Note: Token value doesn't change, no need to update `.env.local`

#### For Fine-Grained Tokens:

1. **Required repository permissions:**
   - **Contents**: Read and write (for cloning and analyzing)
   - **Metadata**: Read-only (automatically included)

2. **Update permissions:**
   - Go to https://github.com/settings/tokens?type=beta
   - Click your token name
   - Under "Repository permissions":
     - Set **Contents** to "Read and write"
   - Click "Save"

### 4. Repository Not Selected (Fine-Grained Tokens)

**Symptoms:**

- HTTP 404 Not Found errors
- Error: "Repository not selected in fine-grained token settings"
- Token works for some repos but not others

**Causes:**

- Fine-grained token configured with "Only select repositories"
- Target repository not in the selected list

**Solutions:**

1. **Add repository to token:**
   - Go to https://github.com/settings/tokens?type=beta
   - Click your token name
   - Under "Repository access":
     - **Option A:** Select "All repositories" (easier, less secure)
     - **Option B:** Select "Only select repositories" and click "Select repositories"
       - Search for the target repository
       - Check the box next to it
   - Click "Save"

2. **Wait for propagation:**
   - Changes may take 1-2 minutes to propagate
   - Try your operation again after waiting

3. **Alternative: Use Classic Token:**
   - Classic tokens automatically work with all accessible repositories
   - Consider using a Classic token if you need access to many repos

### 5. No Push Permission

**Symptoms:**

- HTTP 403 when trying to push
- Error: "Token has read-only access"
- Can clone but cannot commit to architecture hub

**Causes:**

- Token has `public_repo` scope instead of full `repo` scope
- Fine-grained token has "Contents: Read-only" permission
- Repository settings restrict token access

**Solutions:**

1. **For Classic Tokens:**
   - Go to https://github.com/settings/tokens
   - Edit your token
   - Ensure ✅ **repo** is checked (not just **public_repo**)
   - Update token

2. **For Fine-Grained Tokens:**
   - Go to https://github.com/settings/tokens?type=beta
   - Edit your token
   - Set **Contents** permission to **"Read and write"**
   - Save changes

3. **Verify repository access:**
   ```bash
   # Test push access
   python -c "from src.investigator.core.github_diagnostics import diagnose_github_token; \
   import os; \
   result = diagnose_github_token(os.getenv('GITHUB_TOKEN'), 'owner/repo'); \
   print(result.message); \
   print(f'Can push: {result.details.get(\"can_push\", \"Unknown\")}')"
   ```

### 6. Rate Limiting

**Symptoms:**

- HTTP 429 Too Many Requests
- Error: "API rate limit exceeded"
- Operations work but then suddenly fail

**Causes:**

- Exceeded GitHub API rate limit (5000 requests/hour for authenticated requests)
- Many investigations running simultaneously
- Shared token being used by multiple processes

**Solutions:**

1. **Check current rate limit:**

   ```bash
   curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit
   ```

2. **Wait for reset:**
   - Rate limits reset every hour
   - Check the `X-RateLimit-Reset` header for exact reset time
   - Error message includes reset time

3. **Optimize usage:**
   - RepoSwarm caches results to minimize API calls
   - Use `mise investigate-one` instead of `mise investigate-all` during development
   - Avoid running multiple investigations simultaneously

4. **Increase limits:**
   - Upgrade to GitHub Pro for higher limits
   - Use multiple tokens (not recommended for production)

### 7. Network Errors

**Symptoms:**

- Connection timeouts
- DNS resolution failures
- SSL/TLS errors

**Causes:**

- Firewall blocking api.github.com
- Proxy misconfiguration
- GitHub service outage

**Solutions:**

1. **Check GitHub status:**
   - Visit https://www.githubstatus.com
   - Verify API is operational

2. **Test connectivity:**

   ```bash
   # Test basic connectivity
   curl -I https://api.github.com

   # Test with your token
   curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
   ```

3. **Configure proxy (if needed):**

   ```bash
   # In .env.local
   export HTTPS_PROXY=http://proxy.example.com:8080
   export HTTP_PROXY=http://proxy.example.com:8080
   ```

4. **Check firewall rules:**
   - Ensure outbound HTTPS (443) to api.github.com is allowed
   - Verify corporate firewall isn't blocking GitHub API

## Token Types

### Classic Personal Access Tokens (PAT)

**Format:** `ghp_` followed by 40 alphanumeric characters

**Pros:**

- Simple to set up
- Work with all repositories you have access to
- No repository selection needed

**Cons:**

- Broader permissions than necessary
- All-or-nothing scope model
- Deprecated by GitHub (still supported but legacy)

**Creation:**

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Name: "RepoSwarm Analysis"
4. Expiration: 90 days or No expiration
5. Scopes: ✅ repo, ✅ user:email
6. Click "Generate token"
7. Copy token to `.env.local`

### Fine-Grained Personal Access Tokens

**Format:** `github_pat_` followed by additional characters

**Pros:**

- Granular permission control
- Can restrict to specific repositories
- Modern, recommended by GitHub

**Cons:**

- More complex setup
- Must explicitly select repositories
- Requires careful permission configuration

**Creation:**

1. Go to https://github.com/settings/tokens?type=beta
2. Click "Generate new token"
3. Name: "RepoSwarm Analysis"
4. Expiration: Custom (90 days recommended)
5. Repository access:
   - For testing: "All repositories"
   - For production: "Only select repositories" (select target repos)
6. Repository permissions:
   - **Contents**: Read and write
   - **Metadata**: Read-only (auto-selected)
7. Click "Generate token"
8. Copy token to `.env.local`

## Required Permissions

### Minimum Permissions by Operation

| Operation            | Classic Scope           | Fine-Grained Permission | Level        |
| -------------------- | ----------------------- | ----------------------- | ------------ |
| Clone repository     | `repo` or `public_repo` | Contents                | Read         |
| Analyze private repo | `repo`                  | Contents                | Read         |
| Commit to arch hub   | `repo`                  | Contents                | Read + Write |
| Access user info     | `user:email`            | (Not applicable)        | -            |

### Recommended Setup

**For most users (Classic Token):**

```
Scopes:
  ✅ repo (full control of private repositories)
  ✅ user:email
Expiration: 90 days
```

**For security-conscious users (Fine-Grained Token):**

```
Repository Access: Only select repositories
  - Add each target repository
  - Or select "All repositories" if analyzing many repos

Repository Permissions:
  - Contents: Read and write
  - Metadata: Read-only (auto-selected)

Expiration: 90 days
```

## Best Practices

### Security

1. **Never commit tokens to git:**

   ```bash
   # Verify .env.local is in .gitignore
   grep -q ".env.local" .gitignore || echo ".env.local" >> .gitignore
   ```

2. **Use environment variables:**

   ```bash
   # Store in .env.local (not in shell history)
   echo "GITHUB_TOKEN=ghp_YourToken" >> .env.local

   # NOT recommended:
   # export GITHUB_TOKEN=ghp_...  # This goes in shell history!
   ```

3. **Set expiration dates:**
   - Tokens should expire (90 days recommended)
   - Set calendar reminder to regenerate before expiration

4. **Use fine-grained tokens when possible:**
   - Limit to specific repositories
   - Minimal required permissions
   - Easier to audit and revoke

### Maintenance

1. **Regular rotation:**
   - Rotate tokens every 90 days
   - Use calendar reminders for expiration

2. **Monitor usage:**
   - Check https://github.com/settings/tokens periodically
   - Review "Last used" column
   - Revoke unused tokens

3. **Documentation:**
   - Document which tokens are used where
   - Keep track of token purposes
   - Note expiration dates

4. **Backup plan:**
   - Have a process to quickly regenerate tokens
   - Keep this troubleshooting guide handy
   - Test token regeneration before you need it urgently

### Testing

1. **Always verify new tokens:**

   ```bash
   mise verify-config
   ```

2. **Test with single repository first:**

   ```bash
   mise investigate-one https://github.com/your-org/test-repo
   ```

3. **Check permissions before bulk operations:**
   ```bash
   # Use diagnostic tool to verify push access
   python -c "from src.investigator.core.github_diagnostics import diagnose_github_token; \
   import os; \
   result = diagnose_github_token(os.getenv('GITHUB_TOKEN'), 'owner/repo'); \
   print(result.message)"
   ```

## Getting Help

If you're still experiencing issues after following this guide:

1. **Check logs:**

   ```bash
   # Enable debug logging
   export LOG_LEVEL=DEBUG
   mise investigate-one <repo-url>
   ```

2. **Run diagnostics:**

   ```bash
   mise verify-config
   ```

3. **Gather information:**
   - Token type (classic or fine-grained)
   - Error messages (full text)
   - GitHub username and repository being accessed
   - Output of `mise verify-config`

4. **Ask for help:**
   - Include diagnostic output
   - Redact your actual token value
   - Describe what you've tried

## Appendix: Diagnostic Tool Reference

### diagnose_github_token()

Python function that performs comprehensive token validation:

```python
from src.investigator.core.github_diagnostics import diagnose_github_token
import os

# Basic validation
result = diagnose_github_token(os.getenv('GITHUB_TOKEN'))

# Validate with repository access check
result = diagnose_github_token(
    os.getenv('GITHUB_TOKEN'),
    'owner/repo'
)

# Check result
print(f"Status: {result.status.value}")  # success, warning, or error
print(f"Message: {result.message}")
if result.recommendations:
    print("Recommendations:")
    for rec in result.recommendations:
        print(f"  - {rec}")
```

### Return Values

**DiagnosticStatus:**

- `SUCCESS`: Token is valid and has required permissions
- `WARNING`: Token works but has limitations (e.g., read-only)
- `ERROR`: Token is invalid, expired, or insufficient

**TokenIssueType:**

- `INVALID_FORMAT`: Token doesn't match expected pattern
- `EXPIRED_OR_INVALID`: Token rejected by GitHub API
- `INSUFFICIENT_SCOPES`: Missing required permissions
- `REPOSITORY_NOT_SELECTED`: Fine-grained token doesn't include repo
- `NO_PUSH_PERMISSION`: Can read but cannot write
- `RATE_LIMITED`: Exceeded API rate limit
- `NETWORK_ERROR`: Network connectivity issue
