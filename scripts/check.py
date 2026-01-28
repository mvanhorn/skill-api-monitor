#!/usr/bin/env python3
"""
Skill API Monitor - Check APIs for updates and recommend skill changes.

Usage:
  python3 check.py              # Full check
  python3 check.py --skill X    # Check specific skill
  python3 check.py --dry-run    # List skills only
  python3 check.py --json       # JSON output
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Load skill -> API mappings
SCRIPT_DIR = Path(__file__).parent
SKILL_APIS_FILE = SCRIPT_DIR / "skill_apis.json"

def load_skill_apis() -> dict:
    """Load skill to API mappings."""
    if SKILL_APIS_FILE.exists():
        with open(SKILL_APIS_FILE) as f:
            return json.load(f)
    return {}

def get_user_skills(github_user: str = "mvanhorn") -> list:
    """Get list of public Clawdbot skills from GitHub."""
    try:
        result = subprocess.run(
            ["gh", "repo", "list", github_user, "--json", "name,isPrivate", "-L", "100"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            repos = json.loads(result.stdout)
            skills = []
            for repo in repos:
                name = repo["name"]
                if name.startswith("clawdbot-skill-") and not repo["isPrivate"]:
                    skill_name = name.replace("clawdbot-skill-", "")
                    skills.append(skill_name)
                elif name == "nano-triple" and not repo["isPrivate"]:
                    skills.append("nano-triple")
            return skills
    except Exception as e:
        print(f"Error fetching repos: {e}", file=sys.stderr)
    return []

def search_x_for_updates(twitter_handle: str, days: int = 7) -> list:
    """Search X/Twitter for recent announcements."""
    # Use search-x skill if available
    search_script = Path.home() / "clawd/skills/search-x/scripts/search.js"
    if not search_script.exists():
        return []
    
    try:
        query = f"from:{twitter_handle.replace('@', '')} (API OR update OR new OR feature OR release)"
        result = subprocess.run(
            ["node", str(search_script), "--days", str(days), "--json", query],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            return data.get("tweets", [])
    except Exception as e:
        print(f"X search error for {twitter_handle}: {e}", file=sys.stderr)
    return []

def fetch_changelog(url: str) -> str:
    """Fetch changelog/blog content."""
    if not url:
        return ""
    try:
        # Simple curl fetch
        result = subprocess.run(
            ["curl", "-sL", "--max-time", "10", url],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            return result.stdout[:5000]  # Truncate
    except:
        pass
    return ""

def check_skill_api(skill_name: str, api_info: dict, days: int = 7) -> dict:
    """Check a single skill's API for updates."""
    result = {
        "skill": skill_name,
        "api": api_info.get("name", "Unknown"),
        "updates_found": [],
        "recommendation": None
    }
    
    # Check X/Twitter
    twitter = api_info.get("twitter")
    if twitter:
        tweets = search_x_for_updates(twitter, days)
        for tweet in tweets[:3]:  # Limit to 3
            content = tweet.get("text", "")[:200]
            if any(kw in content.lower() for kw in ["api", "new", "update", "feature", "launch", "release"]):
                result["updates_found"].append({
                    "source": "X",
                    "handle": twitter,
                    "content": content
                })
    
    # Check changelog if available
    changelog_url = api_info.get("changelog")
    if changelog_url:
        content = fetch_changelog(changelog_url)
        # Look for recent dates in changelog
        today = datetime.now()
        for i in range(days):
            check_date = today - timedelta(days=i)
            date_str = check_date.strftime("%Y-%m-%d")
            date_str2 = check_date.strftime("%B %d")
            if date_str in content or date_str2 in content:
                result["updates_found"].append({
                    "source": "Changelog",
                    "url": changelog_url,
                    "content": f"Recent update found around {date_str}"
                })
                break
    
    # Generate recommendation
    if result["updates_found"]:
        result["recommendation"] = f"Review {api_info.get('name', skill_name)} updates - potential skill enhancement"
    
    return result

def main():
    parser = argparse.ArgumentParser(description="Skill API Monitor")
    parser.add_argument("--skill", "-s", help="Check specific skill only")
    parser.add_argument("--days", "-d", type=int, default=7, help="Days to look back (default: 7)")
    parser.add_argument("--dry-run", action="store_true", help="List skills without checking")
    parser.add_argument("--json", "-j", action="store_true", help="JSON output")
    parser.add_argument("--github-user", default="mvanhorn", help="GitHub username")
    
    args = parser.parse_args()
    
    skill_apis = load_skill_apis()
    
    # Get skills to check
    if args.skill:
        skills = [args.skill]
    else:
        skills = get_user_skills(args.github_user)
        if not skills:
            # Fallback to configured skills
            skills = list(skill_apis.keys())
    
    if args.dry_run:
        print(f"Skills to check ({len(skills)}):")
        for s in skills:
            api_info = skill_apis.get(s, {})
            api_name = api_info.get("name", "Unknown API")
            print(f"  • {s}: {api_name}")
        return
    
    # Check each skill
    results = []
    for skill in skills:
        api_info = skill_apis.get(skill, {})
        if not api_info:
            continue
        
        if not args.json:
            print(f"Checking {skill}...", file=sys.stderr)
        
        result = check_skill_api(skill, api_info, args.days)
        results.append(result)
    
    # Output
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("\n" + "="*50)
        print("📊 SKILL API MONITOR REPORT")
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
            print("✅ No significant API updates found in the last week.")
        
        print(f"\nChecked {len(results)} skills • {datetime.now().strftime('%Y-%m-%d %H:%M')}")

if __name__ == "__main__":
    main()
