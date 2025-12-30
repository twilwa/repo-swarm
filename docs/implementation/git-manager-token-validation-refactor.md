# Refactoring Plan: git_manager.py validate_github_token()

## Executive Summary

**Goal**: Refactor `validate_github_token()` to use new `github_token_utils.py` utilities while maintaining backward compatibility and enhancing diagnostics with token type information.

**Recommended Approach**: **Option C (Hybrid)** - Format validation first, then API call, with enhanced return dict.

## Current State Analysis

### Current Implementation (`git_manager.py:433-474`)

**Method Signature**:

```python
def validate_github_token(self) -> dict
```

**Current Return Structure**:

```python
{
    "status": str,        # 'no_token' | 'valid' | 'invalid' | 'error'
    "message": str,       # Human-readable message
    "user": str,          # Optional: GitHub username (when status='valid')
    "user_info": dict,    # Optional: Full user object from API (when status='valid')
    "status_code": int,   # Optional: HTTP status code (when status='invalid')
    "error": str          # Optional: Error details (when status='error')
}
```

**Current Behavior**:

1. Checks if `self.github_token` exists
2. Makes HTTP request to `https://api.github.com/user` with `Authorization: token {token}` header
3. Returns user info on success (200), error details on failure

**Current Usage**:

- `scripts/verify_config.py:402` - Checks `status == 'valid'`, uses `user` field
- `src/activities/investigate_activities.py:241` - Checks `status == 'valid'`, uses `message` and `user` fields

### New Utility Available (`github_token_utils.py`)

**Functions**:

1. `detect_github_token_type(token: str) -> GitHubTokenType`
   - Returns enum: `CLASSIC`, `FINE_GRAINED_USER`, `FINE_GRAINED_PAT`, `UNKNOWN`
   - Format-only detection (no API call)

2. `validate_github_token(token: str) -> dict`
   - Returns: `{'valid': bool, 'token_type': GitHubTokenType, 'message': str}`
   - Format-only validation (no API call)

## Design Decision: Hybrid Approach (Option C)

### Why Hybrid?

**Benefits**:

1. **Fast failure detection**: Format validation catches typos/obvious errors immediately (no network call)
2. **Real validation**: API call verifies token actually works (not just correct format)
3. **Backward compatibility**: Existing code continues to work unchanged
4. **Enhanced diagnostics**: Adds token type information for troubleshooting
5. **Better error messages**: Can distinguish format errors from API errors

**Trade-offs**:

- Slightly more complex implementation
- Two validation steps (but format check is instant)
- Still requires network call for real validation (as current implementation does)

### Alternative Approaches Considered

**Option A: Keep Both (Format + API)**

- ✅ Fast format check first
- ✅ Real API validation
- ✅ Backward compatible
- ✅ Enhanced diagnostics
- **Selected**: Best balance of features

**Option B: Replace Entirely (Format Only)**

