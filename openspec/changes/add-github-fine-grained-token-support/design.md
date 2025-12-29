# Design: Fine-Grained GitHub Token Support

## Context

### Background

GitHub introduced fine-grained personal access tokens as a successor to classic PATs, offering:

- Repository-specific access (vs. account-wide)
- Granular permission scopes
- Automatic expiration (max 1 year)
- Organization-level controls
- Improved audit trail

GitHub is actively encouraging migration to fine-grained tokens and may eventually deprecate classic PATs.

### Current State

RepoSwarm only recognizes classic tokens (`ghp_*`):

- Token format validation assumes `ghp_` prefix
- Documentation only mentions classic token generation
- No differentiation between token types in validation or error messages

### Stakeholders

- **Security-conscious users**: Want to use least-privilege fine-grained tokens
- **Enterprise users**: May have organizational policies requiring fine-grained tokens
- **Existing users**: Must continue using classic tokens without disruption

## Goals / Non-Goals

### Goals

- Support all current GitHub token formats (classic and fine-grained)
- Detect token type automatically without user configuration
- Provide helpful error messages when fine-grained token permissions are insufficient
- Maintain 100% backward compatibility with classic tokens
- Document recommended permissions for fine-grained tokens
- No breaking changes to existing API or configuration

### Non-Goals

- OAuth app integration (separate from personal access tokens)
- GitHub App authentication (uses different auth mechanism)
- Automatic token generation or management
- Token rotation or refresh logic
- Multi-token support (still single GITHUB_TOKEN environment variable)
- Token storage encryption (relies on environment variable security)

## Decisions

### Decision 1: Automatic Token Type Detection

**What**: Detect token type based on prefix pattern matching

**Why**:

- Simplest implementation requiring no user configuration
- GitHub token formats have distinct, stable prefixes
- No risk of misclassification
- Zero migration burden for users

**Implementation**:

```python
def detect_github_token_type(token: str) -> GitHubTokenType:
    if token.startswith('ghp_'):
        return GitHubTokenType.CLASSIC
    elif token.startswith('ghu_'):
        return GitHubTokenType.FINE_GRAINED_USER
    elif token.startswith('github_pat_'):
        return GitHubTokenType.FINE_GRAINED_PAT
    else:
        return GitHubTokenType.UNKNOWN
```

**Alternatives Considered**:

- User-specified token type via config: Rejected (unnecessary complexity, error-prone)
- API introspection to detect type: Rejected (extra API call, rate limit impact)

### Decision 2: Standardize on Bearer Authentication

**What**: Use `Authorization: Bearer {token}` for all GitHub API calls

**Why**:

- Fine-grained tokens require Bearer format (GitHub API specification)
- Classic tokens accept both `token` and `Bearer` formats
- Simplifies code by having single authorization format
- Future-proof as GitHub may deprecate `token` format

**Implementation**:

```python
headers = {
    'Authorization': f'Bearer {self.github_token}',
    'Accept': 'application/vnd.github.v3+json'
}
```

**Current State**: Inconsistent usage across codebase

- `git_manager.py` uses: `Authorization: token {token}`
- `update_repos.py` uses: `Authorization: Bearer {token}`

**Migration**: Update all API calls to Bearer format, add code comment explaining backward compatibility

**Alternatives Considered**:

- Keep token format for classic, Bearer for fine-grained: Rejected (unnecessary branching logic)
- Make format configurable: Rejected (over-engineering)

### Decision 3: Enhanced Error Handling for Permission Issues

**What**: Detect and provide actionable error messages for common fine-grained token permission issues

**Why**:

- Fine-grained tokens have repository-specific access
- Generic "403 Forbidden" errors are unhelpful for debugging
- Users need guidance on which permissions to grant
- Reduces support burden

**Implementation**:

```python
def handle_github_api_error(response, token_type):
    if response.status_code == 404 and token_type.is_fine_grained():
        return {
            'error': 'Repository not found or token lacks access',
            'suggestion': 'Ensure your fine-grained token has access to this repository. Visit: https://github.com/settings/tokens',
            'required_permissions': ['Contents: Read', 'Metadata: Read']
        }
```

**Alternatives Considered**:

- Generic error messages: Rejected (poor UX)
- Automatic permission detection via API: Rejected (complex, rate limit impact)

### Decision 4: Minimal Configuration Changes

**What**: No new required environment variables, GITHUB_TOKEN works for all token types

**Why**:

- Backward compatibility paramount
- Simpler mental model for users
- Existing configuration validation already in place

**Configuration**:

```bash
# Existing (no changes)
GITHUB_TOKEN=ghp_xxxx...  # Classic token
GITHUB_TOKEN=ghu_xxxx...  # Fine-grained user token
GITHUB_TOKEN=github_pat_xxxx...  # Fine-grained PAT
```

**Alternatives Considered**:

- Separate GITHUB_FINE_GRAINED_TOKEN variable: Rejected (confusing, unnecessary)
- Auto-selection between multiple tokens: Rejected (out of scope)

### Decision 5: Token Type Diagnostics in verify_config

**What**: Display detected token type during configuration verification

**Why**:

