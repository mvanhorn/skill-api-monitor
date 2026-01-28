---
name: skill-api-monitor
description: Monitor APIs used by your Clawdbot skills and recommend updates when new features are released.
metadata:
  clawdbot:
    emoji: "🔍"
---

# Skill API Monitor 🔍

Automatically checks the APIs behind your Clawdbot skills for new features and recommends updates.

## What it does

1. Scans your GitHub repos for Clawdbot skills (mvanhorn/clawdbot-skill-*)
2. Maps each skill to its underlying API/service
3. Checks changelogs, docs, and X/Twitter for updates
4. Generates recommendations like "Parallel added X - recommend updating skill"

## Usage

```bash
# Run the full check
python3 {baseDir}/scripts/check.py

# Check specific skill
python3 {baseDir}/scripts/check.py --skill parallel

# Output as JSON
python3 {baseDir}/scripts/check.py --json

# Dry run (list skills without checking)
python3 {baseDir}/scripts/check.py --dry-run
```

## Supported Skills & APIs

| Skill | API | Check Sources |
|-------|-----|---------------|
| parallel | Parallel.ai | docs.parallel.ai, @p0 |
| polymarket | Gamma/Polymarket | docs.polymarket.com |
| tesla | Tesla Fleet API | developer.tesla.com |
| xai | xAI/Grok | x.ai/api, @xikidigital |
| search-x | xAI | Same as xai |
| manus | Manus AI | manus.ai |
| supabase | Supabase | supabase.com/changelog |
| remotion-server | Remotion | remotion.dev/changelog |
| nano-triple | Gemini | ai.google.dev |

## Scheduled Run

This skill is designed to run weekly via cron. The cron job calls this skill's check script and sends recommendations to Telegram.

## Adding New Skills

Edit `scripts/skill_apis.json` to add mappings:
```json
{
  "my-new-skill": {
    "name": "My New Skill",
    "api": "some-api.com",
    "docs": "https://docs.some-api.com",
    "changelog": "https://some-api.com/changelog",
    "twitter": "@someapi"
  }
}
```

## Environment

- `GITHUB_TOKEN` - For checking private repos (optional)
- `XAI_API_KEY` - For X/Twitter search via Grok
