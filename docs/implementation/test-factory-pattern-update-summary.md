# Test Factory Pattern Update - Summary & Deliverable

## Questions Answered

### Q1: What test fixtures for both auth modes?

**Answer**: Two types of fixtures needed:

#### Unit Test Fixtures (Mock-based)

- `mock_oauth_client` - Mock ClaudeCLIClient instance
- `mock_api_key_client` - Mock ClaudeSDKClient instance
- `mock_factory_oauth` - Mock factory returning OAuth client
- `mock_factory_api_key` - Mock factory returning API key client
- `mock_factory_both` - Parameterized fixture for both modes

#### Integration Test Fixtures (Real credentials)

- `api_key_env` - Sets up environment for API key auth
- `oauth_env` - Sets up environment for OAuth auth
- `auth_env` - Parameterized fixture for both modes

**Location**: `tests/conftest.py`

### Q2: How to mock authentication detection in unit vs integration tests?

**Answer**: Different strategies for each:

#### Unit Tests: Mock Factory Directly

```python
@patch("investigator.core.claude_analyzer.create_claude_client")
def test_with_mock(mock_factory):
    mock_client = MagicMock()
    mock_factory.return_value = mock_client
    analyzer = ClaudeAnalyzer(logger)
```

#### Integration Tests: Use Real Environment

```python
def test_with_real_api_key(api_key_env):
    # Environment already set up by fixture
    analyzer = ClaudeAnalyzer(logger)
    # Uses real credentials
```

**Key Difference**: Unit tests mock the factory, integration tests use real env vars.

### Q3: Which tests need updates and what changes?

**Answer**:

#### Files Requiring Updates:

1. **`tests/unit/test_claude_analyzer_prompt_cleaning.py`**
   - **Change**: Add parameterization for both auth modes
   - **Impact**: Medium - Update test methods to use fixtures

2. **`tests/unit/test_claude_activity_integration.py`**
   - **Change**: Mock factory in activity context
   - **Impact**: Low - Add mocks for factory calls

3. **`tests/integration/test_claude_client_integration.py`**
   - **Change**: Use new fixtures, add parameterized tests
   - **Impact**: Low - Enhance existing tests

4. **`tests/integration/test_integration.py`** (empty)
   - **Change**: Create new integration tests
   - **Impact**: Medium - New test file

#### Files Already Complete:

- ✅ `tests/unit/test_claude_client_factory.py` - Factory tests complete
- ✅ `tests/unit/test_auth_detector.py` - Auth detection tests complete
- ✅ `tests/unit/test_claude_sdk_client.py` - SDK client tests complete
- ✅ `tests/unit/test_claude_cli_client.py` - CLI client tests complete
- ✅ `tests/unit/test_claude_client_interface.py` - Interface tests complete
- ✅ `tests/unit/test_backward_compatibility.py` - Backward compat tests complete

### Q4: How to ensure backward compatibility?

**Answer**: Three-pronged approach:

1. **Keep Existing Test Structure**
   - Don't break existing unittest-style tests
   - Add parameterization incrementally
   - Maintain existing mock patterns

2. **Verify API Key Path Still Works**

   ```python
   def test_backward_compatibility_api_key():
       """Ensure old API key tests still work."""
       with patch("investigator.core.claude_analyzer.create_claude_client") as mock_factory:
           mock_client = MagicMock()
           mock_factory.return_value = mock_client
           analyzer = ClaudeAnalyzer(logger)
           # Existing test logic unchanged
   ```

3. **Run Full Test Suite**
   - All existing tests must pass
   - No test modifications required for backward compat
   - Factory falls back to API key when OAuth unavailable

### Q5: Recommended pattern for test parameterization?

**Answer**: Use `pytest.mark.parametrize` with fixtures:

```python
@pytest.mark.parametrize("auth_mode", ["oauth", "api_key"])
def test_analyzer_behavior(auth_mode, mock_factory_both):
    """Test works with both auth modes."""
    mock_factory, mock_client, _ = mock_factory_both
    analyzer = ClaudeAnalyzer(logger)
    # Test logic works for both modes
```

**Benefits**:

- Single test covers both modes
- Clear test output showing both paths
- Easy to add more auth modes later

## Deliverable: Implementation Plan

### File List: Tests Requiring Updates

| File                                                  | Priority   | Changes Needed                | Status  |
| ----------------------------------------------------- | ---------- | ----------------------------- | ------- |
| `tests/conftest.py`                                   | **HIGH**   | Create new file with fixtures | ⏳ TODO |
| `tests/unit/test_claude_analyzer_prompt_cleaning.py`  | **HIGH**   | Add parameterization          | ⏳ TODO |
| `tests/unit/test_claude_activity_integration.py`      | **MEDIUM** | Mock factory                  | ⏳ TODO |
| `tests/integration/test_claude_client_integration.py` | **MEDIUM** | Use fixtures, add param tests | ⏳ TODO |
| `tests/integration/test_integration.py`               | **LOW**    | Create new tests              | ⏳ TODO |

### Fixture Patterns

#### Pattern 1: Unit Test Fixtures (Mock-based)

```python
# tests/conftest.py

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

#### Pattern 2: Integration Test Fixtures (Real credentials)

```python
# tests/conftest.py (continued)

import os

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

### Mocking Strategy

