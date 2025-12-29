<!-- OPENSPEC:START -->

# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:

- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:

- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# Agent Instructions

## Project: RepoSwarm

**RepoSwarm** is an AI-powered multi-repository architecture discovery platform that analyzes GitHub repositories using the Claude Code SDK and generates standardized `.arch.md` documentation files.

**For detailed architecture, code paths, and development tools, see [CLAUDE.md](CLAUDE.md).**

## Quick Start

### First Time Setup

1. **Configure environment**:

   ```bash
   cp .env.example .env.local
   # Edit .env.local with your ANTHROPIC_API_KEY
   ```

2. **Install dependencies**:

   ```bash
   mise install
   mise run dev-dependencies
   ```

3. **Test configuration**:

   ```bash
   mise verify-config
   ```

4. **Run investigation**:
   ```bash
   mise investigate-one hello-world
   ```

### Key Commands

**Development**:

```bash
mise dev-temporal          # Start Temporal server
mise dev-worker            # Start Temporal worker
mise kill                  # Stop all Temporal processes
```

**Investigation**:

```bash
mise investigate-all       # Analyze all configured repos
mise investigate-one <repo-url-or-name>  # Analyze single repo
mise investigate-debug <repo>            # Debug mode with verbose logging
```

**Testing**:

```bash
mise test-all              # Run full test suite
mise test-units            # Unit tests only (fast)
mise test-integration      # Integration tests (requires API key)
```

## Project Structure

```
repo-swarm/
├── src/
│   ├── workflows/          # Temporal workflow definitions
│   │   ├── investigate_repos_workflow.py       # Multi-repo coordinator
│   │   └── investigate_single_repo_workflow.py # Single repo analysis
│   │
│   ├── activities/         # Temporal activity implementations
│   │   ├── investigate_activities.py           # Core investigation logic
│   │   └── investigation_cache_activities.py   # Cache validation
│   │
│   ├── investigator/       # Core analysis engine
│   │   ├── investigator.py                     # ClaudeInvestigator main class
│   │   └── core/
│   │       ├── claude_analyzer.py              # Claude API integration
│   │       ├── repository_analyzer.py          # Structure analysis
│   │       ├── analysis_results_collector.py   # Result aggregation
│   │       └── config.py                       # Configuration constants
│   │
│   ├── models/             # Pydantic data models
│   └── utils/              # Storage abstractions
│       ├── prompt_context_base.py              # Abstract storage interface
│       ├── prompt_context_file.py              # File-based storage
│       └── prompt_context_dynamodb.py          # DynamoDB storage
│
├── prompts/                # Analysis prompts by repository type
│   ├── base_prompts.json   # Standard 17-step analysis flow
│   ├── backend/            # Backend-specific prompts
│   ├── frontend/           # Frontend-specific prompts
│   ├── mobile/             # Mobile-specific prompts
│   ├── libraries/          # Library-specific prompts
│   ├── shared/             # Reusable prompt templates
│   └── repos.json          # Repository configuration
│
├── tests/
│   ├── unit/               # Fast, isolated tests
│   └── integration/        # End-to-end tests with real API calls
│
└── temp/                   # Generated .arch.md files (local mode)
```

## Key Architectural Concepts

### Temporal Workflows

RepoSwarm uses **Temporal.io** for reliable, resumable workflow orchestration:

- **`InvestigateReposWorkflow`** - Coordinates analysis of multiple repositories in parallel chunks
- **`InvestigateSingleRepoWorkflow`** - Handles single repository analysis with intelligent caching

**Why Temporal?**

- Durable execution survives crashes/restarts
- Automatic retries with exponential backoff
- Built-in execution history for debugging
- Horizontal scalability via worker distribution

**Key Files**:

- `src/workflows/investigate_repos_workflow.py:53-250` - Multi-repo workflow
- `src/workflows/investigate_single_repo_workflow.py:53-400` - Single repo workflow

### Two-Level Caching

**Investigation-Level Cache** (Repository-wide):

- Stores: commit SHA, branch, prompt versions, full results
- TTL: 90 days
- Purpose: Skip entire analysis if nothing changed
- Location: `investigation_cache` table or `temp/cache/`

**Prompt-Level Cache** (Step-specific):

- Key: `{repo}_{step}_{commit}_v{version}`
- TTL: 90 days (persists across investigations)
- Purpose: Avoid redundant Claude API calls for unchanged prompt+commit combinations
- Location: `analysis_results` table or `temp/prompt_context_storage/`

**Cache Invalidation Triggers**:

1. New commits detected
2. Branch changed
3. Prompt version incremented
4. Force flag set

**Key Files**:

- `src/activities/investigation_cache.py:30-300` - Cache decision logic
- `src/activities/investigation_cache_activities.py:1-200` - Cache activities

### Storage Abstraction

Supports two backends via abstract interface:

- **File-based** (`PROMPT_CONTEXT_STORAGE=file`) - For local development
- **DynamoDB** (`PROMPT_CONTEXT_STORAGE=dynamodb`) - For production

Both implement `PromptContextBase` interface:

