# GitHub Token Diagnostics Analysis

**Date**: 2025-01-29  
**Context**: GH-5.2 - Comprehensive troubleshooting guide and diagnostic utilities for GitHub token permission issues

## Executive Summary

This document analyzes the current token validation and diagnostic infrastructure in RepoSwarm to identify:

- Current diagnostic capabilities
- Gaps in failure mode detection
- Recommendations for enhanced diagnostic utilities
- Common error patterns requiring documentation

## Current Diagnostic Capabilities

### 1. Token Format Validation (`github_token_utils.py`)

**Location**: `src/investigator/core/github_token_utils.py`

**Capabilities**:

- ✅ Detects token type: `CLASSIC` (ghp*), `FINE_GRAINED_USER` (ghu*), `FINE_GRAINED_PAT` (github*pat*)
- ✅ Validates format (length, prefix patterns)
- ✅ Returns structured validation result with `valid`, `token_type`, `message`
- ✅ Handles edge cases (empty strings, whitespace, non-string types)

**Limitations**:

- ❌ Format-only validation (doesn't check if token is expired or revoked)
- ❌ No scope/permission checking
- ❌ No repository access validation

**Example Output**:

```python
{
    'valid': True,
    'token_type': GitHubTokenType.CLASSIC,
    'message': 'Valid CLASSIC token'
}
```

### 2. Token API Validation (`git_manager.py::validate_github_token()`)

**Location**: `src/investigator/core/git_manager.py:586-690`

**Capabilities**:

- ✅ Hybrid validation: format check + API call to `/user` endpoint
- ✅ Detects token type and uses correct auth header format:
  - Classic: `token {token}`
  - Fine-grained: `Bearer {token}`
- ✅ Returns user information on success
- ✅ Handles HTTP status codes: 200, 401, 403
- ✅ Returns structured result with `status`, `message`, `token_type`, `format_valid`, `user`, `status_code`

**Current Status Code Handling**:

- ✅ **200**: Valid token, returns user info
- ✅ **401**: Invalid/expired token (detected but generic message)
- ✅ **403**: Permission denied (detected but generic message)
- ⚠️ **429**: Rate limiting (NOT explicitly handled)
- ⚠️ **404**: Not found (NOT explicitly handled)

**Limitations**:

- ❌ No specific detection for expired tokens (401 could mean expired or invalid)
- ❌ No scope/permission enumeration
- ❌ No repository-specific access checking
- ❌ No rate limit detection/retry logic
- ❌ Generic error messages don't guide users to solutions

**Example Output**:

```python
{
    'status': 'invalid',
    'message': 'API validation failed: HTTP 401',
    'token_type': GitHubTokenType.CLASSIC,
    'format_valid': True,
    'status_code': 401
}
```

### 3. Repository Permission Checking (`git_manager.py::check_repository_permissions()`)

**Location**: `src/investigator/core/git_manager.py:721-811`

**Capabilities**:

- ✅ Checks push permissions for specific repository
- ✅ Uses `/repos/{owner}/{repo}` endpoint
- ✅ Returns permission details (`push`, `admin`, `read`)
- ✅ Handles status codes: 200, 404
- ✅ Returns structured result: `status` (`allowed`, `denied`, `not_found`, `error`)

**Limitations**:

- ❌ Doesn't check read permissions (only push/admin)
- ❌ Doesn't verify fine-grained token repository selection
- ❌ No scope enumeration (can't tell which permissions token has)
- ❌ Generic error messages for 404 (could be "not found" or "no access")
- ❌ No detection of fine-grained token repository selection issues

**Example Output**:

```python
{
    'status': 'denied',
    'message': 'Token does not have push permissions to owner/repo',
    'permissions': {'push': False, 'admin': False, 'read': True},
    'owner': 'owner',
    'repo': 'repo'
}
```

### 4. Configuration Verification Script (`verify_config.py`)

**Location**: `scripts/verify_config.py`

**Capabilities**:

- ✅ Comprehensive configuration validation
- ✅ Token format validation using `github_token_utils`
- ✅ Token API validation using `git_manager.validate_github_token()`
- ✅ Repository permission checks for architecture hub and default repo
- ✅ Fine-grained token warnings
- ✅ Rich console output (with `rich` library) or plain text fallback
- ✅ Structured summary with successes, warnings, errors

**Current Checks**:

1. Token format validation
2. Token API validation (`/user` endpoint)
3. Architecture hub repository permissions
4. Default repository permissions

**Limitations**:

- ❌ No rate limit checking
- ❌ No token expiration detection
- ❌ No scope enumeration
- ❌ No fine-grained token repository selection verification
- ❌ Generic error messages don't provide actionable guidance
- ❌ No detection of common misconfigurations (wrong token type, missing scopes)

**Example Output**:

```
🔐 REPOSITORY ACCESS TEST
────────────────────────────────────────────────────────────
Status Setting              Value                           Details
────────────────────────────────────────────────────────────
✅    Token Type            Classic PAT (ghp_)            Format valid
✅    GitHub Token          username                       Valid
⚠️    Arch Hub (repo)       READ ONLY                     Push denied
```

### 5. Git Clone Error Detection (`git_manager.py`)

**Location**: `src/investigator/core/git_manager.py:151-191`

**Capabilities**:

- ✅ Pattern matching for permission errors in git output
- ✅ Detects: "authentication failed", "repository not found", "permission denied", "403"
- ✅ Builds contextual error messages based on token type
- ✅ Provides hints for fine-grained tokens

**Limitations**:

- ❌ Relies on string matching (fragile, may miss edge cases)
- ❌ No distinction between different failure modes (expired vs. insufficient permissions)
- ❌ No rate limit detection from git errors
- ❌ Generic messages don't guide users to specific solutions

**Example Error Message**:

```
Failed to clone repository: Fine-grained token (FINE_GRAINED_PAT) lacks repository access permissions.
Ensure the token includes this repository and has Contents (read) permission.
```

## Gaps in Failure Mode Detection

### Critical Gaps

1. **Token Expiration Detection**
   - **Current**: HTTP 401 could mean expired or invalid token
   - **Gap**: No way to distinguish expired tokens from invalid tokens
   - **Impact**: Users can't tell if they need to regenerate token or if token is wrong

2. **Rate Limiting Detection**
   - **Current**: No explicit rate limit checking in validation functions
   - **Gap**: HTTP 429 errors not handled, no `X-RateLimit-*` header parsing
   - **Impact**: Users hit rate limits without clear guidance
   - **Note**: `update_repos.py` has rate limit checking, but not in core validation

3. **Fine-Grained Token Repository Selection**
   - **Current**: Can check if token has permissions, but can't verify repository is selected
   - **Gap**: Fine-grained tokens require explicit repository selection; 404 could mean "not selected" vs "doesn't exist"
   - **Impact**: Users can't tell if they need to add repository to token's allowed list

4. **Scope/Permission Enumeration**
   - **Current**: Can check if token works, but can't list what scopes/permissions it has
   - **Gap**: No API call to enumerate token scopes (classic) or permissions (fine-grained)
   - **Impact**: Users can't verify token has required permissions without testing each operation

5. **Invalid Token Format Detection**
   - **Current**: Format validation exists but errors are generic
   - **Gap**: No specific guidance for common mistakes (wrong prefix, wrong length, extra whitespace)
   - **Impact**: Users struggle to fix format issues

### Moderate Gaps

6. **Network/Connectivity Issues**
   - **Current**: Generic exception handling
   - **Gap**: No distinction between network errors, DNS failures, timeouts
   - **Impact**: Users can't tell if issue is token-related or network-related

7. **Repository Visibility Detection**
   - **Current**: 404 could mean "not found" or "no access"
   - **Gap**: Can't distinguish private repo without access vs. non-existent repo
   - **Impact**: Users can't tell if they need to request access or if repo URL is wrong

8. **Token Type Mismatch Detection**
   - **Current**: Can detect token type but doesn't warn if wrong type for use case
   - **Gap**: No guidance that fine-grained tokens need repository selection
   - **Impact**: Users use fine-grained tokens without selecting repositories

## Recommendations for Diagnostic Utility Design

### 1. Enhanced Token Validation Function

**Proposed Function**: `diagnose_github_token(token: str, repo_url: Optional[str] = None) -> dict`

**Capabilities**:

```python
{
    'format': {
        'valid': bool,
        'token_type': GitHubTokenType,
        'issues': List[str]  # Specific format problems
    },
    'api': {
        'status': 'valid' | 'invalid' | 'expired' | 'rate_limited' | 'error',
        'user': Optional[str],
        'scopes': Optional[List[str]],  # For classic tokens
        'permissions': Optional[dict],  # For fine-grained tokens
        'status_code': Optional[int],
        'rate_limit': Optional[dict]  # {remaining, limit, reset}
    },
    'repository': {
        'accessible': Optional[bool],  # If repo_url provided
        'read_permission': Optional[bool],
        'write_permission': Optional[bool],
        'selected': Optional[bool],  # For fine-grained tokens
        'issues': List[str]  # Specific access problems
    },
    'recommendations': List[str]  # Actionable fixes
}
```

**Key Features**:

- Comprehensive validation across all dimensions
- Specific error detection (expired vs. invalid)
- Rate limit awareness
- Repository-specific checks
- Actionable recommendations

### 2. Rate Limit Detection Utility

**Proposed Function**: `check_github_rate_limit(token: str) -> dict`

**Capabilities**:

```python
{
    'remaining': int,
    'limit': int,
    'reset_timestamp': int,
    'reset_datetime': str,
    'status': 'ok' | 'warning' | 'critical',
    'recommendation': str
}
```

**Implementation**:

- Parse `X-RateLimit-*` headers from API responses
- Check `/rate_limit` endpoint
- Provide reset time and recommendations

### 3. Token Scope/Permission Enumeration

**Proposed Function**: `enumerate_token_permissions(token: str) -> dict`

**Capabilities**:

- **Classic tokens**: Use `/user` endpoint, check `scopes` header or `/user` response
- **Fine-grained tokens**: Use token introspection endpoint (if available) or test permissions
- Return structured permission list

**Note**: GitHub API doesn't expose fine-grained token permissions directly; may need to test operations.

### 4. Repository Access Diagnostic

**Proposed Function**: `diagnose_repository_access(token: str, repo_url: str) -> dict`

**Capabilities**:

```python
{
    'repository_exists': bool,
    'token_has_access': bool,
    'read_permission': bool,
    'write_permission': bool,
    'fine_grained_selected': Optional[bool],
    'visibility': 'public' | 'private' | 'unknown',
    'issues': List[str],
    'recommendations': List[str]
}
```

**Key Features**:

- Distinguish "not found" vs "no access"
- Check fine-grained token repository selection
- Provide specific guidance for each failure mode

### 5. Comprehensive Diagnostic Script

**Proposed**: Enhanced `verify_config.py` or new `diagnose_github_token.py`

**Features**:

- Run all diagnostic checks
- Generate comprehensive report
- Provide troubleshooting guide links
- Export results for support

## Common Error Patterns to Document

### 1. Token Expired (HTTP 401)

**Symptoms**:

- `validate_github_token()` returns `status: 'invalid'` with `status_code: 401`
- Git clone fails with "authentication failed"
- API calls return 401 Unauthorized

**Detection**:

- HTTP 401 with valid token format
- Token was previously working
- No changes to token configuration

**Solution**:

- Regenerate token in GitHub settings
- Update `GITHUB_TOKEN` environment variable
- Verify token hasn't been revoked

**User Guidance**:

```
Your GitHub token has expired or been revoked.
1. Go to https://github.com/settings/tokens
2. Generate a new token with required permissions
3. Update GITHUB_TOKEN in your .env.local file
```

### 2. Insufficient Scopes (Classic Token)

**Symptoms**:

- Token validates but repository operations fail
- `check_repository_permissions()` returns `denied`
- Git clone fails with "permission denied"

**Detection**:

- Token format valid, API validation succeeds
- Repository permission check fails
- Token type is CLASSIC

**Solution**:

- Regenerate classic token with `repo` scope
- For private repos, ensure `repo` scope includes private repository access

**User Guidance**:

```
Your classic token lacks required permissions.
1. Go to https://github.com/settings/tokens
2. Edit your token or create new one
3. Select 'repo' scope (includes private repos)
4. Update GITHUB_TOKEN in your .env.local file
```

### 3. Repository Not Selected (Fine-Grained Token)

**Symptoms**:

- Token validates successfully
- Repository permission check returns `not_found` (404)
- Git clone fails with "repository not found"
- Token has correct permissions but can't access repo

**Detection**:

- Token type is FINE_GRAINED_USER or FINE_GRAINED_PAT
- Repository exists (can verify with public API or other token)
- Permission check returns 404
- Token format and API validation succeed

**Solution**:

- Add repository to token's allowed repositories list
- For organization repos, ensure token has organization access

**User Guidance**:

```
Your fine-grained token doesn't have this repository selected.
1. Go to https://github.com/settings/tokens
2. Find your fine-grained token
3. Under 'Repository access', add this repository
4. Save changes (no need to regenerate token)
```

### 4. Invalid Token Format

**Symptoms**:

- `validate_github_token()` returns `format_valid: False`
- Token type is UNKNOWN
- Error message indicates format problem

**Common Mistakes**:

- Wrong prefix (e.g., `ghp` instead of `ghp_`)
- Wrong length (classic tokens must be exactly 44 chars)
- Extra whitespace (leading/trailing spaces)
- Missing characters (truncated token)

**Detection**:

- Format validation fails before API call
- Specific error message indicates format issue

**Solution**:

- Verify token copied completely (no truncation)
- Remove any whitespace
- Check token prefix matches expected format
- Regenerate if format is completely wrong

**User Guidance**:

```
Your token format is invalid. Common issues:
- Classic tokens (ghp_): Must be exactly 44 characters total
- Fine-grained tokens (ghu_ or github_pat_): Must have minimum length after prefix
- No whitespace: Remove any spaces before/after token
- Complete token: Ensure entire token was copied

Check your token in .env.local and regenerate if needed.
```

### 5. Rate Limiting (HTTP 429)

**Symptoms**:

- API calls return HTTP 429
- `X-RateLimit-Remaining: 0` in response headers
- Intermittent failures after many requests

**Detection**:

- HTTP 429 status code
- `X-RateLimit-Remaining` header is 0 or low
- `X-RateLimit-Reset` header indicates reset time

**Solution**:

- Wait for rate limit reset (check `X-RateLimit-Reset` header)
- Use authenticated requests (higher rate limits)
- Reduce request frequency
- Consider using fine-grained tokens (may have different limits)

**User Guidance**:

```
GitHub API rate limit exceeded.
- Remaining requests: {remaining}
- Reset time: {reset_datetime}
- Wait until reset time or reduce request frequency
- Authenticated requests have higher limits (5000/hour)
```

### 6. Network/Connectivity Issues

**Symptoms**:

- `validate_github_token()` returns `status: 'error'`
- Exception messages mention network, DNS, or timeout
- Intermittent failures

**Detection**:

- Exception type is `requests.exceptions.*`
- Error message mentions network, DNS, timeout, connection
- Token format is valid

**Solution**:

- Check internet connectivity
- Verify DNS resolution for `api.github.com`
- Check firewall/proxy settings
- Verify GitHub API is accessible

**User Guidance**:

```
Network connectivity issue detected.
1. Check internet connection
2. Test: curl https://api.github.com
3. Check firewall/proxy settings
4. Verify DNS resolution for api.github.com
```

### 7. Wrong Token Type for Use Case

**Symptoms**:

- Fine-grained token works but repository operations fail
- Token validates but can't access expected repositories

**Detection**:

- Token type is FINE_GRAINED_USER or FINE_GRAINED_PAT
- Repository permission checks fail
- User may not understand fine-grained token requirements

**Solution**:

- Use classic token for simpler setup (if acceptable)
- Or properly configure fine-grained token with repository selection

**User Guidance**:

```
Fine-grained tokens require explicit repository selection.
Options:
1. Use classic token (simpler, but broader permissions)
2. Configure fine-grained token:
   - Add repositories to token's allowed list
   - Ensure correct permissions (Contents: Read/Write)
   - Verify organization access if needed
```

## Implementation Priority

### High Priority (GH-5.2 Core)

1. **Enhanced Token Validation** (`diagnose_github_token()`)
   - Expired token detection
   - Rate limit detection
   - Repository-specific checks
   - Actionable recommendations

2. **Troubleshooting Guide**
   - Document all common error patterns
   - Provide step-by-step solutions
   - Include screenshots/examples
   - Link to GitHub documentation

3. **Improved Error Messages**
   - Replace generic messages with specific guidance
   - Include troubleshooting links
   - Provide actionable next steps

### Medium Priority

4. **Rate Limit Utility**
   - Standalone rate limit checking
   - Reset time calculation
   - Recommendations based on limit status

5. **Repository Access Diagnostic**
   - Comprehensive repository access checking
   - Fine-grained token selection verification
   - Visibility detection

### Low Priority

6. **Permission Enumeration**
   - Scope listing for classic tokens
   - Permission testing for fine-grained tokens
   - Permission comparison utility

## Testing Strategy

### Unit Tests

- Mock GitHub API responses for all status codes
- Test token format validation edge cases
- Test error message generation
- Test recommendation logic

### Integration Tests

- Test with real (but test) tokens
- Test rate limit detection
- Test repository access checks
- Test fine-grained token scenarios

### Manual Testing

- Test with expired tokens
- Test with fine-grained tokens (selected/unselected repos)
- Test rate limit scenarios
- Test network error scenarios

## Files to Modify/Create

### Modify Existing Files

1. `src/investigator/core/github_token_utils.py`
   - Add `diagnose_github_token()` function
   - Add rate limit checking utilities

2. `src/investigator/core/git_manager.py`
   - Enhance `validate_github_token()` with better error detection
   - Improve error messages with recommendations
   - Add rate limit detection

3. `scripts/verify_config.py`
   - Integrate enhanced diagnostics
   - Add troubleshooting guidance
   - Improve error reporting

### Create New Files

1. `src/investigator/core/github_token_diagnostics.py`
   - Comprehensive diagnostic utilities
   - Error pattern detection
   - Recommendation engine

2. `docs/troubleshooting/github-token-issues.md`
   - Comprehensive troubleshooting guide
   - Common error patterns
   - Step-by-step solutions
   - Examples and screenshots

3. `scripts/diagnose_github_token.py`
   - Standalone diagnostic script
   - Comprehensive token analysis
   - Export results for support

## Conclusion

The current diagnostic infrastructure provides basic token validation but lacks:

- Specific error mode detection (expired vs. invalid)
- Rate limit awareness
- Fine-grained token repository selection verification
- Actionable error messages and recommendations

The recommended enhancements will provide comprehensive diagnostics that guide users to solutions rather than just reporting failures.
