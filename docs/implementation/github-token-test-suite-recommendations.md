# GitHub Token Test Suite - Actionable Recommendations

**Quick Reference**: Priority-ordered recommendations for achieving 100% backward compatibility test coverage.

## Priority 1: Critical Gaps (Must Fix)

### 1.1 Expand Parameterized Tests in `test_update_repos_auth.py`

**Issue**: Two parameterized tests don't cover all three token types.

**File**: `tests/unit/test_update_repos_auth.py`

**Current State**:

```python
# Test 1: Missing FINE_GRAINED_PAT
@pytest.mark.parametrize("token,expected_header", [
    ("ghp_" + "a" * 40, "token ghp_" + "a" * 40),
    ("ghu_" + "a" * 15, "Bearer ghu_" + "a" * 15),
])

# Test 2: Missing FINE_GRAINED_USER
@pytest.mark.parametrize("token,expected_header", [
    ("ghp_" + "a" * 40, "token ghp_" + "a" * 40),
    ("github_pat_" + "a" * 25, "Bearer github_pat_" + "a" * 25),
])
```

**Fix**: Add missing token types to both tests:

```python
@pytest.mark.parametrize("token,expected_header", [
    ("ghp_" + "a" * 40, "token ghp_" + "a" * 40),
    ("ghu_" + "a" * 15, "Bearer ghu_" + "a" * 15),
    ("github_pat_" + "a" * 25, "Bearer github_pat_" + "a" * 25),  # ADD THIS
])
```

**Impact**: Ensures auth header selection works for all token types.

---

### 1.2 Add Missing Bearer Auth Test for Fine-Grained PAT

**Issue**: `test_git_manager.py` tests Bearer auth for fine-grained user tokens but not for fine-grained PAT tokens.

**File**: `tests/unit/test_git_manager.py`

**Current State**: Has `test_bearer_format_in_api_call()` for FINE_GRAINED_USER, but no equivalent for FINE_GRAINED_PAT.

**Fix**: Add new test:

```python
def test_fine_grained_pat_token_format_in_api_call(self, git_manager):
    """Test that API call uses Bearer format for fine-grained PAT tokens."""
    valid_pat_token = "github_pat_" + "a" * 25
    git_manager.github_token = valid_pat_token

    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"login": "testuser"}
        mock_get.return_value = mock_response

        git_manager.validate_github_token()

        call_args = mock_get.call_args
        headers = call_args.kwargs.get("headers") or call_args[1].get("headers")

        auth_header = headers.get("Authorization", "")
        assert auth_header == f"Bearer {valid_pat_token}"
```

**Impact**: Verifies fine-grained PAT tokens use Bearer auth (not token auth).

---

### 1.3 Complete Incomplete Test

**Issue**: `test_token_type_detection_priority()` has empty body.

**File**: `tests/unit/test_git_manager.py:258`

**Current State**:

```python
def test_token_type_detection_priority(self, git_manager):
    """Test that github_pat_ prefix has priority over ghu_."""
    # This tests the priority of token detection
    # EMPTY BODY
```

**Fix**: Implement test:

```python
def test_token_type_detection_priority(self, git_manager):
    """Test that github_pat_ prefix has priority over ghu_."""
    # Token that starts with github_pat_ should be detected as FINE_GRAINED_PAT
    # even if it contains ghu_ substring
    token = "github_pat_ghu_something12345"
    git_manager.github_token = token

    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"login": "testuser"}
        mock_get.return_value = mock_response

        result = git_manager.validate_github_token()

    assert result["token_type"] == GitHubTokenType.FINE_GRAINED_PAT
```

**Impact**: Ensures token detection priority is correct (github*pat* > ghu* > ghp*).

---

## Priority 2: Enhancements (Should Fix)

### 2.1 Add Missing Token Constant

**Issue**: `test_github_diagnostics.py` only defines CLASSIC and FINE_GRAINED_PAT constants.

**File**: `tests/unit/test_github_diagnostics.py:16-17`

**Current State**:

```python
VALID_CLASSIC_TOKEN = "ghp_" + "a" * 40
VALID_FINEGRAINED_TOKEN = "github_pat_" + "a" * 30  # Only PAT, missing USER
```

**Fix**: Add missing constant:

```python
VALID_CLASSIC_TOKEN = "ghp_" + "a" * 40
VALID_FINEGRAINED_USER_TOKEN = "ghu_" + "a" * 15
VALID_FINEGRAINED_PAT_TOKEN = "github_pat_" + "a" * 30
```

**Impact**: Enables tests to use all three token types consistently.

---

### 2.2 Create Token Factory Fixture

**Issue**: No centralized fixture for generating tokens of all types.

**Fix**: Add to `conftest.py` or test file:

