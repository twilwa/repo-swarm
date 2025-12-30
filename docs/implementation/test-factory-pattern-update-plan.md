# Test Factory Pattern Update Plan

## Overview

This document outlines the plan to update all tests to work with the new Claude authentication factory pattern that supports both OAuth and API key authentication.

## Current State

### Factory Pattern Architecture

- **Factory**: `src/investigator/core/claude_client_factory.py`
  - `create_claude_client(logger)` - Detects auth method and returns appropriate client
  - Routes to `ClaudeCLIClient` (OAuth) or `ClaudeSDKClient` (API key)
- **Authentication Detection**: `src/investigator/core/auth_detector.py`
  - `get_claude_authentication()` - Checks env vars in priority order:
    1. `CLAUDE_CODE_OAUTH_TOKEN` (highest priority)
    2. `CLAUDE_OAUTH_TOKEN`
    3. `ANTHROPIC_API_KEY` (fallback)

- **ClaudeAnalyzer**: `src/investigator/core/claude_analyzer.py`
  - Uses `create_claude_client()` in `__init__`
  - No direct API key parameter - relies on factory

### Test Files Requiring Updates

#### Direct ClaudeAnalyzer Usage

1. **`tests/unit/test_claude_analyzer_prompt_cleaning.py`**
   - Currently mocks `create_claude_client`
   - Needs: Parameterized tests for both auth modes

2. **`tests/integration/test_claude_client_integration.py`**
   - Already has OAuth and API key tests
   - Status: Mostly complete, may need fixture improvements

#### Indirect Usage (via activities/workflows)

3. **`tests/unit/test_claude_activity_integration.py`**
   - Tests activity functions that use ClaudeAnalyzer
   - Needs: Mock factory for both auth modes

4. **`tests/integration/test_integration.py`**
   - Empty file - may need new integration tests

5. **`tests/integration/test_shared_prompts.py`**
   - Empty file - may need new integration tests

#### Factory Tests (Already Complete)

6. **`tests/unit/test_claude_client_factory.py`**
   - Status: ✅ Complete - Tests factory selection logic

7. **`tests/unit/test_auth_detector.py`**
   - Status: ✅ Complete - Tests auth detection

#### Client Implementation Tests (Already Complete)

8. **`tests/unit/test_claude_sdk_client.py`**
   - Status: ✅ Complete - Tests SDK client

9. **`tests/unit/test_claude_cli_client.py`**
   - Status: ✅ Complete - Tests CLI client

10. **`tests/unit/test_claude_client_interface.py`**
    - Status: ✅ Complete - Tests protocol interface

11. **`tests/unit/test_backward_compatibility.py`**
    - Status: ✅ Complete - Tests backward compatibility

## Implementation Strategy

### 1. Test Fixtures for Both Auth Modes

#### Unit Test Fixtures (Mock-based)

Create reusable fixtures in `tests/conftest.py`:

```python
import pytest
from unittest.mock import Mock, MagicMock, patch

@pytest.fixture
def mock_oauth_client():
    """Mock OAuth client (ClaudeCLIClient) for unit tests."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Mock OAuth response")]
    mock_client.messages.create.return_value = mock_response
    return mock_client

@pytest.fixture
def mock_api_key_client():
    """Mock API key client (ClaudeSDKClient) for unit tests."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Mock API key response")]
    mock_client.messages.create.return_value = mock_response
    return mock_client

@pytest.fixture
def mock_factory_oauth(mock_oauth_client):
    """Mock factory returning OAuth client."""
    with patch("investigator.core.claude_analyzer.create_claude_client") as mock_factory:
        mock_factory.return_value = mock_oauth_client
        yield mock_factory, mock_oauth_client

@pytest.fixture
def mock_factory_api_key(mock_api_key_client):
    """Mock factory returning API key client."""
    with patch("investigator.core.claude_analyzer.create_claude_client") as mock_factory:
        mock_factory.return_value = mock_api_key_client
        yield mock_factory, mock_api_key_client

@pytest.fixture(params=["oauth", "api_key"])
def mock_factory_both(request, mock_oauth_client, mock_api_key_client):
    """Parameterized fixture for both auth modes."""
    auth_mode = request.param
    mock_client = mock_oauth_client if auth_mode == "oauth" else mock_api_key_client

    with patch("investigator.core.claude_analyzer.create_claude_client") as mock_factory:
        mock_factory.return_value = mock_client
        yield mock_factory, mock_client, auth_mode
```

#### Integration Test Fixtures (Real credentials)

