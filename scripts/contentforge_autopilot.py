#!/usr/bin/env python3
"""
scripts/contentforge_autopilot.py

ContentForge Autopilot — fully autonomous promotional tweet scheduler.

Runs in the background and posts ContentForge promotional tweets across
both Twitter accounts on a randomized schedule. Combines:
  1. Pre-written promo templates (high-quality, hand-crafted)
  2. AI-generated niche tweets (via local Ollama or Gemini)
  3. ContentForge API dogfooding (score each draft, pick the best)

The script handles:
  - Account rotation (alternates between niche_launch_1 and EyeCatcher)
  - Cooldown enforcement (minimum hours between posts per account)
  - Time-of-day awareness (posts during peak engagement windows)
  - Template deduplication (never repeats the same template)
  - Graceful stop (create .mp/runtime/autopilot.stop to halt)
  - State persistence (survives restarts)

Usage:
  python scripts/contentforge_autopilot.py                  # run once (pick best, post)
  python scripts/contentforge_autopilot.py --loop           # daemon mode: post on schedule
  python scripts/contentforge_autopilot.py --dry-run        # score + pick, no post
  python scripts/contentforge_autopilot.py --loop --interval 4  # post every ~4 hours
  python scripts/contentforge_autopilot.py --account EyeCatcher  # target specific account
  python scripts/contentforge_autopilot.py --template-only  # only use hand-crafted templates
  python scripts/contentforge_autopilot.py --ai-only        # only use AI-generated tweets

Environment:
  MPV2_HEADLESS=1   — forces headless browser mode (set by VS Code tasks)
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "src"
SCRIPTS_DIR = ROOT / "scripts"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

RUNTIME_DIR = ROOT / ".mp" / "runtime"
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = RUNTIME_DIR / "autopilot_state.json"
STOP_FILE = RUNTIME_DIR / "autopilot.stop"
PID_FILE = RUNTIME_DIR / "autopilot.pid"

RAPIDAPI_URL = "https://rapidapi.com/captainarmoreddude/api/contentforge1"

# ---------------------------------------------------------------------------
# Promo template library — hand-crafted, high-converting tweets
# ---------------------------------------------------------------------------
PROMO_TEMPLATES: list[dict] = [
    # --- Value-first / problem-solution ---
    {
        "id": "headline_problem",
        "text": (
            "your headline is 80% of whether anyone clicks\n\n"
            "I built a free API that tells you exactly why yours is weak "
            "and how to fix it\n\n"
            "paste any headline → get a score, grade, and specific suggestions\n\n"
            f"ContentForge on RapidAPI — free tier, no card\n{RAPIDAPI_URL}"
        ),
        "accounts": ["niche_launch_1", "EyeCatcher"],
    },
    {
        "id": "tweet_scorer_spotlight",
        "text": (
            "ever wonder if your tweet is actually good before you post it?\n\n"
            "I built a Tweet Scorer API endpoint\n\n"
            "paste your draft → 0-100 score, letter grade, hashtag analysis, "
            "power word detection, and improvement tips\n\n"
            f"instant. no AI needed. free on RapidAPI\n{RAPIDAPI_URL}"
        ),
        "accounts": ["niche_launch_1", "EyeCatcher"],
    },
    {
        "id": "hot_take",
        "text": (
            "most people spend 30 minutes writing a post and 5 seconds "
            "on the headline\n\n"
            "that's backwards\n\n"
            "I built ContentForge to fix it — scores headlines, scores tweets, "
            "generates content calendars\n\n"
            f"it's free on RapidAPI. go break your next post.\n{RAPIDAPI_URL}"
        ),
        "accounts": ["niche_launch_1"],
    },
    {
        "id": "builder_story",
        "text": (
            "I built an API that scores headlines, scores tweet drafts, "
            "and generates viral hooks.\n\n"
            "It's called ContentForge — and it's live on RapidAPI.\n\n"
            "Free tier: 50 AI calls/month. No credit card needed.\n\n"
            f"Here's what it does ↓\n{RAPIDAPI_URL}"
        ),
        "accounts": ["niche_launch_1"],
    },
    {
        "id": "content_calendar_spotlight",
        "text": (
            '"what should I post this week?"\n\n'
            "I kept asking myself that, so I built a fix\n\n"
            "ContentForge /content_calendar — give it your niche, "
            "get 7 days of themes + ready-to-post drafts\n\n"
            f"free on RapidAPI\n{RAPIDAPI_URL}"
        ),
        "accounts": ["niche_launch_1", "EyeCatcher"],
    },
    {
        "id": "social_proof_numbers",
        "text": (
            "ContentForge now has 10 API endpoints:\n\n"
            "✦ Headline Scorer (instant)\n"
            "✦ Tweet Scorer (instant)\n"
            "✦ AI Hook Generator\n"
            "✦ Content Calendar\n"
            "✦ Thread Outline Builder\n"
            "✦ Bio Generator\n"
            "+ 4 more\n\n"
            f"all free to start. no card needed.\n{RAPIDAPI_URL}"
        ),
        "accounts": ["niche_launch_1", "EyeCatcher"],
    },
    {
        "id": "eyecatcher_attention",
        "text": (
            "the first 3 words of your tweet decide if anyone reads the rest\n\n"
            "ContentForge scores your draft before you post\n\n"
            "it checks: power words, length, hashtags, emojis, readability\n\n"
            f"score your next tweet free → {RAPIDAPI_URL}\n\n"
            "#buildinpublic #contentcreator"
        ),
        "accounts": ["EyeCatcher"],
    },
    {
        "id": "eyecatcher_scroll_stop",
        "text": (
            "scroll-stopping content isn't luck — it's structure\n\n"
            "ContentForge generates hooks, scores headlines, and builds "
            "7-day content calendars\n\n"
            "I use it to plan every post on this account\n\n"
            f"free API on RapidAPI: {RAPIDAPI_URL}\n\n"
            "#contentmarketing #growthhacking"
        ),
        "accounts": ["EyeCatcher"],
    },
    {
        "id": "weekend_build",
        "text": (
            "built this API in a weekend with Python + Gemini\n\n"
            "it scores your headlines and tweets before you post them\n\n"
            "no more guessing if your content is good enough\n\n"
            f"ContentForge — free on RapidAPI\n{RAPIDAPI_URL}\n\n"
            "#indiehackers #buildinpublic"
        ),
        "accounts": ["niche_launch_1"],
    },
    {
        "id": "thread_outline_pitch",
        "text": (
            "writing a Twitter thread used to take me 2 hours\n\n"
            "now I give ContentForge a topic and get:\n"
            "→ scroll-stopping hook\n"
            "→ numbered body tweets\n"
            "→ CTA closing tweet\n\n"
            "all in one API call. all under 280 chars each.\n\n"
            f"try it free: {RAPIDAPI_URL}"
        ),
        "accounts": ["niche_launch_1", "EyeCatcher"],
    },
    {
        "id": "bio_generator_pitch",
        "text": (
            "your bio is the most-read thing on your profile\n\n"
            "and most people write it in 30 seconds\n\n"
            "ContentForge /generate_bio takes your name + niche → "
            "outputs a punchy, platform-optimized bio\n\n"
            "Twitter (160c), LinkedIn (300c), Instagram (150c) — auto-trimmed\n\n"
            f"free: {RAPIDAPI_URL}"
        ),
        "accounts": ["niche_launch_1", "EyeCatcher"],
    },
]

# AI-generated tweet niches per account
AI_NICHES: dict[str, list[str]] = {
    "niche_launch_1": [
        "headline writing and copywriting tips — mention ContentForge API as a free tool on RapidAPI",
        "tweet optimization for engagement — mention ContentForge's tweet scorer endpoint",
        "content marketing automation with APIs — plug ContentForge on RapidAPI",
        "indie hacking and building in public — share building ContentForge as a story",
        "AI tools for solo creators — include ContentForge as an example",
    ],
    "EyeCatcher": [
        "attention psychology in social media — mention ContentForge as a tool for testing hooks",
        "how to write scroll-stopping content — plug ContentForge's headline scorer",
        "content strategy for personal brands — mention ContentForge's content calendar endpoint",
        "why most tweets fail and how to fix them — mention ContentForge's tweet scorer",
        "visual storytelling and brand building — mention ContentForge for bio generation",
    ],
}


# ---------------------------------------------------------------------------
# State management (survive restarts)
# ---------------------------------------------------------------------------
def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"used_templates": [], "last_post": {}, "cycle_count": 0, "posts": []}


def _save_state(state: dict) -> None:
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(STATE_FILE)


# ---------------------------------------------------------------------------
# Tweet scoring (local function — no API call needed)
# ---------------------------------------------------------------------------
try:
    from api_prototype import score_tweet as _score_tweet_local
    _HAS_LOCAL_SCORER = True
except ImportError:
    _HAS_LOCAL_SCORER = False


def _score(text: str) -> dict:
    """Score a tweet using the local scoring function."""
    if _HAS_LOCAL_SCORER:
        return _score_tweet_local(text)
    # Fallback: basic scoring if import fails
    score = 50
    if len(text) >= 50:
        score += 10
    if "#" in text:
        score += 5
    if "?" in text:
        score += 5
    if any(w in text.lower() for w in ["free", "build", "hack", "secret", "proven"]):
        score += 10
    grade = "A" if score >= 80 else "B" if score >= 60 else "C" if score >= 40 else "D"
    return {"score": score, "grade": grade, "text": text}


# ---------------------------------------------------------------------------
# AI tweet generation (local Ollama → Gemini fallback)
# ---------------------------------------------------------------------------
def _generate_ai_tweet(niche: str) -> str | None:
    """Generate a single promotional tweet via LLM."""
    try:
        from api_prototype import _llm_generate
    except ImportError:
        return None

    prompt = (
        f"Write ONE tweet (under 270 characters) for this topic:\n"
        f"{niche}\n\n"
        f"Rules:\n"
        f"- Include the link: {RAPIDAPI_URL}\n"
        f"- Conversational, not salesy. Sound like a real person.\n"
        f"- Use 1-2 hashtags max\n"
        f"- Include a concrete benefit or use case\n"
        f"- NO quotes around the tweet. Just the raw text.\n"
        f"Return ONLY the tweet text, nothing else."
    )
    try:
        raw = _llm_generate(prompt).strip().strip('"').strip("'")
        # Enforce 280 char limit
        if len(raw) > 280:
            raw = raw[:277] + "..."
        if len(raw) < 20:
            return None
        return raw
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Account selection + posting
# ---------------------------------------------------------------------------
def _get_accounts() -> list[dict]:
    """Load Twitter accounts from cache."""
    try:
        from cache import get_twitter_cache_path
        data = json.loads(Path(get_twitter_cache_path()).read_text())
        return data.get("accounts", [])
    except Exception:
        return []


def _pick_account(state: dict, prefer: str | None = None) -> str | None:
    """Pick the account that hasn't posted most recently."""
    accounts = _get_accounts()
    nicknames = [a["nickname"] for a in accounts if a.get("nickname")]

    if prefer and prefer in nicknames:
        return prefer

    # Sort by last autopilot post time (oldest first)
    last_posts = state.get("last_post", {})
    candidates = sorted(
        nicknames,
        key=lambda n: last_posts.get(n, "2000-01-01T00:00:00"),
    )
    return candidates[0] if candidates else None


