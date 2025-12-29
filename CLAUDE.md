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

# ABOUTME: RepoSwarm Agent Guide - Architecture, Development Tools, and Code Paths

# ABOUTME: This guide provides AI agents with high-level overviews and implementation details for working with RepoSwarm

## Project Overview

RepoSwarm is an AI-powered multi-repository architecture discovery platform that:

- Analyzes GitHub repositories using Claude Code SDK
- Generates standardized `.arch.md` architecture documentation
- Runs via Temporal workflows for reliable, resumable execution
- Implements intelligent caching to minimize redundant API calls
- Supports multiple repository types (backend, frontend, mobile, libraries, infrastructure)

**Key Insight**: This is a meta-analysis system - it uses AI to analyze codebases and generate documentation that helps other AI agents understand those codebases.

## Architecture Overview

### Core Components & Their Interactions

```
┌─────────────────────────────────────────────────────────────┐
│  Temporal Workflows (Orchestration Layer)                    │
│  ├─ InvestigateReposWorkflow     (Multi-repo coordinator)   │
│  └─ InvestigateSingleRepoWorkflow (Single repo analysis)    │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Temporal Activities (Task Execution Layer)                  │
│  ├─ clone_repository_activity                                │
│  ├─ check_if_repo_needs_investigation (Cache validation)    │
│  ├─ analyze_repository_structure_activity                    │
│  ├─ save_prompt_context_activity                            │
│  ├─ analyze_with_claude_context (Claude API calls)          │
│  └─ save_to_arch_hub (Result persistence)                   │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Core Analysis Engine (Business Logic Layer)                 │
│  ├─ ClaudeInvestigator        (Main orchestrator)           │
│  ├─ ClaudeAnalyzer             (Claude API integration)      │
│  ├─ RepositoryAnalyzer         (Structure analysis)          │
│  ├─ GitRepositoryManager       (Git operations)              │
│  ├─ RepositoryTypeDetector     (Type detection)              │
│  └─ AnalysisResultsCollector   (Result aggregation)         │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Storage Abstraction Layer (Data Persistence)                │
│  ├─ PromptContextBase          (Abstract interface)          │
│  ├─ DynamoDBPromptContext      (AWS DynamoDB impl)          │
│  └─ FileBasedPromptContext     (Local file impl)            │
└─────────────────────────────────────────────────────────────┘
```

### Key Files by Layer

**Workflows** (`src/workflows/`):

- `investigate_repos_workflow.py:53-250` - Multi-repo workflow with Continue-As-New pattern
- `investigate_single_repo_workflow.py:53-400` - Single repo workflow with cache checks

**Activities** (`src/activities/`):

- `investigate_activities.py:1-800` - Core investigation activities
- `investigation_cache_activities.py:1-200` - Cache check/save activities
- `investigation_cache.py:30-300` - Cache decision logic and metadata management

**Core Engine** (`src/investigator/core/`):

- `investigator.py:37-500` - `ClaudeInvestigator` main class
- `claude_analyzer.py:15-200` - Claude API integration
- `repository_analyzer.py:15-300` - Repository structure analysis
- `analysis_results_collector.py:10-250` - Result aggregation and validation
- `config.py:8-147` - Configuration constants and validation

**Storage** (`src/utils/`):

- `prompt_context_base.py:10-150` - Abstract storage interface
- `prompt_context_dynamodb.py:20-400` - DynamoDB implementation
- `prompt_context_file.py:20-300` - File-based implementation

**Models** (`src/models/`):

- `investigation.py:10-200` - Investigation metadata and cache models
- `activities.py:10-300` - Activity input/output models
- `workflows.py:10-200` - Workflow request/response models
- `cache.py:10-100` - Cache-specific models

## Critical Code Paths

### 1. Investigation Flow (Happy Path)

**Entry**: `mise investigate-all` or `mise investigate-one [repo]`

**Path**:

```
1. client.py:main()
   └─> Triggers InvestigateReposWorkflow

2. investigate_repos_workflow.py:InvestigateReposWorkflow.run()
   ├─> read_repos_config() → prompts/repos.json
   ├─> update_repos_list() → GitHub API (optional)
   └─> For each repo chunk (parallel):
       └─> InvestigateSingleRepoWorkflow.run()

3. investigate_single_repo_workflow.py:InvestigateSingleRepoWorkflow.run()
   ├─> check_dynamodb_health() → Validate storage
   ├─> clone_repository_activity() → Clone repo to temp/
   ├─> get_prompts_config_activity() → Load prompts/[type]/prompts.json
   ├─> check_if_repo_needs_investigation()
   │   └─> investigation_cache.py:InvestigationCache.check_needs_investigation()
   │       ├─> Compare commit SHA
   │       ├─> Compare branch
   │       ├─> Compare prompt versions
   │       └─> Return InvestigationDecision (SKIP or INVESTIGATE)
   │
   ├─> IF SKIP: Return cached metadata, cleanup, exit
   │
   ├─> IF INVESTIGATE:
   │   ├─> analyze_repository_structure_activity()
   │   │   └─> repository_analyzer.py:analyze_structure()
   │   │
   │   ├─> read_dependencies_activity() + cache_dependencies_activity()
   │   │
   │   ├─> FOR EACH analysis step in processing_order:
   │   │   ├─> save_prompt_context_activity()
   │   │   │   └─> PromptContext.save_prompt_data()
   │   │   │
   │   │   ├─> analyze_with_claude_context()
   │   │   │   ├─> PromptContext.get_prompt_and_context()
   │   │   │   ├─> Build context from previous steps
   │   │   │   ├─> Check prompt-level cache
   │   │   │   ├─> IF CACHE MISS: Call Claude API
   │   │   │   └─> Save result to storage
   │   │   │
   │   │   └─> Continue to next step...
   │   │
   │   ├─> retrieve_all_results_activity()
   │   │   └─> PromptContextManager.retrieve_all_results()
   │   │
   │   ├─> AnalysisResultsCollector.combine_results()
   │   │   ├─> Validate all base sections present
   │   │   └─> Generate final markdown
   │   │
   │   ├─> write_analysis_result_activity()
   │   │   └─> Write .arch.md to temp/
   │   │
   │   ├─> save_to_arch_hub()
   │   │   └─> Commit to architecture hub repo
   │   │
   │   └─> save_investigation_metadata()
   │       └─> Cache metadata for future runs
   │
   └─> cleanup_repository_activity()
```

### 2. Cache Validation Path

**Entry**: `investigation_cache_activities.py:check_if_repo_needs_investigation()`

**Path**:

```
check_if_repo_needs_investigation(input: CacheCheckInput)
└─> InvestigationCache.check_needs_investigation()
    ├─> storage.get_investigation_metadata(repo_name)
    │   └─> DynamoDB query OR file read
    │
    ├─> IF no cached metadata:
    │   └─> Return INVESTIGATE (reason: "No previous investigation")
    │
    ├─> GitRepositoryManager.get_current_state(repo_path)
    │   └─> Returns: (commit_sha, branch, has_uncommitted_changes)
    │
    ├─> Compare cached vs current:
    │   ├─> IF commit_sha != cached.latest_commit:
    │   │   └─> Return INVESTIGATE (reason: "New commits")
    │   │
    │   ├─> IF branch != cached.branch_name:
    │   │   └─> Return INVESTIGATE (reason: "Branch changed")
    │   │
    │   └─> IF prompt_versions != cached.prompt_metadata.versions:
    │       └─> Return INVESTIGATE (reason: "Prompts updated")
    │
    └─> Return SKIP (reason: "Up to date")
```

### 3. Prompt Processing Path

**Entry**: `investigate_activities.py:analyze_with_claude_context()`

**Path**:

```
analyze_with_claude_context(input: AnalyzeWithClaudeInput)
├─> PromptContext.get_prompt_and_context(step_name)
│   ├─> Load prompt template from storage
│   ├─> Load repository structure
│   ├─> Build context section:
│   │   └─> For each referenced step in context config:
│   │       └─> Retrieve previous step result
│   └─> Return: (prompt_text, context_text, repo_structure)
│
├─> Generate cache key: f"{repo_name}_{step_name}_{commit}_v{version}"
│
├─> Check prompt-level cache:
│   ├─> storage.get_result(cache_key)
│   └─> IF HIT: Return cached result
│
├─> IF MISS:
│   ├─> ClaudeAnalyzer.analyze_with_prompt()
│   │   ├─> Clean version header from prompt
│   │   ├─> Replace placeholders: {{STRUCTURE}}, {{CONTEXT}}
│   │   ├─> Call Anthropic API (claude-opus-4-5-20251101)
│   │   └─> Return analysis text
│   │
│   └─> storage.save_result(cache_key, result)
│
└─> Return result + metadata
```

