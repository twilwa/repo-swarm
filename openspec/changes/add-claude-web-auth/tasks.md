# Implementation Tasks

## 1. Core Authentication Detection

- [ ] 1.1 Create authentication detection utility
  - Function: `get_claude_authentication() -> dict`
  - Check for OAuth tokens: `CLAUDE_CODE_OAUTH_TOKEN`, `CLAUDE_OAUTH_TOKEN`
  - Check for API key: `ANTHROPIC_API_KEY`
  - Return: `{'method': 'oauth'|'api_key', 'token': str, 'use_cli': bool}`
  - Location: New file `src/investigator/core/auth_detector.py`

- [ ] 1.2 Add authentication validation
  - Validate OAuth token format (`sk-ant-oat01-...`)
  - Validate API key format (`sk-ant-api03-...`)
  - Return clear error messages for invalid tokens
  - Include setup instructions in error messages

## 2. Claude CLI Client Wrapper

- [ ] 2.1 Create ClaudeCLIClient class
  - New file: `src/investigator/core/claude_cli_client.py`
  - Method: `messages_create()` - Compatible with Anthropic SDK interface
  - Use `claude --print --output-format json` for subprocess calls
  - Parse JSON output from CLI
  - Handle errors and timeouts

- [ ] 2.2 Add environment variable handling
  - Set `CLAUDE_CODE_OAUTH_TOKEN` in subprocess environment
  - Set `CLAUDE_USE_SUBSCRIPTION=true` to force subscription mode
  - Remove `ANTHROPIC_API_KEY` from subprocess environment if present
  - Pass through other relevant environment variables

- [ ] 2.3 Implement subprocess management
  - Use `subprocess.run()` with timeout (default 300 seconds)
  - Capture stdout and stderr
  - Handle non-zero exit codes
  - Sanitize OAuth token from error messages

## 3. SDK Client Wrapper (Refactor Existing)

- [ ] 3.1 Create ClaudeSDKClient class
  - New file: `src/investigator/core/claude_sdk_client.py`
  - Wrap existing `Anthropic(api_key=...)` logic
  - Method: `messages_create()` - Same interface as CLI client
  - Migrate existing code from `claude_analyzer.py`

- [ ] 3.2 Maintain backward compatibility
  - Ensure existing API key flow works identically
  - No changes to API call parameters
  - Preserve error handling behavior

## 4. Client Factory

- [ ] 4.1 Create client factory
  - New file: `src/investigator/core/claude_client_factory.py`
  - Function: `create_claude_client() -> ClaudeClient`
  - Use auth detection to choose SDK or CLI client
  - Return unified interface

- [ ] 4.2 Add client interface
  - Define common interface for both clients
  - Method: `messages_create(model, max_tokens, messages) -> Response`
  - Ensure both clients return compatible response objects

## 5. Update Existing Code

- [ ] 5.1 Update ClaudeAnalyzer
  - Modify `src/investigator/core/claude_analyzer.py`
  - Replace direct `Anthropic(api_key=...)` with factory
  - Use `client = create_claude_client()`
  - No changes to `analyze_with_context()` method signature

- [ ] 5.2 Update ClaudeInvestigator
  - Modify `src/investigator/investigator.py:55-58`
  - Remove direct API key parameter passing
  - Let factory handle authentication detection

- [ ] 5.3 Update Temporal activities
  - Modify `src/activities/investigate_activities.py:614-618`
  - Update to use factory instead of direct API key
  - Ensure OAuth token available in worker environment

- [ ] 5.4 Update worker initialization
  - Modify `src/worker.py:42-51`
  - Validate either API key OR OAuth token present
  - Provide clear error message if neither found

## 6. Configuration

- [ ] 6.1 Update environment variables
  - Add to `.env.example`:
    - `CLAUDE_CODE_OAUTH_TOKEN=` (OAuth token from claude setup-token)
    - `CLAUDE_OAUTH_TOKEN=` (alternative OAuth token variable)
  - Document both API key and OAuth options
  - Add comments explaining when to use each

- [ ] 6.2 Update config validation
  - Modify `src/investigator/core/config.py`
  - Add OAuth token format validation
  - Add helpful error messages for authentication issues

## 7. CLI Commands

- [ ] 7.1 Add mise claude-login command
  - Add to `mise.toml`:
    ```toml
    [tasks.claude-login]
    description = "Generate Claude OAuth token for Max subscription"
    run = "claude setup-token"
    ```
  - Add instructions to copy token to .env file

- [ ] 7.2 Add mise claude-status command
  - Add to `mise.toml`:
    ```toml
    [tasks.claude-status]
    description = "Check Claude authentication status"
    run = "python scripts/check_claude_auth.py"
    ```
  - Create `scripts/check_claude_auth.py` to show auth method and status

## 8. Documentation

- [ ] 8.1 Update README.md
  - Add section: "Claude Authentication Options"
  - Document OAuth authentication with Claude Max
  - Document API key authentication
  - Add troubleshooting guide for auth issues

- [ ] 8.2 Update .env.example
  - Add detailed comments for OAuth variables
  - Show example OAuth token format
  - Explain difference between OAuth and API key

- [ ] 8.3 Update openspec/project.md
  - Document authentication abstraction pattern
  - Update Claude API dependency section
  - Add OAuth to tech stack dependencies

## 9. Testing

- [ ] 9.1 Unit tests for CLI client
  - Test subprocess call construction
  - Test JSON parsing from CLI output
  - Test error handling (non-zero exit, timeout)
  - Test OAuth token sanitization in errors
  - Mock subprocess calls

- [ ] 9.2 Unit tests for authentication detection
  - Test OAuth token detection
  - Test API key detection
  - Test priority (OAuth over API key)
  - Test error cases (no credentials)

- [ ] 9.3 Integration tests
  - Test with real API key (existing tests)
  - Test with real OAuth token (if available in CI)
  - Test authentication fallback
  - Test both auth methods produce compatible results

- [ ] 9.4 Update existing tests
  - Ensure tests work with factory pattern
  - Add test fixtures for both auth methods
  - Mock authentication detection in unit tests

## 10. Validation and Deployment

- [ ] 10.1 Manual testing
  - Test with API key (existing flow)
  - Test with OAuth token from `claude setup-token`
  - Test error messages for missing credentials
  - Test authentication status command

- [ ] 10.2 Performance testing
  - Measure CLI subprocess overhead
  - Compare API key (SDK) vs OAuth (CLI) response times
  - Verify no regression for API key users

- [ ] 10.3 Documentation review
  - Verify setup instructions are clear
  - Test authentication flow from scratch
  - Update any missing documentation

- [ ] 10.4 OpenSpec validation
  - Run `openspec validate add-claude-web-auth --strict`
  - Fix any validation errors
  - Ensure all scenarios in spec.md are implemented

## Summary

**Total Tasks**: 40 (simplified from 41 in original proposal)

**Removed Complexity** (from original browser automation approach):

- ❌ No browser automation (playwright, selenium)
- ❌ No session token extraction from browser
- ❌ No custom OAuth flow implementation
- ❌ No token refresh mechanism (1-year tokens)
- ❌ No keychain integration
- ❌ No headless browser support
- ❌ No manual token input fallback

**Key Simplifications**:

- ✅ Use official `claude` CLI (not reverse-engineered)
- ✅ Simple subprocess calls (not complex browser automation)
- ✅ OAuth tokens from `claude setup-token` (not custom flow)
- ✅ 1-year token validity (not complex refresh logic)
- ✅ ToS compliant (official tool, not web scraping)
