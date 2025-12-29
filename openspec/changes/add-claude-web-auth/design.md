# Design: Claude Max Web Authentication

## Context

### Background

RepoSwarm currently requires users to provide an Anthropic API key (`ANTHROPIC_API_KEY`) to access Claude AI. This creates friction for users who:

- Already pay for Claude Max subscriptions (claude.ai)
- Want to use their existing subscription limits instead of paying per API call
- Find API key setup more complex than web authentication

### Current State

- **Single Authentication Method**: ANTHROPIC_API_KEY only
- **Direct Client Initialization**: `Anthropic(api_key=key)` in claude_analyzer.py
- **No Abstraction**: Authentication logic tightly coupled with Claude client creation
- **No Session Management**: No concept of persistent sessions or token refresh

### Problem Statement

Users with Claude Max accounts cannot leverage their subscriptions, forcing them to:

1. Pay for API access separately (additional cost)
2. Manage separate authentication credentials
3. Miss out on claude.ai usage tracking and limits

### Stakeholders

- **Claude Max Subscribers**: Primary beneficiaries, want to use existing subscription
- **Free/Trial Users**: May prefer web auth over API key procurement
- **API Key Users**: Must not be disrupted, need backward compatibility
- **Enterprise Users**: May have organizational claude.ai accounts

### Critical Constraint: Terms of Service

**⚠️ BLOCKER**: This design assumes Anthropic permits web authentication for programmatic access. **Implementation cannot proceed without ToS verification.**

## Goals / Non-Goals

### Goals

- Support both API key and web-based authentication methods
- Enable Claude Max users to use their subscriptions for RepoSwarm
- Create authentication abstraction layer for future extensibility
- Maintain 100% backward compatibility with existing API key authentication
- Provide clear, secure session token management
- Implement automatic token refresh for web sessions
- Gracefully handle authentication failures with actionable error messages

### Non-Goals