def _hours_since_last_post(state: dict, account: str) -> float:
    """Hours since this account's last autopilot post."""
    ts = state.get("last_post", {}).get(account)
    if not ts:
        return 999.0
    try:
        last = datetime.fromisoformat(ts)
        return (datetime.now() - last).total_seconds() / 3600
    except Exception:
        return 999.0


def _post_tweet(account: str, text: str, headless: bool = True) -> bool:
    """Post a tweet by injecting it as a topic override into smart_post."""
    try:
        from cache import get_twitter_cache_path
        cache_path = Path(get_twitter_cache_path())
        data = json.loads(cache_path.read_text())

        original_topic = None
        for acc in data.get("accounts", []):
            if acc.get("nickname") == account:
                original_topic = acc.get("topic", "")
                acc["topic"] = (
                    f"Write EXACTLY this tweet and nothing else — do not modify it, "
                    f"do not add anything, return it verbatim:\n\n{text}\n\n"
                    f"Original topic context: {original_topic}"
                )
                break
        else:
            print(f"  [autopilot] Account '{account}' not found in cache.")
            return False

        cache_path.write_text(json.dumps(data, indent=2))

        # Resolve python binary
        python_bin = str(ROOT / ".runtime-venv" / "bin" / "python")
        if not Path(python_bin).exists():
            python_bin = sys.executable

        cmd = [python_bin, str(ROOT / "scripts" / "smart_post_twitter.py")]
        if headless:
            cmd.append("--headless")

        env = os.environ.copy()
        env["MPV2_HEADLESS"] = "1"

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=180,
            cwd=str(ROOT), env=env,
        )
        output = result.stdout + result.stderr

        # Restore original topic immediately
        try:
            data2 = json.loads(cache_path.read_text())
            for acc in data2.get("accounts", []):
                if acc.get("nickname") == account and original_topic is not None:
                    acc["topic"] = original_topic
            cache_path.write_text(json.dumps(data2, indent=2))
        except Exception:
            pass

        posted = "posted" in output.lower() and "confidence" in output.lower()
        if posted:
            # Extract URL if available
            for line in output.splitlines():
                if "x.com/" in line or "twitter.com/" in line:
                    print(f"  [autopilot] 🔗 {line.strip()}")
            return True
        return False

    except subprocess.TimeoutExpired:
        print("  [autopilot] Post timed out (180s).")
        # Restore topic on timeout too
        try:
            data2 = json.loads(cache_path.read_text())
            for acc in data2.get("accounts", []):
                if acc.get("nickname") == account and original_topic is not None:
                    acc["topic"] = original_topic
            cache_path.write_text(json.dumps(data2, indent=2))
        except Exception:
            pass
        return False
    except Exception as ex:
        print(f"  [autopilot] Post failed: {ex}")
        return False


