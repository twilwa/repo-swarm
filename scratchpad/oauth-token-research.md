# OAuth Token Authentication Research

## Problem Summary

**OAuth tokens (`sk-ant-oat01-...`) from `claude setup-token` DO NOT work with the Anthropic API (`api.anthropic.com`).**

### Error Received

```
Error code: 401 - {
  'type': 'error',
  'error': {
    'type': 'authentication_error',
    'message': 'invalid x-api-key'
  }
}
```

### Root Cause

There are **TWO SEPARATE authentication systems**:

1. **Anthropic API** (`api.anthropic.com`)
   - Uses API keys: `sk-ant-api03-...`
   - Obtained from: https://console.anthropic.com/
   - Used by: `anthropic` Python SDK
   - **Does NOT accept OAuth tokens**

2. **Claude Code CLI** (internal endpoints)
   - Uses OAuth tokens: `sk-ant-oat01-...`
   - Obtained from: `claude setup-token` command
   - Used by: Claude Code CLI, claude.ai web interface
   - **Works with Claude Max subscription**

### Official Confirmation

From GitHub Issue #9887:

```json
{
  "type": "authentication_error",
  "message": "OAuth authentication is currently not supported."
}
```

---

## Solution Options

### Option 1: Use Claude Code CLI Directly (Recommended)

Call the `claude` CLI programmatically instead of using the Anthropic SDK.

**Advantages:**

- ✅ Works with OAuth tokens
- ✅ Uses Claude Max subscription
- ✅ Official Anthropic tool
- ✅ ToS compliant

**Disadvantages:**

- ❌ Requires subprocess calls (slower)
- ❌ Less control over streaming/retries
- ❌ Different API surface

**Implementation:**

```python
import subprocess
import json

def analyze_with_claude_cli(prompt: str, oauth_token: str) -> str:
    """Use Claude Code CLI with OAuth token"""
    env = os.environ.copy()
    env['CLAUDE_CODE_OAUTH_TOKEN'] = oauth_token

    result = subprocess.run(
        ['claude', '--print', prompt],
        capture_output=True,
        text=True,
        env=env
    )

    if result.returncode != 0:
        raise RuntimeError(f"Claude CLI failed: {result.stderr}")

    return result.stdout
```

---

### Option 2: Use CLAUDE_USE_SUBSCRIPTION Environment Variable

Found in "Unlocking Claude Code's Full Subscription" article:

**The Discovery:**

> The Claude Code CLI, when run programmatically, was hardcoded to only use API Key Authentication, ignoring OAuth tokens.

**The Solution:**

```python
import os
import subprocess

# Force CLI to use subscription instead of API key
env = os.environ.copy()
env['CLAUDE_USE_SUBSCRIPTION'] = 'true'
if 'ANTHROPIC_API_KEY' in env:
    del env['ANTHROPIC_API_KEY']  # CRITICAL: Remove API key
env['CLAUDE_CODE_OAUTH_TOKEN'] = oauth_token

result = subprocess.run(
    ['claude', '--print', prompt],
    capture_output=True,
    text=True,
    env=env
)
```

---

### Option 3: Hybrid Approach (Best UX)

Support both authentication methods with automatic detection:

```python
def get_claude_authentication():
    """Auto-detect best authentication method"""

    # Priority 1: Check for OAuth token (Max subscription)
    oauth_token = os.getenv('CLAUDE_CODE_OAUTH_TOKEN') or os.getenv('CLAUDE_OAUTH_TOKEN')
    if oauth_token and oauth_token.startswith('sk-ant-oat01-'):
        return {
            'method': 'oauth',
            'token': oauth_token,
            'use_cli': True  # Must use CLI for OAuth
        }

    # Priority 2: Check for API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key and api_key.startswith('sk-ant-api'):
        return {
            'method': 'api_key',
            'token': api_key,
            'use_cli': False  # Can use SDK directly
        }

    raise AuthenticationError(
        "No Claude authentication found. Please either:\\n"
        "  1. Run: claude setup-token (for Max subscription)\\n"
        "     Then: export CLAUDE_CODE_OAUTH_TOKEN=<token>\\n"
        "  2. Or: export ANTHROPIC_API_KEY=<api-key> (from console.anthropic.com)"
    )


class ClaudeClient:
    def __init__(self):
        self.auth = get_claude_authentication()

        if self.auth['use_cli']:
            # OAuth: Use CLI
            self.analyzer = ClaudeCLIAnalyzer(self.auth['token'])
        else:
            # API Key: Use SDK
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.auth['token'])
            self.analyzer = ClaudeSDKAnalyzer(self.client)
```