- OAuth 2.0 integration (Anthropic doesn't provide OAuth)
- Multi-account support (single active authentication)
- Social login integration (Google, GitHub, etc.)
- API key management UI (command-line only)
- Token rotation automation (user manages credentials)
- Enterprise SSO integration (out of scope)
- Anthropic account creation from RepoSwarm

## Decisions

### Decision 1: Authentication Abstraction Layer

**What**: Create abstract base class for authentication methods, with concrete implementations for API key and web auth

**Why**:

- Decouples authentication from Claude client usage
- Enables easy addition of future auth methods (OAuth, SSO, etc.)
- Simplifies testing with mock authentication
- Centralizes authentication logic

**Implementation**:

```python
# src/investigator/core/claude_auth_base.py
from abc import ABC, abstractmethod
from anthropic import Anthropic

class ClaudeAuthBase(ABC):
    @abstractmethod
    def get_client(self) -> Anthropic:
        """Returns authenticated Anthropic client."""
        pass

    @abstractmethod
    def is_authenticated(self) -> bool:
        """Checks if currently authenticated."""
        pass

    @abstractmethod
    def refresh(self) -> bool:
        """Refreshes authentication if possible."""
        pass

    @abstractmethod
    def get_auth_info(self) -> dict:
        """Returns authentication metadata for diagnostics."""
        pass
```

**Usage**:

```python
# In ClaudeAnalyzer
class ClaudeAnalyzer:
    def __init__(self, auth: ClaudeAuthBase, logger):
        self.auth = auth
        self.client = auth.get_client()

    def analyze_with_context(self, prompt: str) -> str:
        # Refresh auth if needed before API call
        if not self.auth.is_authenticated():
            if not self.auth.refresh():
                raise AuthenticationError("Authentication expired, please re-authenticate")

        response = self.client.messages.create(...)
        return response.content
```

**Alternatives Considered**:

- Factory pattern with if/else: Rejected (less extensible, harder to test)
- Strategy pattern with runtime swapping: Rejected (over-engineering for current needs)
- No abstraction, duplicate code: Rejected (poor maintainability)

### Decision 2: Environment-Based Authentication Mode Selection

**What**: Use environment variables to select authentication mode automatically

**Why**:

- Simplest configuration for users
- No code changes required to switch auth methods
- Aligns with existing ANTHROPIC_API_KEY pattern
- Enables easy testing with different auth modes

**Configuration Priority**:

1. **Explicit mode**: If `CLAUDE_AUTH_MODE` is set, use specified mode ("api_key" or "web")
2. **Auto-detect**: If not set, detect based on available credentials:
   - If `ANTHROPIC_API_KEY` present → API key mode
   - If `CLAUDE_SESSION_TOKEN` present → Web mode
   - If both present → Default to API key (safer)
   - If neither present → Error with setup instructions

**Example Configurations**:

```bash
# API key authentication (existing behavior)
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Web authentication
CLAUDE_AUTH_MODE=web
CLAUDE_SESSION_TOKEN=session-xxxxx

# Explicit API key mode (even if session token exists)
CLAUDE_AUTH_MODE=api_key
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

**Alternatives Considered**:

- CLI flag for auth mode: Rejected (inconvenient, must specify on every command)
- Configuration file: Rejected (adds complexity, env vars sufficient)
- Interactive prompt at runtime: Rejected (breaks automation, CI/CD)

### Decision 3: Session Token Storage Strategy

**What**: Phase 1: Environment variables. Phase 2 (future): Encrypted file or system keychain

**Why Phase 1 (Environment Variables)**:

- Simplest implementation
- Consistent with existing ANTHROPIC_API_KEY pattern
- No additional dependencies
- Works in all environments (local, Docker, CI/CD)

**Limitations of Phase 1**:

- Less secure than keychain (tokens in plaintext environment)
- Manual token management required
- No automatic persistence across sessions

**Why Phase 2 (Encrypted File/Keychain)**:

- Better security for long-lived tokens
- Automatic persistence
- Platform-native security (macOS Keychain, Windows Credential Manager, Linux Secret Service)

**Implementation Path**:

```python
# Phase 1: Environment variable
class ClaudeSessionManager:
    def get_session_token(self) -> Optional[str]:
        return os.getenv('CLAUDE_SESSION_TOKEN')

    def save_session_token(self, token: str) -> None:
        # Manual: User must add to .env file
        print(f"Add to .env file: CLAUDE_SESSION_TOKEN={token}")

# Phase 2 (future): Keychain integration
class ClaudeSessionManager:
    def get_session_token(self) -> Optional[str]:
        # Try environment variable first
        if env_token := os.getenv('CLAUDE_SESSION_TOKEN'):
            return env_token
        # Fall back to keychain
        return keyring.get_password("reposwarm", "claude_session")

    def save_session_token(self, token: str) -> None:
        keyring.set_password("reposwarm", "claude_session", token)
```

**Alternatives Considered**:

- SQLite database: Rejected (overkill for single credential)
- Encrypted JSON file: Rejected (key management complexity)
- Direct keychain only: Rejected (platform dependencies, harder to test)

### Decision 4: Browser-Based Authentication Flow

**What**: Use playwright library for browser automation to capture session token

**Why**:

- Programmatic browser control for headless environments
- Cross-platform (Windows, macOS, Linux)
- Maintained library with good documentation
- Can run headless for server deployments

**Flow**:

1. Launch browser (visible or headless mode)
2. Navigate to claude.ai login page
3. Wait for user to complete login
4. Extract session token from browser cookies/localStorage
5. Save token to environment/keychain
6. Close browser

**Implementation**:

```python
from playwright.sync_api import sync_playwright

class ClaudeWebAuth(ClaudeAuthBase):
    def authenticate_browser(self, headless: bool = False) -> str:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page()
            page.goto('https://claude.ai')

            # Wait for user to login (detect auth cookies)
            page.wait_for_url('https://claude.ai/chats', timeout=300000)  # 5 min

            # Extract session token from cookies or localStorage
            cookies = page.context.cookies()
            session_token = extract_session_token(cookies)

            browser.close()
            return session_token
```

**Alternatives Considered**:

- Selenium: Rejected (heavier weight, more complex setup)
- Manual browser + token copy-paste: Considered as fallback option
- Headless HTTP requests to mimic login: Rejected (fragile, may violate ToS)

### Decision 5: Token Refresh Strategy

**What**: Implement proactive token refresh before API calls, with fallback to manual re-authentication

**Why**:

- Prevents mid-operation authentication failures
- Better user experience (no interruptions during analysis)
- Allows long-running workflows to complete

**Implementation**:

```python
class ClaudeWebAuth(ClaudeAuthBase):
    def is_token_expired(self) -> bool:
        # Check token expiration (if token includes expiry metadata)
        # Or attempt a test API call to detect expiration
        try:
            self.client.messages.create(
                model="claude-opus-4-5-20251101",
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}]
            )
            return False
        except AuthenticationError:
            return True

    def refresh(self) -> bool:
        if not self.is_token_expired():
            return True  # Already valid

        # Attempt automatic refresh (if refresh token available)
        if refresh_token := self.session_manager.get_refresh_token():
            try:
                new_token = self._refresh_with_token(refresh_token)
                self.session_manager.save_session_token(new_token)
                self.client = self._create_client(new_token)
                return True
            except RefreshError:
                pass  # Fall through to manual re-auth

        # Require manual re-authentication
        return False