# ---------------------------------------------------------------------------
# Core: pick the best tweet from all sources
# ---------------------------------------------------------------------------
def _pick_best_tweet(
    account: str,
    state: dict,
    template_only: bool = False,
    ai_only: bool = False,
) -> tuple[str, int, str, str]:
    """Returns (text, score, grade, source) for the best tweet."""
    candidates: list[tuple[str, int, str, str]] = []  # (text, score, grade, source)
    used = set(state.get("used_templates", []))

    # 1. Score available templates
    if not ai_only:
        for tpl in PROMO_TEMPLATES:
            if tpl["id"] in used:
                continue
            if account not in tpl["accounts"]:
                continue
            text = tpl["text"].strip()
            if len(text) > 280:
                # Try trimming to fit
                text = text[:277] + "..."
            result = _score(text)
            score = result.get("score", 0)
            grade = result.get("grade", "D")
            candidates.append((text, score, grade, f"template:{tpl['id']}"))

    # 2. Generate AI tweets
    if not template_only:
        niches = AI_NICHES.get(account, AI_NICHES["niche_launch_1"])
        niche = random.choice(niches)
        for _ in range(3):  # generate 3 AI candidates
            tweet = _generate_ai_tweet(niche)
            if tweet:
                result = _score(tweet)
                score = result.get("score", 0)
                grade = result.get("grade", "D")
                candidates.append((tweet, score, grade, "ai_generated"))

    if not candidates:
        return ("", 0, "D", "none")

    # Sort by score descending, prefer templates for consistency
    candidates.sort(key=lambda c: (-c[1], c[3] != "ai_generated"))
    return candidates[0]