- Helps users confirm correct token type is detected
- Useful for troubleshooting permission issues
- Minimal implementation cost

**Output Example**:

```
✓ GitHub token found in environment
  Type: Fine-grained PAT (github_pat_)
  Format: Valid
  API Access: Verified
  Repository Permissions: Read access confirmed
```

**Alternatives Considered**:

- Silent detection: Rejected (less user-friendly for debugging)
- Verbose permission enumeration: Rejected (too complex for initial implementation)

## Risks / Trade-offs

### Risk 1: Fine-Grained Token Permission Complexity

**Risk**: Users may not grant sufficient permissions, causing cryptic errors

**Likelihood**: Medium (fine-grained tokens default to minimal permissions)

**Impact**: Medium (confusing errors, support requests)

**Mitigation**:

- Comprehensive documentation of required permissions
- Enhanced error messages detecting common permission issues
- Example fine-grained token configuration in README
- Troubleshooting guide for permission errors

### Risk 2: GitHub Token Format Changes

**Risk**: GitHub may introduce new token formats or change existing prefixes

**Likelihood**: Low (stable API, would be breaking change for GitHub)

**Impact**: Medium (would require code update)

**Mitigation**:

- Use UNKNOWN token type as fallback (degrades gracefully)
- Comprehensive unit tests for format detection
- Log warnings for UNKNOWN token types
- Monitor GitHub API changelog

### Risk 3: Inconsistent Behavior Between Token Types

**Risk**: Fine-grained and classic tokens may behave differently with same API calls

**Likelihood**: Low (GitHub API is token-type agnostic)

**Impact**: Medium (unexpected failures)

**Mitigation**:

- Integration tests with both token types
- Document any discovered behavioral differences
- Add specific error handling for known differences

### Trade-off: Bearer vs Token Format

**Decision**: Standardize on Bearer format for all tokens

**Benefits**:

- Single code path for all token types
- Future-proof (recommended format)
- Required for fine-grained tokens

**Costs**:

- Minor risk if GitHub deprecates Bearer for classic tokens (very unlikely)
- Theoretical performance impact (negligible)

**Conclusion**: Benefits outweigh costs significantly

## Migration Plan

### Phase 1: Implementation (Week 1)

1. Implement token detection utility
2. Update git_manager.py authorization headers
3. Add token type diagnostics
4. Write unit tests

### Phase 2: Testing (Week 1)

1. Integration tests with real fine-grained tokens
2. Verify backward compatibility with classic tokens
3. Test permission error scenarios
4. Security review of token handling

### Phase 3: Documentation (Week 2)

1. Update README with fine-grained token instructions
2. Create troubleshooting guide
3. Update code examples
4. Update openspec/project.md

### Phase 4: Validation (Week 2)

1. Manual testing with all token types
2. OpenSpec validation
3. User acceptance testing (if applicable)

### Rollback Plan

- No database or state changes required
- Can revert code changes in single commit
- Classic token support never removed, so rollback has no user impact
- Fine-grained token support simply becomes unavailable

### Success Criteria

- [ ] All three token types (ghp*, ghu*, github*pat*) work for repository operations
- [ ] Existing users with classic tokens experience zero disruption
- [ ] Documentation includes fine-grained token setup instructions
- [ ] Error messages provide actionable guidance for permission issues
- [ ] OpenSpec validation passes
- [ ] All tests (unit and integration) pass

## Open Questions

### Q1: Should we detect and warn about expiring tokens?

**Context**: Fine-grained tokens have expiration dates, classic tokens do not

**Options**:

1. Parse token and detect expiration (if possible via API)
2. Catch expiration errors and provide helpful message
3. No special handling (rely on GitHub API errors)

**Decision Required**: Before implementation phase 2

**Recommendation**: Option 2 (detect error, provide message) - balances complexity and UX

### Q2: Should we support GitHub App authentication?

**Context**: GitHub Apps use installation tokens (different from PATs)

**Decision**: No - out of scope for this change. Can be separate future enhancement.

**Rationale**: Different authentication mechanism, different use case (organization-wide vs. user)

### Q3: Should we enumerate fine-grained token permissions?

**Context**: Fine-grained tokens include permission metadata in API responses

**Options**:

1. Call API to enumerate permissions, display during verification
2. Only display token type, rely on error messages for permission issues
3. Document required permissions, don't programmatically verify

**Decision Required**: Before implementation phase 1

**Recommendation**: Option 3 for initial implementation - simplest, avoids extra API calls

### Q4: Should we support token rotation?

**Context**: Security best practice is to rotate tokens periodically

**Decision**: No - out of scope. Token rotation is user responsibility.

**Rationale**: Requires secret management system (AWS SSM, HashiCorp Vault, etc.) - significant complexity

## References

- GitHub Docs: [Fine-grained personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token#fine-grained-personal-access-tokens)
- GitHub API: [Authentication](https://docs.github.com/en/rest/overview/authenticating-to-the-rest-api)
- RepoSwarm: `src/investigator/core/git_manager.py:433-596` (current implementation)
- RepoSwarm: `scripts/verify_config.py:195-313` (current validation)
