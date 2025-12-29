# Implementation Tasks

**⚠️ PREREQUISITE: Confirm Anthropic Terms of Service compliance before starting implementation**

## 0. Legal and Compliance Verification (REQUIRED FIRST)

- [ ] 0.1 Review Anthropic Terms of Service
  - Read current ToS at https://www.anthropic.com/legal/consumer-terms
  - Identify any clauses about automated access or API usage
  - Document relevant sections and interpretations

- [ ] 0.2 Contact Anthropic Support
  - Submit support request asking about web authentication for programmatic access
  - Explain use case: CLI tool for repository analysis using Claude Max accounts
  - Obtain written confirmation or denial

- [ ] 0.3 Decision Gate
  - **IF APPROVED**: Proceed to Phase 1
  - **IF DENIED**: Abandon this proposal, close as "not feasible due to ToS"
  - **IF UNCLEAR**: Consult legal counsel before proceeding

## 1. Research and Design (IF ToS APPROVED)

- [ ] 1.1 Research authentication mechanisms
  - Investigate claude.ai authentication flow (browser network inspection)
  - Document endpoints, headers, token formats
  - Identify session token structure and expiration times
  - Check for existing third-party libraries or implementations

- [ ] 1.2 Evaluate implementation approaches
  - Option A: Official SDK (if available)
  - Option B: Third-party library (e.g., pyClaude, claude-api-py - check if they exist)
  - Option C: Direct implementation (reverse-engineered)
  - Document pros/cons of each approach

- [ ] 1.3 Define authentication flow
  - Design browser-based login flow (OAuth-like)
  - Define session token storage mechanism
  - Design token refresh flow
  - Design fallback to API key on failure

## 2. Core Authentication Abstraction Layer

- [ ] 2.1 Create abstract authentication interface
  - New file: `src/investigator/core/claude_auth_base.py`
  - Abstract method: `get_client() -> Anthropic`
  - Abstract method: `is_authenticated() -> bool`
  - Abstract method: `refresh() -> bool`
  - Abstract method: `get_auth_info() -> dict`

- [ ] 2.2 Implement API key authentication adapter
  - New file: `src/investigator/core/claude_api_key_auth.py`
  - Implement `ClaudeApiKeyAuth(ClaudeAuthBase)`
  - Wrap existing API key logic from `claude_analyzer.py`
  - Add validation and error handling

- [ ] 2.3 Implement web authentication adapter
  - New file: `src/investigator/core/claude_web_auth.py`
  - Implement `ClaudeWebAuth(ClaudeAuthBase)`
  - Implement browser-based login flow
  - Implement session token extraction
  - Add token refresh logic

## 3. Session Token Management

- [ ] 3.1 Create session token storage
  - New file: `src/investigator/core/claude_session_manager.py`
  - Implement token save/load from environment variable
  - Implement token save/load from file (with encryption)
  - Add token expiration detection
  - Add secure token cleanup on logout

- [ ] 3.2 Implement token refresh mechanism
  - Detect token expiration before API calls
  - Automatically refresh expired tokens
  - Handle refresh failures gracefully
  - Notify user when manual re-authentication required

- [ ] 3.3 Add token security measures
  - Ensure tokens are not logged
  - Implement secure file permissions (0600) for token files
  - Add token sanitization in error messages
  - Consider keychain integration (future enhancement)

## 4. Browser-Based Authentication Flow

- [ ] 4.1 Implement browser automation (if needed)
  - Evaluate: playwright, selenium, or manual browser flow
  - Launch browser with login URL
  - Detect authentication success
  - Extract session token from browser
  - Close browser after token extraction

- [ ] 4.2 Add headless authentication support
  - Support headless mode for servers without display
  - Provide manual token input option as fallback
  - Add clear user instructions for manual auth

- [ ] 4.3 Add authentication CLI commands
  - New command: `mise claude-login` (interactive browser login)
  - New command: `mise claude-logout` (clear session token)
  - New command: `mise claude-status` (show auth status)
  - Update mise.toml with new tasks

## 5. Integration with Existing Code

- [ ] 5.1 Update ClaudeAnalyzer
  - Modify constructor to accept `ClaudeAuthBase` instead of raw API key
  - Update client initialization to use `auth.get_client()`
  - Add authentication refresh before API calls
  - Handle authentication failures gracefully

- [ ] 5.2 Update ClaudeInvestigator
  - Modify initialization to create appropriate auth adapter
  - Add auth mode detection logic
  - Pass auth adapter to ClaudeAnalyzer
  - Add authentication validation during initialization

- [ ] 5.3 Update Temporal activities
  - Modify `investigate_activities.py` to use auth abstraction
  - Ensure auth works in Temporal worker context
  - Handle session token in distributed worker environment
  - Add authentication error recovery in activities