# ---------------------------------------------------------------------------
# Single post cycle
# ---------------------------------------------------------------------------
def _run_cycle(
    state: dict,
    prefer_account: str | None = None,
    headless: bool = True,
    dry_run: bool = False,
    template_only: bool = False,
    ai_only: bool = False,
    min_cooldown_hours: float = 3.0,
) -> bool:
    """Run a single post cycle. Returns True if a tweet was posted."""

    account = _pick_account(state, prefer_account)
    if not account:
        print("  [autopilot] No accounts available.")
        return False

    hours = _hours_since_last_post(state, account)
    if hours < min_cooldown_hours:
        print(
            f"  [autopilot] {account} posted {hours:.1f}h ago "
            f"(cooldown: {min_cooldown_hours}h). Skipping."
        )
        return False

    print(f"\n{'='*60}")
    print(f"  ContentForge Autopilot — Cycle #{state.get('cycle_count', 0) + 1}")
    print(f"{'='*60}")
    print(f"  Account  : {account}")
    print(f"  Last post: {hours:.1f}h ago")
    print(f"  Time     : {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    text, score, grade, source = _pick_best_tweet(
        account, state, template_only=template_only, ai_only=ai_only,
    )

    if not text:
        print("  [autopilot] No tweet candidates available.")
        return False

    print(f"\n  🏆 Best tweet (Score: {score}, Grade: {grade}, Source: {source})")
    print(f"  📝 {text[:120]}{'...' if len(text) > 120 else ''}")
    print(f"  📏 {len(text)} chars")

    if score < 50:
        print(f"  ⚠️  Score too low ({score}). Skipping.")
        return False

    if dry_run:
        print("  [dry-run] Would post. Exiting cycle.")
        return False

    print(f"\n  Posting to @{account}...")
    success = _post_tweet(account, text, headless=headless)

    if success:
        print(f"  ✅ Posted successfully to {account}!")
        # Update state
        state["last_post"][account] = datetime.now().isoformat()
        state["cycle_count"] = state.get("cycle_count", 0) + 1
        if source.startswith("template:"):
            tpl_id = source.split(":", 1)[1]
            state.setdefault("used_templates", []).append(tpl_id)
        state.setdefault("posts", []).append({
            "account": account,
            "text": text[:200],
            "score": score,
            "grade": grade,
            "source": source,
            "ts": datetime.now().isoformat(),
        })
        _save_state(state)
    else:
        print(f"  ❌ Post failed for {account}.")

    return success


