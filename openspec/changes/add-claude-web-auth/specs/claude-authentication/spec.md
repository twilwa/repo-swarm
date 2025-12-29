## ADDED Requirements

### Requirement: Authentication Method Abstraction

The system SHALL provide an abstract authentication interface supporting multiple Claude authentication methods.

#### Scenario: API Key Authentication Adapter

- **GIVEN** a valid Anthropic API key
- **WHEN** authentication is initialized with API key
- **THEN** an API key authentication adapter is created
- **AND** the adapter provides an authenticated Anthropic client
- **AND** the adapter reports authentication status as valid

#### Scenario: Web Session Authentication Adapter

- **GIVEN** a valid Claude web session token
- **WHEN** authentication is initialized with web session
- **THEN** a web authentication adapter is created
- **AND** the adapter provides an authenticated Anthropic client
- **AND** the adapter reports authentication status as valid

#### Scenario: Authentication Method Selection by Environment

- **GIVEN** environment variable `CLAUDE_AUTH_MODE` is set to "api_key"
- **WHEN** authentication is initialized
- **THEN** API key authentication method is used
- **AND** web session authentication is not attempted

### Requirement: Authentication Mode Auto-Detection

The system SHALL automatically detect and select the appropriate authentication method based on available credentials.

#### Scenario: Auto-Detect API Key

- **GIVEN** `ANTHROPIC_API_KEY` is set in environment
- **AND** `CLAUDE_SESSION_TOKEN` is not set
- **AND** `CLAUDE_AUTH_MODE` is not explicitly set
- **WHEN** authentication is initialized
- **THEN** API key authentication method is automatically selected
- **AND** authentication succeeds

#### Scenario: Auto-Detect Web Session

- **GIVEN** `CLAUDE_SESSION_TOKEN` is set in environment
- **AND** `ANTHROPIC_API_KEY` is not set
- **AND** `CLAUDE_AUTH_MODE` is not explicitly set
- **WHEN** authentication is initialized
- **THEN** web session authentication method is automatically selected
- **AND** authentication succeeds

#### Scenario: Both Credentials Available - Default to API Key

- **GIVEN** both `ANTHROPIC_API_KEY` and `CLAUDE_SESSION_TOKEN` are set
- **AND** `CLAUDE_AUTH_MODE` is not explicitly set
- **WHEN** authentication is initialized
- **THEN** API key authentication method is selected by default
- **AND** web session is not used

#### Scenario: No Credentials Available

- **GIVEN** neither `ANTHROPIC_API_KEY` nor `CLAUDE_SESSION_TOKEN` are set
- **WHEN** authentication is initialized
- **THEN** initialization fails with clear error message
- **AND** error message provides setup instructions for both auth methods
- **AND** links to documentation for API key and web authentication

### Requirement: Browser-Based Authentication Flow

The system SHALL provide browser-based authentication for obtaining Claude web session tokens.

#### Scenario: Interactive Browser Login

- **GIVEN** user runs `mise claude-login` command
- **WHEN** command is executed
- **THEN** browser window opens to claude.ai login page
- **AND** system waits for user to complete login
- **AND** once authenticated, session token is extracted from browser
- **AND** session token is saved to environment/keychain
- **AND** success message displays with instructions to set CLAUDE_SESSION_TOKEN

#### Scenario: Headless Browser Login

- **GIVEN** user runs `mise claude-login --headless` command
- **WHEN** command is executed in headless environment
- **THEN** headless browser is launched
- **AND** login URL is displayed to user for manual authentication in separate browser
- **AND** system waits for authentication completion
- **AND** session token is extracted when available
- **AND** token is saved and displayed to user

#### Scenario: Browser Authentication Timeout

- **GIVEN** user runs `mise claude-login` command
- **AND** user does not complete login within 5 minutes
- **WHEN** timeout period elapses
- **THEN** browser is closed
- **AND** error message indicates authentication timeout
- **AND** user is prompted to retry with `mise claude-login`

#### Scenario: Browser Authentication Failure

- **GIVEN** user runs `mise claude-login` command
- **WHEN** browser automation fails (missing playwright, browser crash, etc.)
- **THEN** system falls back to manual token input mode
- **AND** user is prompted to manually obtain session token
- **AND** instructions provided for extracting token from browser cookies
- **AND** user can paste token directly into prompt

### Requirement: Session Token Management

The system SHALL securely store, retrieve, and manage Claude web session tokens.

#### Scenario: Session Token Storage in Environment

- **GIVEN** a valid session token is obtained from browser authentication
- **WHEN** token is saved
- **THEN** token is stored in `CLAUDE_SESSION_TOKEN` environment variable
- **AND** user is instructed to add token to .env file for persistence
- **AND** token is not logged or displayed in console output (truncated for security)

#### Scenario: Session Token Retrieval

- **GIVEN** `CLAUDE_SESSION_TOKEN` is set in environment
- **WHEN** web authentication adapter is initialized
- **THEN** token is retrieved from environment variable
- **AND** token is validated before use
- **AND** if validation fails, error is raised with re-authentication instructions

