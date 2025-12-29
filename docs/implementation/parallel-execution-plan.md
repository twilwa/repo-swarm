# RepoSwarm Authentication Enhancement - Workstream Summary

## Overview

Created **49 tasks** across **2 major features** optimized for parallel gpt-5-deployer execution.

### Features

- **repo-swarm-w8a**: GitHub Fine-Grained Token Support (21 tasks)
- **repo-swarm-vyr**: Claude Max OAuth Authentication (28 tasks)

## Parallel Execution Structure

### GitHub Fine-Grained Token Support (21 tasks)

```
WAVE 1 (Sequential - Foundation)
├─ repo-swarm-wqh: GH-1.1 Create token detection utility ✓ READY
├─ repo-swarm-l8v: GH-1.2 Add token validation
└─ repo-swarm-cx4: GH-1.3 Update git_manager validation

WAVE 2 (7 parallel tasks after foundation)
├─ API Updates (2 tasks)
│  ├─ repo-swarm-vme: GH-2.1 Standardize API auth headers
│  └─ repo-swarm-qo0: GH-2.2 Update git URL auth
├─ Config/Diagnostics (2 tasks)
│  ├─ repo-swarm-msq: GH-3.1 Update verify_config
│  └─ repo-swarm-9k4: GH-3.2 Update env config
└─ Documentation (3 tasks)
   ├─ repo-swarm-c7z: GH-4.1 Update README
   ├─ repo-swarm-775: GH-4.2 Update examples
   └─ repo-swarm-md6: GH-4.3 Update openspec

WAVE 3 (Error Handling - 2 parallel tasks)
├─ repo-swarm-u9q: GH-5.1 Improve error messages
└─ repo-swarm-692: GH-5.2 Add troubleshooting

WAVE 4 (Testing - 3 parallel tasks)
├─ repo-swarm-8vs: GH-6.1 Unit tests
├─ repo-swarm-9wc: GH-6.2 Integration tests
└─ repo-swarm-8nt: GH-6.3 Update existing tests

WAVE 5 (Validation - 3 parallel tasks)
├─ repo-swarm-ylh: GH-7.1 Manual testing
├─ repo-swarm-t4o: GH-7.2 Security review
└─ repo-swarm-jq3: GH-7.3 OpenSpec validation

WAVE 6 (Deployment - 3 parallel tasks)
├─ repo-swarm-jft: GH-8.1 Update CHANGELOG
├─ repo-swarm-acu: GH-8.2 Migration guide
└─ repo-swarm-mr2: GH-8.3 Communication plan
```

### Claude Max OAuth Authentication (28 tasks)

```
WAVE 1 (Sequential - Foundation)
├─ repo-swarm-7t4: CL-1.1 Create auth detection ✓ READY
└─ repo-swarm-6wg: CL-1.2 Add auth validation

WAVE 2 (2 parallel client workstreams)
├─ CLI Client Workstream (3 sequential tasks)
│  ├─ repo-swarm-mft: CL-2.1 Create ClaudeCLIClient
│  ├─ repo-swarm-jmm: CL-2.2 Add env handling
│  └─ repo-swarm-l2z: CL-2.3 Subprocess management
└─ SDK Client Workstream (2 sequential tasks)
   ├─ repo-swarm-ag9: CL-3.1 Create ClaudeSDKClient
   └─ repo-swarm-pyv: CL-3.2 Backward compatibility

WAVE 3 (Factory - needs both clients)
├─ repo-swarm-lou: CL-4.1 Create factory
└─ repo-swarm-b92: CL-4.2 Add interface

WAVE 4 (11 parallel tasks after factory)
├─ Integration (4 tasks)
│  ├─ repo-swarm-ben: CL-5.1 Update ClaudeAnalyzer
│  ├─ repo-swarm-jpo: CL-5.2 Update ClaudeInvestigator
│  ├─ repo-swarm-0ie: CL-5.3 Update Temporal activities
│  └─ repo-swarm-7rp: CL-5.4 Update worker init
├─ Configuration (2 tasks)
│  ├─ repo-swarm-2ml: CL-6.1 Update env vars
│  └─ repo-swarm-xyc: CL-6.2 Update config validation
├─ CLI Tools (2 tasks)
│  ├─ repo-swarm-m49: CL-7.1 Add claude-login
│  └─ repo-swarm-l04: CL-7.2 Add claude-status
└─ Documentation (3 tasks)
   ├─ repo-swarm-j58: CL-8.1 Update README
   ├─ repo-swarm-5e2: CL-8.2 Update .env.example
   └─ repo-swarm-wq8: CL-8.3 Update openspec

WAVE 5 (Testing - 4 parallel tasks)
├─ repo-swarm-sed: CL-9.1 Unit tests CLI client
├─ repo-swarm-k48: CL-9.2 Unit tests auth detection
├─ repo-swarm-397: CL-9.3 Integration tests
└─ repo-swarm-ttb: CL-9.4 Update existing tests

WAVE 6 (Validation - 4 parallel tasks)
├─ repo-swarm-48v: CL-10.1 Manual testing
├─ repo-swarm-a1v: CL-10.2 Performance testing
├─ repo-swarm-0x9: CL-10.3 Documentation review
└─ repo-swarm-pak: CL-10.4 OpenSpec validation
```

## Maximum Parallelization Points

### Most Parallel Execution Opportunities

**GitHub Token Support:**

- **Wave 2**: 7 parallel tasks (API, Config, Docs)
- **Wave 4-6**: 3 parallel tasks per wave

**Claude OAuth:**

- **Wave 2**: 2 parallel workstreams (CLI + SDK clients)
- **Wave 4**: 11 parallel tasks (Integration, Config, Tools, Docs)
- **Wave 5-6**: 4 parallel tasks per wave

### Combined Cross-Feature Parallelism

Both features are **completely independent** and can run in parallel:

- Start both foundation tasks simultaneously (GH-1.1 + CL-1.1)
- Continue parallel execution across both features throughout
- **Theoretical max parallel agents**: ~18 agents during Wave 4 Claude OAuth + Wave 2 GitHub

## Ready to Start (4 tasks)

✓ **repo-swarm-wqh**: GH-1.1 Create token type detection utility
✓ **repo-swarm-7t4**: CL-1.1 Create auth detection utility
✓ **repo-swarm-w8a**: GitHub Fine-Grained Token Support (epic)
✓ **repo-swarm-vyr**: Claude Max OAuth Authentication (epic)

## Next Steps

1. Start with 2 parallel gpt-5-deployer agents on foundation tasks:
   - Agent 1: `repo-swarm-wqh` (GitHub token detection)
   - Agent 2: `repo-swarm-7t4` (Claude auth detection)

2. As tasks complete, `bd ready` will show newly unblocked work

3. Deploy more agents as parallel opportunities open up (Waves 2, 4, etc.)

4. Monitor progress with:
   ```bash
   bd stats              # Overall statistics
   bd blocked            # See blocked tasks
   bd list --status=in_progress  # Active work
   ```
