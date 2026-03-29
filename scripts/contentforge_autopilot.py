#!/usr/bin/env python3
"""
scripts/contentforge_autopilot.py

ContentForge Autopilot — fully autonomous promotional tweet scheduler.

Runs in the background and posts ContentForge promotional tweets across
both Twitter accounts on a randomized schedule.  It combines:
  1. 22 hand-crafted, high-scoring templates (all verified 70+)
  2. AI-generated tweets (local Ollama -> Gemini fallback)
  3. Live scoring via ContentForge's own score_tweet() — eat the dog food

Self-managing features:
  - Account auto-discovery from cache (no manual config needed)
  - Account rotation (alternates based on oldest last-post)
  - Cooldown enforcement (min hours between posts per account)
  - Peak-hour awareness (posts more during engagement windows)
  - Template deduplication + auto-recycle when library exhausted
  - Graceful stop (create .mp/runtime/autopilot.stop to halt daemon)
  - Full state persistence (survives restarts)
  - Proof log (.mp/runtime/autopilot_posts.log) — every post detail

Commands:
  python scripts/contentforge_autopilot.py --init              # check system readiness
  python scripts/contentforge_autopilot.py --verify            # score all templates
  python scripts/contentforge_autopilot.py --dry-run           # preview picks, no post
  python scripts/contentforge_autopilot.py                     # run once
  python scripts/contentforge_autopilot.py --loop              # daemon (default 4h)
  python scripts/contentforge_autopilot.py --loop --interval 3 # custom interval
  python scripts/contentforge_autopilot.py --account EyeCatcher
  python scripts/contentforge_autopilot.py --template-only
  python scripts/contentforge_autopilot.py --ai-only
  python scripts/contentforge_autopilot.py --verbose           # show all candidates
  python scripts/contentforge_autopilot.py --status
  python scripts/contentforge_autopilot.py --report            # full history
  python scripts/contentforge_autopilot.py --stop
  python scripts/contentforge_autopilot.py --reset

Environment:
  MPV2_HEADLESS=1   forces headless browser (set automatically by VS Code tasks)
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
LOG_FILE = RUNTIME_DIR / "autopilot_posts.log"

RAPIDAPI_URL = "https://rapidapi.com/captainarmoreddude/api/contentforge1"
API_BASE = "https://contentforge-api-lpp9.onrender.com"

# Minimum score to allow posting (raise to enforce higher quality bar)
MIN_SCORE = 70

# ===========================================================================
# Template library — 22 hand-crafted tweets
# Every template is engineered for 70+ score by including:
#   - power words: free, proven, instant, hack, tip, strategy, secret, boost…
#   - 1-2 hashtags
#   - 1-2 emojis
#   - a question OR digit opener for hook strength
#   - total length kept under 240 chars (no -8 length penalty)
# ===========================================================================
PROMO_TEMPLATES: list[dict] = [

    # ── niche_launch_1 + EyeCatcher ─────────────────────────────────────────
    {
        "id": "tweet_score_question",
        "text": (
            "ever post a tweet that flopped? 📉\n\n"
            "the fix is instant — ContentForge's free Tweet Scorer\n\n"
            "paste any draft -> proven score 0-100, grade, and tips to boost it\n\n"
            f"no card needed: {RAPIDAPI_URL} #buildinpublic"
        ),
        "accounts": ["niche_launch_1", "EyeCatcher"],
    },
    {
        "id": "proven_headline_fix",
        "text": (
            "proven: your headline is 80% of your clicks 🎯\n\n"
            "most creators guess. ContentForge scores it instantly\n\n"
            "free Headline Scorer API — paste any headline, get a grade + fix\n\n"
            f"try it free: {RAPIDAPI_URL} #contentmarketing"
        ),
        "accounts": ["niche_launch_1", "EyeCatcher"],
    },
    {
        "id": "instant_feedback",
        "text": (
            "want instant feedback on any content draft? 📊\n\n"
            "ContentForge's free API scores headlines AND tweets\n\n"
            "power words, hashtags, emoji use, readability — all checked\n\n"
            f"free on RapidAPI: {RAPIDAPI_URL} #growthhacking"
        ),
        "accounts": ["niche_launch_1", "EyeCatcher"],
    },
    {
        "id": "five_sec_mistake",
        "text": (
            "5 seconds vs 30 minutes 🤔\n\n"
            "most people write their headline in 5s and their body in 30 min\n\n"
            "that's the mistake. ContentForge's free scorer proves it\n\n"
            f"{RAPIDAPI_URL} #copywriting #buildinpublic"
        ),
        "accounts": ["niche_launch_1"],
    },
    {
        "id": "free_10_tools",
        "text": (
            "10 free content tools in one API 🛠\n\n"
            "headline scorer · tweet scorer · hook generator\n"
            "content calendar · thread outline · bio writer\n\n"
            "ContentForge — 50 free AI calls/month, no card\n\n"
            f"{RAPIDAPI_URL} #indiehackers"
        ),
        "accounts": ["niche_launch_1", "EyeCatcher"],
    },
    {
        "id": "builder_revealed",
        "text": (
            "revealed: I built ContentForge over a weekend 🧑‍💻\n\n"
            "free headline scorer + tweet scorer + AI hook generator\n\n"
            "proven system — I score every post on this account with it\n\n"
            f"{RAPIDAPI_URL} #buildinpublic"
        ),
        "accounts": ["niche_launch_1"],
    },
    {
        "id": "content_calendar_hack",
        "text": (
            "the quick hack that killed 'what do I post today?' forever 📅\n\n"
            "ContentForge /content_calendar — give it your niche\n"
            "get 7 days of themes + ready-to-post tweet drafts instantly\n\n"
            f"free: {RAPIDAPI_URL} #contentcreator"
        ),
        "accounts": ["niche_launch_1", "EyeCatcher"],
    },
    {
        "id": "insider_strategy",
        "text": (
            "insider strategy: score your tweet BEFORE you post it 🏆\n\n"
            "ContentForge gives every draft a proven 0-100 score\n\n"
            "only post your best. stop guessing.\n\n"
            f"free API: {RAPIDAPI_URL} #twittergrowth"
        ),
        "accounts": ["niche_launch_1", "EyeCatcher"],
    },
    {
        "id": "earn_more_clicks",
        "text": (
            "want to earn more clicks on every post? 🔗\n\n"
            "the secret: score your headline BEFORE it goes live\n\n"
            "ContentForge Headline Scorer — free, instant, no signup\n\n"
            f"{RAPIDAPI_URL} #copywriting"
        ),
        "accounts": ["niche_launch_1", "EyeCatcher"],
    },
    {
        "id": "discover_hook_gen",
        "text": (
            "discover how to write viral hooks in seconds 🚀\n\n"
            "ContentForge's free AI Hook Generator — give it a topic\n"
            "get 5 proven opening lines engineered to grab attention\n\n"
            f"try it free: {RAPIDAPI_URL} #contentcreator"
        ),
        "accounts": ["niche_launch_1", "EyeCatcher"],
    },
    {
        "id": "simple_bio_fix",
        "text": (
            "is your Twitter bio actually working for you? 🤔\n\n"
            "simple fix: ContentForge's free Bio Generator\n\n"
            "give it your niche + name -> get a punchy, proven bio instantly\n\n"
            f"{RAPIDAPI_URL} #personalbranding"
        ),
        "accounts": ["niche_launch_1", "EyeCatcher"],
    },
    {
        "id": "thread_hack",
        "text": (
            "thread outline in seconds — here's the hack 🧵\n\n"
            "ContentForge /thread_outline -> hook + numbered tweets + CTA\n\n"
            "all under 280 chars each. free to use. instant.\n\n"
            f"try it: {RAPIDAPI_URL} #twitterthreads"
        ),
        "accounts": ["niche_launch_1", "EyeCatcher"],
    },
    {
        "id": "dogfooding_proof",
        "text": (
            "I score every tweet on this account with ContentForge 📊\n\n"
            "proven system — if a draft scores under 70 it doesn't go live\n\n"
            "free API I built myself, live on RapidAPI\n\n"
            f"{RAPIDAPI_URL} #buildinpublic"
        ),
        "accounts": ["niche_launch_1"],
    },
    {
        "id": "free_forever_tier",
        "text": (
            "50 free AI content calls every month — no catch 🎁\n\n"
            "ContentForge free tier: headline scorer, tweet scorer, hook gen,\n"
            "content calendars, thread outlines, bio writer\n\n"
            "proven tools. instant results. no card.\n\n"
            f"{RAPIDAPI_URL} #freestuff"
        ),
        "accounts": ["niche_launch_1", "EyeCatcher"],
    },
    {
        "id": "number_3_tools",
        "text": (
            "3 free ContentForge tools most creators don't know exist 👇\n\n"
            "1. Tweet Scorer — instant grade before you post\n"
            "2. Hook Generator — proven viral openers\n"
            "3. Content Calendar — 7-day plan in one call\n\n"
            f"all free: {RAPIDAPI_URL} #growthhacking"
        ),
        "accounts": ["niche_launch_1", "EyeCatcher"],
    },

    # ── EyeCatcher-specific ─────────────────────────────────────────────────
    {
        "id": "ec_scroll_stop",
        "text": (
            "why do some posts stop your scroll instantly? 👀\n\n"
            "it's a proven formula — ContentForge reverse-engineers it\n\n"
            "free headline + tweet scorer: instant feedback on what grabs attention\n\n"
            f"{RAPIDAPI_URL} #contentmarketing #psychology"
        ),
        "accounts": ["EyeCatcher"],
    },
    {
        "id": "ec_attention_boost",
        "text": (
            "want to boost content engagement? here's a free proven system 📈\n\n"
            "ContentForge scores your drafts: power words, hooks, readability,\n"
            "hashtag strategy — instant feedback on what drives clicks\n\n"
            f"free API: {RAPIDAPI_URL} #socialmedia"
        ),
        "accounts": ["EyeCatcher"],
    },
    {
        "id": "ec_secret_formula",
        "text": (
            "the secret formula behind viral content? 🔥\n\n"
            "it's not luck — it's structure. ContentForge scores it\n\n"
            "free tool: paste your headline or tweet draft, get an instant grade\n\n"
            f"{RAPIDAPI_URL} #contentcreator #buildinpublic"
        ),
        "accounts": ["EyeCatcher"],
    },
    {
        "id": "ec_mistake_revealed",
        "text": (
            "revealed: why are your headlines invisible to most readers? 👁️\n\n"
            "the mistake: no power words, no proven structure, no score\n\n"
            "ContentForge's free Headline Scorer is the instant fix\n\n"
            f"{RAPIDAPI_URL} #copywriting #contentmarketing"
        ),
        "accounts": ["EyeCatcher"],
    },
    {
        "id": "ec_visual_tip",
        "text": (
            "tip: your first line is a visual decision before it's a reading one 🎨\n\n"
            "ContentForge scores how well your hook grabs attention instantly\n\n"
            "free API — no account, no card, no limits on instant endpoints\n\n"
            f"{RAPIDAPI_URL} #personalbranding"
        ),
        "accounts": ["EyeCatcher"],
    },

    # ── niche_launch_1-specific ─────────────────────────────────────────────
    {
        "id": "nl_api_builder",
        "text": (
            "want a free content API that actually works? 🛠️\n\n"
            "ContentForge: proven headline scoring, tweet grading,\n"
            "AI hook generation, content calendars, thread outlines\n\n"
            "50 free calls/month, no card\n\n"
            f"{RAPIDAPI_URL} #indiehackers"
        ),
        "accounts": ["niche_launch_1"],
    },
    {
        "id": "nl_rapid_launch",
        "text": (
            "launched ContentForge on RapidAPI 🚀\n\n"
            "free tier: 50 AI calls/month, instant endpoints unlimited\n\n"
            "proven tools: headline scorer, tweet scorer, hook gen, bio writer\n\n"
            f"{RAPIDAPI_URL} #buildinpublic"
        ),
        "accounts": ["niche_launch_1"],
    },
]

# ---------------------------------------------------------------------------
# AI generation prompts per account — tuned for high-scoring output
# ---------------------------------------------------------------------------
AI_NICHES: dict[str, list[str]] = {
    "niche_launch_1": [
        (
            "Write a tweet about headline writing tips. Mention ContentForge's free Headline Scorer "
            f"on RapidAPI. Include: {RAPIDAPI_URL}. Use power words like 'proven', 'free', 'instant'. "
            "Add 1 hashtag like #copywriting. Add 1 emoji. Under 260 chars total."
        ),
        (
            "Write a tweet about tweet optimization for engagement. Mention ContentForge's free Tweet Scorer. "
            f"Link: {RAPIDAPI_URL}. Use 'hack', 'instant', 'boost'. Add #buildinpublic. Add 1 emoji. "
            "Under 260 chars."
        ),
        (
            "Write a tweet about building in public and indie hacking. Mention ContentForge API on RapidAPI. "
            f"Link: {RAPIDAPI_URL}. Use 'revealed', 'free', 'simple'. Add #indiehackers. Add 1 emoji. "
            "Under 260 chars."
        ),
        (
            "Write a tweet about content marketing automation. Plug ContentForge's free content calendar endpoint. "
            f"Link: {RAPIDAPI_URL}. Use 'quick', 'strategy', 'free'. Add #contentmarketing. 1 emoji. "
            "Under 260 chars."
        ),
    ],
    "EyeCatcher": [
        (
            "Write a tweet about the psychology of attention and scroll-stopping content. "
            "Mention ContentForge's free headline scorer. "
            f"Link: {RAPIDAPI_URL}. Use 'secret', 'proven', 'discover'. Add #contentcreator. 1 emoji. "
            "Under 260 chars."
        ),
        (
            "Write a tweet about writing viral hooks and scroll-stopping content. "
            f"Mention ContentForge's Tweet Scorer. Link: {RAPIDAPI_URL}. "
            "Use 'instant', 'boost', 'strategy'. Add #socialmedia. 1 emoji. Under 260 chars."
        ),
        (
            "Write a tweet about personal brand building on Twitter. "
            "Mention ContentForge's free bio generator. "
            f"Link: {RAPIDAPI_URL}. Use 'powerful', 'simple', 'free'. Add #personalbranding. 1 emoji. "
            "Under 260 chars."
        ),
        (
            "Write a tweet about why most tweets fail. "
            "Mention ContentForge's free tweet scoring. "
            f"Link: {RAPIDAPI_URL}. Use 'mistake', 'revealed', 'hack'. Add #twittergrowth. 1 emoji. "
            "Under 260 chars."
        ),
    ],
}


# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------
def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {
        "used_templates": [],
        "last_post": {},
        "cycle_count": 0,
        "posts": [],
        "recycles": 0,
    }


def _save_state(state: dict) -> None:
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(STATE_FILE)


def _append_log(entry: str) -> None:
    """Append a timestamped entry to the proof log."""
    with LOG_FILE.open("a") as f:
        f.write(entry + "\n")


# ---------------------------------------------------------------------------
# Tweet scoring — uses ContentForge's own scorer (eating the dog food)
# ---------------------------------------------------------------------------
try:
    from api_prototype import score_tweet as _score_tweet_local
    _HAS_LOCAL_SCORER = True
except ImportError:
    _HAS_LOCAL_SCORER = False


def _score(text: str) -> dict:
    """Score a tweet via the local ContentForge scorer with a safe fallback."""
    if _HAS_LOCAL_SCORER:
        return _score_tweet_local(text)
    # Fallback when api_prototype can't be imported
    import re as _re
    score = 40
    if len(text) >= 50:
        score += 10
    if _re.search(r'#\w+', text):
        score += 8
    if any(ord(c) > 0x1F300 for c in text):
        score += 8
    if "?" in text:
        score += 7
    if _re.search(r'https?://', text):
        score += 5
    for pw in ["free", "hack", "secret", "proven", "instant", "tip", "boost", "strategy",
               "revealed", "discover", "simple", "quick", "earn", "mistake"]:
        if pw in text.lower():
            score += 4
    score = min(100, score)
    grade = "A" if score >= 80 else "B" if score >= 60 else "C" if score >= 40 else "D"
    return {
        "score": score, "grade": grade, "text": text,
        "char_count": len(text), "power_words_found": [],
        "hashtag_count": len(_re.findall(r'#\w+', text)),
        "emoji_count": sum(1 for c in text if ord(c) > 0x1F300),
        "suggestions": [],
    }


# ---------------------------------------------------------------------------
# AI tweet generation — LLM via api_prototype (Ollama or Gemini)
# ---------------------------------------------------------------------------
def _generate_ai_tweet(prompt_hint: str) -> str | None:
    """Generate a promotional tweet via LLM using a detailed prompt."""
    try:
        from api_prototype import _llm_generate
    except ImportError:
        return None

    prompt = (
        f"Write ONE tweet (under 260 characters total including the link) for this purpose:\n"
        f"{prompt_hint}\n\n"
        "Strict rules:\n"
        "- Sound like a real person, conversational, NOT salesy\n"
        "- Include exactly 1-2 hashtags\n"
        "- Include exactly 1 emoji\n"
        "- Use at least 2 power words from: free, proven, instant, hack, tip, "
        "  strategy, secret, boost, discover, revealed, simple, quick, earn, mistake\n"
        "- NO quotes around the tweet\n"
        "Return ONLY the raw tweet text, nothing else."
    )
    try:
        raw = _llm_generate(prompt).strip().strip('"').strip("'")
        if len(raw) > 280:
            raw = raw[:277] + "..."
        return raw if len(raw) >= 20 else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Account management — fully auto from cache, no manual config required
# ---------------------------------------------------------------------------
def _get_accounts() -> list[dict]:
    """Load all Twitter accounts from cache."""
    try:
        from cache import get_twitter_cache_path
        data = json.loads(Path(get_twitter_cache_path()).read_text())
        return [a for a in data.get("accounts", []) if a.get("nickname")]
    except Exception:
        return []


def _pick_account(state: dict, prefer: str | None = None) -> str | None:
    """Pick the account with the oldest last autopilot post (fair round-robin)."""
    accounts = _get_accounts()
    nicknames = [a["nickname"] for a in accounts]
    if not nicknames:
        return None
    if prefer and prefer in nicknames:
        return prefer
    last_posts = state.get("last_post", {})
    return min(nicknames, key=lambda n: last_posts.get(n, "2000-01-01T00:00:00"))


def _hours_since_last_post(state: dict, account: str) -> float:
    ts = state.get("last_post", {}).get(account)
    if not ts:
        return 999.0
    try:
        return (datetime.now() - datetime.fromisoformat(ts)).total_seconds() / 3600
    except Exception:
        return 999.0


# ---------------------------------------------------------------------------
# Posting via topic-override injection into smart_post_twitter.py
# ---------------------------------------------------------------------------
def _post_tweet(account: str, text: str, headless: bool = True) -> tuple[bool, str]:
    """
    Post a tweet using the topic-override injection pattern.
    Returns (success, tweet_url_or_empty).
    Always restores the original topic — even on failure or timeout.
    """
    cache_path: Path | None = None
    original_topic: str | None = None

    try:
        from cache import get_twitter_cache_path
        cache_path = Path(get_twitter_cache_path())
        data = json.loads(cache_path.read_text())

        for acc in data.get("accounts", []):
            if acc.get("nickname") == account:
                original_topic = acc.get("topic", "")
                acc["topic"] = (
                    "Write EXACTLY this tweet text — verbatim, no changes at all:\n\n"
                    + text
                )
                break
        else:
            print(f"  [autopilot] Account '{account}' not found in cache.")
            return False, ""

        tmp = cache_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2))
        tmp.replace(cache_path)

        python_bin = str(ROOT / ".runtime-venv" / "bin" / "python")
        if not Path(python_bin).exists():
            python_bin = sys.executable

        cmd = [python_bin, str(ROOT / "scripts" / "smart_post_twitter.py")]
        if headless:
            cmd.append("--headless")

        env = os.environ.copy()
        env["MPV2_HEADLESS"] = "1"

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=190,
            cwd=str(ROOT), env=env,
        )
        output = result.stdout + result.stderr
        out_lower = output.lower()

        posted = (
            ("posted" in out_lower or "tweet" in out_lower)
            and ("confidence" in out_lower or "success" in out_lower or "score" in out_lower)
        )

        tweet_url = ""
        for line in output.splitlines():
            m = re.search(r'https?://(?:x\.com|twitter\.com)/\S+', line.strip())
            if m:
                tweet_url = m.group(0).rstrip(".")
                break

        # If clean exit and tweet text appears in output, treat as success
        if not posted and result.returncode == 0 and text[:25].lower() in out_lower:
            posted = True

        return posted, tweet_url

    except subprocess.TimeoutExpired:
        print("  [autopilot] Post timed out after 190s.")
        return False, ""
    except Exception as ex:
        print(f"  [autopilot] Post error: {ex}")
        return False, ""
    finally:
        if cache_path and original_topic is not None:
            try:
                data2 = json.loads(cache_path.read_text())
                for acc in data2.get("accounts", []):
                    if acc.get("nickname") == account:
                        acc["topic"] = original_topic
                tmp2 = cache_path.with_suffix(".tmp")
                tmp2.write_text(json.dumps(data2, indent=2))
                tmp2.replace(cache_path)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Template selection and candidate ranking
# ---------------------------------------------------------------------------
def _available_templates(account: str, used: set[str]) -> list[dict]:
    return [t for t in PROMO_TEMPLATES if t["id"] not in used and account in t["accounts"]]


def _pick_best_tweet(
    account: str,
    state: dict,
    template_only: bool = False,
    ai_only: bool = False,
) -> tuple[str, int, str, str, list[tuple[str, int, str, str]]]:
    """
    Returns (text, score, grade, source, all_candidates_sorted_by_score).
    Automatically recycles the template library when exhausted.
    """
    used = set(state.get("used_templates", []))
    candidates: list[tuple[str, int, str, str]] = []

    if not ai_only:
        avail = _available_templates(account, used)
        if not avail:
            print(f"  [autopilot] All templates used for {account} — auto-recycling library.")
            _append_log(f"[{datetime.now().isoformat()}] RECYCLE account={account}")
            state["recycles"] = state.get("recycles", 0) + 1
            state["used_templates"] = []
            used = set()
            avail = _available_templates(account, used)

        for tpl in avail:
            text = tpl["text"].strip()
            if len(text) > 280:
                text = text[:277] + "..."
            r = _score(text)
            candidates.append((text, r["score"], r["grade"], f"template:{tpl['id']}"))

    if not template_only:
        niches = AI_NICHES.get(account, AI_NICHES["niche_launch_1"])
        hint = random.choice(niches)
        ai_added = 0
        for _ in range(4):
            tweet = _generate_ai_tweet(hint)
            if tweet:
                r = _score(tweet)
                candidates.append((tweet, r["score"], r["grade"], "ai_generated"))
                ai_added += 1
                if ai_added >= 2:
                    break

    if not candidates:
        return ("", 0, "D", "none", [])

    candidates.sort(key=lambda c: (-c[1], c[3].startswith("ai")))
    best = candidates[0]
    return (best[0], best[1], best[2], best[3], candidates)


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
    verbose: bool = False,
) -> bool:
    account = _pick_account(state, prefer_account)
    if not account:
        print("  [autopilot] No accounts found. Run --init to diagnose.")
        return False

    hours = _hours_since_last_post(state, account)
    if hours < min_cooldown_hours:
        print(f"  [autopilot] {account} posted {hours:.1f}h ago (cooldown {min_cooldown_hours}h). Skipping.")
        return False

    cycle_num = state.get("cycle_count", 0) + 1
    print(f"\n{'=' * 62}")
    print(f"  ContentForge Autopilot  —  Cycle #{cycle_num}")
    print(f"{'=' * 62}")
    print(f"  Account   : {account}")
    print(f"  Last post : {hours:.1f}h ago")
    print(f"  Time      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Mode      : {'DRY-RUN' if dry_run else 'LIVE'} | "
          f"templates={'off' if ai_only else 'on'} | ai={'off' if template_only else 'on'}")

    text, score, grade, source, all_candidates = _pick_best_tweet(
        account, state, template_only=template_only, ai_only=ai_only,
    )

    if not text:
        print("  [autopilot] No tweet candidates available.")
        return False

    if dry_run or verbose:
        print(f"\n  ── All Candidates (ranked) ─────────────────────────────────")
        for i, (t, s, g, src) in enumerate(all_candidates[:8], 1):
            marker = ">" if i == 1 else " "
            preview = t.replace("\n", " ")[:55]
            print(f"  {marker} #{i}  Score:{s:3d} {g}  [{src[:32]:<32}]  {preview!r}")
        print()

    preview = text.replace("\n", " ")
    print(f"  Winner  Score:{score:3d} ({grade})  Source: {source}")
    print(f"  Text   : {preview[:120]}{'...' if len(preview) > 120 else ''}")
    print(f"  Length : {len(text)} chars")

    if score < MIN_SCORE:
        print(f"  [autopilot] Score {score} below threshold {MIN_SCORE}. Skipping.")
        return False

    if dry_run:
        print(f"\n  [dry-run] Would post to @{account}. Not sending.")
        return False

    print(f"\n  Posting to @{account} ...")
    success, tweet_url = _post_tweet(account, text, headless=headless)

    if success:
        print(f"  Posted to {account}!")
        if tweet_url:
            print(f"  Tweet URL: {tweet_url}")

        state["last_post"][account] = datetime.now().isoformat()
        state["cycle_count"] = cycle_num
        if source.startswith("template:"):
            state.setdefault("used_templates", []).append(source.split(":", 1)[1])
        state.setdefault("posts", []).append({
            "account": account,
            "text": text[:250],
            "score": score,
            "grade": grade,
            "source": source,
            "url": tweet_url,
            "ts": datetime.now().isoformat(),
        })
        _save_state(state)

        log_line = (
            f"[{datetime.now().isoformat()}] "
            f"account={account} score={score} grade={grade} source={source} "
            f"url={tweet_url or 'not_captured'} | {text[:100].replace(chr(10), ' ')}"
        )
        _append_log(log_line)
    else:
        print(f"  Post failed for {account}.")

    return success


# ---------------------------------------------------------------------------
# Peak-hour helper
# ---------------------------------------------------------------------------
def _is_peak_hour() -> bool:
    return datetime.now().hour in (7, 8, 9, 12, 13, 17, 18, 19, 21, 22)


# ---------------------------------------------------------------------------
# Daemon loop
# ---------------------------------------------------------------------------
def _run_loop(args: argparse.Namespace, state: dict) -> None:
    PID_FILE.write_text(str(os.getpid()))
    STOP_FILE.unlink(missing_ok=True)

    base_secs = args.interval * 3600
    print(f"\n  [autopilot] Daemon started — PID {os.getpid()}")
    print(f"  [autopilot] Base interval : ~{args.interval}h")
    print(f"  [autopilot] Proof log     : {LOG_FILE}")
    print(f"  [autopilot] Stop daemon   : touch {STOP_FILE}")
    print(f"  [autopilot] State file    : {STATE_FILE}\n")

    try:
        while True:
            if STOP_FILE.exists():
                print("  [autopilot] Stop file detected. Shutting down cleanly.")
                STOP_FILE.unlink(missing_ok=True)
                break

            _run_cycle(
                state,
                prefer_account=args.account,
                headless=True,
                dry_run=getattr(args, "dry_run", False),
                template_only=getattr(args, "template_only", False),
                ai_only=getattr(args, "ai_only", False),
                min_cooldown_hours=max(2.0, args.interval * 0.75),
                verbose=getattr(args, "verbose", False),
            )

            jitter = random.uniform(-0.15, 0.20) * base_secs
            sleep_secs = base_secs + jitter
            if not _is_peak_hour():
                sleep_secs *= 1.4

            wake = datetime.now() + timedelta(seconds=sleep_secs)
            print(f"\n  [autopilot] Sleeping {sleep_secs / 3600:.1f}h -> next cycle ~{wake.strftime('%H:%M')}")

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
# --init: System readiness check
# ---------------------------------------------------------------------------
def _cmd_init() -> None:
    ok = True
    print("\n  ContentForge Autopilot — System Readiness Check")
    print("  " + "-" * 50)

    accounts = _get_accounts()
    if accounts:
        print(f"  OK  Accounts found: {[a['nickname'] for a in accounts]}")
    else:
        print("  ERR No Twitter accounts in cache — add one via main.py > Twitter > Add Account")
        ok = False

    for acct in accounts:
        profile = acct.get("firefox_profile") or acct.get("profile_path", "")
        if profile and Path(profile).exists():
            print(f"  OK  Firefox profile: {acct['nickname']} -> {Path(profile).name}")
        elif profile:
            print(f"  WRN Firefox profile NOT FOUND: {acct['nickname']} -> {profile}")
        else:
            print(f"  WRN No Firefox profile set for {acct['nickname']}")

    if _HAS_LOCAL_SCORER:
        print("  OK  ContentForge scorer loaded (api_prototype.py)")
    else:
        print("  WRN Scorer not importable — templates use fallback scoring")

    smart_post = ROOT / "scripts" / "smart_post_twitter.py"
    if smart_post.exists():
        print("  OK  smart_post_twitter.py found")
    else:
        print("  ERR smart_post_twitter.py missing — cannot post")
        ok = False

    try:
        import urllib.request as _ur
        with _ur.urlopen("http://localhost:11434/api/tags", timeout=3) as r:
            data = json.loads(r.read())
            models = [m["name"] for m in data.get("models", [])]
            print(f"  OK  Ollama running — models: {models[:3]}")
    except Exception:
        print("  WRN Ollama not reachable at localhost:11434 — AI gen will use Gemini fallback")

    try:
        import urllib.request as _ur
        with _ur.urlopen(f"{API_BASE}/health", timeout=8) as r:
            health = json.loads(r.read())
            print(f"  OK  ContentForge API: {health.get('status', 'ok')} ({API_BASE})")
    except Exception as e:
        print(f"  WRN ContentForge API cold/unreachable: {e}")
        print("       -> Scoring still works locally. Tweet posting is independent.")

    state = _load_state()
    used = set(state.get("used_templates", []))
    all_avail = sum(
        1 for t in PROMO_TEMPLATES
        if any(a["nickname"] in t["accounts"] for a in accounts)
        and t["id"] not in used
    )
    print(f"  OK  Templates available: {all_avail} / {len(PROMO_TEMPLATES)}")
    print()

    if ok:
        print("  System ready. Run --dry-run to preview, then --loop to start the daemon.")
    else:
        print("  Issues found above. Fix before running the autopilot.")


# ---------------------------------------------------------------------------
# --verify: Ranked template score table
# ---------------------------------------------------------------------------
def _cmd_verify() -> None:
    print("\n  ContentForge Autopilot — Template Score Table")
    print(f"  {'ID':<35} {'Score':>5} {'G':>3} {'PW':>4} {'H':>3} {'E':>3} {'Chars':>6}  Accounts")
    print("  " + "-" * 70)

    scored = []
    for tpl in PROMO_TEMPLATES:
        r = _score(tpl["text"])
        scored.append({
            "id": tpl["id"],
            "score": r["score"],
            "grade": r["grade"],
            "pw": len(r.get("power_words_found", [])),
            "hashtags": r.get("hashtag_count", 0),
            "emojis": r.get("emoji_count", 0),
            "chars": r.get("char_count", len(tpl["text"])),
            "accounts": tpl["accounts"],
        })

    scored.sort(key=lambda x: -x["score"])
    for t in scored:
        acct_tag = "both" if len(t["accounts"]) > 1 else t["accounts"][0]
        flag = " OK" if t["score"] >= MIN_SCORE else " LOW"
        print(
            f"  {t['id']:<35} {t['score']:>5} {t['grade']:>3} "
            f"{t['pw']:>4} {t['hashtags']:>3} {t['emojis']:>3} {t['chars']:>6}  "
            f"{acct_tag:<22}{flag}"
        )

    passing = sum(1 for t in scored if t["score"] >= MIN_SCORE)
    avg = sum(t["score"] for t in scored) / len(scored) if scored else 0
    print(f"\n  Postable (score >= {MIN_SCORE}): {passing} / {len(scored)}")
    print(f"  Average score : {avg:.1f}")
    print(f"  (PW=power words, H=hashtags, E=emojis)")


# ---------------------------------------------------------------------------
# --report: Full posting history
# ---------------------------------------------------------------------------
def _cmd_report(state: dict) -> None:
    posts = state.get("posts", [])
    print("\n  ContentForge Autopilot — Posting Report")
    print("  " + "-" * 60)
    print(f"  Total cycles    : {state.get('cycle_count', 0)}")
    print(f"  Total posts     : {len(posts)}")
    print(f"  Library recycles: {state.get('recycles', 0)}")

    if posts:
        scores = [p["score"] for p in posts]
        print(f"  Avg post score  : {sum(scores) / len(scores):.1f}")
        print(f"  Best post score : {max(scores)}")
        by_acct: dict[str, int] = {}
        for p in posts:
            by_acct[p["account"]] = by_acct.get(p["account"], 0) + 1
        for acct, cnt in by_acct.items():
            print(f"  Posts ({acct:<22}): {cnt}")

    print(f"\n  {'#':>3}  {'Timestamp':<18}  {'Account':<22}  {'Sc':>3}  {'Source':<28}  URL")
    print("  " + "-" * 100)
    for i, p in enumerate(posts, 1):
        url = p.get("url", "") or "(not captured)"
        print(
            f"  {i:>3}  {p['ts'][:16]:<18}  {p['account']:<22}  "
            f"{p['score']:>3}  {p['source']:<28}  {url}"
        )
    if not posts:
        print("  No posts recorded yet.")

    print(f"\n  Proof log: {LOG_FILE}")
    if LOG_FILE.exists():
        print(f"  Log entries: {len(LOG_FILE.read_text().strip().splitlines())}")


# ---------------------------------------------------------------------------
# --status: Quick summary
# ---------------------------------------------------------------------------
def _cmd_status(state: dict) -> None:
    posts = state.get("posts", [])
    accounts = _get_accounts()
    used = set(state.get("used_templates", []))

    print("\n  ContentForge Autopilot — Status")
    print("  " + "-" * 44)
    print(f"  Cycles completed : {state.get('cycle_count', 0)}")
    print(f"  Posts recorded   : {len(posts)}")
    print(f"  Library recycles : {state.get('recycles', 0)}")
    print(f"  Templates used   : {len(used)} / {len(PROMO_TEMPLATES)}")

    for acct in accounts:
        nick = acct["nickname"]
        hrs = _hours_since_last_post(state, nick)
        avail = len(_available_templates(nick, used))
        last_ts = state.get("last_post", {}).get(nick, "never")
        if last_ts != "never":
            last_ts = last_ts[:16]
        print(f"  {nick:<24}: last={last_ts:<17} ({hrs:.1f}h ago)  templates_left={avail}")

    if PID_FILE.exists():
        pid = PID_FILE.read_text().strip()
        print(f"\n  Daemon running: PID {pid}")
    else:
        print("\n  Daemon: not running")

    if posts:
        print("\n  Last 3 posts:")
        for p in posts[-3:]:
            url = p.get("url", "")
            print(f"    [{p['ts'][:16]}] {p['account']} score={p['score']} {p['text'][:60]}...")
            if url:
                print(f"    {url}")


# ---------------------------------------------------------------------------
# Main CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="ContentForge Autopilot — autonomous promotional tweet scheduler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Quick start:\n"
            "  python scripts/contentforge_autopilot.py --init        # check readiness\n"
            "  python scripts/contentforge_autopilot.py --verify      # score all templates\n"
            "  python scripts/contentforge_autopilot.py --dry-run     # preview picks\n"
            "  python scripts/contentforge_autopilot.py --loop        # start daemon\n"
        ),
    )
    parser.add_argument("--init", action="store_true",
                        help="Check system readiness (accounts, profiles, Ollama, API)")
    parser.add_argument("--verify", action="store_true",
                        help="Score all templates — show full ranked table")
    parser.add_argument("--dry-run", action="store_true",
                        help="Score, rank, and preview — no posting")
    parser.add_argument("--loop", action="store_true",
                        help="Run as a daemon (post on schedule)")
    parser.add_argument("--interval", type=float, default=4.0,
                        help="Hours between posts in loop mode (default: 4)")
    parser.add_argument("--account", default=None,
                        help="Pin to a specific account nickname")
    parser.add_argument("--template-only", action="store_true",
                        help="Only use hand-crafted templates")
    parser.add_argument("--ai-only", action="store_true",
                        help="Only use AI-generated tweets")
    parser.add_argument("--verbose", action="store_true",
                        help="Show all scored candidates during a cycle")
    parser.add_argument("--status", action="store_true",
                        help="Print status summary")
    parser.add_argument("--report", action="store_true",
                        help="Print full posting history")
    parser.add_argument("--stop", action="store_true",
                        help="Signal daemon to stop")
    parser.add_argument("--reset", action="store_true",
                        help="Reset used-template tracker")
    args = parser.parse_args()

    if os.environ.get("MPV2_HEADLESS") == "1":
        pass  # headless is always on when posting

    if args.init:
        _cmd_init()
        return

    if args.verify:
        _cmd_verify()
        return

    if args.stop:
        STOP_FILE.write_text("stop")
        print("  Stop signal written. Daemon will halt after current sleep.")
        return

    state = _load_state()

    if args.status:
        _cmd_status(state)
        return

    if args.report:
        _cmd_report(state)
        return

    if args.reset:
        state["used_templates"] = []
        _save_state(state)
        print(f"  Template tracker reset. {len(PROMO_TEMPLATES)} templates available.")
        return

    if args.loop:
        _run_loop(args, state)
    else:
        _run_cycle(
            state,
            prefer_account=args.account,
            headless=True,
            dry_run=args.dry_run,
            template_only=args.template_only,
            ai_only=args.ai_only,
            verbose=args.verbose,
        )


if __name__ == "__main__":
    main()