#### Scenario: Session Token Expiration Detection

- **GIVEN** a session token is stored
- **WHEN** token is used for API call
- **AND** token has expired
- **THEN** API call fails with authentication error
- **AND** system detects expiration
- **AND** user is prompted to re-authenticate with `mise claude-login`

#### Scenario: Session Token Logout

- **GIVEN** user runs `mise claude-logout` command
- **WHEN** command is executed
- **THEN** session token is removed from storage
- **AND** environment variable is cleared
- **AND** confirmation message indicates logout success

### Requirement: Session Token Refresh

The system SHALL attempt to refresh expired session tokens automatically before failing.

#### Scenario: Automatic Token Refresh Success

- **GIVEN** a session token is about to expire or has expired
- **AND** a refresh token is available
- **WHEN** API call is attempted
- **THEN** system detects token expiration
- **AND** automatically refreshes token using refresh token
- **AND** new token is saved to storage
- **AND** API call proceeds with new token
- **AND** operation completes without user intervention

#### Scenario: Automatic Token Refresh Failure

- **GIVEN** a session token has expired
- **AND** no refresh token is available OR refresh fails
- **WHEN** API call is attempted
- **THEN** system attempts token refresh
- **AND** refresh fails
- **AND** operation is aborted with clear error message
- **AND** user is instructed to run `mise claude-login` to re-authenticate

#### Scenario: Proactive Token Validation

- **GIVEN** web authentication is active
- **WHEN** starting a long-running workflow
- **THEN** system checks token validity before workflow starts
- **AND** if token will expire during workflow, warning is displayed
- **AND** user is offered option to refresh token before proceeding

### Requirement: Authentication Status and Diagnostics

The system SHALL provide clear visibility into current authentication method and status.

#### Scenario: Authentication Status Check

- **GIVEN** user runs `mise claude-status` command
- **WHEN** command is executed
- **THEN** current authentication method is displayed (API key or Web session)
- **AND** authentication validity is checked
- **AND** if web session: token expiration time is shown (if available)
- **AND** if API key: API key format and prefix are validated
- **AND** authenticated user info is displayed (username, email if available)

#### Scenario: Authentication Diagnostics in verify_config

- **GIVEN** user runs `mise verify-config` command
- **WHEN** configuration validation is performed
- **THEN** authentication method is detected and displayed
- **AND** authentication credentials are validated
- **AND** for web auth: session token validity and expiration are checked
- **AND** for API key: API access is verified with test call
- **AND** overall authentication status (PASS/FAIL) is reported

#### Scenario: Authentication Mode in Logs

- **GIVEN** any workflow or analysis is started
- **WHEN** logging is initialized
- **THEN** authentication method is logged (without sensitive credentials)
- **AND** log entry: "Using Claude authentication: [API Key | Web Session]"
- **AND** no tokens or API keys are included in log output

### Requirement: Graceful Authentication Fallback

The system SHALL attempt fallback authentication methods when primary method fails.

#### Scenario: Web Auth Fails, Fall Back to API Key

- **GIVEN** `CLAUDE_AUTH_MODE` is not set (auto mode)
- **AND** both `CLAUDE_SESSION_TOKEN` and `ANTHROPIC_API_KEY` are set
- **AND** web session token is invalid or expired
- **WHEN** authentication is initialized
- **THEN** web authentication is attempted first
- **AND** web authentication fails
- **AND** system falls back to API key authentication
- **AND** fallback is logged with warning
- **AND** operation continues successfully with API key

#### Scenario: API Key Fails, Fall Back to Web Session

- **GIVEN** `CLAUDE_AUTH_MODE` is not set (auto mode)
- **AND** both `ANTHROPIC_API_KEY` and `CLAUDE_SESSION_TOKEN` are set
- **AND** API key is invalid
- **WHEN** authentication is initialized with API key attempted first
- **AND** API key authentication fails
- **THEN** system falls back to web session authentication
- **AND** fallback is logged with warning
- **AND** operation continues successfully with web session

#### Scenario: All Authentication Methods Fail

- **GIVEN** both `ANTHROPIC_API_KEY` and `CLAUDE_SESSION_TOKEN` are set
- **AND** both credentials are invalid
- **WHEN** authentication is initialized
- **THEN** both authentication methods are attempted
- **AND** both fail
- **AND** error message lists all failed methods
- **AND** user is provided with remediation steps for each method
- **AND** operation is aborted

### Requirement: Security and Token Protection

The system SHALL protect authentication credentials from exposure in logs, error messages, and storage.

#### Scenario: Session Token Sanitization in Logs

- **GIVEN** web authentication is active
- **WHEN** any operation is logged
- **THEN** session token is not included in log output
- **AND** token is replaced with `***HIDDEN***` or `[REDACTED]` if referenced
- **AND** only token prefix (first 8 characters) may be shown for diagnostics

#### Scenario: Session Token Sanitization in Errors

