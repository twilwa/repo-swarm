# Changelog

All notable changes to RepoSwarm will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **GitHub Fine-Grained Personal Access Token Support** - RepoSwarm now supports GitHub's fine-grained personal access tokens (`github_pat_*` and `ghu_*` formats) in addition to classic tokens (`ghp_*`). This provides:
  - Enhanced security through granular repository-level permissions
  - Reduced security risk surface with time-limited, scope-restricted tokens
  - Automatic token type detection and appropriate authentication header formatting
  - Improved error messages with token-type-specific troubleshooting guidance
  - Full backward compatibility with existing classic PATs

  See [GitHub Token Migration Guide](docs/GITHUB_TOKEN_MIGRATION.md) for details on switching to fine-grained tokens.

### Changed

- GitHub API authentication now uses `Bearer` token format for both classic and fine-grained tokens (with automatic fallback for compatibility)
- Token validation and error handling enhanced to provide token-type-specific guidance
- Environment configuration documentation updated with fine-grained token setup instructions

### Security

- Token sanitization in error messages and logs now handles all token formats (classic, fine-grained user, and fine-grained PAT)
- Diagnostic output in `verify_config.py` improved to mask tokens while still providing format validation feedback

---

## [1.0.0] - Initial Release

### Added

- Initial RepoSwarm release with multi-repository architecture discovery
- Claude Code SDK integration for AI-powered analysis
- Temporal workflow orchestration for reliable execution
- DynamoDB and file-based storage options
- Intelligent caching to minimize redundant API calls
- Support for multiple repository types (backend, frontend, mobile, libraries, infrastructure)
- Standardized .arch.md architecture documentation generation
