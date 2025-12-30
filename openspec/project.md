# Project Context

## Purpose

RepoSwarm is an AI-powered multi-repository architecture discovery platform that:

- **Generates Standardized Documentation**: Produces `.arch.md` architecture files for codebases using AI analysis
- **Analyzes GitHub Repositories**: Uses Claude AI to deeply understand repository structure, patterns, and conventions
- **Enables Agent Context**: Creates documentation specifically designed to help other AI agents understand codebases
- **Provides Intelligent Caching**: Implements two-level caching to minimize redundant API calls and optimize costs
- **Supports Multiple Repository Types**: Tailors analysis based on repository type (backend, frontend, mobile, libraries, infrastructure)

**Key Insight**: This is a meta-analysis system - it uses AI to analyze codebases and generate documentation that helps other AI agents understand those codebases more effectively.

## Tech Stack

### Core Technologies

- **Python 3.12+** - Primary programming language
- **Temporal** - Workflow orchestration with durable execution and automatic retries
- **Anthropic Claude API** - AI-powered code analysis (claude-opus-4-5-20251101)
- **mise** - Environment and task management
- **uv** - Modern Python package manager

### Key Libraries

- **GitPython** - Repository cloning and git operations
- **boto3** - AWS DynamoDB integration for production caching
- **pytest + pytest-asyncio** - Testing framework
- **rich** - Enhanced console output and formatting
- **requests** - HTTP client for GitHub API

### Storage Options

- **File-based storage** - Local development (no AWS required)
- **AWS DynamoDB** - Production deployment with TTL-based cache expiration

### Infrastructure

- **Docker** - Containerization for production deployments
- **GitHub Actions** - CI/CD (potential)
- **AWS Systems Manager** - Secret management for production

## Project Conventions

### Code Style

- **Python Standards**: Follow PEP 8 with type hints for all public APIs
- **File Headers**: All code files start with two-line `ABOUTME:` comments explaining the file's purpose
- **Naming Conventions**:
  - Classes: PascalCase (e.g., `ClaudeInvestigator`, `PromptContextBase`)
  - Functions/methods: snake_case (e.g., `analyze_with_claude_context`, `check_needs_investigation`)
  - Constants: UPPER_SNAKE_CASE (e.g., `WORKFLOW_CHUNK_SIZE`, `CACHE_TTL_DAYS`)
  - Private methods: prefix with `_` (e.g., `_extract_version`, `_build_context`)
- **Imports**: Group imports (standard library, third-party, local) with clear separation
- **Type Hints**: Required for all function signatures in public APIs
- **Dataclasses**: Prefer dataclasses for models and configuration objects

### Architecture Patterns

1. **Storage Abstraction Pattern**
   - Abstract base class (`PromptContextBase`) defines storage interface
   - Multiple implementations (file-based, DynamoDB) share common interface
   - Configuration-driven selection via environment variables
   - Enables seamless switching between local dev and production

2. **Authentication Abstraction Pattern**
   - Unified authentication detection via `auth_detector.py`
   - Supports multiple authentication methods (OAuth tokens, API keys)
   - Priority-based credential resolution (OAuth > API key)
   - Client factory pattern selects appropriate client (CLI vs SDK)
   - Transparent switching between authentication methods
   - Location: `src/investigator/core/auth_detector.py`, `claude_client_factory.py`

3. **Temporal Workflow Pattern**
   - Durable execution survives process crashes
   - Automatic retry with exponential backoff
   - Continue-As-New pattern for long-running workflows
   - Activity-based composition for testability

4. **Two-Level Caching**
   - **Investigation-level cache**: Repository-wide (commit SHA + branch + prompt versions)
   - **Prompt-level cache**: Step-specific (repo + step + commit + version)
   - Granular cache invalidation based on changes

5. **Prompt Versioning System**
   - Each prompt file starts with `version=N` header
   - Version changes trigger selective re-analysis
   - Cache keys include prompt version for reproducibility
   - Version header stripped before sending to Claude API