```python
import os
import pytest
from unittest.mock import patch

@pytest.fixture
def api_key_env():
    """Set up environment for API key authentication."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")

    with patch.dict(
        os.environ,
        {
            "CLAUDE_CODE_OAUTH_TOKEN": "",
            "CLAUDE_OAUTH_TOKEN": "",
            "ANTHROPIC_API_KEY": api_key,
        },
        clear=False,
    ):
        yield api_key

@pytest.fixture
def oauth_env():
    """Set up environment for OAuth authentication."""
    oauth_token = (
        os.getenv("CLAUDE_CODE_OAUTH_TOKEN")
        or os.getenv("CLAUDE_OAUTH_TOKEN")
    )
    if not oauth_token:
        pytest.skip("No OAuth token set")

    with patch.dict(
        os.environ,
        {
            "CLAUDE_CODE_OAUTH_TOKEN": oauth_token,
            "ANTHROPIC_API_KEY": "",  # Clear API key
        },
        clear=False,
    ):
        yield oauth_token

@pytest.fixture(params=["api_key", "oauth"])
def auth_env(request, api_key_env, oauth_env):
    """Parameterized fixture for both auth modes in integration tests."""
    if request.param == "api_key":
        return api_key_env
    else:
        return oauth_env
```

### 2. Mocking Strategy

#### Unit Tests: Mock Factory and Auth Detection

**Pattern 1: Mock factory directly (recommended for ClaudeAnalyzer tests)**

```python
@patch("investigator.core.claude_analyzer.create_claude_client")
def test_analyzer_with_oauth(mock_factory):
    mock_client = MagicMock()
    mock_factory.return_value = mock_client
    analyzer = ClaudeAnalyzer(logger)
    # Test analyzer behavior
```

**Pattern 2: Mock auth detector (for factory tests)**

```python
@patch("investigator.core.claude_client_factory.get_claude_authentication")
@patch("investigator.core.claude_client_factory.ClaudeCLIClient")
def test_factory_oauth_path(mock_cli_client, mock_auth):
    mock_auth.return_value = {
        "method": "oauth",
        "token": "sk-ant-oat01-...",
        "use_cli": True,
    }
    # Test factory behavior
```

#### Integration Tests: Use Real Environment

```python
def test_analyzer_with_api_key(api_key_env):
    """Test with real API key from environment."""
    analyzer = ClaudeAnalyzer(logger)
    result = analyzer.analyze_with_context(...)
    assert result is not None

def test_analyzer_with_oauth(oauth_env):
    """Test with real OAuth token from environment."""
    analyzer = ClaudeAnalyzer(logger)
    result = analyzer.analyze_with_context(...)
    assert result is not None
```

### 3. Test Parameterization Pattern

Use `pytest.mark.parametrize` for testing both auth modes:

```python
import pytest

@pytest.mark.parametrize("auth_mode", ["oauth", "api_key"])
def test_analyzer_cleans_prompt(auth_mode, mock_factory_both):
    """Test prompt cleaning works with both auth modes."""
    mock_factory, mock_client, _ = mock_factory_both
    analyzer = ClaudeAnalyzer(logger)

    result = analyzer.clean_prompt("version=1\nContent")

    assert "version=1" not in result
    assert "Content" in result
```

### 4. Backward Compatibility Verification

#### Test Existing API Key Tests Still Pass

1. **Verify existing API key mocks still work**:

   ```python
   def test_backward_compatibility_api_key():
       """Ensure old API key tests still work."""
       with patch("investigator.core.claude_analyzer.create_claude_client") as mock_factory:
           mock_client = MagicMock()
           mock_factory.return_value = mock_client
           analyzer = ClaudeAnalyzer(logger)
           # Existing test logic should work unchanged
   ```

2. **Verify factory falls back to API key**:
   ```python
   def test_factory_fallback_to_api_key():
       """Factory should use API key when OAuth not available."""
       with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-api03-..."}):
           with patch("investigator.core.claude_client_factory.ClaudeSDKClient") as mock_sdk:
               create_claude_client()
               mock_sdk.assert_called_once()
   ```

## Detailed Update Plan

### Phase 1: Create Test Fixtures

