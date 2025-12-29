# Change: Add Claude Max OAuth Authentication via Claude Code CLI

## Why

RepoSwarm currently requires users to provide an `ANTHROPIC_API_KEY` environment variable to access Claude AI for repository analysis. This creates several limitations:

1. **API Key Cost Barrier**: API keys require direct payment per token usage, which can be expensive for heavy users
2. **No Claude Max Integration**: Users who pay for Claude Max subscriptions (5x/20x plans) cannot use their existing subscription for RepoSwarm
3. **Redundant Costs**: Power users may pay for both Claude Max subscription AND API usage
4. **Existing OAuth Tokens Unused**: Users who run `claude setup-token` cannot use those tokens with RepoSwarm

Many users already have Claude Max accounts with generous usage limits. The official Claude Code CLI supports OAuth tokens from `claude setup-token`, but RepoSwarm currently uses the Anthropic SDK which only accepts API keys.

**Critical Discovery**: OAuth tokens (`sk-ant-oat01-...`) from `claude setup-token` **do not work** with the Anthropic API (`api.anthropic.com`). The API explicitly rejects them with "OAuth authentication is currently not supported." However, the Claude Code CLI **does** support OAuth tokens and can be called programmatically.

## What Changes

- **Add Claude CLI client wrapper** - Call `claude --print` programmatically to support OAuth tokens
- **Create authentication abstraction layer** - Abstract Claude client creation to support both SDK (API key) and CLI (OAuth)
- **Add authentication method detection** - Automatically choose CLI (OAuth) or SDK (API key) based on available credentials
- **Add OAuth token environment variable support** - Recognize `CLAUDE_CODE_OAUTH_TOKEN` and `CLAUDE_OAUTH_TOKEN`
- **Add `mise claude-login` command** - Wrapper for `claude setup-token` to help users generate OAuth tokens
- **Update documentation** - Add instructions for OAuth authentication setup with Claude Max
- **Maintain API key support** - Existing ANTHROPIC_API_KEY authentication continues to work unchanged (uses SDK)

**BREAKING CHANGES**: None - API key authentication remains the default and uses the existing SDK code path

## Impact

### Affected Specs

- **claude-authentication** (NEW) - Authentication methods, session management, token refresh, client initialization

### Affected Code

- **Core Authentication** (NEW):
  - `src/investigator/core/claude_client_factory.py` (NEW) - Factory for creating SDK or CLI clients
  - `src/investigator/core/claude_cli_client.py` (NEW) - Claude CLI subprocess wrapper
  - `src/investigator/core/claude_sdk_client.py` (NEW) - Anthropic SDK wrapper (refactored from existing)

- **Existing Authentication Updates**:
  - `src/investigator/core/claude_analyzer.py:13-14` - Update to use client factory
  - `src/investigator/investigator.py:55-58` - Update initialization to use factory
  - `src/activities/investigate_activities.py:614-618` - Update to use factory

- **Configuration**:
  - `.env.example` - Add `CLAUDE_CODE_OAUTH_TOKEN`, `CLAUDE_OAUTH_TOKEN` variables
  - `src/investigator/core/config.py` - Add OAuth token detection and validation

- **Worker Initialization**:
  - `src/worker.py:42-51` - Update validation to handle both auth methods

- **New CLI Commands**:
  - Add `mise claude-login` task - Wrapper for `claude setup-token`
  - Add `mise claude-status` task - Check authentication status

- **Testing**:
  - New unit tests for CLI client wrapper (mock subprocess)
  - New integration tests for OAuth flow (with real CLI)
  - Update existing tests to work with both auth methods

### User Benefits

- **Cost Savings**: Claude Max users can leverage existing subscription instead of paying for API usage
- **Lower Barrier to Entry**: Users without API keys can use web authentication
- **Flexibility**: Users can choose authentication method based on their needs
- **Better UX**: Web authentication may be more familiar for non-technical users
- **Usage Tracking**: Web auth usage appears in claude.ai account (consolidated tracking)

### Technical Benefits

- **Authentication Abstraction**: Creates extensible pattern for future auth methods
- **Session Management**: Reusable session token handling for other features
- **Graceful Degradation**: Falls back to API key if web auth fails

### Risks

- **OAuth Token Expiration**: OAuth tokens expire after 1 year, requiring re-authentication
- **Claude CLI Dependency**: Requires Claude Code CLI to be installed (`npm install -g @anthropic-ai/claude-code`)
- **Subprocess Performance**: CLI calls via subprocess slower than direct SDK calls
- **CLI API Changes**: Claude CLI output format may change (mitigated by JSON output mode)
- **Maintenance Burden**: Two code paths to maintain and test (SDK + CLI)

### Risk Mitigation

- OAuth tokens valid for 1 year (minimal re-auth burden)
- Document Claude CLI installation in setup instructions
- Cache CLI client initialization, use `--output-format json` for stable parsing
- Abstract both clients behind common interface, easy to update if CLI changes
- Comprehensive testing for both auth methods with shared test suite
- **Much lower risk than browser automation approach** (no reverse-engineering, official CLI)

## Impact Assessment

### Low Risk Areas

- API key authentication (unchanged, continues to work)
- Repository analysis workflow (unaffected by auth method)
- Existing user configurations (no migration required)

### Medium Risk Areas

- Session token expiration handling (requires careful UX design)
- Web authentication reverse engineering (Anthropic API undocumented)
- Token refresh logic (complex edge cases)

### Low Risk Areas (Compared to Browser Automation)

- **✅ ToS Compliant**: Uses official Claude Code CLI (not reverse-engineered)
- **✅ API Stable**: CLI interface is official Anthropic tool
- **✅ No Legal Issues**: OAuth tokens obtained through official `claude setup-token` command

### Migration Strategy

- **Phase 1**: Implement CLI client wrapper and authentication factory
- **Phase 2**: Test with both API key (SDK) and OAuth (CLI)
- **Phase 3**: Deploy as stable feature (no experimental label needed)
- **Rollback**: Easy - remove CLI code path, keep SDK only

## Open Questions (Non-Blocking)

**Q1: Should we cache CLI client initialization?**

- **Recommendation**: Yes - avoid repeated subprocess overhead
- **Decision**: Implement lazy initialization with cached client instance

**Q2: Should we support automatic fallback from OAuth to API key?**

- **Option A**: Auto-fallback if OAuth fails
- **Option B**: Explicit auth method selection only
- **Recommendation**: Option A - better UX, try OAuth first if token present

**Q3: Should we add authentication status to verify_config?**

- **Recommendation**: Yes - show which auth method is active
- **Decision**: Add auth method and token type to diagnostic output

### Implementation Complexity

- **Estimated Effort**: 1-2 days for implementation, 1 day for testing
- **Dependencies**: Requires Claude Code CLI installed (`@anthropic-ai/claude-code`)
- **Expertise Required**: Subprocess management, environment variable handling

### Recommendation

**✅ PROCEED** - This is a low-risk, high-value enhancement:

1. **No ToS concerns** - Uses official CLI
2. **Stable implementation** - CLI is official Anthropic tool
3. **Low complexity** - Subprocess wrapper much simpler than browser automation
4. **High user value** - Enables Claude Max users to use their subscriptions

**Proposed Action**: Implement as planned with simplified design (CLI wrapper instead of browser automation)
