# Claude Authentication Verification Checklist

Use this checklist to verify your RepoSwarm Claude authentication is properly configured.

## Prerequisites

- [ ] Python 3.12+ installed
- [ ] `mise` tool installed (`brew install mise` on macOS)
- [ ] RepoSwarm dependencies installed (`mise dev-dependencies`)

## Step 1: Choose Your Authentication Method

### Option A: OAuth Token (Claude Max Subscription)

- [ ] You have an active Claude Max subscription
- [ ] Run `mise claude-login` to generate OAuth token
- [ ] Copy the displayed token (starts with `sk-ant-oat01-`)
- [ ] Add to `.env.local`:
  ```bash
  CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-your-token-here
  ```

### Option B: API Key (Standard Anthropic API)

- [ ] Visit https://console.anthropic.com/
- [ ] Create or copy your API key (starts with `sk-ant-api03-`)
- [ ] Add to `.env.local`:
  ```bash
  ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
  ```

## Step 2: Verify Configuration

Run the authentication status check:

```bash
mise claude-status
```

Expected output for valid configuration:

```
✅ Claude authentication is configured correctly!
```

### Verify Token Format

| Token Type  | Expected Prefix | Expected Length   |
| ----------- | --------------- | ----------------- |
| OAuth Token | `sk-ant-oat01-` | 50-200 characters |
| API Key     | `sk-ant-api03-` | 50-200 characters |

## Step 3: Verify Full Configuration

Run comprehensive configuration check:

```bash
mise verify-config
```

This validates:

- [ ] Claude authentication credentials
- [ ] GitHub token (if configured)
- [ ] Repository access
- [ ] Storage configuration

## Step 4: Test Investigation

Run a quick test investigation:

```bash
mise investigate-one hello-world
```

Expected behavior:

- [ ] No authentication errors
- [ ] Analysis starts successfully
- [ ] Results generated in `temp/` directory

## Troubleshooting

### "No Claude authentication credentials found"

**Cause**: No valid credentials in environment variables.

**Fix**:

1. Ensure `.env.local` exists (not just `.env.example`)
2. Run `mise claude-login` for OAuth setup
3. Or add `ANTHROPIC_API_KEY` from https://console.anthropic.com/

### "Invalid token format"

**Cause**: Token doesn't match expected prefix or length.

**Fix**:

- OAuth tokens must start with `sk-ant-oat01-`
- API keys must start with `sk-ant-api03-`
- Verify token was copied correctly (no extra spaces or newlines)
- Token must be 50-200 characters long

### "Token expired"

**Cause**: OAuth token or API key has expired.

**Fix**:

- For OAuth: Run `mise claude-login` to generate a new token
- For API keys: Regenerate in Anthropic Console

### "Authentication method not working"

**Cause**: Token is valid format but rejected by API.

**Fix**:

1. Verify token is still active
2. Check rate limits in Anthropic dashboard
3. Ensure correct environment variable name

## Authentication Priority

RepoSwarm checks credentials in this order:

1. `CLAUDE_CODE_OAUTH_TOKEN` (highest priority)
2. `CLAUDE_OAUTH_TOKEN` (second priority)
3. `ANTHROPIC_API_KEY` (fallback)

If multiple are set, the highest priority one is used.

## Quick Reference Commands

| Command                       | Purpose                             |
| ----------------------------- | ----------------------------------- |
| `mise claude-login`           | Generate OAuth token (Claude Max)   |
| `mise claude-status`          | Check current authentication status |
| `mise verify-config`          | Full configuration validation       |
| `mise investigate-one <repo>` | Test investigation with single repo |

## Environment Variable Template

Copy to `.env.local`:

```bash
# Choose ONE of the following:

# Option 1: OAuth (Claude Max subscription)
CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-...

# Option 2: API Key (standard Anthropic API)
ANTHROPIC_API_KEY=sk-ant-api03-...
```

## Success Criteria

Authentication is properly configured when:

- [x] `mise claude-status` shows "✅ Valid"
- [x] `mise verify-config` passes auth checks
- [x] `mise investigate-one hello-world` runs without auth errors