---

## Recommendation for RepoSwarm

### Update `add-claude-web-auth` Proposal

**Simplified Approach:**

1. **Remove browser automation complexity** (playwright, session management)
2. **Use Claude Code CLI** with OAuth tokens
3. **Support both auth methods** (API key + OAuth)

**New Implementation:**

```python
# src/investigator/core/claude_client_factory.py
def create_claude_client():
    auth = get_claude_authentication()

    if auth['method'] == 'oauth':
        return ClaudeCLIClient(auth['token'])  # Uses subprocess
    else:
        return ClaudeSDKClient(auth['token'])  # Uses SDK


# src/investigator/core/claude_cli_client.py
class ClaudeCLIClient:
    def __init__(self, oauth_token: str):
        self.oauth_token = oauth_token

    def messages_create(self, model: str, max_tokens: int, messages: list) -> str:
        """Compatible interface with Anthropic SDK"""
        prompt = messages[0]['content']  # Simplified

        env = os.environ.copy()
        env['CLAUDE_CODE_OAUTH_TOKEN'] = self.oauth_token
        env['CLAUDE_USE_SUBSCRIPTION'] = 'true'
        if 'ANTHROPIC_API_KEY' in env:
            del env['ANTHROPIC_API_KEY']

        result = subprocess.run(
            ['claude', '--print', prompt, '--output-format', 'json'],
            capture_output=True,
            text=True,
            env=env,
            timeout=300
        )

        if result.returncode != 0:
            raise RuntimeError(f"Claude CLI error: {result.stderr}")

        return self._parse_cli_output(result.stdout)
```

---

## Updated Proposal Tasks

**Simplified from 41 to ~12 tasks:**

1. ✅ Create authentication detection utility
2. Create ClaudeCLIClient wrapper
3. Update ClaudeAnalyzer to use factory pattern
4. Add `mise claude-login` command (calls `claude setup-token`)
5. Update configuration validation
6. Add OAuth token environment variable support
7. Test with both API key and OAuth token
8. Update documentation
9. Write unit tests (mock subprocess calls)
10. Write integration tests (with real CLI)
11. Update error messages
12. Validate with OpenSpec

**Removed complexity:**

- ❌ No browser automation
- ❌ No session token extraction
- ❌ No custom OAuth flow
- ❌ No token refresh (1-year tokens)
- ❌ No keychain integration

---

## Environment Variables

**For OAuth (Claude Max):**

```bash
# Option 1: Run setup-token and copy
claude setup-token
export CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-xxxxx...

# Option 2: Use existing token
export CLAUDE_OAUTH_TOKEN=sk-ant-oat01-xxxxx...
```

**For API Key:**

```bash
export ANTHROPIC_API_KEY=sk-ant-api03-xxxxx...
```

**Auto-detection priority:**

1. `CLAUDE_CODE_OAUTH_TOKEN` (OAuth)
2. `CLAUDE_OAUTH_TOKEN` (OAuth alternate)
3. `ANTHROPIC_API_KEY` (API key)

---

## Testing

**Verify OAuth token is set:**

```bash
echo $CLAUDE_CODE_OAUTH_TOKEN
# Should start with: sk-ant-oat01-
```

**Test CLI directly:**

```bash
claude --print "Hello, world"
# Should return response without errors
```

**Test programmatically:**

```python
import subprocess
result = subprocess.run(
    ['claude', '--print', 'Hello'],
    capture_output=True,
    text=True
)
print(result.stdout)
```

---

## References

- GitHub Issue #9887: OAuth authentication not supported by API
- Article: "Unlocking Claude Code's Full Subscription"
- Claude Code CLI docs: `claude --help`
- Anthropic API docs: Does not mention OAuth tokens
