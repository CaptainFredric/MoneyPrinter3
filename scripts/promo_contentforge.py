#!/usr/bin/env python3
"""
scripts/promo_contentforge.py

ContentForge Self-Promotion Script — dogfoods the live API to generate and
score promotional tweet drafts, then posts the highest-scoring one via the
Twitter bot.

Flow:
  1. Call ContentForge /v1/tweet_ideas for the target niche
  2. Score each draft with ContentForge /v1/score_tweet
  3. Pick the highest-scoring tweet (grade A preferred, then B)
  4. Post it via smart_post_twitter.py using the target account

Usage:
  python scripts/promo_contentforge.py
  python scripts/promo_contentforge.py --account EyeCatcher
  python scripts/promo_contentforge.py --niche "content marketing" --dry-run
  python scripts/promo_contentforge.py --headless

Options:
  --account     Target account (niche_launch_1 or EyeCatcher, default: best available)
  --niche       Override niche for tweet generation
  --dry-run     Generate and score without posting
  --headless    Pass headless flag to browser automation
  --count       Number of tweet ideas to generate (default: 10, best one is picked)
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "src"
SCRIPTS_DIR = ROOT / "scripts"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Import local functions from api_prototype (uses Ollama locally, Gemini in prod)
try:
    from api_prototype import (
        score_tweet as _score_tweet_fn,
        _llm_generate,
        batch_score as _batch_score_fn,
    )
    _LOCAL_API_AVAILABLE = True
except ImportError:
    try:
        from api_prototype import score_tweet as _score_tweet_fn, _llm_generate
        _batch_score_fn = None
        _LOCAL_API_AVAILABLE = True
    except ImportError:
        _LOCAL_API_AVAILABLE = False
        _batch_score_fn = None

# ---------------------------------------------------------------------------
# ContentForge API client (direct HTTP — no external deps)
# ---------------------------------------------------------------------------
CONTENTFORGE_BASE = "https://contentforge-api-lpp9.onrender.com"
LOCAL_BASE = "http://127.0.0.1:8081"

# Niches per account — aligned with their topic/persona
ACCOUNT_NICHES: dict[str, list[str]] = {
    "niche_launch_1": [
        "headline writing and copywriting",
        "viral hooks and content marketing",
        "building in public and indie hacking",
        "tweet optimization and growth hacking",
        "AI tools for content creators",
    ],
    "EyeCatcher": [
        "attention psychology in social media",
        "scroll-stopping content design",
        "visual storytelling and brand building",
        "content strategy for personal brands",
        "neuroscience of viral content",
    ],
}

DEFAULT_NICHE_APPEND = (
    " — occasionally mention ContentForge API, a free tool on RapidAPI that "
    "scores headlines and tweet drafts instantly"
)


def _call_api(endpoint: str, payload: dict, base: str = CONTENTFORGE_BASE) -> dict | None:
    url = f"{base}{endpoint}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"  API error {e.code} on {endpoint}: {body[:200]}", file=sys.stderr)
        return None
    except Exception as ex:
        print(f"  Connection error on {endpoint}: {ex}", file=sys.stderr)
        return None


def _get_tweet_ideas(niche: str, count: int = 10) -> list[str]:
    """Generate tweet ideas. Uses local Ollama first, falls back to production API."""
    # 1. Try local LLM (fastest, no quota issues)
    if _LOCAL_API_AVAILABLE:
        try:
            prompt = (
                f"Generate {count} tweet ideas for someone in the '{niche}' niche.\n"
                f"Rules:\n"
                f"- Each tweet under 280 characters\n"
                f"- Mix formats: hot take, tip, question, story hook, list\n"
                f"- Include 1-2 relevant hashtags per tweet\n"
                f"- Return ONLY a JSON array of strings\n"
                f"Example: [\"Tweet 1\", \"Tweet 2\"]"
            )
            raw = _llm_generate(prompt)
            match = re.search(r'\[.*?\]', raw, re.DOTALL)
            if match:
                tweets = json.loads(match.group(0))
                tweets = [t for t in tweets if isinstance(t, str) and 10 < len(t) <= 300][:count]
                if tweets:
                    return tweets
        except Exception as ex:
            print(f"  Local LLM attempt failed: {ex}. Trying production API...")

    # 2. Fall back to production HTTP API
    result = _call_api("/v1/tweet_ideas", {
        "niche": niche,
        "count": count,
        "hashtags": True,
    })
    if result and "tweets" in result:
        return result["tweets"]
    return []


def _score_tweet(text: str) -> dict:
    """Score a tweet draft. Uses local function if available."""
    if _LOCAL_API_AVAILABLE:
        try:
            return _score_tweet_fn(text)
        except Exception:
            pass
    # Fall back to HTTP
    result = _call_api("/v1/score_tweet", {"text": text})
    return result or {}


def _pick_best_tweet(tweets: list[str], verbose: bool = True) -> tuple[str, int, str]:
    """Score all tweets and return (best_text, best_score, best_grade).

    Uses batch_score (one local call) when available; falls back to sequential scoring.
    """
    best_text = ""
    best_score = -1
    best_grade = "D"

    if verbose:
        print(f"\n  Scoring {len(tweets)} tweet drafts via ContentForge...\n")

    # --- Fast path: local batch_score (one call) ---
    if _LOCAL_API_AVAILABLE and _batch_score_fn is not None:
        try:
            results = _batch_score_fn(tweets)  # list of dicts with score/grade/text
            if results:
                # batch_score returns sorted best-first
                top = results[0]
                for i, r in enumerate(results):
                    if verbose:
                        grade = r.get("grade", "D")
                        score = r.get("score", 0)
                        preview = tweets[r.get("index", i)][:70]
                        print(f"  [{r.get('index', i)+1:2d}] Grade {grade} | Score {score:3d} — {preview}...")
                return tweets[top.get("index", 0)], top.get("score", 0), top.get("grade", "D")
        except Exception as ex:
            print(f"  batch_score failed ({ex}), falling back to sequential scoring...")

    # --- Slow path: score one at a time ---
    for i, text in enumerate(tweets):
        if not text or len(text) < 10:
            continue
        result = _score_tweet(text)
        score = result.get("score", 0)
        grade = result.get("grade", "D")
        char_count = result.get("char_count", len(text))
        suggestions = result.get("suggestions", [])

        if verbose:
            print(f"  [{i+1:2d}] Grade {grade} | Score {score:3d} | {char_count}c — {text[:70]}...")
            if suggestions:
                print(f"       💡 {suggestions[0]}")

        if score > best_score:
            best_score = score
            best_text = text
            best_grade = grade

        time.sleep(0.2)  # be polite to the API

    return best_text, best_score, best_grade


def _post_override(account: str, content: str, headless: bool) -> bool:
    """Inject the chosen tweet as a forced post via smart_post_twitter.py."""
    try:
        from runtime_python import resolve_runtime_python
        venv_python = Path(resolve_runtime_python())
    except ImportError:
        # Fallback to known venv locations, checked in priority order
        candidates = [
            ROOT / "venv" / "bin" / "python",
            ROOT / ".runtime-venv" / "bin" / "python",
            ROOT / ".venv" / "bin" / "python",
        ]
        venv_python = next((p for p in candidates if p.exists()), Path(sys.executable))

    try:
        from cache import get_twitter_cache_path
        import copy

        cache_path = Path(get_twitter_cache_path())
        data = json.loads(cache_path.read_text())
        accounts = data.get("accounts", [])
        original_topic = None
        for acc in accounts:
            if acc.get("nickname") == account:
                original_topic = acc.get("topic", "")
                # Temporarily set the topic to force the specific tweet
                acc["topic"] = (
                    f"Write EXACTLY this tweet and nothing else — do not modify it, "
                    f"do not add anything, return it verbatim:\n\n{content}\n\n"
                    f"Original topic context: {original_topic}"
                )
                break

        cache_path.write_text(json.dumps(data, indent=2))
        print(f"\n  Injected tweet for {account}. Posting via smart_post_twitter.py...")

        cmd = [
            str(venv_python),
            str(ROOT / "scripts" / "smart_post_twitter.py"),
        ]
        if headless:
            cmd.append("--headless")

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180, cwd=str(ROOT))
        output = result.stdout + result.stderr

        # Restore original topic immediately
        data2 = json.loads(cache_path.read_text())
        for acc in data2.get("accounts", []):
            if acc.get("nickname") == account and original_topic is not None:
                acc["topic"] = original_topic
        cache_path.write_text(json.dumps(data2, indent=2))

        if "posted:confidence" in output:
            print("  ✅ Posted successfully!")
            # Print the tweet URL if found
            for line in output.splitlines():
                if "x.com/" in line or "twitter.com/" in line:
                    print(f"  🔗 {line.strip()}")
            return True
        else:
            print("  ⚠️  Post may not have succeeded. Output:", output[-500:])
            return False

    except Exception as ex:
        print(f"  ❌ Post injection failed: {ex}", file=sys.stderr)
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="ContentForge self-promotion tweet poster")
    parser.add_argument("--account", default=None, choices=["niche_launch_1", "EyeCatcher"],
                        help="Target Twitter account")
    parser.add_argument("--niche", default=None, help="Override niche for tweet generation")
    parser.add_argument("--count", type=int, default=10, help="Number of tweet ideas to generate")
    parser.add_argument("--dry-run", action="store_true", help="Generate + score but don't post")
    parser.add_argument("--headless", action="store_true", help="Headless browser mode")
    parser.add_argument("--min-score", type=int, default=65,
                        help="Minimum score to accept for posting (default: 65)")
    args = parser.parse_args()

    # Determine account — prefer the one with higher health score
    account = args.account
    if not account:
        try:
            states_path = ROOT / ".mp" / "runtime" / "account_states.json"
            if states_path.exists():
                states = json.loads(states_path.read_text())
                accts = states.get("accounts", {})
                active = [(k, v) for k, v in accts.items() if v.get("state") == "active"]
                if active:
                    account = max(active, key=lambda x: x[1].get("health_score", 0))[0]
        except Exception:
            pass
        account = account or "niche_launch_1"

    # Pick niche
    import random
    niche = args.niche or random.choice(ACCOUNT_NICHES.get(account, ACCOUNT_NICHES["niche_launch_1"]))

    print("=" * 60)
    print("  ContentForge Self-Promotion Runner")
    print("=" * 60)
    print(f"  Account : {account}")
    print(f"  Niche   : {niche}")
    print(f"  Count   : {args.count}")
    print(f"  Dry run : {args.dry_run}")
    print()

    # 1. Generate tweet ideas
    print(f"  Calling ContentForge /v1/tweet_ideas...")
    tweets = _get_tweet_ideas(niche, count=args.count)
    if not tweets:
        print("  ❌ No tweets generated. Is the API reachable?", file=sys.stderr)
        sys.exit(1)
    print(f"  Got {len(tweets)} tweet ideas")

    # 2. Score all and pick the best
    best_text, best_score, best_grade = _pick_best_tweet(tweets, verbose=True)

    if not best_text:
        print("  ❌ No valid tweet found after scoring.", file=sys.stderr)
        sys.exit(1)

    print(f"\n  🏆 Best tweet: Grade {best_grade} | Score {best_score}")
    print(f"  📝 Text: {best_text}\n")

    if best_score < args.min_score:
        print(f"  ⚠️  Best score ({best_score}) is below threshold ({args.min_score}). Skipping post.")
        sys.exit(0)

    if args.dry_run:
        print("  [dry-run] Would post this tweet. Exiting.")
        sys.exit(0)

    # 3. Post it
    print(f"  Posting to {account}...")
    success = _post_override(account, best_text, args.headless)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
