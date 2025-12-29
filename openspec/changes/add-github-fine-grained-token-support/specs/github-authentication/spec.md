## ADDED Requirements

### Requirement: Token Type Detection

The system SHALL automatically detect GitHub token type based on token prefix without requiring user configuration.

#### Scenario: Classic PAT Detection

- **GIVEN** a GitHub token starting with `ghp_`
- **WHEN** the system validates the token
- **THEN** the token is classified as CLASSIC type
- **AND** appropriate validation logic is applied

#### Scenario: Fine-Grained User Token Detection

- **GIVEN** a GitHub token starting with `ghu_`
- **WHEN** the system validates the token
- **THEN** the token is classified as FINE_GRAINED_USER type
- **AND** appropriate validation logic is applied

#### Scenario: Fine-Grained PAT Detection

- **GIVEN** a GitHub token starting with `github_pat_`
- **WHEN** the system validates the token
- **THEN** the token is classified as FINE_GRAINED_PAT type
- **AND** appropriate validation logic is applied

#### Scenario: Unknown Token Format

- **GIVEN** a GitHub token with an unrecognized prefix
- **WHEN** the system validates the token
- **THEN** the token is classified as UNKNOWN type
- **AND** a warning is logged indicating unrecognized format
- **AND** validation attempts to proceed with default authentication

### Requirement: Token Format Validation

The system SHALL validate GitHub token format for all supported token types.

#### Scenario: Valid Classic Token Format

- **GIVEN** a classic token with prefix `ghp_` and 40 characters after prefix
- **WHEN** format validation is performed
- **THEN** the token is marked as valid
- **AND** token type is set to CLASSIC

#### Scenario: Valid Fine-Grained Token Format

- **GIVEN** a fine-grained token with prefix `ghu_` or `github_pat_` followed by valid characters
- **WHEN** format validation is performed
- **THEN** the token is marked as valid
- **AND** token type is set appropriately (FINE_GRAINED_USER or FINE_GRAINED_PAT)

#### Scenario: Invalid Token Format

- **GIVEN** a malformed token (empty string, wrong prefix, invalid characters)
- **WHEN** format validation is performed
- **THEN** the token is marked as invalid
- **AND** an error message describes the format issue

### Requirement: GitHub API Authentication

The system SHALL authenticate to GitHub REST API using Bearer authorization header for all token types.

#### Scenario: API Authentication with Classic Token

- **GIVEN** a valid classic token (ghp\_)
- **WHEN** making GitHub API requests
- **THEN** the request includes header `Authorization: Bearer {token}`
- **AND** the API call succeeds with proper authentication

#### Scenario: API Authentication with Fine-Grained Token

- **GIVEN** a valid fine-grained token (ghu* or github_pat*)
- **WHEN** making GitHub API requests
- **THEN** the request includes header `Authorization: Bearer {token}`
- **AND** the API call succeeds with proper authentication

#### Scenario: API Authentication Failure

- **GIVEN** an invalid or expired token
- **WHEN** making GitHub API requests
- **THEN** the API returns 401 Unauthorized
- **AND** the system provides an actionable error message
- **AND** the error message suggests checking token validity and expiration

### Requirement: Git URL Authentication

The system SHALL embed GitHub tokens in HTTPS URLs for git operations (clone, fetch, push) for all token types.

#### Scenario: Git Clone with Classic Token

- **GIVEN** a valid classic token and a GitHub repository URL
- **WHEN** performing git clone operation
- **THEN** the URL is modified to `https://{token}@github.com/{owner}/{repo}`
- **AND** the clone operation succeeds

#### Scenario: Git Clone with Fine-Grained Token

- **GIVEN** a valid fine-grained token with repository access and a GitHub repository URL
- **WHEN** performing git clone operation
- **THEN** the URL is modified to `https://{token}@github.com/{owner}/{repo}`
- **AND** the clone operation succeeds

#### Scenario: Git Push with Insufficient Permissions

- **GIVEN** a fine-grained token without push permissions
- **WHEN** attempting git push operation
- **THEN** git returns permission denied error
- **AND** the system detects fine-grained token type
- **AND** the error message suggests checking token repository permissions

### Requirement: Token Validation and Diagnostics

The system SHALL validate GitHub tokens by calling GitHub API and provide diagnostic information about token type and status.

#### Scenario: Successful Token Validation

- **GIVEN** a valid GitHub token (any type)
- **WHEN** running token validation
- **THEN** the system calls GitHub API `/user` endpoint
- **AND** returns success status with user information
- **AND** includes detected token type in response
- **AND** indicates token format validation passed

#### Scenario: Token Validation with Insufficient Scopes

- **GIVEN** a fine-grained token without required permissions
- **WHEN** running token validation
- **THEN** the system detects 403 Forbidden responses from GitHub API
- **AND** provides error message specific to fine-grained tokens
- **AND** suggests required permissions: Contents (read), Metadata (read)
- **AND** includes link to GitHub token settings