6. **Context Chaining**
   - Prompts can reference previous analysis steps
   - Results build incrementally with growing context
   - Enables complex multi-step analysis workflows

### Testing Strategy

**Unit Tests** (`tests/unit/`):

- Mock all external dependencies (Git, Claude API, DynamoDB)
- Test individual components in isolation
- Fast execution target: <10 seconds total
- Focus: Logic validation, cache decision algorithms, prompt loading

**Integration Tests** (`tests/integration/`):

- Use real Claude API with actual API key
- Test end-to-end workflows with test repositories
- Slower execution: 30-60 seconds acceptable
- Focus: Component interactions, real API behavior, repository type detection

**Test Organization**:

- Run unit tests frequently during development: `mise test-units`
- Run integration tests before commits: `mise test-integration`
- Run all tests before releases: `mise test-all`
- DynamoDB-specific tests: `mise test-dynamodb`

**Test Requirements**:

- All new features require both unit and integration tests
- Tests must use real data, not mocked behavior
- Test output must be pristine (no unexpected logs/errors)
- Cache behavior must be explicitly tested

### Git Workflow

- **Main Branch**: `main` (stable, production-ready code)
- **Development**: Feature branches merged to main via PRs
- **Commit Convention**: Descriptive messages focusing on "why" not "what"
- **License**: Polyform Noncommercial License 1.0.0 (contact for commercial use)
- **No Beads**: This project does not use beads workflow (uses standard git workflow)

## Domain Context

### Repository Types

RepoSwarm categorizes repositories into specialized types, each with tailored analysis prompts:

- **backend**: APIs, databases, services, data layers, events/messaging
- **frontend**: Components, state management, routing, UI frameworks
- **mobile**: Device features, offline support, platform-specific code, navigation
- **libraries**: Public API surface, internal implementations, versioning
- **infra-as-code**: Resources, environments, deployment configurations
- **generic**: Fallback for unknown/mixed repository types

### Prompt System

- **Base Prompts** (`prompts/base_prompts.json`): 17 standard analysis steps shared across all types
- **Type-Specific Prompts** (`prompts/[type]/prompts.json`): Override or extend base prompts
- **Shared Templates** (`prompts/shared/*.md`): Reusable prompt templates with placeholders
- **Processing Order**: Sequential execution with dependency tracking

### Analysis Workflow

1. **Clone & Detect**: Clone repository, detect type
2. **Structure Analysis**: Build file tree, identify key patterns
3. **Incremental Analysis**: Execute prompts in processing_order
4. **Context Building**: Each step receives previous results as context
5. **Result Aggregation**: Combine all steps into final `.arch.md`
6. **Cache & Commit**: Save metadata, commit to architecture hub

### Key Concepts

- **Architecture Hub**: Separate repository where `.arch.md` files are committed
- **Cache Invalidation**: Triggered by new commits, branch changes, or prompt version updates
- **Prompt Placeholders**: `{{STRUCTURE}}` (file tree), `{{CONTEXT}}` (previous results)
- **Investigation Metadata**: Tracks commit SHA, branch, prompt versions, timestamps

## Important Constraints

### Technical Constraints

- **Python Version**: Requires Python 3.12+ (not compatible with older versions)
- **Claude API**: Requires valid Anthropic API key with Opus 4.5 access
- **Memory**: Large repositories may require significant memory for structure analysis
- **Rate Limits**: Claude API has rate limits; workflow chunks repos to manage this
- **GitHub Access**: Private repositories require GitHub token with appropriate permissions

### Business Constraints

- **License**: Polyform Noncommercial License 1.0.0 - commercial use requires explicit permission
- **API Costs**: Claude API calls are expensive; caching is critical for cost control
- **Analysis Time**: Large repositories can take 30-60 minutes per full analysis

### Regulatory Constraints