# ---------------------------------------------------------------------------
# Loop mode (daemon)
# ---------------------------------------------------------------------------
def _is_peak_hour() -> bool:
    """Check if current hour is in a peak engagement window (US timezones)."""
    hour = datetime.now().hour
    # Peak: 7-9am, 12-1pm, 5-7pm, 9-10pm (loose windows)
    return hour in (7, 8, 9, 12, 13, 17, 18, 19, 21, 22)


def _run_loop(
    args: argparse.Namespace,
    state: dict,
) -> None:
    """Daemon loop: post on schedule, sleep between cycles."""
    PID_FILE.write_text(str(os.getpid()))
    STOP_FILE.unlink(missing_ok=True)

    base_interval = args.interval * 3600  # hours → seconds
    print(f"\n  [autopilot] Daemon started. PID={os.getpid()}")
    print(f"  [autopilot] Base interval: {args.interval}h")
    print(f"  [autopilot] Stop file: {STOP_FILE}")
    print(f"  [autopilot] State file: {STATE_FILE}\n")

    try:
        while True:
            if STOP_FILE.exists():
                print("  [autopilot] Stop file detected. Shutting down.")
                STOP_FILE.unlink(missing_ok=True)
                break

            success = _run_cycle(
                state,
                prefer_account=args.account,
                headless=True,
                dry_run=args.dry_run,
                template_only=args.template_only,
                ai_only=args.ai_only,
                min_cooldown_hours=max(2.0, args.interval * 0.8),
            )

            # Calculate next sleep with jitter
            jitter = random.uniform(-0.15, 0.25) * base_interval
            sleep_secs = base_interval + jitter

            # Sleep longer during off-peak hours
            if not _is_peak_hour():
                sleep_secs *= 1.5

            # If post failed, retry sooner
            if not success:
                sleep_secs = min(sleep_secs, 1800)  # retry in 30 min max

            wake_time = datetime.now() + timedelta(seconds=sleep_secs)
            print(f"\n  [autopilot] Next cycle at ~{wake_time.strftime('%H:%M')} "
                  f"({sleep_secs / 3600:.1f}h)")

            # Sleep in 60-second chunks so we can check the stop file
            elapsed = 0
            while elapsed < sleep_secs:
                if STOP_FILE.exists():
                    break
                time.sleep(min(60, sleep_secs - elapsed))
                elapsed += 60

    finally:
        PID_FILE.unlink(missing_ok=True)
        print("  [autopilot] Daemon stopped.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="ContentForge Autopilot — autonomous promotional tweet scheduler",
    )
    parser.add_argument("--loop", action="store_true",
                        help="Run in daemon mode (post on schedule)")
    parser.add_argument("--interval", type=float, default=4.0,
                        help="Hours between posts in loop mode (default: 4)")
    parser.add_argument("--account", default=None,
                        help="Target specific account (default: auto-rotate)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Score and pick but don't post")
    parser.add_argument("--template-only", action="store_true",
                        help="Only use hand-crafted templates")
    parser.add_argument("--ai-only", action="store_true",
                        help="Only use AI-generated tweets")
    parser.add_argument("--headless", action="store_true",
                        help="Headless browser mode")
    parser.add_argument("--reset", action="store_true",
                        help="Reset used-template tracker")
    parser.add_argument("--status", action="store_true",
                        help="Print current autopilot status")
    parser.add_argument("--stop", action="store_true",
                        help="Signal running daemon to stop")
    args = parser.parse_args()

    # Handle headless from env
    if os.environ.get("MPV2_HEADLESS") == "1":
        args.headless = True

    # Quick actions
    if args.stop:
        STOP_FILE.write_text("stop")
        print("  Stop signal sent. Daemon will halt after current sleep cycle.")
        return

    if args.status:
        state = _load_state()
        print(f"  Cycles completed : {state.get('cycle_count', 0)}")
        print(f"  Templates used   : {len(state.get('used_templates', []))} / {len(PROMO_TEMPLATES)}")
        for acct, ts in state.get("last_post", {}).items():
            hrs = _hours_since_last_post(state, acct)
            print(f"  Last post ({acct}): {ts} ({hrs:.1f}h ago)")
        if PID_FILE.exists():
            print(f"  Daemon PID: {PID_FILE.read_text().strip()}")
        else:
            print("  Daemon: not running")
        recent = state.get("posts", [])[-5:]
        if recent:
            print(f"\n  Recent posts:")
            for p in recent:
                print(f"    [{p['ts'][:16]}] {p['account']}: {p['text'][:80]}... "
                      f"(Score: {p['score']}, {p['source']})")
        return

    if args.reset:
        state = _load_state()
        state["used_templates"] = []
        _save_state(state)
        print("  Template tracker reset.")
        return

    state = _load_state()

    if args.loop:
        _run_loop(args, state)
    else:
        _run_cycle(
            state,
            prefer_account=args.account,
            headless=args.headless or True,
            dry_run=args.dry_run,
            template_only=args.template_only,
            ai_only=args.ai_only,
        )


if __name__ == "__main__":
    main()