## Development Tools & Commands

### Mise Task Reference

RepoSwarm uses **mise** for environment and task management. All tasks follow a logical naming convention:

**Development Tasks** (`dev-*`):

```bash
mise dev-temporal          # Start Temporal server (localhost:7233)
mise dev-worker            # Start Temporal worker (processes workflows)
mise dev-client            # Trigger workflow client
mise dev-hello             # Test basic workflow (sanity check)
mise kill                  # Stop all Temporal processes
mise dev-repos-list        # List configured repositories
mise dev-repos-update      # Update repo list from GitHub API
```

**Investigation Tasks** (`investigate-*`):

```bash
mise investigate-all       # Analyze all repos in prompts/repos.json
mise investigate-one       # Analyze single repo: mise investigate-one <repo-url-or-name>
mise investigate-public    # Analyze public repo (no auth required)
mise investigate-debug     # Run with DEBUG logging
```

**Testing Tasks** (`test-*`):

```bash
mise verify-config         # Validate .env.local and test repo access
mise test-all              # Run complete test suite (unit + integration)
mise test-units            # Unit tests only (fast)
mise test-integration      # Integration tests (slower, requires API key)
mise test-dynamodb         # DynamoDB-specific tests
```

**Maintenance Tasks**:

```bash
mise cleanup-temp          # Remove temp/ directory contents
mise monitor-workflow      # Check workflow status: mise monitor-workflow <workflow-id>
```

### Key Configuration Files

**Environment** (`.env.local` - create from `.env.example`):

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Local testing mode (file-based storage, no AWS)
LOCAL_TESTING=true
SKIP_DYNAMODB_CHECK=true
PROMPT_CONTEXT_STORAGE=file

# Architecture Hub (where .arch.md files are saved)
ARCH_HUB_REPO_NAME=repo-swarm-sample-results-hub
ARCH_HUB_BASE_URL=https://github.com/royosherove

# Git identity for commits
GIT_USER_NAME="Architecture Bot"
GIT_USER_EMAIL=archbot@example.com
```

**Repository List** (`prompts/repos.json`):

```json
{
  "default": "https://github.com/user/repo",
  "repositories": {
    "repo-name": {
      "url": "https://github.com/org/repo",
      "type": "backend", // backend, frontend, mobile, libraries, infra-as-code
      "description": "Short description"
    }
  }
}
```

**Prompts Configuration** (`prompts/[type]/prompts.json`):

```json
{
  "processing_order": [
    {
      "name": "hl_overview",
      "file": "../shared/hl_overview.md",
      "description": "High level overview",
      "context": [] // No dependencies
    },
    {
      "name": "module_deep_dive",
      "file": "../shared/module_deep_dive.md",
      "description": "Module analysis",
      "context": [
        { "type": "step", "val": "hl_overview" } // Depends on hl_overview
      ]
    }
  ]
}
```

### Testing Strategy

**Unit Tests** (`tests/unit/`):

- Mock external dependencies (Git, Claude API, DynamoDB)
- Test individual components in isolation
- Fast execution (<10 seconds total)
- Examples:
  - `test_analysis_results_collector.py` - Result aggregation logic
  - `test_investigation_cache.py` - Cache decision logic
  - `test_prompt_loading.py` - Prompt parsing and loading

**Integration Tests** (`tests/integration/`):

- Use real Claude API (requires `ANTHROPIC_API_KEY`)
- Test end-to-end workflows with test repositories
- Slower execution (30-60 seconds total)
- Examples:
  - `test_integration.py` - Full investigation workflow
  - `test_metadata_detection.py` - Repository type detection
  - `test_shared_prompts.py` - Prompt processing pipeline

**Running Tests**:

```bash
# All tests with coverage
mise test-all

# Fast feedback loop (unit tests only)
mise test-units

# Full integration testing
mise test-integration