```

**User Experience on Expiration**:

```
Warning: Your Claude session has expired.
Please re-authenticate:
  1. Run: mise claude-login
  2. Complete login in browser
  3. Re-run your command

Or switch to API key authentication:
  1. Set ANTHROPIC_API_KEY in .env file
  2. Unset CLAUDE_SESSION_TOKEN
```

**Alternatives Considered**:

- Automatic browser re-launch: Rejected (disruptive during workflow)
- Silent failure and fallback to API key: Rejected (unexpected behavior)
- No refresh, immediate failure: Rejected (poor UX)

### Decision 6: Graceful Degradation and Fallback

**What**: If web auth fails, attempt fallback to API key if available

**Why**:

- Resilience to session expiration
- Allows users to configure both auth methods for redundancy
- Better UX during auth transitions

**Implementation**:

```python
def create_claude_auth() -> ClaudeAuthBase:
    auth_mode = os.getenv('CLAUDE_AUTH_MODE', 'auto')

    if auth_mode == 'api_key' or auth_mode == 'auto':
        if api_key := os.getenv('ANTHROPIC_API_KEY'):
            try:
                auth = ClaudeApiKeyAuth(api_key)
                if auth.is_authenticated():
                    return auth
            except Exception as e:
                logger.warning(f"API key auth failed: {e}")

    if auth_mode == 'web' or auth_mode == 'auto':
        if session_token := os.getenv('CLAUDE_SESSION_TOKEN'):
            try:
                auth = ClaudeWebAuth(session_token)
                if auth.is_authenticated():
                    return auth
            except Exception as e:
                logger.warning(f"Web auth failed: {e}")

    raise AuthenticationError("No valid authentication method available")