- [ ] 5.4 Update worker initialization
  - Modify `src/worker.py` to validate either API key or web session
  - Add auth mode detection
  - Provide clear error messages for missing authentication
  - Validate authentication before worker starts

## 6. Configuration and Environment

- [ ] 6.1 Add new environment variables
  - `CLAUDE_AUTH_MODE`: "api_key" (default) or "web"
  - `CLAUDE_SESSION_TOKEN`: (optional) session token for web auth
  - `CLAUDE_SESSION_FILE`: (optional) path to session token file
  - Document in `.env.example`

- [ ] 6.2 Update config validation
  - Add auth mode validation in `config.py`
  - Validate required variables based on auth mode
  - Add helpful error messages for misconfiguration

- [ ] 6.3 Add authentication mode auto-detection
  - If ANTHROPIC_API_KEY present, use API key auth
  - If CLAUDE_SESSION_TOKEN present, use web auth
  - If both present, use CLAUDE_AUTH_MODE to choose
  - If neither present, provide clear setup instructions

## 7. Error Handling and User Experience

- [ ] 7.1 Implement authentication error handling
  - Detect expired session tokens
  - Detect invalid API keys
  - Provide actionable error messages
  - Guide users to re-authenticate when needed

- [ ] 7.2 Add authentication status indicators
  - Show current auth mode in verify_config output
  - Display session expiration time (if available)
  - Show authenticated user info
  - Indicate when re-authentication needed

- [ ] 7.3 Implement graceful fallback
  - Try web auth first (if configured)
  - Fall back to API key on web auth failure
  - Log fallback events for debugging
  - Allow user to force specific auth method

## 8. Documentation

- [ ] 8.1 Update README.md
  - Add section: "Authentication Options"
  - Document web authentication setup steps
  - Document API key authentication (existing)
  - Add troubleshooting for auth issues

- [ ] 8.2 Create authentication guide
  - New file: `docs/authentication.md`
  - Detailed web login instructions with screenshots
  - Session token management guide
  - Security best practices
  - FAQ for common auth issues

- [ ] 8.3 Update openspec/project.md
  - Document auth abstraction pattern
  - Update Claude API dependency section
  - Add web auth to tech stack

- [ ] 8.4 Add inline code documentation
  - Comprehensive docstrings for auth classes
  - Examples of using auth abstraction
  - Security warnings for token handling

## 9. Testing

- [ ] 9.1 Unit tests for authentication abstraction
  - Test API key auth adapter
  - Test web auth adapter (with mocked session)
  - Test auth mode detection
  - Test fallback logic
  - Test token expiration handling

- [ ] 9.2 Integration tests
  - Test with real API key (existing)
  - Test with web session token (if available in test environment)
  - Test authentication failures and recovery
  - Test token refresh flow

- [ ] 9.3 Security testing
  - Verify tokens not logged
  - Verify token file permissions
  - Test token sanitization in errors
  - Verify no token leakage in exceptions

- [ ] 9.4 Update existing tests
  - Ensure all tests work with both auth methods
  - Add auth method parameterization to test suites
  - Mock authentication in unit tests

## 10. Validation and Deployment

- [ ] 10.1 Manual testing
  - Test web authentication login flow
  - Test session token refresh
  - Test API key authentication (existing)
  - Test fallback scenarios
  - Test all mise commands with both auth methods

- [ ] 10.2 Security review
  - Review token storage security
  - Review authentication flow for vulnerabilities
  - Review ToS compliance (again)
  - Consider third-party security audit if using in production

- [ ] 10.3 Performance testing
  - Measure auth overhead
  - Test with expired tokens
  - Test under rate limiting
  - Verify no performance degradation vs. API key

- [ ] 10.4 OpenSpec validation
  - Run `openspec validate add-claude-web-auth --strict`
  - Fix any validation errors
  - Ensure all scenarios in spec.md are implemented

## 11. Release Preparation

- [ ] 11.1 Mark as experimental
  - Add EXPERIMENTAL flag to web auth
  - Document in README that web auth is beta
  - Add disclaimer about potential ToS/stability issues

- [ ] 11.2 Create migration guide
  - How to switch from API key to web auth
  - How to switch back if needed
  - Troubleshooting common issues

- [ ] 11.3 Update CHANGELOG.md
  - Document new feature
  - Note experimental status
  - List configuration changes

- [ ] 11.4 Prepare announcement
  - Highlight cost savings for Claude Max users
  - Explain limitations and experimental status
  - Link to documentation

## Notes

- **Security Priority**: Token handling must be secure - this is sensitive credential data
- **User Experience Priority**: Auth failures should provide clear, actionable guidance
- **Stability Priority**: API key auth must continue to work flawlessly regardless of web auth status
- **Legal Priority**: ToS compliance is non-negotiable - must halt if not permitted
