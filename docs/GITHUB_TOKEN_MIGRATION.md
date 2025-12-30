# GitHub Token Migration Guide

This guide helps you migrate from GitHub classic personal access tokens (PATs) to fine-grained personal access tokens for enhanced security.

## Why Migrate to Fine-Grained Tokens?

Fine-grained personal access tokens provide several security advantages over classic tokens:

- **Repository-level permissions**: Grant access only to specific repositories instead of all accessible repositories
- **Granular permissions**: Control exactly which operations the token can perform (read, write, admin, etc.)
- **Expiration enforcement**: Tokens can have enforced expiration dates (up to 1 year)
- **Better audit trail**: More detailed logging of token usage in GitHub's security log
- **Reduced risk**: If compromised, the token has limited scope and duration

## Token Format Comparison

| Token Type              | Prefix        | Length                 | Example                                  |
| ----------------------- | ------------- | ---------------------- | ---------------------------------------- |
| Classic PAT             | `ghp_`        | ~40 chars after prefix | `ghp_1234567890abcdefghijklmnopqrstuvwx` |
| Fine-grained User Token | `ghu_`        | Variable               | `ghu_ABCDefgh123456...`                  |
| Fine-grained PAT        | `github_pat_` | Variable               | `github_pat_11AAAA...`                   |

## Creating a Fine-Grained Personal Access Token

### Step 1: Navigate to Token Settings

1. Go to GitHub Settings: https://github.com/settings/tokens
2. Click **"Fine-grained tokens"** tab
3. Click **"Generate new token"**

### Step 2: Configure Basic Settings

1. **Token name**: `RepoSwarm - <Your Machine Name>` (e.g., "RepoSwarm - MacBook Pro")
2. **Expiration**: Choose an expiration period (recommended: 90 days with calendar reminders to rotate)
3. **Description**: "Token for RepoSwarm architecture analysis on [machine name]"
4. **Resource owner**: Select your username or organization

### Step 3: Repository Access

Choose one of:

- **Only select repositories**: Recommended - Choose only the repositories you want RepoSwarm to analyze
- **All repositories**: Gives access to all current and future repositories (similar to classic PAT)

### Step 4: Set Permissions

RepoSwarm requires the following **Repository permissions**:

| Permission    | Access Level     | Reason                                                     |
| ------------- | ---------------- | ---------------------------------------------------------- |
| **Contents**  | Read and Write   | Clone repositories, commit `.arch.md` files to results hub |
| **Metadata**  | Read (automatic) | Access basic repository information                        |
| **Workflows** | Read (optional)  | Analyze GitHub Actions workflows (if present)              |

**Important**: Do NOT grant additional permissions unless specifically needed.

### Step 5: Generate and Copy Token

1. Click **"Generate token"**
2. **Copy the token immediately** - you won't be able to see it again
3. Store it securely (password manager recommended)

## Updating RepoSwarm Configuration

### Update `.env.local`

Replace your existing classic token with the new fine-grained token:

```bash
# Old (classic PAT)
GITHUB_TOKEN=ghp_1234567890abcdefghijklmnopqrstuvwx

# New (fine-grained PAT)
GITHUB_TOKEN=github_pat_11AAAA5QI0h3qZfGhQNkl9_AbCd...
```

### Verify Configuration

Run the configuration verification script:

```bash
mise verify-config
```

You should see output confirming the token type:

```
GitHub token format check: github_pat... (length: 93)
Token type: Fine-grained PAT (valid format)
✓ GitHub API access verified
```

## Testing Your New Token

### Test with a Single Repository

```bash
mise investigate-one https://github.com/your-org/your-repo
```

### Monitor for Permission Issues

If you see errors like:

```
❌ 403 Forbidden - Resource not accessible by personal access token
❌ 404 Not Found (repository may be private or token lacks access)
```

**Solution**: Return to token settings and verify:

1. The repository is selected in "Repository access"
2. "Contents" permission is set to "Read and Write"
3. Token hasn't expired

## Common Migration Issues

### Issue: "Repository not found" (404)

**Cause**: Fine-grained token doesn't have access to the repository.

**Solution**:

1. Go to https://github.com/settings/tokens
2. Click on your RepoSwarm token
3. Under "Repository access", click "All repositories" or add the specific repository
4. Click "Save" at the bottom

### Issue: "Permission denied" (403)

**Cause**: Insufficient permissions on the token.

**Solution**:

1. Edit your token settings
2. Under "Repository permissions", ensure:
   - **Contents**: Read and Write
   - **Metadata**: Read (should be automatic)
3. Save changes

### Issue: Token expired

**Cause**: Fine-grained tokens have mandatory expiration.

**Solution**:

1. Generate a new token following the steps above
2. Update `.env.local` with the new token
3. Set a calendar reminder to rotate before expiration

## Security Best Practices

### Token Storage

- **DO**: Store tokens in `.env.local` (git-ignored)
- **DO**: Use a password manager for backup
- **DON'T**: Commit tokens to git
- **DON'T**: Share tokens in Slack/email/chat

### Token Rotation

- Set tokens to expire in 90 days
- Create calendar reminders 1 week before expiration
- Generate new token before old one expires
- Delete old tokens after successful migration

### Monitoring

- Review GitHub security log regularly: https://github.com/settings/security-log
- Look for unexpected repository access
- Revoke tokens for machines you no longer use

## Backward Compatibility

RepoSwarm maintains full backward compatibility with classic PATs:

- Existing classic tokens (`ghp_*`) continue to work
- No code changes required when switching token types
- Authentication headers automatically adapt to token type
- Error messages provide token-type-specific guidance

## Troubleshooting

For detailed troubleshooting, see:

- [GitHub Token Troubleshooting Guide](GITHUB_TOKEN_TROUBLESHOOTING.md)
- [GitHub Token Diagnostics Summary](github-token-diagnostics-summary.md)

## Need Help?

If you encounter issues not covered here:

1. Run diagnostics: `mise verify-config`
2. Check token permissions in GitHub settings
3. Review error logs in `temp/investigation.log` (if using local mode)
4. Open an issue with:
   - Token type (without the actual token value)
   - Error message
   - Output from `mise verify-config`

## References

- [GitHub Documentation: Fine-grained PATs](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token)
- [GitHub: Token Best Practices](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/token-expiration-and-revocation)
