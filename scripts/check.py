#!/usr/bin/env python3
"""
Skill API Monitor - Dynamically discover skills and check APIs for updates.

Supports both Moltbot (new name) and Clawdbot (old name) skill patterns.
MoltHub/ClawdHub registry support included.

Usage:
  python3 check.py              # Full check
  python3 check.py --skill X    # Check specific skill
  python3 check.py --dry-run    # List skills only
  python3 check.py --json       # JSON output
  python3 check.py --discover   # Just discover skills
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
SKILL_APIS_FILE = SCRIPT_DIR / "skill_apis.json"

# Known API patterns to detect from SKILL.md content
API_PATTERNS = {
    "parallel.ai": {"name": "Parallel.ai", "docs": "https://docs.parallel.ai", "twitter": "@p0", "changelog": "https://parallel.ai/blog"},
    "polymarket": {"name": "Polymarket/Gamma", "docs": "https://docs.polymarket.com", "twitter": "@Polymarket"},
    "gamma-api": {"name": "Polymarket/Gamma", "docs": "https://docs.polymarket.com", "twitter": "@Polymarket"},
    "tesla": {"name": "Tesla Fleet API", "docs": "https://developer.tesla.com/docs/fleet-api", "twitter": "@Tesla", "changelog": "https://developer.tesla.com/docs/fleet-api"},
    "x.ai": {"name": "xAI/Grok", "docs": "https://docs.x.ai", "twitter": "@xikidigital"},
    "xai": {"name": "xAI/Grok", "docs": "https://docs.x.ai", "twitter": "@xikidigital"},
    "grok": {"name": "xAI/Grok", "docs": "https://docs.x.ai", "twitter": "@xikidigital"},
    "manus": {"name": "Manus AI", "docs": "https://docs.manus.ai", "twitter": "@maboroshiAI"},
    "supabase": {"name": "Supabase", "docs": "https://supabase.com/docs", "twitter": "@supabase", "changelog": "https://supabase.com/changelog"},
    "remotion": {"name": "Remotion", "docs": "https://www.remotion.dev/docs", "twitter": "@remotion_dev", "changelog": "https://www.remotion.dev/changelog"},
    "gemini": {"name": "Google Gemini", "docs": "https://ai.google.dev/gemini-api/docs", "twitter": "@GoogleAI"},
    "spotify": {"name": "Spotify Web API", "docs": "https://developer.spotify.com/documentation/web-api", "twitter": "@SpotifyPlatform"},
    "opensnow": {"name": "OpenSnow", "docs": "https://opensnow.com", "twitter": "@openaboret"},
    "clay": {"name": "Clay.com", "docs": "https://docs.clay.com", "twitter": "@clay"},
    "granola": {"name": "Granola AI", "docs": "https://granola.ai", "twitter": "@granaborai"},
}


def discover_public_skills(github_user: str = "mvanhorn") -> list:
    """Dynamically discover public Moltbot/Clawdbot skills from GitHub.
    
    Note: Clawdbot was renamed to Moltbot. ClawdHub is now MoltHub.
    This function handles both naming conventions during the transition.
    """
    skills = []
    
    # Patterns to match (old and new naming)
    SKILL_PREFIXES = [
        "moltbot-skill-",      # New naming
        "clawdbot-skill-",     # Old naming (still common)
        "molt-skill-",         # Possible short form
        "clawd-skill-",        # Possible short form
    ]
    
    # Keywords that indicate a skill repo
    SKILL_KEYWORDS = [
        "moltbot", "clawdbot", "molthub", "clawdhub",
        "skill", "agent skill", "agentskill"
    ]
    
    try:
        result = subprocess.run(
            ["gh", "repo", "list", github_user, "--json", "name,isPrivate,description", "-L", "200"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            repos = json.loads(result.stdout)
            for repo in repos:
                name = repo["name"]
                is_private = repo.get("isPrivate", True)
                desc = repo.get("description", "") or ""
                
                # Skip private repos
                if is_private:
                    continue
                
                # Check prefixes (moltbot-skill-*, clawdbot-skill-*, etc.)
                skill_name = None
                for prefix in SKILL_PREFIXES:
                    if name.startswith(prefix):
                        skill_name = name.replace(prefix, "")
                        break
                
                if skill_name:
                    skills.append({
                        "name": skill_name,
                        "repo": f"{github_user}/{name}",
                        "description": desc
                    })
                    continue
                
                # Check for keyword matches in name or description
                name_lower = name.lower()
                desc_lower = desc.lower()
                combined = f"{name_lower} {desc_lower}"
                
                # Must have at least one moltbot/clawdbot keyword AND skill-related keyword
                has_brand = any(kw in combined for kw in ["moltbot", "clawdbot", "molthub", "clawdhub"])
                has_skill = "skill" in combined
                
                if has_brand and has_skill:
                    skills.append({
                        "name": name,
                        "repo": f"{github_user}/{name}",
                        "description": desc
                    })
                    continue
                
                # Also check repos that might be skills without the prefix
                # by looking for SKILL.md with moltbot/clawdbot metadata
                if name not in ["dotfiles", "config", ".github"]:  # Skip common non-skill repos
                    try:
                        # Fetch SKILL.md content to verify it's a Moltbot/Clawdbot skill
                        check = subprocess.run(
                            ["gh", "api", f"repos/{github_user}/{name}/contents/SKILL.md", "-q", ".content"],
                            capture_output=True, text=True, timeout=10
                        )
                        if check.returncode == 0 and check.stdout.strip():
                            import base64
                            content = base64.b64decode(check.stdout.strip()).decode('utf-8', errors='ignore').lower()
                            # Only include if it has moltbot/clawdbot metadata
                            is_moltbot_skill = any(kw in content for kw in [
                                "moltbot:", "clawdbot:", "metadata:", 
                                "molthub", "clawdhub", "{basedir}"
                            ])
                            if is_moltbot_skill:
                                skills.append({
                                    "name": name,
                                    "repo": f"{github_user}/{name}",
                                    "description": desc,
                                    "detected_via": "SKILL.md"
                                })
                    except:
                        pass
    except Exception as e:
        print(f"Error discovering skills: {e}", file=sys.stderr)
    
    return skills


def fetch_skill_readme(repo: str) -> str:
    """Fetch SKILL.md content from a repo."""
    try:
        # Try SKILL.md first
        result = subprocess.run(
            ["gh", "api", f"repos/{repo}/contents/SKILL.md", "-q", ".content"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0 and result.stdout.strip():
            import base64
            return base64.b64decode(result.stdout.strip()).decode('utf-8', errors='ignore')
    except:
        pass
    return ""


def detect_api_from_content(content: str, skill_name: str) -> dict:
    """Detect which API a skill uses from its SKILL.md content."""
    content_lower = content.lower()
    
    # Check known patterns
    for pattern, api_info in API_PATTERNS.items():
        if pattern.lower() in content_lower:
            return api_info.copy()
    
    # Try to extract from URLs in content
    url_match = re.search(r'https?://(?:docs\.|api\.|www\.)?([a-zA-Z0-9-]+)\.(com|ai|dev|io)', content)
    if url_match:
        domain = url_match.group(1)
        for pattern, api_info in API_PATTERNS.items():
            if domain in pattern or pattern in domain:
                return api_info.copy()
    
    # Fallback: use skill name to guess
    for pattern, api_info in API_PATTERNS.items():
        if pattern in skill_name or skill_name in pattern:
            return api_info.copy()
    
    return {"name": f"Unknown ({skill_name})", "docs": None, "twitter": None}


def search_x_for_updates(twitter_handle: str, days: int = 7) -> list:
    """Search X/Twitter for recent announcements."""
    if not twitter_handle:
        return []
    
    search_script = Path.home() / "clawd/skills/search-x/scripts/search.js"
    if not search_script.exists():
        return []
    
    try:
        handle = twitter_handle.replace('@', '')
        query = f"from:{handle} (API OR update OR new OR feature OR release OR announce OR launch)"
        result = subprocess.run(
            ["node", str(search_script), "--days", str(days), "--json", query],
            capture_output=True, text=True, timeout=90
        )
        if result.returncode == 0 and result.stdout.strip():
            try:
                data = json.loads(result.stdout)
                return data.get("tweets", [])
            except json.JSONDecodeError:
                pass
    except Exception as e:
        print(f"X search error for {twitter_handle}: {e}", file=sys.stderr)
    return []


def fetch_changelog(url: str) -> str:
    """Fetch changelog/blog content."""
    if not url:
        return ""
    try:
        result = subprocess.run(
            ["curl", "-sL", "--max-time", "10", url],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            return result.stdout[:10000]
    except:
        pass
    return ""


def check_skill_api(skill: dict, api_info: dict, days: int = 7, skip_x: bool = False) -> dict:
    """Check a single skill's API for updates."""
    result = {
        "skill": skill["name"],
        "repo": skill.get("repo", ""),
        "api": api_info.get("name", "Unknown"),
        "updates_found": [],
        "recommendation": None
    }
    
    # Check X/Twitter (skip if flag set - it's slow)
    twitter = api_info.get("twitter")
    if twitter and not skip_x:
        tweets = search_x_for_updates(twitter, days)
        for tweet in tweets[:3]:
            content = tweet.get("text", tweet.get("content", ""))[:200]
            if content and any(kw in content.lower() for kw in ["api", "new", "update", "feature", "launch", "release", "announce"]):
                result["updates_found"].append({
                    "source": "X",
                    "handle": twitter,
                    "content": content
                })
    
    # Check changelog if available
    changelog_url = api_info.get("changelog")
    if changelog_url:
        content = fetch_changelog(changelog_url)
        if content:
            today = datetime.now()
            for i in range(days):
                check_date = today - timedelta(days=i)
                date_formats = [
                    check_date.strftime("%Y-%m-%d"),
                    check_date.strftime("%B %d"),
                    check_date.strftime("%b %d"),
                ]
                for date_str in date_formats:
                    if date_str in content:
                        result["updates_found"].append({
                            "source": "Changelog",
                            "url": changelog_url,
                            "content": f"Recent update found around {check_date.strftime('%Y-%m-%d')}"
                        })
                        break
                else:
                    continue
                break
    
    # Generate recommendation
    if result["updates_found"]:
        result["recommendation"] = f"Review {api_info.get('name', skill['name'])} updates - potential skill enhancement"
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Skill API Monitor")
    parser.add_argument("--skill", "-s", help="Check specific skill only")
    parser.add_argument("--days", "-d", type=int, default=7, help="Days to look back (default: 7)")
    parser.add_argument("--dry-run", action="store_true", help="List skills without checking APIs")
    parser.add_argument("--discover", action="store_true", help="Just discover and list skills with detected APIs")
    parser.add_argument("--json", "-j", action="store_true", help="JSON output")
    parser.add_argument("--github-user", "-u", default="mvanhorn", help="GitHub username")
    parser.add_argument("--skip-x", action="store_true", help="Skip X/Twitter search (faster)")
    
    args = parser.parse_args()
    
    # Discover skills dynamically
    print(f"🔍 Discovering public skills for {args.github_user}...", file=sys.stderr)
    skills = discover_public_skills(args.github_user)
    
    if not skills:
        print("No public Clawdbot skills found.", file=sys.stderr)
        return
    
    print(f"   Found {len(skills)} public skills", file=sys.stderr)
    
    # Detect APIs for each skill
    skill_data = []
    for skill in skills:
        print(f"   Analyzing {skill['name']}...", file=sys.stderr)
        readme = fetch_skill_readme(skill["repo"])
        api_info = detect_api_from_content(readme, skill["name"])
        skill_data.append({
            "skill": skill,
            "api_info": api_info
        })
    
    if args.discover or args.dry_run:
        print(f"\n📊 **Public Skills for {args.github_user}** ({len(skill_data)} found)\n")
        for sd in skill_data:
            skill = sd["skill"]
            api = sd["api_info"]
            print(f"• **{skill['name']}**")
            print(f"  Repo: {skill['repo']}")
            print(f"  API: {api.get('name', 'Unknown')}")
            if api.get('twitter'):
                print(f"  Twitter: {api['twitter']}")
            if api.get('docs'):
                print(f"  Docs: {api['docs']}")
            print()
        return
    
    # Filter to specific skill if requested
    if args.skill:
        skill_data = [sd for sd in skill_data if sd["skill"]["name"] == args.skill]
        if not skill_data:
            print(f"Skill '{args.skill}' not found", file=sys.stderr)
            return
    
    # Check each skill
    print(f"\n⏳ Checking APIs for updates (last {args.days} days)...", file=sys.stderr)
    results = []
    for sd in skill_data:
        result = check_skill_api(sd["skill"], sd["api_info"], args.days, skip_x=args.skip_x)
        results.append(result)
    
    # Output
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("\n" + "="*50)
        print("📊 SKILL API MONITOR REPORT")
        print(f"   User: {args.github_user}")
        print(f"   Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"   Lookback: {args.days} days")
        print("="*50 + "\n")
        
        updates_found = False
        for r in results:
            if r["updates_found"]:
                updates_found = True
                print(f"🔔 **{r['skill']}** ({r['api']})")
                for u in r["updates_found"]:
                    source = u.get("source", "")
                    content = u.get("content", "")[:150]
                    print(f"   [{source}] {content}")
                if r["recommendation"]:
                    print(f"   💡 {r['recommendation']}")
                print()
        
        if not updates_found:
            print("✅ No significant API updates found.\n")
            print("Skills checked:")
            for r in results:
                print(f"  • {r['skill']} ({r['api']})")
        
        print(f"\n📈 Checked {len(results)} skills")


if __name__ == "__main__":
    main()
