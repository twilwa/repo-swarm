# Implementation Tasks

## 1. Core Token Detection and Validation

- [ ] 1.1 Create token type detection utility function
  - Input: GitHub token string
  - Output: Token type enum (CLASSIC, FINE_GRAINED_USER, FINE_GRAINED_PAT, UNKNOWN)
  - Location: New file `src/investigator/core/github_token_utils.py`

- [ ] 1.2 Add token format validation
  - Validate `ghp_*` (classic) - 40 characters after prefix
  - Validate `ghu_*` (fine-grained user) - variable length
  - Validate `github_pat_*` (fine-grained PAT) - variable length
  - Return validation result with detected type

- [ ] 1.3 Update git_manager.py token validation
  - Modify `validate_github_token()` method to detect token type
  - Update validation logic to handle all token types
  - Add token type to return dict for diagnostics

## 2. API Authentication Updates

- [ ] 2.1 Standardize GitHub API authorization headers
  - Update `git_manager.py:448` to use `Bearer` format (works for both types)
  - Update `update_repos.py:176-180` to consistently use `Bearer` format
  - Remove legacy `token` format usage (keep as fallback comment)

- [ ] 2.2 Update git URL authentication
  - Verify both token types work in `https://token@github.com/...` URLs
  - Test with fine-grained token in `_add_authentication()` method
  - Add error handling for permission issues (fine-grained tokens may have limited scopes)

## 3. Configuration and Diagnostics

- [ ] 3.1 Update verify_config.py
  - Add token type detection to diagnostic output
  - Display token type: "classic (ghp*)" or "fine-grained (ghu*/github*pat*)"
  - Add warnings if fine-grained token may have insufficient permissions

- [ ] 3.2 Update environment configuration
  - Add comments in `.env.example` about both token types
  - Document required permissions for fine-grained tokens
  - Add troubleshooting section for permission errors

## 4. Documentation Updates

- [ ] 4.1 Update README.md
  - Add section: "Generating Fine-Grained Personal Access Tokens"
  - Document required permissions: Contents (read), Metadata (read), Workflows (read if analyzing Actions)
  - Add screenshots or detailed steps for GitHub UI
  - Keep existing classic token instructions with note about deprecation

- [ ] 4.2 Update example code
  - Modify `example_private_repo.py` to mention both token types
  - Add example environment variable with fine-grained format

- [ ] 4.3 Update openspec/project.md
  - Update GitHub API dependency documentation
  - Document both token types in configuration section

## 5. Error Handling and User Guidance

- [ ] 5.1 Improve error messages
  - Detect permission errors specific to fine-grained tokens
  - Provide actionable guidance: "Your fine-grained token may not have access to this repository"
  - Link to documentation for permission configuration

- [ ] 5.2 Add permission troubleshooting
  - Detect common issues: token expired, insufficient scopes, repository not selected
  - Create troubleshooting guide in documentation

## 6. Testing

- [ ] 6.1 Unit tests for token detection
  - Test classic token format detection (ghp\_)
  - Test fine-grained user token detection (ghu\_)
  - Test fine-grained PAT detection (github*pat*)
  - Test invalid token format detection
  - Test edge cases: empty string, malformed tokens

- [ ] 6.2 Integration tests with real tokens
  - Test classic PAT with public repository
  - Test fine-grained token with repository access (if available)
  - Test permission error handling with restricted fine-grained token

- [ ] 6.3 Update existing tests
  - Review all tests using mock GitHub tokens
  - Ensure tests don't hardcode `ghp_` format assumptions
  - Add test cases covering both token types

## 7. Validation and Review

- [ ] 7.1 Manual testing with real tokens
  - Test with actual classic PAT
  - Test with actual fine-grained user token
  - Test with actual fine-grained PAT
  - Verify all GitHub operations work: clone, push, API calls

- [ ] 7.2 Security review
  - Ensure tokens are not logged or exposed in error messages
  - Verify existing sanitization works for new token formats
  - Test token leak prevention in logs and exceptions

- [ ] 7.3 Validate openspec compliance
  - Run `openspec validate add-github-fine-grained-token-support --strict`
  - Fix any validation errors
  - Ensure all scenarios in spec.md are implemented

## 8. Deployment Preparation

- [ ] 8.1 Update CHANGELOG.md
  - Document new feature and benefits
  - Note backward compatibility

- [ ] 8.2 Migration guide
  - Create guide for users wanting to switch to fine-grained tokens
  - Document permission requirements
  - Add troubleshooting section

- [ ] 8.3 Communication plan
  - Update user documentation
  - Prepare announcement highlighting security benefits