#### Unit Tests: Mock Factory

```python
# Example: test_claude_analyzer_prompt_cleaning.py

import pytest
from unittest.mock import Mock, MagicMock, patch
from investigator.core.claude_analyzer import ClaudeAnalyzer

@pytest.mark.parametrize("auth_mode", ["oauth", "api_key"])
def test_clean_prompt_removes_version_line(auth_mode, mock_factory_both):
    """Test that version lines are removed from prompts."""
    mock_factory, mock_client, _ = mock_factory_both
    mock_logger = Mock()

    analyzer = ClaudeAnalyzer(mock_logger)

    prompt_with_version = """version=2
## Repository Structure and Files

{repo_structure}"""

    cleaned = analyzer.clean_prompt(prompt_with_version)

    # Should not contain version line
    assert "version=2" not in cleaned
    # Should start with the actual content
    assert cleaned.startswith("## Repository Structure")
```

#### Integration Tests: Real Environment

```python
# Example: test_claude_client_integration.py

import pytest
import logging
from src.investigator.core.claude_analyzer import ClaudeAnalyzer

def test_analyzer_uses_factory_with_api_key(api_key_env):
    """Test ClaudeAnalyzer works with API key authentication via factory."""
    logger = logging.getLogger(__name__)
    analyzer = ClaudeAnalyzer(logger=logger)

    result = analyzer.analyze_with_context(
        prompt_template="Explain what 'hello world' means in one sentence.",
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

    result = analyzer.analyze_with_context(
        prompt_template="Say 'test'",
        repo_structure="",
        previous_context=None,
        config_overrides={"max_tokens": 50},
    )

    assert result is not None
    assert "test" in result.lower()
```

### Code Examples for Updated Test Patterns

#### Example 1: Unit Test with Parameterization

```python
# tests/unit/test_claude_analyzer_prompt_cleaning.py

import pytest
from unittest.mock import Mock
from investigator.core.claude_analyzer import ClaudeAnalyzer

@pytest.mark.parametrize("auth_mode", ["oauth", "api_key"])
def test_clean_prompt_removes_version_line(auth_mode, mock_factory_both):
    """Test that version lines are removed from prompts."""
    mock_factory, mock_client, _ = mock_factory_both
    mock_logger = Mock()

    analyzer = ClaudeAnalyzer(mock_logger)

    prompt_with_version = """version=2
## Repository Structure"""

    cleaned = analyzer.clean_prompt(prompt_with_version)

    assert "version=2" not in cleaned
    assert cleaned.startswith("## Repository Structure")
```

#### Example 2: Activity Test with Mocked Factory

```python
# tests/unit/test_claude_activity_integration.py

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
```

#### Example 3: Integration Test with Real Credentials

```python
# tests/integration/test_claude_client_integration.py

import pytest
import logging
from src.investigator.core.claude_analyzer import ClaudeAnalyzer

@pytest.mark.parametrize("auth_mode", ["api_key", "oauth"])
def test_analyzer_end_to_end(auth_env):
    """Test ClaudeAnalyzer end-to-end with both auth modes."""
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

### Verification Approach for Backward Compatibility

#### Step 1: Run Existing Tests (Baseline)

```bash
# Capture baseline results
pytest tests/unit/test_claude_analyzer_prompt_cleaning.py -v > baseline_unit.txt
pytest tests/integration/test_claude_client_integration.py -v > baseline_integration.txt
```

#### Step 2: Update Tests Incrementally

```bash
# After each file update, verify no regressions
pytest tests/unit/test_claude_analyzer_prompt_cleaning.py -v
pytest tests/unit/test_claude_activity_integration.py -v
```

#### Step 3: Verify Both Auth Modes

```bash
# Unit tests should test both modes
pytest tests/unit/test_claude_analyzer_prompt_cleaning.py -v
# Should see tests run for both "oauth" and "api_key" parameters

# Integration tests (requires credentials)
ANTHROPIC_API_KEY=sk-ant-api03-... pytest tests/integration/test_claude_client_integration.py::test_analyzer_uses_factory_with_api_key -v
CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-... pytest tests/integration/test_claude_client_integration.py::test_analyzer_uses_factory_with_oauth -v
```

#### Step 4: Full Test Suite Verification

```bash
# Run all tests
pytest tests/ -v

# Check coverage
pytest tests/ --cov=src/investigator/core --cov-report=term-missing
```

### Success Criteria Checklist

- [ ] `tests/conftest.py` created with all fixtures
- [ ] `test_claude_analyzer_prompt_cleaning.py` updated and passing
- [ ] `test_claude_activity_integration.py` updated and passing
- [ ] `test_claude_client_integration.py` enhanced and passing
- [ ] All existing tests still pass (backward compatibility)
- [ ] Both OAuth and API key modes tested
- [ ] Integration tests work with real credentials
- [ ] Test coverage maintained or improved
- [ ] No test execution time regression

## Next Steps

1. **Create `tests/conftest.py`** with fixtures (30 min)
2. **Update `test_claude_analyzer_prompt_cleaning.py`** (1 hour)
3. **Update `test_claude_activity_integration.py`** (30 min)
4. **Enhance `test_claude_client_integration.py`** (1 hour)
5. **Run verification** (30 min)
6. **Document any deviations** (15 min)

**Total Estimated Time**: 3-4 hours