- ❌ Loses real-time validation (can't detect expired tokens)
- ❌ Breaks expectation that method validates token works
- ❌ Callers expect `user` field from API call
- **Rejected**: Too much functionality loss

**Option C: Hybrid (Format + Optional API)**

- ✅ Fast format check
- ✅ Optional real validation
- ✅ Backward compatible (default: API call enabled)
- ✅ Enhanced diagnostics
- **Selected**: Best approach

## Refactoring Plan

### Step 1: Import New Utilities

**Location**: Top of `git_manager.py`

```python
from .github_token_utils import detect_github_token_type, validate_github_token as validate_token_format, GitHubTokenType
```

### Step 2: Refactor Method Implementation

**New Implementation Flow**:

1. **Check token exists** (unchanged)
   - Return `{"status": "no_token", ...}` if missing

2. **Format validation** (NEW)
   - Call `validate_token_format(self.github_token)`
   - If format invalid, return early with enhanced error message
   - Extract `token_type` from validation result

3. **API validation** (ENHANCED)
   - Use `Bearer` header format (works for all token types)
   - Call GitHub API `/user` endpoint
   - Include `token_type` in success response
   - Enhanced error messages for fine-grained token permission issues

4. **Return enhanced dict** (BACKWARD COMPATIBLE)
   - Maintain all existing fields
   - Add new `token_type` field (optional, for diagnostics)

### Step 3: Enhanced Return Structure

**Backward Compatible Return** (all existing fields preserved):

```python
{
    # Existing fields (unchanged)
    "status": str,           # 'no_token' | 'valid' | 'invalid' | 'error'
    "message": str,          # Human-readable message
    "user": str,             # Optional: GitHub username (when status='valid')
    "user_info": dict,       # Optional: Full user object (when status='valid')
    "status_code": int,      # Optional: HTTP status code (when status='invalid')
    "error": str,            # Optional: Error details (when status='error')

    # New fields (additive, optional)
    "token_type": str,       # Optional: 'CLASSIC' | 'FINE_GRAINED_USER' | 'FINE_GRAINED_PAT' | 'UNKNOWN'
    "format_valid": bool      # Optional: True if format validation passed
}
```

### Step 4: Error Message Enhancements

**Format Validation Errors**:

- Include detected token type (even if invalid)
- Provide specific guidance: "CLASSIC tokens must have exactly 40 characters after prefix"

**API Validation Errors**:

- Detect fine-grained token permission issues (403 Forbidden)
- Enhanced messages: "Fine-grained token may not have access to this repository"
- Include token type in error context

**Example Enhanced Messages**:

```python
# Format error
{
    "status": "invalid",
    "message": "GitHub token format invalid: CLASSIC tokens must have exactly 40 characters after prefix (ghp_)",
    "token_type": "UNKNOWN",
    "format_valid": False
}

# API error with token type
{
    "status": "invalid",
    "message": "GitHub token validation failed: HTTP 403. Fine-grained token may not have required permissions.",
    "token_type": "FINE_GRAINED_PAT",
    "status_code": 403,
    "format_valid": True
}

# Success with token type
{
    "status": "valid",
    "message": "GitHub token authenticated as user: octocat (CLASSIC token)",
    "user": "octocat",
    "user_info": {...},
    "token_type": "CLASSIC",
    "format_valid": True
}
```

### Step 5: Update Authorization Header

**Current**: `Authorization: token {token}` (legacy format)
**New**: `Authorization: Bearer {token}` (standard format, works for all token types)

**Rationale**:

- Spec requirement: "SHALL authenticate using Bearer authorization header for all token types"
- Both formats work, but Bearer is standard and future-proof

## Implementation Details

### Code Structure

```python
def validate_github_token(self) -> dict:
    """
    Validate the GitHub token and return user information.

    Performs format validation first (fast), then API validation (real-time check).
    Returns token type information for diagnostics.

    Returns:
        Dictionary with validation status, user info, and token type:
        {
            "status": "no_token" | "valid" | "invalid" | "error",
            "message": str,
            "user": str (optional),
            "user_info": dict (optional),
            "token_type": str (optional),  # NEW: Token type for diagnostics
            "format_valid": bool (optional),  # NEW: Format validation result
            "status_code": int (optional),
            "error": str (optional)
        }
    """
    # Step 1: Check token exists
    if not self.github_token:
        return {
            "status": "no_token",
            "message": "No GitHub token found in environment"
        }

    # Step 2: Format validation (fast, catches obvious errors)
    format_result = validate_token_format(self.github_token)
    token_type = format_result['token_type']

    if not format_result['valid']:
        return {
            "status": "invalid",
            "message": f"GitHub token format invalid: {format_result['message']}",
            "token_type": token_type.value if isinstance(token_type, GitHubTokenType) else str(token_type),
            "format_valid": False
        }

    # Step 3: API validation (real-time check)
    try:
        import requests
        headers = {
            'Authorization': f'Bearer {self.github_token}',  # Updated to Bearer format
            'Accept': 'application/vnd.github.v3+json'
        }
        response = requests.get('https://api.github.com/user', headers=headers, timeout=10)

        if response.status_code == 200:
            user_info = response.json()
            token_type_str = token_type.value if isinstance(token_type, GitHubTokenType) else str(token_type)
            return {
                "status": "valid",
                "message": f"GitHub token authenticated as user: {user_info.get('login', 'unknown')} ({token_type_str} token)",
                "user": user_info.get('login', 'unknown'),
                "user_info": user_info,
                "token_type": token_type_str,  # NEW: Include token type
                "format_valid": True  # NEW: Format validation passed
            }
        elif response.status_code == 403:
            # Fine-grained token permission issue
            token_type_str = token_type.value if isinstance(token_type, GitHubTokenType) else str(token_type)
            return {
                "status": "invalid",
                "message": f"GitHub token validation failed: HTTP 403. {token_type_str} token may not have required permissions.",
                "token_type": token_type_str,
                "status_code": 403,
                "format_valid": True
            }
        else:
            token_type_str = token_type.value if isinstance(token_type, GitHubTokenType) else str(token_type)
            return {
                "status": "invalid",
                "message": f"GitHub token validation failed: HTTP {response.status_code}",
                "token_type": token_type_str,
                "status_code": response.status_code,
                "format_valid": True
            }

    except Exception as e:
        token_type_str = token_type.value if isinstance(token_type, GitHubTokenType) else str(token_type)
        return {
            "status": "error",
            "message": f"Could not validate GitHub token: {str(e)}",
            "token_type": token_type_str,
            "error": str(e),
            "format_valid": True
        }
```

## Backward Compatibility Analysis

### Existing Callers

**1. `scripts/verify_config.py:402`**

```python
token_result = self.git_manager.validate_github_token()
if token_result['status'] == 'valid':
    self._add_success(f"GitHub token valid for user: {token_result['user']}")
```

✅ **Compatible**: Uses `status` and `user` fields (both preserved)

**2. `src/activities/investigate_activities.py:241`**

```python
token_validation = git_manager.validate_github_token()
if token_validation["status"] == "valid":
    activity.logger.info(token_validation["message"])
    user_info = token_validation.get("user", "unknown")
```

✅ **Compatible**: Uses `status`, `message`, and `user` fields (all preserved)

### Breaking Changes

**None**: All existing fields preserved, new fields are additive and optional.

### Migration Required

**None**: Existing code continues to work without changes.

## Testing Strategy

### Unit Tests

1. **Format validation integration**
   - Test with invalid format tokens (should return early)
   - Test with valid format tokens (should proceed to API call)

2. **Token type detection**
   - Test CLASSIC token detection and inclusion in response
   - Test FINE_GRAINED_USER token detection
   - Test FINE_GRAINED_PAT token detection

3. **API validation**
   - Mock successful API response (200)
   - Mock permission error (403) with fine-grained token
   - Mock invalid token (401)
   - Mock network error

4. **Backward compatibility**
   - Verify existing return structure preserved
   - Verify new fields are optional (don't break existing code)

### Integration Tests

1. **Real token validation**
   - Test with actual classic PAT
   - Test with actual fine-grained token (if available)
   - Verify token type appears in response

2. **Error scenarios**
   - Test with expired token
   - Test with token without permissions
   - Test with malformed token

## Implementation Checklist

- [ ] Add import for `github_token_utils`
- [ ] Refactor `validate_github_token()` method
  - [ ] Add format validation step
  - [ ] Update authorization header to `Bearer` format
  - [ ] Add token type to return dict
  - [ ] Enhance error messages with token type
  - [ ] Add fine-grained token permission detection (403 handling)
- [ ] Update docstring with new return fields
- [ ] Write unit tests
  - [ ] Format validation integration
  - [ ] Token type detection
  - [ ] API validation scenarios
  - [ ] Backward compatibility
- [ ] Write integration tests
  - [ ] Real token validation
  - [ ] Error scenarios
- [ ] Update callers (if needed for enhanced diagnostics)
  - [ ] `verify_config.py` - Display token type in output
  - [ ] `investigate_activities.py` - Log token type in messages
- [ ] Verify backward compatibility
  - [ ] Run existing tests
  - [ ] Manual testing with existing code

## Open Questions

1. **Authorization Header Format**: Should we keep `token` format as fallback, or fully migrate to `Bearer`?
   - **Decision**: Migrate to `Bearer` (spec requirement, works for all token types)

2. **Error Message Detail**: How detailed should format error messages be?
   - **Decision**: Include specific guidance (e.g., "CLASSIC tokens must have exactly 40 characters")

3. **Token Type Display**: Should token type be included in success messages?
   - **Decision**: Yes, for diagnostics (e.g., "authenticated as user: octocat (CLASSIC token)")

## References

- Spec: `openspec/changes/add-github-fine-grained-token-support/specs/github-authentication/spec.md`
- Task: `openspec/changes/add-github-fine-grained-token-support/tasks.md` (Task 1.3)
- Current Implementation: `src/investigator/core/git_manager.py:433-474`
- New Utility: `src/investigator/core/github_token_utils.py`
