# GitHub Token Diagnostics Implementation Summary

## Overview

Implemented comprehensive GitHub token diagnostic utilities to help users troubleshoot authentication and permission issues (GH-5.2).

## Components Created

### 1. Core Diagnostic Module (`src/investigator/core/github_diagnostics.py`)

**Purpose**: Programmatic token validation and issue detection

**Key Features**:

- Detects 7 common token issues:
  - Invalid format
  - Expired or invalid tokens
  - Insufficient scopes/permissions
  - Repository not selected (fine-grained tokens)
  - No push permission
  - Rate limiting
  - Network errors

**API**:

```python
from src.investigator.core.github_diagnostics import diagnose_github_token

# Basic validation
result = diagnose_github_token(token)

# With repository access check
result = diagnose_github_token(token, 'owner/repo')

# Result includes:
# - status: SUCCESS, WARNING, or ERROR
# - message: Human-readable description
# - issue_type: Specific problem category
# - recommendations: List of actionable fixes
# - troubleshooting_url: Link to documentation
# - details: Additional metadata
```

### 2. CLI Diagnostic Tool (`scripts/diagnose_token.py`)

**Purpose**: Command-line interface for token troubleshooting

**Usage**:

```bash
# Diagnose token from environment
uv run python scripts/diagnose_token.py

# Check specific repository access
uv run python scripts/diagnose_token.py owner/repo

# Diagnose specific token
uv run python scripts/diagnose_token.py --token ghp_xxx

# Verbose output
uv run python scripts/diagnose_token.py --verbose
```

**Output Example**:

```
🔍 Diagnosing GitHub token...

❌ Token has invalid format - doesn't match any known GitHub token pattern

Issue Type: Invalid Format

Recommendations:
  1. Verify you copied the complete token without extra spaces
  2. Classic tokens should start with 'ghp_'
  3. Fine-grained tokens should start with 'github_pat_'
  4. Check the troubleshooting guide for token format details

For more help, see: docs/GITHUB_TOKEN_TROUBLESHOOTING.md
```

### 3. Troubleshooting Guide (`docs/GITHUB_TOKEN_TROUBLESHOOTING.md`)

**Purpose**: Comprehensive user documentation for token issues

**Contents**:

- Quick diagnostic instructions
- 7 common issues with symptoms, causes, and solutions
- Token type comparison (classic vs fine-grained)
- Required permissions reference
- Security best practices
- Maintenance guidelines
- Diagnostic tool API reference

**Structure**:

1. Quick Diagnostic - Get started fast
2. Common Issues - Detailed troubleshooting for each error type
3. Token Types - When to use classic vs fine-grained
4. Required Permissions - What scopes/permissions you need
5. Best Practices - Security and maintenance tips

### 4. Unit Tests (`tests/unit/test_github_diagnostics.py`)

**Coverage**: 9 test cases covering:

- Valid token validation
- Expired token detection
- Insufficient scopes detection
- Repository not selected detection
- Rate limiting detection
- Invalid format detection
- No push permission detection
- Recommendations validation
- Troubleshooting URL validation

**Test Results**: All tests passing (356 total unit tests passing)

## Integration Points

### Existing Code Integration

1. **Uses existing token utilities**: Builds on `github_token_utils.py` for token type detection
2. **Can integrate with verify_config**: Enhancement code provided in `/tmp/verify_config_enhancement.py`
3. **Follows project patterns**: Uses dataclasses, type hints, logging

### Future Integration Opportunities

1. **verify_config.py**: Replace current token validation with diagnostic tool
2. **Error handling**: Catch GitHub API errors and suggest diagnostic tool
3. **CI/CD**: Add token validation step in deployment pipeline

## Usage Examples

### For Users (Quick Troubleshooting)

```bash
# Problem: Investigation failing with 404
uv run python scripts/diagnose_token.py owner/repo

# Output identifies: "Repository not selected in fine-grained token settings"
# Provides: Direct link to fix in GitHub settings
```

### For Developers (Programmatic Validation)

```python
from src.investigator.core.github_diagnostics import diagnose_github_token

def validate_setup():
    result = diagnose_github_token(
        os.getenv('GITHUB_TOKEN'),
        'target/repository'
    )

    if result.status != DiagnosticStatus.SUCCESS:
        logger.error(f"Token issue: {result.message}")
        for rec in result.recommendations:
            logger.info(f"  → {rec}")
        return False

    return True
```

### For Automation (Pre-flight Checks)

```bash
# In CI/CD pipeline
if ! uv run python scripts/diagnose_token.py; then
    echo "Token validation failed - check logs"
    exit 1
fi
```

## Testing

### Unit Tests

```bash
mise run test-units
# Result: 356 passed, 5 skipped

# Just diagnostic tests
uv run python -m pytest tests/unit/test_github_diagnostics.py -v
# Result: 9 passed
```

### Manual Testing

```bash
# Test invalid format
uv run python scripts/diagnose_token.py --token "bad_token"
# ✅ Correctly identifies invalid format

# Test with real token (if available)
uv run python scripts/diagnose_token.py
# ✅ Validates token and shows rate limit info
```

## Documentation

### User-Facing Documentation

- **Primary**: `docs/GITHUB_TOKEN_TROUBLESHOOTING.md` (comprehensive guide)
- **Quick Reference**: `scripts/diagnose_token.py --help` (CLI usage)

### Developer Documentation

- **API**: Docstrings in `github_diagnostics.py`
- **Tests**: Examples in `test_github_diagnostics.py`
- **This Summary**: Implementation overview

## Files Modified/Created

### Created

- `src/investigator/core/github_diagnostics.py` (268 lines)
- `tests/unit/test_github_diagnostics.py` (187 lines)
- `docs/GITHUB_TOKEN_TROUBLESHOOTING.md` (600+ lines)
- `scripts/diagnose_token.py` (132 lines)
- `docs/github-token-diagnostics-summary.md` (this file)

### Enhanced (Future)

- `scripts/verify_config.py` (enhancement code prepared)

## Benefits

1. **User Experience**:
   - Clear, actionable error messages
   - Step-by-step troubleshooting guidance
   - Reduces support burden

2. **Developer Experience**:
   - Reusable diagnostic API
   - Easy to integrate into workflows
   - Comprehensive test coverage

3. **Operations**:
   - Automated token validation
   - Pre-flight checks for deployments
   - Better error reporting

## Next Steps

1. ✅ Core diagnostic module implemented
2. ✅ Unit tests written and passing
3. ✅ Troubleshooting guide created
4. ✅ CLI tool created
5. ⏳ Integration with verify_config (code ready, needs review)
6. ⏳ Add mise task for easy access (recommended: `mise diagnose-token`)
7. ⏳ Update README with diagnostics section

## Related Issues

- **Implements**: GH-5.2 (Add permission troubleshooting)
- **Depends on**: GH-2.1 (Standardize GitHub API auth headers) - COMPLETE
- **Blocks**: GH-6.1, GH-6.2, GH-6.3 (Testing tasks)

## Metrics

- **Lines of Code**: ~1,187 (including tests and docs)
- **Test Coverage**: 9 test cases, 100% passing
- **Documentation**: 600+ lines of troubleshooting guide
- **Issues Detected**: 7 distinct token problem categories
