# Sybil-OS Maintainer Agent

Automated code review and approval for the Sybil-OS repository.

## Setup

1. Generate a GitHub Personal Access Token with `repo` scope.

2. Add to your `.env`:
```bash
GITHUB_TOKEN=your_github_token_here
GITHUB_REPO=hmnuiodaryim0-lab/sybil-OS
CREATOR_MENTION=hmnuiodaryim0-lab
```

3. Run:
```bash
python -m core.maintainer
```

## Cron Setup (Every Hour)

```bash
# Edit crontab
crontab -e

# Add:
0 * * * * cd /path/to/sybil-OS && python -m core.maintainer >> maintainer.log 2>&1
```

## Features

- **Security Scan**: Detects hardcoded secrets (API keys, tokens, passwords)
- **Architecture Validation**: Ensures HumanCognitiveProfile compatibility
- **ETHICS.md Compliance**: Flags potential ethical violations
- **Auto-Merge**: Minor doc updates merge automatically
- **Manual Review**: Code changes tag creator for approval
- **Security Risk**: Suspicious PRs get closed and labeled
