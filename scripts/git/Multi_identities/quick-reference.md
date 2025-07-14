# Multi-Git Quick Reference Card

## Initial Setup
```bash
./setup-multi-git.sh
source ~/.bashrc
```

## Daily Commands

### Switch Context
```bash
use-personal    # Switch to personal account
use-work       # Switch to work account  
git-context    # Show current context
```

### Clone New Repos

**SSH (Recommended)**
```bash
# Personal
git clone git@github.com-personal:username/repo.git

# Work
git clone git@github.com-work:organization/repo.git
```

**HTTPS (Context-dependent)**
```bash
use-personal  # or use-work
git clone https://github.com/username/repo.git
```

### Convert Existing Repos
```bash
# Auto-detect
./setup-multi-git.sh --convert

# Force specific
./setup-multi-git.sh --convert --personal
./setup-multi-git.sh --convert --work

# Scan all
./setup-multi-git.sh --scan
```

## File Locations

| File | Purpose |
|------|---------|
| `~/.env-personal` | Personal credentials |
| `~/.env-work` | Work credentials |
| `~/.ssh/id_ed25519_personal` | Personal SSH key |
| `~/.ssh/id_ed25519_work` | Work SSH key |
| `~/.gitconfig-personal` | Personal git config |
| `~/.gitconfig-work` | Work git config |

## Quick Fixes

**Wrong account pushing?**
```bash
# Convert to correct account
./setup-multi-git.sh --convert
```

**Token expired?**
```bash
# Edit credentials
nano ~/.env-personal  # or ~/.env-work
# Reload
use-personal  # or use-work
```

**SSH not working?**
```bash
# Test connection
ssh -T git@github.com-personal
ssh -T git@github.com-work
```

## URLs Cheat Sheet

| Type | Personal | Work |
|------|----------|------|
| SSH | `git@github.com-personal:user/repo.git` | `git@github.com-work:org/repo.git` |
| HTTPS | `https://github.com/user/repo.git` | `https://github.com/org/repo.git` |

Remember: SSH = always correct account, HTTPS = depends on context