**File**: `tests/conftest.py` (create if doesn't exist)

**Tasks**:

1. Add unit test fixtures (`mock_oauth_client`, `mock_api_key_client`, `mock_factory_oauth`, `mock_factory_api_key`, `mock_factory_both`)
2. Add integration test fixtures (`api_key_env`, `oauth_env`, `auth_env`)
3. Ensure fixtures work with both unittest and pytest

**Verification**:

- Run `pytest tests/conftest.py -v` to verify fixtures load
- Check fixture availability: `pytest --fixtures | grep -E "oauth|api_key"`

### Phase 2: Update Unit Tests

#### 2.1 Update `test_claude_analyzer_prompt_cleaning.py`

**Current State**: Uses `patch("investigator.core.claude_analyzer.create_claude_client")` in `setUp`

**Changes Needed**:

1. Replace `setUp` with parameterized fixtures
2. Add tests for both auth modes using `mock_factory_both`
3. Ensure all existing tests pass with both modes

**Example Update**:

```python
class TestClaudeAnalyzerPromptCleaning(unittest.TestCase):
    """Test suite for prompt cleaning functionality."""

    @pytest.fixture(autouse=True)
    def setup_mock_factory(self, mock_factory_both):
        """Auto-inject mock factory for all tests."""
        self.mock_factory, self.mock_client, self.auth_mode = mock_factory_both

    def test_clean_prompt_removes_version_line(self):
        """Test that version lines are removed from prompts."""
        # Test works with both OAuth and API key
        analyzer = ClaudeAnalyzer(self.mock_logger)
        # ... rest of test
```

**Alternative (simpler)**: Keep unittest style, add parameterized test methods:

```python
@pytest.mark.parametrize("auth_mode", ["oauth", "api_key"])
def test_clean_prompt_removes_version_line(auth_mode, mock_factory_both):
    """Test that version lines are removed from prompts."""
    mock_factory, mock_client, _ = mock_factory_both
    analyzer = ClaudeAnalyzer(logger)
    # ... test logic
```

#### 2.2 Update `test_claude_activity_integration.py`

**Current State**: Tests Pydantic models, doesn't directly test ClaudeAnalyzer

**Changes Needed**:

1. Add mocks for `create_claude_client` in activity tests
2. Ensure activity functions work with both auth modes
3. Mock factory in activity context

**Example Update**:

```python
@patch("activities.investigate_activities.create_claude_client")
def test_activity_with_oauth(mock_factory):
    """Test activity works with OAuth client."""
    mock_client = MagicMock()
    mock_factory.return_value = mock_client
    # Test activity function
```

### Phase 3: Update Integration Tests

#### 3.1 Enhance `test_claude_client_integration.py`

**Current State**: Already has OAuth and API key tests

**Changes Needed**:

1. Use new fixtures (`api_key_env`, `oauth_env`)
2. Add parameterized tests using `auth_env` fixture
3. Ensure both modes are tested consistently

**Example Update**:

```python
def test_analyzer_uses_factory_with_api_key(api_key_env):
    """Test ClaudeAnalyzer works with API key authentication via factory."""
    import logging
    logger = logging.getLogger(__name__)
    analyzer = ClaudeAnalyzer(logger=logger)
    # ... rest of test

@pytest.mark.parametrize("auth_mode", ["api_key", "oauth"])
def test_analyzer_works_with_both_auth_modes(auth_env):
    """Test ClaudeAnalyzer works with both authentication methods."""
    import logging
    logger = logging.getLogger(__name__)
    analyzer = ClaudeAnalyzer(logger=logger)
    result = analyzer.analyze_with_context(
        prompt_template="Explain 'hello world' in one sentence.",
        repo_structure="",
        previous_context=None,
        config_overrides={"max_tokens": 100},
    )
    assert result is not None
    assert len(result) > 0
```

#### 3.2 Create/Update `test_integration.py`

**Current State**: Empty file

**Changes Needed**:

1. Add end-to-end integration tests
2. Test full workflow with both auth modes
3. Use `auth_env` fixture for parameterization

**Example**:

```python
@pytest.mark.parametrize("auth_mode", ["api_key", "oauth"])
def test_full_investigation_workflow(auth_env, tmp_path):
    """Test complete investigation workflow with both auth modes."""
    # Setup test repo
    # Run investigation
    # Verify results
```

### Phase 4: Verification and Backward Compatibility

#### 4.1 Run All Existing Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Full test suite
pytest tests/ -v
```

#### 4.2 Verify Backward Compatibility

1. **Check existing API key tests still pass**:

   ```bash
   pytest tests/unit/test_claude_analyzer_prompt_cleaning.py -v
   pytest tests/unit/test_backward_compatibility.py -v
   ```

2. **Verify factory tests cover both paths**:

   ```bash
   pytest tests/unit/test_claude_client_factory.py -v
   ```

3. **Check integration tests work with real credentials**:

   ```bash
   # With API key
   ANTHROPIC_API_KEY=sk-ant-api03-... pytest tests/integration/test_claude_client_integration.py::TestClaudeAnalyzerIntegration::test_analyzer_uses_factory_with_api_key -v

   # With OAuth
   CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-... pytest tests/integration/test_claude_client_integration.py::TestClaudeAnalyzerIntegration::test_analyzer_uses_factory_with_oauth -v
   ```

## Code Examples

### Example 1: Updated Unit Test with Parameterization

```python
import pytest
from unittest.mock import Mock, MagicMock, patch
from investigator.core.claude_analyzer import ClaudeAnalyzer

@pytest.mark.parametrize("auth_mode", ["oauth", "api_key"])
def test_analyzer_cleans_prompt_version_line(auth_mode):
    """Test prompt cleaning works with both auth modes."""
    mock_logger = Mock()
    mock_client = MagicMock()

    with patch("investigator.core.claude_analyzer.create_claude_client") as mock_factory:
        mock_factory.return_value = mock_client
        analyzer = ClaudeAnalyzer(mock_logger)

        prompt_with_version = "version=2\n## Repository Structure\n{repo_structure}"
        cleaned = analyzer.clean_prompt(prompt_with_version)

        assert "version=2" not in cleaned
        assert "## Repository Structure" in cleaned
```

### Example 2: Updated Integration Test with Fixture

```python
import pytest
import logging
from src.investigator.core.claude_analyzer import ClaudeAnalyzer

def test_analyzer_works_with_api_key(api_key_env):
    """Test ClaudeAnalyzer with real API key."""
    logger = logging.getLogger(__name__)
    analyzer = ClaudeAnalyzer(logger=logger)

    result = analyzer.analyze_with_context(
        prompt_template="Explain 'hello world' in one sentence.",
        repo_structure="",
        previous_context=None,
        config_overrides={"max_tokens": 100},
    )

    assert result is not None
    assert len(result) > 0

@pytest.mark.parametrize("auth_mode", ["api_key", "oauth"])
def test_analyzer_works_with_both_modes(auth_env):
    """Test ClaudeAnalyzer works with both authentication methods."""
    logger = logging.getLogger(__name__)
    analyzer = ClaudeAnalyzer(logger=logger)

    # Simple test that works with both modes
    result = analyzer.analyze_with_context(
        prompt_template="Say 'test'",
        repo_structure="",
        previous_context=None,
        config_overrides={"max_tokens": 50},
    )

    assert result is not None
    assert "test" in result.lower()
```

### Example 3: Activity Test with Mocked Factory

```python
from unittest.mock import patch, MagicMock
from activities.investigate_activities import analyze_with_claude_context

@patch("activities.investigate_activities.create_claude_client")
def test_activity_with_mocked_factory(mock_factory):
    """Test activity function with mocked Claude client."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Analysis result")]
    mock_client.messages.create.return_value = mock_response
    mock_factory.return_value = mock_client

    # Test activity function
    input_model = AnalyzeWithClaudeInput(...)
    output = analyze_with_claude_context(input_model)

    assert output.status == "success"
    assert output.result_length > 0
```

## Testing Checklist

### Pre-Implementation

- [ ] Review all test files that use ClaudeAnalyzer or Anthropic client
- [ ] Identify test patterns (unittest vs pytest)
- [ ] Document current test coverage

### Implementation

- [ ] Create `tests/conftest.py` with fixtures
- [ ] Update `test_claude_analyzer_prompt_cleaning.py`
- [ ] Update `test_claude_activity_integration.py`
- [ ] Enhance `test_claude_client_integration.py`
- [ ] Create/update `test_integration.py`

### Verification

- [ ] All unit tests pass: `pytest tests/unit/ -v`
- [ ] All integration tests pass: `pytest tests/integration/ -v`
- [ ] Backward compatibility verified: `pytest tests/unit/test_backward_compatibility.py -v`
- [ ] Both auth modes tested: Check test output for both OAuth and API key paths
- [ ] No regressions: Compare test results before/after changes

### Documentation

- [ ] Update test README if exists
- [ ] Document fixture usage patterns
- [ ] Add examples for new test patterns

## Risk Mitigation

### Risk 1: Breaking Existing Tests

**Mitigation**:

- Keep existing test structure where possible
- Add parameterization incrementally
- Run full test suite after each change

### Risk 2: Fixture Conflicts

**Mitigation**:

- Use unique fixture names
- Document fixture scope (function/class/module)
- Test fixtures in isolation

### Risk 3: Integration Test Dependencies

**Mitigation**:

- Make integration tests skip gracefully if credentials missing
- Use `pytest.skip()` for missing credentials
- Document required environment variables

## Success Criteria

1. ✅ All existing tests pass without modification (backward compatibility)
2. ✅ New tests verify both OAuth and API key authentication modes
3. ✅ Test fixtures are reusable and well-documented
4. ✅ Integration tests work with real credentials (when available)
5. ✅ Test coverage maintained or improved
6. ✅ No test execution time regression

## Timeline Estimate

- **Phase 1** (Fixtures): 1-2 hours
- **Phase 2** (Unit Tests): 2-3 hours
- **Phase 3** (Integration Tests): 2-3 hours
- **Phase 4** (Verification): 1-2 hours
- **Total**: 6-10 hours

## Next Steps

1. Review and approve this plan
2. Create `tests/conftest.py` with fixtures
3. Update test files incrementally
4. Run verification after each phase
5. Document any deviations from plan
