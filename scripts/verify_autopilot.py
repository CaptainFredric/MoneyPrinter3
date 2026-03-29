#!/usr/bin/env python3
"""
Quick verification script to ensure ContentForge Autopilot is ready to go.
Run this anytime to validate system state.

Usage:
    python scripts/verify_autopilot.py
"""

import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "src"
SCRIPTS_DIR = ROOT / "scripts"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

def verify():
    """Run all verifications."""
    print("\n" + "=" * 60)
    print("  ContentForge Autopilot — Quick Verification")
    print("=" * 60)
    
    checks_passed = 0
    checks_total = 0
    
    # Check 1: Autopilot script exists
    checks_total += 1
    autopilot = SCRIPTS_DIR / "contentforge_autopilot.py"
    if autopilot.exists():
        print(f"  ✅ Autopilot script: {autopilot.name}")
        checks_passed += 1
    else:
        print(f"  ❌ Autopilot script missing: {autopilot}")
    
    # Check 2: Smart post script exists
    checks_total += 1
    smart_post = SCRIPTS_DIR / "smart_post_twitter.py"
    if smart_post.exists():
        print(f"  ✅ Twitter poster: {smart_post.name}")
        checks_passed += 1
    else:
        print(f"  ❌ Twitter poster missing: {smart_post}")
    
    # Check 3: API prototype exists
    checks_total += 1
    api_proto = SCRIPTS_DIR / "api_prototype.py"
    if api_proto.exists():
        print(f"  ✅ API module: {api_proto.name}")
        checks_passed += 1
    else:
        print(f"  ❌ API module missing: {api_proto}")
    
    # Check 4: Scorer importable
    checks_total += 1
    try:
        from api_prototype import score_tweet
        print(f"  ✅ Scorer function: score_tweet() available")
        checks_passed += 1
    except Exception as e:
        print(f"  ❌ Scorer error: {e}")
    
    # Check 5: Accounts in cache
    checks_total += 1
    try:
        from cache import get_twitter_cache_path
        cache_data = json.loads(Path(get_twitter_cache_path()).read_text())
        accounts = [a for a in cache_data.get("accounts", []) if a.get("nickname")]
        if len(accounts) >= 2:
            acct_names = [a["nickname"] for a in accounts]
            print(f"  ✅ Accounts: {', '.join(acct_names)}")
            checks_passed += 1
        else:
            print(f"  ❌ Not enough accounts: {len(accounts)} (need ≥2)")
    except Exception as e:
        print(f"  ❌ Cache error: {e}")
    
    # Check 6: Ollama reachable
    checks_total += 1
    try:
        import urllib.request as _ur
        with _ur.urlopen("http://localhost:11434/api/tags", timeout=3) as r:
            data = json.loads(r.read())
            models = [m["name"] for m in data.get("models", [])]
            if models:
                print(f"  ✅ Ollama: {models[0]} available")
                checks_passed += 1
            else:
                print(f"  ❌ Ollama: no models found")
    except Exception as e:
        print(f"  ❌ Ollama unreachable: {str(e)[:40]}")
    
    # Check 7: Proof log exists
    checks_total += 1
    runtime_dir = ROOT / ".mp" / "runtime"
    log_file = runtime_dir / "autopilot_posts.log"
    if log_file.exists():
        with open(log_file) as f:
            lines = len(f.readlines())
        print(f"  ✅ Proof log: {lines} post(s) recorded")
        checks_passed += 1
    else:
        print(f"  ⚠️  Proof log: not yet created (will be on first post)")
    
    # Check 8: State file exists
    checks_total += 1
    state_file = runtime_dir / "autopilot_state.json"
    if state_file.exists():
        with open(state_file) as f:
            state = json.load(f)
        posts = state.get("posts", [])
        cycles = state.get("cycle_count", 0)
        print(f"  ✅ State: {cycles} cycle(s), {len(posts)} post(s)")
        checks_passed += 1
    else:
        print(f"  ⚠️  State file: not yet created (will be on first run)")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"  Result: {checks_passed}/{checks_total} checks passed")
    if checks_passed == checks_total:
        print("  ✅ READY TO POST")
        print("\n  Next: python scripts/contentforge_autopilot.py --loop")
    elif checks_passed >= checks_total - 2:
        print("  ⚠️  MOSTLY READY (log/state will be created on first run)")
        print("\n  Next: python scripts/contentforge_autopilot.py --dry-run")
    else:
        print("  ❌ NOT READY — fix errors above")
        sys.exit(1)
    
    print("=" * 60 + "\n")

if __name__ == "__main__":
    verify()