#### Scenario: Expired Token Detection

- **GIVEN** an expired fine-grained token
- **WHEN** running token validation
- **THEN** GitHub API returns 401 Unauthorized
- **AND** error message indicates token may be expired
- **AND** suggests regenerating token

### Requirement: Repository Permission Verification

The system SHALL check GitHub token permissions for specific repositories and provide clear feedback for fine-grained token permission issues.

#### Scenario: Repository Access Check with Full Permissions

- **GIVEN** a GitHub token with push and admin permissions for a repository
- **WHEN** checking repository permissions
- **THEN** the system calls GitHub API `/repos/{owner}/{repo}` endpoint
- **AND** returns permissions object with push: true, admin: true
- **AND** confirms sufficient permissions for all operations

#### Scenario: Fine-Grained Token with Read-Only Access

- **GIVEN** a fine-grained token with only read access to a repository
- **WHEN** checking repository permissions
- **THEN** the system returns permissions object with push: false
- **AND** provides warning that push operations will fail
- **AND** suggests updating token permissions for write access

#### Scenario: Fine-Grained Token Without Repository Access

- **GIVEN** a fine-grained token that does not include a specific repository
- **WHEN** checking repository permissions
- **THEN** GitHub API returns 404 Not Found
- **AND** the system detects fine-grained token type
- **AND** provides error message: "Your fine-grained token does not have access to this repository"
- **AND** suggests adding repository to token's repository access list

### Requirement: Token Security and Sanitization

The system SHALL prevent GitHub tokens from being exposed in logs, error messages, or console output for all token types.

#### Scenario: Token Sanitization in Logs

- **GIVEN** a git operation using authenticated URL with any token type
- **WHEN** the operation is logged or printed
- **THEN** the token is replaced with `***HIDDEN***`
- **AND** the URL structure is preserved: `https://***HIDDEN***@github.com/{owner}/{repo}`

#### Scenario: Token Sanitization in Error Messages

- **GIVEN** a git operation fails with token in URL
- **WHEN** error message is generated
- **THEN** the error message does not contain the raw token
- **AND** the token is replaced with `***HIDDEN***` or completely removed
- **AND** the error remains actionable without token exposure

#### Scenario: Token Presence Indication

- **GIVEN** configuration verification is run
- **WHEN** displaying token status
- **THEN** system indicates "GitHub token found in environment"
- **AND** displays detected token type (Classic, Fine-grained User, Fine-grained PAT)
- **AND** does NOT display the raw token value

### Requirement: Documentation for Token Types

The system documentation SHALL provide clear instructions for generating and configuring both classic and fine-grained GitHub tokens.

#### Scenario: Fine-Grained Token Setup Instructions

- **GIVEN** a user reading the documentation
- **WHEN** they need to generate a fine-grained token
- **THEN** documentation includes step-by-step instructions for creating fine-grained token
- **AND** specifies required permissions: Contents (read), Metadata (read)
- **AND** explains repository selection in token configuration
- **AND** notes that fine-grained tokens expire (max 1 year)

#### Scenario: Classic Token Setup Instructions

- **GIVEN** a user reading the documentation
- **WHEN** they need to generate a classic token
- **THEN** documentation includes step-by-step instructions for creating classic token
- **AND** specifies required scope: `repo`
- **AND** notes that classic tokens provide broader access than fine-grained
- **AND** mentions GitHub recommendation to prefer fine-grained tokens

#### Scenario: Token Troubleshooting Guide

- **GIVEN** a user experiencing token permission errors
- **WHEN** they consult troubleshooting documentation
- **THEN** documentation covers common fine-grained token issues
- **AND** includes solutions for "repository not found" (add repo to token)
- **AND** includes solutions for "permission denied on push" (grant push permission)
- **AND** includes solutions for "token expired" (regenerate token)

### Requirement: Backward Compatibility

The system SHALL maintain full backward compatibility with existing classic token configurations and workflows.

#### Scenario: Existing Classic Token Continues Working

- **GIVEN** an existing configuration using classic token (ghp\_)
- **WHEN** the fine-grained token support is deployed
- **THEN** all existing operations continue to function unchanged
- **AND** no configuration updates are required
- **AND** no user action is needed

#### Scenario: Environment Variable Unchanged

- **GIVEN** the GITHUB_TOKEN environment variable is set
- **WHEN** the fine-grained token support is deployed
- **THEN** the same environment variable works for all token types
- **AND** no new environment variables are required
- **AND** token type is detected automatically

#### Scenario: No API Breaking Changes

- **GIVEN** code using GitRepositoryManager class
- **WHEN** the fine-grained token support is deployed
- **THEN** all existing method signatures remain unchanged
- **AND** all existing method behaviors remain unchanged for classic tokens
- **AND** no code changes are required in calling code