- **Data Privacy**: Repository code is sent to Anthropic's API (review their data policies)
- **Secret Scanning**: Should not analyze repositories containing production secrets

### Development Constraints

- **Local Testing**: Requires Temporal server running locally for workflow testing
- **DynamoDB**: Optional for local dev, required for production deployments
- **Environment Files**: `.env.local` must be created manually (not in version control)

## External Dependencies

### Required Services

**Anthropic Claude API**

- **Purpose**: AI-powered code analysis and documentation generation
- **Model**: claude-opus-4-5-20251101 (configurable)
- **Authentication**: Supports two methods:
  - **OAuth Token** (Claude Max): `CLAUDE_CODE_OAUTH_TOKEN` or `CLAUDE_OAUTH_TOKEN` - Generated via `claude setup-token`, provides access to Claude Max models
  - **API Key** (Standard): `ANTHROPIC_API_KEY` - Standard Anthropic API key from console
- **Authentication Priority**: OAuth tokens checked first, then API key (fallback)
- **Client Selection**: OAuth uses Claude CLI subprocess, API key uses Anthropic SDK directly
- **Rate Limits**: Varies by tier, managed via workflow chunking
- **Docs**: https://docs.anthropic.com/

**Temporal**

- **Purpose**: Workflow orchestration, durable execution, automatic retries
- **Server**: Local development or remote Temporal Cloud
- **Port**: Default 7233 for server, 8233 for UI
- **Authentication**: Optional for Temporal Cloud deployments
- **Docs**: https://docs.temporal.io/

**GitHub API**

- **Purpose**: Repository cloning, metadata fetching, organization repo listing
- **Authentication**: `GITHUB_TOKEN` supports classic PATs (ghp*) and fine-grained tokens (ghu*, github*pat*\*) for private repos
- **Fine-grained permissions**: Repository contents (read) and metadata (read); add extra read scopes only if needed
- **Recommendation**: Prefer fine-grained tokens for least-privilege access
- **Rate Limits**: 5000 requests/hour (authenticated), 60 requests/hour (unauthenticated)
- **Docs**: https://docs.github.com/en/rest

### Optional Services

**AWS DynamoDB**

- **Purpose**: Production-grade caching with TTL support
- **Tables**: `temporary_analysis_data`, `analysis_results`, `investigation_cache`
- **Authentication**: AWS credentials via boto3 (IAM role or access keys)
- **Region**: Configurable via AWS SDK
- **Alternative**: File-based storage for local development

**AWS Systems Manager (SSM)**

- **Purpose**: Secret management for production deployments
- **Use Case**: Store environment variables in Parameter Store
- **Command**: `mise deploy-secrets` uploads `.env` to SSM
- **Docs**: https://docs.aws.amazon.com/systems-manager/

### Key Configuration Variables

```bash
# Required - Claude Authentication (choose one)
# Option 1: OAuth Token (Claude Max subscription)
CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-...  # Generate via: mise claude-login
# Option 2: API Key (Standard Anthropic API)
ANTHROPIC_API_KEY=sk-ant-api03-...        # Get from: https://console.anthropic.com/

# Local Development (file-based storage)
LOCAL_TESTING=true                     # Use file storage instead of DynamoDB
SKIP_DYNAMODB_CHECK=true              # Skip DynamoDB health checks
PROMPT_CONTEXT_STORAGE=file           # Storage backend: 'file' or 'dynamodb'

# Architecture Hub (result repository)
ARCH_HUB_REPO_NAME=results-hub        # Repository name for .arch.md files
ARCH_HUB_BASE_URL=https://github.com/user  # Base URL for hub repository

# Git Identity (for commits)
GIT_USER_NAME="Architecture Bot"      # Git author name
GIT_USER_EMAIL=bot@example.com        # Git author email

# Optional
GITHUB_TOKEN=ghp_...                  # GitHub PAT for private repositories
```