- **GIVEN** an error occurs during web authentication
- **WHEN** error message is generated
- **THEN** error message does not contain raw session token
- **AND** token is sanitized or omitted
- **AND** error remains actionable without token exposure

#### Scenario: Secure Token File Permissions

- **GIVEN** session token is saved to file (future enhancement)
- **WHEN** file is created
- **THEN** file permissions are set to 0600 (read/write for owner only)
- **AND** file is created in user's home directory or secure location
- **AND** file location is not world-readable

#### Scenario: Token Validation Before Storage

- **GIVEN** a session token is obtained from browser
- **WHEN** token is about to be saved
- **THEN** token is validated with test API call
- **AND** only valid tokens are saved to storage
- **AND** invalid tokens trigger re-authentication prompt

### Requirement: Authentication Error Handling

The system SHALL provide clear, actionable error messages for authentication failures.

#### Scenario: Expired Session Token Error

- **GIVEN** web session token has expired
- **WHEN** API call is attempted
- **THEN** authentication error is raised
- **AND** error message clearly states "Your Claude session has expired"
- **AND** provides re-authentication command: `mise claude-login`
- **AND** suggests alternative: "Or use API key by setting ANTHROPIC_API_KEY"

#### Scenario: Invalid API Key Error

- **GIVEN** API key is invalid or malformed
- **WHEN** authentication is initialized
- **THEN** validation fails
- **AND** error message states "Invalid Anthropic API key"
- **AND** provides instructions to obtain valid API key
- **AND** links to Anthropic API key generation page

#### Scenario: Network Error During Authentication

- **GIVEN** network connectivity is unavailable
- **WHEN** authentication validation is attempted
- **THEN** network error is detected
- **AND** error message indicates "Cannot reach Anthropic API - check network connection"
- **AND** suggests retrying after network is restored
- **AND** does not fail permanently (allows retry)

#### Scenario: Browser Automation Unavailable

- **GIVEN** playwright is not installed or browser cannot launch
- **WHEN** `mise claude-login` is executed
- **THEN** browser automation fails
- **AND** system detects automation failure
- **AND** falls back to manual token input mode
- **AND** provides instructions for manually obtaining token from browser

### Requirement: Backward Compatibility with API Key Authentication

The system SHALL maintain full backward compatibility with existing API key authentication workflows.

#### Scenario: Existing API Key Configuration Unchanged

- **GIVEN** an existing configuration using `ANTHROPIC_API_KEY`
- **AND** web authentication feature is deployed
- **WHEN** any operation is executed
- **THEN** API key authentication continues to work exactly as before
- **AND** no configuration changes are required
- **AND** no new environment variables are needed
- **AND** behavior is identical to pre-web-auth implementation

#### Scenario: API Key as Default Authentication

- **GIVEN** no explicit `CLAUDE_AUTH_MODE` is set
- **AND** `ANTHROPIC_API_KEY` is provided
- **WHEN** authentication is initialized
- **THEN** API key authentication is used
- **AND** web authentication is not attempted
- **AND** this is documented as default behavior

#### Scenario: No Impact on API-Only Users

- **GIVEN** a user who only uses API key authentication
- **AND** web authentication feature is deployed
- **WHEN** any workflow is executed
- **THEN** no browser dependencies are loaded
- **AND** no web auth code is executed
- **AND** performance is identical to pre-web-auth implementation
- **AND** no additional logs or warnings appear

### Requirement: Documentation for Multiple Authentication Methods

The system documentation SHALL provide comprehensive setup and troubleshooting instructions for all authentication methods.

#### Scenario: Web Authentication Setup Guide

- **GIVEN** a user reading the documentation
- **WHEN** they want to set up web authentication
- **THEN** documentation includes step-by-step browser authentication guide
- **AND** explains how to run `mise claude-login`
- **AND** shows how to set `CLAUDE_SESSION_TOKEN` in environment
- **AND** documents token expiration and refresh behavior
- **AND** includes troubleshooting for common browser auth issues

#### Scenario: API Key Setup Guide

- **GIVEN** a user reading the documentation
- **WHEN** they want to set up API key authentication
- **THEN** documentation includes instructions for obtaining Anthropic API key
- **AND** explains how to set `ANTHROPIC_API_KEY` in environment
- **AND** notes that API key is more stable than web session
- **AND** recommends API key for CI/CD and production environments

#### Scenario: Authentication Method Comparison

- **GIVEN** a user reading the documentation
- **WHEN** they need to choose an authentication method
- **THEN** documentation provides comparison table of methods
- **AND** lists pros/cons of API key vs. web session
- **AND** provides recommendations based on use case (personal vs. production)
- **AND** explains when to use each method

#### Scenario: Troubleshooting Authentication Failures

- **GIVEN** a user experiencing authentication issues
- **WHEN** they consult troubleshooting documentation
- **THEN** documentation covers common errors for both methods
- **AND** provides specific solutions for "session expired", "invalid API key", "browser automation failed"
- **AND** includes commands to check authentication status
- **AND** explains how to switch between authentication methods
