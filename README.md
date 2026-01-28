# Skill API Monitor 🔍

Monitor the APIs behind your Moltbot/Clawdbot skills and get notified when new features are released.

## Installation

```bash
# Clone into your skills directory
git clone https://github.com/mvanhorn/skill-api-monitor.git ~/.clawdbot/skills/skill-api-monitor
```

Or install via ClawdHub:
```bash
clawdhub install skill-api-monitor
```

## Usage

```bash
# First time? Run interactive setup
python3 scripts/check.py --setup

# Or specify your username directly
python3 scripts/check.py --github-user YOUR_USERNAME --discover

# Check for API updates (last 7 days)
python3 scripts/check.py --github-user YOUR_USERNAME --days 7

# After setup saves your username, just run:
python3 scripts/check.py --days 7
```

### Setup Walkthrough

The `--setup` command guides you through:
1. **Enter username** - Your GitHub username
2. **Discover skills** - Finds your moltbot-skill-*/clawdbot-skill-* repos
3. **Detect APIs** - Shows which API each skill uses
4. **Save config** - Optionally saves username for future runs

## How It Works

1. **Discovers** your public Moltbot skills from GitHub
   - Matches `moltbot-skill-*` and `clawdbot-skill-*` repos
   - Also detects repos with SKILL.md containing Moltbot metadata

2. **Auto-detects** which API each skill uses
   - Reads SKILL.md content
   - Pattern matches against 20+ known APIs

3. **Scans** changelogs and docs
   - Fetches changelog/blog pages
   - Looks for recent dates + update keywords

4. **Reports** recommendations
   - Lists skills with recent API updates
   - Suggests reviewing for potential enhancements

## Supported APIs

Auto-detects: Parallel.ai, Supabase, Tesla, xAI, Remotion, Gemini, Polymarket, Spotify, OpenAI, Anthropic, Stripe, Notion, Slack, Discord, GitHub, Linear, Vercel, and more.

Add your own in `scripts/skill_apis.json`.

## Automatic Weekly Checks

This skill doesn't run automatically by default - you set up your own schedule.

### Option 1: Moltbot Cron (Recommended)

If you're using Moltbot, ask your agent to set up a weekly cron:

> "Set up a weekly cron job to run skill-api-monitor every Sunday at 10 AM"

### Option 2: System Cron

Add to your crontab (`crontab -e`):

```bash
# Run every Sunday at 10 AM
0 10 * * 0 python3 /path/to/skill-api-monitor/scripts/check.py --github-user YOUR_USERNAME --days 7
```

### Option 3: GitHub Actions

Create `.github/workflows/check.yml` in your repo:

```yaml
name: Weekly API Check
on:
  schedule:
    - cron: '0 10 * * 0'  # Sundays 10 AM UTC
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python3 scripts/check.py --github-user YOUR_USERNAME --days 7
```

## Requirements

- Python 3.10+
- `gh` CLI (GitHub CLI)
- `curl`

## License

MIT