- `save_prompt_data()` - Store prompt + repo structure
- `get_prompt_and_context()` - Retrieve with context from previous steps
- `get_result()` - Get analysis result
- `cleanup()` - Remove temporary data

**Key Files**:

- `src/utils/prompt_context_base.py:10-150` - Abstract interface
- `src/utils/prompt_context_file.py:20-300` - File implementation
- `src/utils/prompt_context_dynamodb.py:20-400` - DynamoDB implementation

### Prompt System

**Organization**:

- `prompts/base_prompts.json` - 17 standard analysis steps (shared across all types)
- `prompts/[type]/prompts.json` - Type-specific prompt configurations
- `prompts/shared/*.md` - Reusable prompt templates

**Prompt Versioning**:

- First line of each prompt: `version=N`
- Used for cache invalidation
- Incremented when prompt logic changes

**Context Chaining**:

- Steps can reference previous steps as context
- Example: `module_deep_dive` includes results from `hl_overview`
- Enables Claude to build on previous insights

**Key Files**:

- `prompts/base_prompts.json:1-200` - Base analysis configuration
- `prompts/shared/hl_overview.md` - High-level overview prompt
- `src/investigator/core/claude_analyzer.py:50-100` - Version extraction

## Common Workflows

### Add a New Repository

1. Edit `prompts/repos.json`:

   ```json
   {
     "my-repo": {
       "url": "https://github.com/org/repo",
       "type": "backend", // or frontend, mobile, libraries, infra-as-code
       "description": "API service for X"
     }
   }
   ```

2. Test analysis:

   ```bash
   mise investigate-one my-repo
   ```

3. Verify output:
   ```bash
   ls temp/my-repo.arch.md
   cat temp/my-repo.arch.md
   ```

### Modify a Prompt

1. Find prompt file: `prompts/shared/[name].md`

2. Increment version:

   ```diff
   - version=2
   + version=3
   ```

3. Make changes to prompt text

4. Test with single repo:

   ```bash
   mise investigate-one test-repo
   ```

5. Verify cache invalidation (should re-run that step only)

### Debug Failed Investigation

1. **Enable debug logging**:

   ```bash
   mise investigate-debug <repo-url>
   ```

2. **Check Temporal UI** (if running):
   - Open http://localhost:8233
   - View workflow execution history
   - Check activity failures and stack traces

3. **Common issues**:
   - **DynamoDB health check failed**: Set `SKIP_DYNAMODB_CHECK=true` in `.env.local`
   - **No prompts.json found**: Check `type` field matches directory name
   - **Claude API error**: Verify `ANTHROPIC_API_KEY` is valid
   - **Git clone failed**: Add `GITHUB_TOKEN` for private repos

4. **Verify configuration**:
   ```bash
   mise verify-config
   ```

## Testing Guidelines

**Unit Tests** (`tests/unit/`):

- Mock external dependencies (Git, Claude API, DynamoDB)
- Fast execution (<10 seconds total)
- Run before committing: `mise test-units`

**Integration Tests** (`tests/integration/`):

- Use real Claude API (requires `ANTHROPIC_API_KEY`)
- Test with real repositories
- Slower execution (30-60 seconds)
- Run before major changes: `mise test-integration`

**Full Test Suite**:

```bash
mise test-all  # Run all tests with coverage
```

**Writing Tests**:

- Place unit tests in `tests/unit/test_*.py`
- Place integration tests in `tests/integration/test_*.py`
- Follow existing patterns (see `test_investigation_cache.py` for example)
- Mock at boundaries: Git operations, API calls, storage

## Configuration Reference

**Environment Variables** (`.env.local`):

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Local development mode (recommended for dev)
LOCAL_TESTING=true
SKIP_DYNAMODB_CHECK=true
PROMPT_CONTEXT_STORAGE=file

# Architecture Hub (where results are saved)
ARCH_HUB_REPO_NAME=repo-swarm-sample-results-hub
ARCH_HUB_BASE_URL=https://github.com/royosherove

# Temporal (usually defaults are fine)
TEMPORAL_SERVER_URL=localhost:7233
TEMPORAL_NAMESPACE=default
TEMPORAL_TASK_QUEUE=investigate-task-queue

# Git identity for commits
GIT_USER_NAME="Architecture Bot"
GIT_USER_EMAIL=archbot@example.com

# Optional: For private repos
GITHUB_TOKEN=ghp_...
```

**Core Config** (`src/investigator/core/config.py`):

```python
CLAUDE_MODEL = "claude-opus-4-5-20251101"
MAX_TOKENS = 6000
WORKFLOW_CHUNK_SIZE = 8    # Parallel repo processing
WORKFLOW_SLEEP_HOURS = 6   # Sleep between workflow cycles
```

## Issue Tracking with Beads

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd sync               # Sync with git
```

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
   ```bash
   mise test-all  # Run full test suite
   ```
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**

- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds

## Additional Resources

- **Architecture Deep Dive**: See [CLAUDE.md](CLAUDE.md) for detailed code paths and architecture
- **README**: See [README.md](README.md) for user-facing documentation and getting started
- **Example Results**: https://github.com/royosherove/repo-swarm-sample-results-hub
- **Temporal Docs**: https://docs.temporal.io/