# Watch mode (requires pytest-watch)
pytest-watch tests/unit/
```

## Prompt System Architecture

### Prompt Organization

**Base Prompts** (`prompts/base_prompts.json`):

- Defines 17 standard analysis steps
- Shared across all repository types
- Steps can reference previous steps for context

**Type-Specific Prompts** (`prompts/[type]/prompts.json`):

- Override or extend base prompts
- `backend/` - Database, API, events, messaging
- `frontend/` - Components, state, routing, UI
- `mobile/` - Device features, offline, platform-specific
- `libraries/` - API surface, internals, public/private interfaces
- `infra-as-code/` - Resources, deployment, scaling
- `generic/` - Fallback for unknown types

**Shared Templates** (`prompts/shared/*.md`):

- Actual prompt text files
- First line: `version=N` for cache invalidation
- Support placeholders: `{{STRUCTURE}}`, `{{CONTEXT}}`

### Prompt Versioning & Cache Invalidation

**Version Extraction** (`analysis_results_collector.py:extract_prompt_version()`):

```python
# Example prompt file:
# version=3
#
# Analyze the repository structure...

# Version is extracted and stored separately
# Used in cache key: f"{repo}_{step}_{commit}_v{version}"
# Note: Version line is removed from prompt before sending to Claude
```

**Cache Invalidation Triggers**:

1. Prompt version incremented → Re-analyze that step only
2. New commit → Re-analyze all steps
3. Branch changed → Re-analyze all steps
4. Force flag → Re-analyze all steps

**Context Chaining**:

```json
// module_deep_dive references hl_overview
{
  "name": "module_deep_dive",
  "context": [{ "type": "step", "val": "hl_overview" }]
}

// This means: Include hl_overview result in prompt context
// Enables Claude to build on previous insights
```

## Storage Abstraction Pattern

### Why Abstraction?

RepoSwarm supports two storage backends:

- **File-based**: For local development (no AWS required)
- **DynamoDB**: For production (scalable, distributed)

Both implement the same abstract interface, enabling seamless switching via config.

### Interface Design

**`PromptContextBase`** (`src/utils/prompt_context_base.py:10-80`):

```python
class PromptContextBase(ABC):
    @abstractmethod
    def save_prompt_data(self, step_name: str, prompt: str, structure: str) -> str:
        """Save prompt + context data, return reference key"""
        pass

    @abstractmethod
    def get_prompt_and_context(self, step_name: str) -> Tuple[str, str, str]:
        """Retrieve prompt, context from previous steps, structure"""
        pass

    @abstractmethod
    def get_result(self, step_name: str) -> Optional[str]:
        """Get analysis result for a step"""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up temporary storage"""
        pass
```

### Implementation Selection

**Configuration-driven** (`src/utils/prompt_context.py:15-40`):

```python
def create_prompt_context_manager(repo_name: str, ...) -> PromptContextManagerBase:
    storage_type = os.getenv("PROMPT_CONTEXT_STORAGE", "dynamodb")

    if storage_type == "file":
        return FileBasedPromptContextManager(...)
    elif storage_type == "dynamodb":
        return DynamoDBPromptContextManager(...)
    else:
        raise ValueError(f"Unknown storage type: {storage_type}")
```

**File Storage** (`prompt_context_file.py:20-200`):

- Stores in `temp/prompt_context_storage/[repo]/[step].json`
- Simple JSON serialization
- No TTL (manual cleanup)

**DynamoDB Storage** (`prompt_context_dynamodb.py:20-300`):

- Tables: `temporary_analysis_data`, `analysis_results`, `investigation_cache`
- TTL: 60 minutes for temp data, 90 days for cache
- Reference-based retrieval using unique keys

## Caching Strategy

### Two-Level Cache

**Level 1: Investigation-Level** (Repository-wide):

- **Key**: `repository_name`
- **Data**: Commit SHA, branch, prompt versions, full results
- **TTL**: 90 days
- **Purpose**: Skip entire investigation if nothing changed
- **Location**: `investigation_cache` table or `temp/cache/`

**Level 2: Prompt-Level** (Step-specific):

- **Key**: `{repo}_{step}_{commit}_v{version}` (note: `_v` prefix on version)
- **Data**: Single step analysis result
- **TTL**: 90 days (persists across investigations)
- **Purpose**: Avoid redundant Claude API calls for unchanged prompt+commit combinations
- **Location**: `analysis_results` table or `temp/prompt_context_storage/`

### Cache Decision Logic

**Implemented in**: `investigation_cache.py:InvestigationCache.check_needs_investigation()`

```python
def check_needs_investigation(...) -> InvestigationDecision:
    cached = storage.get_investigation_metadata(repo_name)

    if not cached:
        return INVESTIGATE("No previous investigation")

    current_commit, current_branch, _ = git.get_current_state(repo_path)

    if current_commit != cached.latest_commit:
        return INVESTIGATE("New commits detected")

    if current_branch != cached.branch_name:
        return INVESTIGATE("Branch changed")

    if prompt_versions != cached.prompt_metadata.versions:
        changed = find_changed_prompts(prompt_versions, cached.prompt_metadata.versions)
        return INVESTIGATE(f"Prompts updated: {changed}")

    return SKIP("Repository up to date")
```

### Cache Warming

**Automatic warming** during investigation:

1. Each step saves result immediately after Claude API call
2. Next step can retrieve previous results from cache
3. Final metadata saved at end with all versions/commits

**Manual cache clear**:

```bash
# No built-in command currently
# Workaround: Delete DynamoDB item or temp/cache/[repo].json
```

## Common Workflows

### Adding a New Repository Type

1. **Create prompts directory**:

   ```bash
   mkdir -p prompts/my-new-type
   ```

2. **Create prompts.json** (`prompts/my-new-type/prompts.json`):

   ```json
   {
     "processing_order": [
       {
         "name": "hl_overview",
         "file": "../shared/hl_overview.md",
         "description": "High level overview",
         "context": []
       },
       {
         "name": "custom_analysis",
         "file": "./custom_analysis.md",
         "description": "Type-specific analysis",
         "context": [{ "type": "step", "val": "hl_overview" }]
       }
     ]
   }
   ```

3. **Create custom prompts** (if needed):

   ```bash
   echo "version=1\n\nAnalyze this repository..." > prompts/my-new-type/custom_analysis.md
   ```

4. **Add repo to repos.json**:

   ```json
   {
     "my-repo": {
       "url": "https://github.com/org/repo",
       "type": "my-new-type",
       "description": "Description"
     }
   }
   ```

5. **Test**:
   ```bash
   mise investigate-one my-repo
   ```

### Modifying an Existing Prompt

1. **Find prompt file**: `prompts/shared/[prompt-name].md`

2. **Increment version**:

   ```diff
   - version=2
   + version=3

   Analyze the repository...
   ```

3. **Test with single repo**:

   ```bash
   mise investigate-one test-repo
   ```

   Verify cache is invalidated and step re-runs.

4. **Deploy to all repos**:

   ```bash
   mise investigate-all
   ```

   Only repos that used this prompt will be re-analyzed for that step.

### Debugging a Failed Investigation

1. **Check logs**:

   ```bash
   # Workflow logs
   mise monitor-workflow investigate-repos-workflow

   # Local file logs (if LOCAL_TESTING=true)
   tail -f temp/investigation.log
   ```

2. **Enable debug logging**:

   ```bash
   mise investigate-debug <repo-url>
   ```

3. **Verify configuration**:

   ```bash
   mise verify-config
   ```

4. **Check Temporal UI** (if running):
   - Open http://localhost:8233
   - View workflow execution history
   - Check activity failures and retry attempts

5. **Common issues**:
   - **"DynamoDB health check failed"**: Set `SKIP_DYNAMODB_CHECK=true` for local testing
   - **"No prompts.json found"**: Check `type` field in repos.json matches directory name
   - **"Claude API error"**: Verify `ANTHROPIC_API_KEY` is set and valid
   - **"Git clone failed"**: Check `GITHUB_TOKEN` for private repos

## Key Architectural Decisions

### Why Temporal?

- **Durable Execution**: Workflows survive process crashes/restarts
- **Reliable Retries**: Automatic retry with exponential backoff
- **Visibility**: Built-in execution history and debugging
- **Scalability**: Distribute workers across multiple machines
- **Continue-As-New**: Reset event history for long-running workflows

**File**: `src/workflows/investigate_repos_workflow.py:200-250` - Continue-As-New implementation

### Why Storage Abstraction?

- **Local Development**: Fast iteration without AWS setup
- **Production Scalability**: DynamoDB for distributed systems
- **Testing**: Easy to mock/fake storage layer
- **Future Flexibility**: Can add Redis, PostgreSQL, etc.

**File**: `src/utils/prompt_context_base.py:10-150` - Abstract interface

### Why Two-Level Caching?

- **Cost Optimization**: Minimize Claude API calls (expensive)
- **Selective Re-analysis**: Only re-run changed prompts
- **Fast Iteration**: Prompt authors get quick feedback
- **Granular Control**: Track exactly which prompt versions were used

**File**: `src/activities/investigation_cache.py:30-300` - Cache implementation

### Why Prompt Versioning?

- **Cache Invalidation**: Automatically re-analyze when prompts change
- **Reproducibility**: Know exactly which prompt version produced results
- **Gradual Rollout**: Update prompts incrementally, verify results
- **Debugging**: Trace issues to specific prompt versions

**File**: `src/investigator/core/claude_analyzer.py:50-100` - Version extraction

## Troubleshooting Reference

### Investigation Not Running

**Symptom**: `mise investigate-all` does nothing

**Diagnosis**:

```bash
# 1. Check Temporal server
mise monitor-temporal

# 2. Check worker
ps aux | grep investigate_worker

# 3. Check client trigger
mise dev-client
```

**Solution**: Ensure server + worker are running, then trigger client.

### Cache Always Hits (No Re-analysis)

**Symptom**: Changes not detected, investigation skipped

**Diagnosis**:

```bash
# Check git status in cloned repo
cd temp/repos/[repo-name]
git log -1  # Current commit
git status  # Uncommitted changes
```

**Solution**:

- Force re-analysis: Pass `force=true` in workflow input
- Clear cache: Delete `temp/cache/[repo].json` or DynamoDB item
- Verify prompt versions incremented

### Prompt Not Found

**Symptom**: `FileNotFoundError: prompts/backend/prompts.json`

**Diagnosis**:

```bash
# Check repo type
cat prompts/repos.json | grep -A3 "repo-name"

# Check directory exists
ls -la prompts/
```

**Solution**:

- Fix `type` field in repos.json
- Create missing prompts directory
- Use `"type": "generic"` as fallback

### Claude API Errors

**Symptom**: `APIError: rate_limit_exceeded` or `invalid_api_key`

**Diagnosis**:

```bash
# Verify key
echo $ANTHROPIC_API_KEY | head -c 20

# Check rate limits in Anthropic dashboard
# https://console.anthropic.com/
```

**Solution**:

- Wait for rate limit reset (check `Retry-After` header)
- Upgrade API tier for higher limits
- Reduce `WORKFLOW_CHUNK_SIZE` in config.py

## File Reference Quick Index

**Entry Points**:

- `src/client.py:1-100` - Workflow trigger
- `src/investigator/investigator.py:37-200` - Main investigator class

**Core Logic**:

- `src/workflows/investigate_single_repo_workflow.py:53-400` - Single repo workflow
- `src/activities/investigate_activities.py:1-800` - Investigation activities
- `src/investigator/core/claude_analyzer.py:15-200` - Claude integration

**Caching**:

- `src/activities/investigation_cache.py:30-300` - Cache logic
- `src/activities/investigation_cache_activities.py:1-200` - Cache activities

**Storage**:

- `src/utils/prompt_context_base.py:10-150` - Abstract interface
- `src/utils/prompt_context_file.py:20-300` - File implementation
- `src/utils/prompt_context_dynamodb.py:20-400` - DynamoDB implementation

**Configuration**:

- `src/investigator/core/config.py:8-147` - Core config
- `.env.example:1-45` - Environment template
- `prompts/repos.json:1-120` - Repository list

**Prompts**:

- `prompts/base_prompts.json:1-200` - Base analysis steps
- `prompts/shared/*.md` - Shared prompt templates
- `prompts/[type]/prompts.json` - Type-specific configurations

**Testing**:

- `tests/unit/test_investigation_cache.py` - Cache logic tests
- `tests/integration/test_integration.py` - End-to-end tests
- `tests/integration/test_shared_prompts.py` - Prompt processing tests
