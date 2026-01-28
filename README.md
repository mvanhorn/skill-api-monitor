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
# Discover your public skills
python3 scripts/check.py --github-user YOUR_USERNAME --discover

# Check for API updates (last 7 days)
python3 scripts/check.py --github-user YOUR_USERNAME --days 7

# Full check with X/Twitter (slower)
python3 scripts/check.py --github-user YOUR_USERNAME --days 7 --include-x
```

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

## Requirements

- Python 3.10+
- `gh` CLI (GitHub CLI)
- `curl`

## License

MIT
