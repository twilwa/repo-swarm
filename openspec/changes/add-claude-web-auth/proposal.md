# Change: Add Claude Max Web Authentication

## Why

RepoSwarm currently requires users to provide an `ANTHROPIC_API_KEY` environment variable to access Claude AI for repository analysis. This creates several limitations:

1. **API Key Cost Barrier**: API keys require direct payment per token usage, which can be expensive for heavy users
2. **No Claude Max Integration**: Users who pay for Claude Max subscriptions (claude.ai) cannot use their existing subscription for RepoSwarm
3. **Redundant Costs**: Power users may pay for both Claude Max subscription AND API usage
4. **Authentication Friction**: Obtaining API keys requires separate setup from web authentication

Many users already have Claude Max accounts through claude.ai with generous usage limits. Enabling web-based authentication would allow these users to leverage their existing subscriptions, reducing cost barriers and improving accessibility.

**Market Context**: Other AI tools (ChatGPT, Gemini) support both web and API authentication, making this a competitive feature gap.

## What Changes

- **Add web-based authentication flow** - Support browser-based login to claude.ai alongside existing API key authentication
- **Implement session token management** - Store and refresh session tokens obtained from web login
- **Create authentication abstraction layer** - Abstract Claude client creation to support multiple auth methods
- **Add authentication method detection** - Automatically choose web auth or API key based on configuration
- **Implement token refresh mechanism** - Automatically refresh expired web session tokens
- **Add authentication mode configuration** - Allow users to specify preferred authentication method
- **Update documentation** - Add instructions for web authentication setup
- **Maintain API key support** - Existing ANTHROPIC_API_KEY authentication continues to work unchanged

**BREAKING CHANGES**: None - API key authentication remains the default, web auth is opt-in

## Impact

### Affected Specs

- **claude-authentication** (NEW) - Authentication methods, session management, token refresh, client initialization

### Affected Code

- **Core Authentication** (NEW):
  - `src/investigator/core/claude_auth.py` (NEW) - Authentication abstraction layer
  - `src/investigator/core/claude_web_auth.py` (NEW) - Web-based authentication implementation
  - `src/investigator/core/claude_session_manager.py` (NEW) - Session token storage and refresh

- **Existing Authentication Updates**:
  - `src/investigator/core/claude_analyzer.py:13-14` - Update to use authentication abstraction
  - `src/investigator/investigator.py:55-58` - Update initialization to support both auth methods
  - `src/activities/investigate_activities.py:614-618` - Update to use auth abstraction

- **Configuration**:
  - `.env.example` - Add CLAUDE_AUTH_MODE, CLAUDE_SESSION_TOKEN variables
  - `src/investigator/core/config.py` - Add auth mode validation

- **Worker Initialization**:
  - `src/worker.py:42-51` - Update validation to handle both auth methods

- **Testing**:
  - New unit tests for authentication abstraction
  - New integration tests for web auth (with mock session tokens)
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

- **Session Token Expiration**: Web sessions may expire, requiring user re-authentication
- **Anthropic API Changes**: Web authentication is not officially documented by Anthropic
- **Browser Dependency**: Initial auth requires browser for login flow
- **Token Storage Security**: Session tokens must be stored securely
- **Maintenance Burden**: Two auth methods to maintain and test

### Risk Mitigation

- Implement automatic token refresh with user notification on failure
- Design abstraction layer to easily swap implementations if Anthropic API changes
- Support headless browser automation for CLI-only environments
- Use secure token storage (environment variables, encrypted files, or system keychain)
- Comprehensive testing for both auth methods with shared test suite

## Impact Assessment

### Low Risk Areas

- API key authentication (unchanged, continues to work)
- Repository analysis workflow (unaffected by auth method)
- Existing user configurations (no migration required)

### Medium Risk Areas

- Session token expiration handling (requires careful UX design)
- Web authentication reverse engineering (Anthropic API undocumented)
- Token refresh logic (complex edge cases)

### High Risk Areas

- **Anthropic Terms of Service**: Using web authentication for API-like access may violate ToS
- **API Stability**: Web authentication mechanism may change without notice
- **Legal/Compliance**: Must verify this usage is permitted

### Migration Strategy

- **Phase 1**: Add web auth as experimental feature (opt-in, clearly marked beta)
- **Phase 2**: Gather user feedback, monitor stability
- **Phase 3**: Promote to stable if no ToS/legal issues arise
- **Fallback**: Can remove feature or make API-key-only if issues discovered

## Open Questions Requiring User Input

### Critical Decision Points

**Q1: Is web authentication permitted under Anthropic's Terms of Service?**

- **Status**: REQUIRES INVESTIGATION
- **Action**: Review Anthropic ToS, contact Anthropic support if unclear
- **Blocker**: YES - cannot proceed without ToS compliance

**Q2: Should we use official Anthropic web SDK or reverse-engineer the API?**

- **Option A**: Wait for official web SDK from Anthropic (if they release one)
- **Option B**: Reverse-engineer claude.ai authentication (risky, may break)
- **Option C**: Use third-party libraries that may exist (dependency risk)
- **Recommendation**: Check for official SDK first, consider third-party, reverse-engineer only as last resort

**Q3: How should session tokens be stored?**

- **Option A**: Environment variables (simple, less secure)
- **Option B**: Encrypted file in user's home directory (more secure)
- **Option C**: System keychain integration (most secure, platform-specific)
- **Recommendation**: Start with Option A for simplicity, add Option C later

**Q4: Should we support both web auth and API key simultaneously?**

- **Option A**: One method at a time (simpler)
- **Option B**: Try web auth, fall back to API key (better UX)
- **Option C**: Use both in parallel for redundancy (complex)
- **Recommendation**: Option B - try preferred method, fall back to alternative

### Implementation Complexity

- **Estimated Effort**: 2-3 weeks for full implementation and testing
- **Dependencies**: May require additional Python packages (e.g., playwright for browser automation)
- **Expertise Required**: Understanding of OAuth-like flows, session management, web APIs

### Recommendation

Given the **high risk of ToS violation** and **API stability concerns**, I recommend:

1. **FIRST**: Investigate Anthropic ToS and contact their support to confirm web auth is permitted
2. **IF PERMITTED**: Proceed with design.md and implementation
3. **IF NOT PERMITTED**: Close this proposal and explore alternatives (e.g., Anthropic API rate limit optimizations, caching improvements)

**Proposed Action**: Pause this proposal pending ToS investigation. User should verify legal compliance before investing engineering effort.