```

**Alternatives Considered**:

- No fallback, fail immediately: Rejected (poor resilience)
- Always prefer web auth over API key: Rejected (API key may be more stable)
- User-configurable fallback order: Considered for future enhancement

## Risks / Trade-offs

### Risk 1: Anthropic Terms of Service Violation

**Risk**: Using web authentication for programmatic access may violate Anthropic's ToS

**Likelihood**: Medium-High (unofficial API usage often prohibited)

**Impact**: Critical (project cannot ship this feature if prohibited)

**Mitigation**:

- **BLOCKER**: Contact Anthropic support before implementation
- Obtain written confirmation that this use is permitted
- If denied, abandon this proposal
- Mark feature as "experimental" if approved with caveats
- Include disclaimer in documentation about unofficial status

**Decision Gate**: MUST resolve before proceeding to implementation

### Risk 2: Session Token Instability

**Risk**: Session token format or authentication mechanism may change without notice

**Likelihood**: Medium (Anthropic may change web auth at any time)

**Impact**: High (feature breaks, users lose access)

**Mitigation**:

- Design abstraction to easily swap authentication implementation
- Comprehensive error handling with fallback to API key
- Monitor for authentication failures (add telemetry/logging)
- Provide clear upgrade path in case of breaking changes
- Keep API key auth as stable primary option

### Risk 3: Security - Token Leakage

**Risk**: Session tokens may be exposed in logs, error messages, or insecure storage

**Likelihood**: Low (with proper implementation)

**Impact**: Critical (account compromise)

**Mitigation**:

- Implement token sanitization in all log output
- Use secure file permissions (0600) for token files
- Add token validation before usage
- Comprehensive security testing
- Clear documentation on token security best practices
- Consider keychain integration for Phase 2

### Risk 4: Browser Dependency

**Risk**: Browser automation may fail in headless/server environments

**Likelihood**: Medium (various Docker, CI/CD environments)

**Impact**: Medium (can't authenticate in some environments)

**Mitigation**:

- Provide manual token input option as fallback
- Support both headless and visible browser modes
- Clear documentation for server/CI authentication
- Consider API key as recommended method for CI/CD

### Risk 5: Maintenance Burden

**Risk**: Two authentication methods = double the testing, debugging, and documentation

**Likelihood**: High (inevitable)

**Impact**: Medium (ongoing cost)

**Mitigation**:

- Shared test suite for both auth methods
- Abstraction layer reduces duplication
- Comprehensive automated testing
- Clear documentation with troubleshooting guides
- Consider deprecating one method if burden becomes too high

## Trade-offs

### Trade-off 1: Complexity vs. Flexibility

**Added Complexity**:

- New dependencies (playwright, keyring in future)
- Authentication abstraction layer
- Session token management
- Browser automation logic

**Gained Flexibility**:

- Support for Claude Max users
- Lower cost barrier for entry
- Future-proof for additional auth methods

**Conclusion**: Worthwhile trade-off IF ToS permits AND user demand exists

### Trade-off 2: Security vs. Usability

**Security Concerns**:

- Session tokens in environment variables (Phase 1)
- Browser automation risks (XSS, token interception)
- Automatic token refresh may hide expiration

**Usability Gains**:

- Web login more familiar than API key for non-technical users
- Automatic token refresh reduces interruptions
- Integration with existing claude.ai accounts

**Conclusion**: Phase 1 acceptable for opt-in feature, Phase 2 (keychain) required for production-grade security

### Trade-off 3: Official vs. Unofficial API

**Unofficial Approach** (reverse-engineered web auth):

- Benefits: Works today, leverages Claude Max
- Risks: May break, may violate ToS, unsupported

**Official Approach** (wait for official web SDK):

- Benefits: Stable, supported, ToS-compliant
- Risks: May never exist, timing unknown

**Decision**: Prefer official if available within reasonable timeframe (3-6 months), otherwise consider unofficial with clear experimental label

## Migration Plan

### Phase 1: Implementation (IF ToS APPROVED)

**Week 1-2: Core Implementation**

1. Authentication abstraction layer
2. API key auth adapter (refactor existing)
3. Web auth adapter (browser automation)
4. Session token management

**Week 3: Integration**

1. Update ClaudeAnalyzer, ClaudeInvestigator
2. Update Temporal activities
3. Add configuration validation
4. Implement graceful fallback

**Week 4: Testing & Documentation**

1. Comprehensive test suite
2. Security testing
3. Documentation and guides
4. OpenSpec validation

### Phase 2: Beta Release

**Week 5-6: Beta Testing**

1. Release as experimental feature
2. Gather user feedback
3. Monitor stability and errors
4. Refine based on feedback

**Week 7: Stabilization**

1. Fix discovered issues
2. Improve error messages
3. Add telemetry/monitoring
4. Update documentation

### Phase 3: General Availability (Conditional)

**IF**: Beta successful AND no ToS issues AND stable for 30 days
**THEN**: Promote to stable feature
**ELSE**: Keep as experimental or deprecate

### Rollback Plan

- Feature flag to disable web auth (fall back to API key only)
- No database migrations = easy rollback
- Remove web auth code in single commit if needed
- Users with API keys unaffected by rollback

### Success Criteria

- [ ] Anthropic confirms ToS compliance
- [ ] Both auth methods work reliably
- [ ] Zero disruption to API key users
- [ ] Session token refresh works automatically
- [ ] Browser authentication works in 90%+ of environments
- [ ] Security review passes (no token leakage)
- [ ] User documentation clear and comprehensive
- [ ] All tests pass (unit, integration, security)

## Open Questions

### Q1: What is the session token format and expiration time?

**Status**: Requires research/reverse engineering
**Blocker**: No, can discover during implementation
**Action**: Inspect claude.ai network traffic during implementation

### Q2: Does Anthropic provide a refresh token mechanism?

**Status**: Unknown
**Blocker**: No, can implement periodic re-authentication if refresh unavailable
**Action**: Research during implementation, document findings

### Q3: Should we support multiple concurrent sessions?

**Status**: Design decision needed
**Recommendation**: No for Phase 1 (YAGNI), consider if users request it

### Q4: Should web auth be default or opt-in?

**Status**: Design decision needed
**Recommendation**: API key remains default (stable), web auth opt-in (experimental)

### Q5: What dependencies are acceptable for browser automation?

**Status**: Requires user input
**Options**: playwright (50MB), selenium (lighter?), manual browser (no deps)
**Recommendation**: playwright for Phase 1 (most reliable), add manual fallback

## References

- Anthropic ToS: https://www.anthropic.com/legal/consumer-terms
- Anthropic API Docs: https://docs.anthropic.com/
- Playwright Docs: https://playwright.dev/python/
- RepoSwarm Current Auth: `src/investigator/core/claude_analyzer.py:13-14`
- RepoSwarm Worker Validation: `src/worker.py:42-51`