```python
@pytest.fixture(params=[
    GitHubTokenType.CLASSIC,
    GitHubTokenType.FINE_GRAINED_USER,
    GitHubTokenType.FINE_GRAINED_PAT,
])
def token_factory(request):
    """Factory fixture that generates tokens for all types."""
    token_type = request.param

    if token_type == GitHubTokenType.CLASSIC:
        return "ghp_" + "a" * 40
    elif token_type == GitHubTokenType.FINE_GRAINED_USER:
        return "ghu_" + "a" * 15
    elif token_type == GitHubTokenType.FINE_GRAINED_PAT:
        return "github_pat_" + "a" * 25
    else:
        pytest.fail(f"Unknown token type: {token_type}")
```

**Usage Example**:

```python
def test_something_works_with_all_token_types(token_factory):
    token = token_factory
    # Test logic that should work with any token type
```

**Impact**: Reduces duplication and ensures tests automatically cover all token types.

---

## Priority 3: Nice-to-Have (Optional)

### 3.1 Convert Test Cases to Parameterized Tests

**Issue**: Some tests use loops instead of `@pytest.mark.parametrize`.

**File**: `tests/unit/test_git_manager.py:414`

**Current State**:

```python
def test_all_token_types_detected_correctly(self, git_manager):
    test_cases = [
        ("ghp_" + "a" * 40, GitHubTokenType.CLASSIC),
        ("ghu_" + "a" * 15, GitHubTokenType.FINE_GRAINED_USER),
        ("github_pat_" + "a" * 25, GitHubTokenType.FINE_GRAINED_PAT),
    ]
    for token, expected_type in test_cases:
        # ... test logic ...
```

**Fix**: Convert to parameterized:

```python
@pytest.mark.parametrize("token,expected_type", [
    ("ghp_" + "a" * 40, GitHubTokenType.CLASSIC),
    ("ghu_" + "a" * 15, GitHubTokenType.FINE_GRAINED_USER),
    ("github_pat_" + "a" * 25, GitHubTokenType.FINE_GRAINED_PAT),
])
def test_all_token_types_detected_correctly(self, git_manager, token, expected_type):
    git_manager.github_token = token
    # ... test logic ...
```

**Impact**: Better test reporting (each token type shows as separate test).

---

### 3.2 Add Documentation Comments

**Issue**: Some tests skip classic tokens without clear explanation.

**File**: `tests/integration/test_github_token_integration.py:195`

**Current State**:

```python
if github_token.startswith("ghp_"):
    pytest.skip("This test is for fine-grained tokens only")
```

**Fix**: Add detailed comment:

```python
# Skip classic tokens: This test specifically validates fine-grained token
# repository access restrictions. Classic tokens don't have repository selection
# limitations, so this test doesn't apply to them.
if github_token.startswith("ghp_"):
    pytest.skip("This test is for fine-grained tokens only")
```

**Impact**: Improves test maintainability and understanding.

---

## Implementation Checklist

- [ ] **Priority 1.1**: Expand `test_fetch_all_organization_repos_uses_expected_auth_header` to include FINE_GRAINED_PAT
- [ ] **Priority 1.1**: Expand `test_has_recent_activity_uses_expected_auth_header` to include FINE_GRAINED_USER
- [ ] **Priority 1.2**: Add `test_fine_grained_pat_token_format_in_api_call()` to `test_git_manager.py`
- [ ] **Priority 1.3**: Implement `test_token_type_detection_priority()` body
- [ ] **Priority 2.1**: Add `VALID_FINEGRAINED_USER_TOKEN` constant to `test_github_diagnostics.py`
- [ ] **Priority 2.2**: Create `token_factory` fixture in `conftest.py`
- [ ] **Priority 3.1**: Convert `test_all_token_types_detected_correctly()` to parameterized test
- [ ] **Priority 3.2**: Add documentation comments to skip conditions

---

## Verification Steps

After implementing fixes, verify:

1. **Run full test suite**: `mise test-all`
2. **Check test count**: Should still be 356+ tests (may increase with new tests)
3. **Verify coverage**: All three token types appear in test output
4. **Check parameterized tests**: Each token type shows as separate test case

---

## Expected Outcomes

After implementing Priority 1 fixes:

- ✅ All three token types tested in parameterized auth header tests
- ✅ Bearer auth verified for both fine-grained token types
- ✅ Token detection priority validated
- ✅ **100% coverage parity** across all token types

After implementing Priority 2 fixes:

- ✅ Consistent token constants across test files
- ✅ Reduced duplication with token factory fixture
- ✅ Easier to add new tests that cover all token types

---

## Related Files

- `tests/unit/test_update_repos_auth.py` - Auth header selection tests
- `tests/unit/test_git_manager.py` - Core git manager tests
- `tests/unit/test_github_diagnostics.py` - Diagnostic utility tests
- `tests/integration/test_github_token_integration.py` - Integration tests
- `src/investigator/core/github_token_utils.py` - Token detection implementation
