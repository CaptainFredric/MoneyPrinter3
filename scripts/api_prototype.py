#!/usr/bin/env python3
"""ContentForge API — AI-powered content toolkit for creators and marketers.

Endpoints:
  POST /v1/analyze_headline    — Score & improve any headline (heuristic, instant)
  POST /v1/score_tweet         — Score a tweet draft before posting (heuristic, instant)
  POST /v1/score_linkedin_post — Score a LinkedIn post for reach/engagement (heuristic, instant)
  POST /v1/score_instagram     — Score an Instagram caption for engagement (heuristic, instant)
  POST /v1/score_youtube_title — Score a YouTube title for CTR (heuristic, instant)
  POST /v1/score_email_subject — Score an email subject line for open rate (heuristic, instant)
  POST /v1/score_multi         — Score text across multiple platforms in one call (heuristic, instant)
  POST /v1/score_readability   — Score text for readability w/ Flesch-Kincaid (heuristic, instant)
  POST /v1/score_tiktok        — Score a TikTok caption for engagement/reach (heuristic, instant)
  POST /v1/score_threads       — Score a Meta Threads post for engagement (heuristic, instant)
  POST /v1/score_facebook      — Score a Facebook post for organic reach (heuristic, instant)
  POST /v1/analyze_hashtags    — Analyze hashtags for quality, spam risk, platform fit (heuristic, instant)
  POST /v1/improve_headline    — AI-rewrites a headline into N better scored versions (AI)
  POST /v1/generate_hooks      — Generate scroll-stopping hooks for a topic (AI)
  POST /v1/rewrite             — Rewrite text for a target platform/tone (AI)
  POST /v1/tweet_ideas         — Generate tweet ideas for a niche/topic (AI)
  POST /v1/content_calendar    — AI-generated 7-day content calendar for any niche (AI)
  POST /v1/thread_outline      — AI-generated Twitter thread outline (hook + body + CTA) (AI)
  POST /v1/generate_bio        — AI-generated social media bio (Twitter/LinkedIn/Instagram) (AI)
  POST /v1/generate_caption    — AI-generated Instagram or TikTok caption (AI)
  POST /v1/generate_linkedin_post — AI-generated LinkedIn post (storytelling/professional/motivational) (AI)
  GET  /health                 — Service health check

Run smoke test:
  .runtime-venv/bin/python scripts/api_prototype.py --test

Run as server:
  .runtime-venv/bin/python scripts/api_prototype.py
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from functools import wraps
from pathlib import Path

from flask import Flask, request, jsonify, g

# ---------------------------------------------------------------------------
# Setup: add src/ so we can use the project's LLM provider
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

app = Flask(__name__)


# ---------------------------------------------------------------------------
# CORS — allow browser clients (RapidAPI playground, web apps)
# ---------------------------------------------------------------------------
@app.after_request
def _add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = (
        "Content-Type, X-RapidAPI-Proxy-Secret, X-RapidAPI-User, X-RapidAPI-Key"
    )
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/<path:dummy>", methods=["OPTIONS"])
@app.route("/", methods=["OPTIONS"])
def _cors_preflight(dummy=""):
    from flask import Response
    return Response(status=204, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": (
            "Content-Type, X-RapidAPI-Proxy-Secret, X-RapidAPI-User, X-RapidAPI-Key"
        ),
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    })

# ---------------------------------------------------------------------------
# Usage tracking (simple JSON log for analytics / future billing)
# ---------------------------------------------------------------------------
USAGE_LOG = ROOT_DIR / ".mp" / "api_usage.json"


def _log_usage(endpoint: str, latency_ms: int):
    try:
        USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "endpoint": endpoint,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "latency_ms": latency_ms,
        }
        entries = []
        if USAGE_LOG.exists():
            try:
                entries = json.loads(USAGE_LOG.read_text())[-999:]
            except Exception:
                entries = []
        entries.append(entry)
        USAGE_LOG.write_text(json.dumps(entries))
    except Exception:
        pass


# ---------------------------------------------------------------------------
# RapidAPI proxy-secret verification
# ---------------------------------------------------------------------------
_RAPIDAPI_SECRET = os.environ.get("RAPIDAPI_PROXY_SECRET", "")


def _verify_rapidapi_request() -> bool:
    """When RAPIDAPI_PROXY_SECRET is set, only allow requests that carry the
    matching X-RapidAPI-Proxy-Secret header.  This prevents callers from
    bypassing RapidAPI's billing layer and hitting the backend directly."""
    if not _RAPIDAPI_SECRET:
        return True  # not configured — open access (local / direct testing)
    return request.headers.get("X-RapidAPI-Proxy-Secret", "") == _RAPIDAPI_SECRET


# ---------------------------------------------------------------------------
# Rate limiting (simple in-memory, per-IP)
# ---------------------------------------------------------------------------
_rate_buckets: dict[str, list[float]] = {}
RATE_LIMIT = 30  # requests per minute per IP


def _check_rate_limit() -> tuple[bool, int]:
    """Returns (allowed, remaining_this_minute)."""
    ip = request.headers.get("X-RapidAPI-User") or request.remote_addr or "unknown"
    now = time.time()
    # Purge stale buckets every ~100 requests to prevent unbounded growth
    if len(_rate_buckets) > 500:
        stale = [k for k, v in _rate_buckets.items() if not v or now - v[-1] > 120]
        for k in stale:
            del _rate_buckets[k]
    bucket = _rate_buckets.setdefault(ip, [])
    bucket[:] = [t for t in bucket if now - t < 60]
    remaining = max(0, RATE_LIMIT - len(bucket))
    if len(bucket) >= RATE_LIMIT:
        return False, 0
    bucket.append(now)
    return True, max(0, remaining - 1)


def _add_rate_headers(response, remaining: int):
    """Attach standard rate-limit headers so API consumers can self-monitor."""
    response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Window"] = "60s"
    return response


# ---------------------------------------------------------------------------
# LLM helper — Ollama (local) → Gemini (cloud) fallback chain
# ---------------------------------------------------------------------------
def _llm_generate(prompt: str) -> str:
    """Generate text via local Ollama first, then Gemini API as fallback."""
    # 1. Try the project's built-in provider (Ollama → Gemini chain)
    try:
        from llm_provider import generate_text
        return generate_text(prompt)
    except Exception:
        pass

    # 2. Direct Ollama attempt
    try:
        import ollama as _ollama
        client = _ollama.Client(host=os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"))
        model = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
        resp = client.generate(model=model, prompt=prompt)
        text = resp.get("response", "").strip()
        if text:
            return text
    except Exception:
        pass

    # 3. Direct Gemini attempt (for cloud deployment where Ollama isn't available)
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if api_key:
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.9, max_output_tokens=300),
            )
            text = (response.text or "").strip()
            if text:
                return text
        except Exception as e:
            err_str = str(e).lower()
            if "resource_exhausted" in err_str or "quota" in err_str:
                raise RuntimeError(
                    "Gemini API quota exhausted for today. "
                    "The instant endpoints (analyze_headline, score_tweet, health) "
                    "still work — they don't use AI. AI endpoints will resume "
                    "when the quota resets (usually midnight Pacific)."
                )
            raise RuntimeError(f"Gemini failed: {e}")

    raise RuntimeError(
        "No LLM available. Set GEMINI_API_KEY for cloud deployment, "
        "or run Ollama locally."
    )


# ---------------------------------------------------------------------------
# 1. Headline Analyzer (heuristic — instant, no LLM needed)
# ---------------------------------------------------------------------------
def analyze_headline(text: str) -> dict:
    if not isinstance(text, str):
        text = str(text or "")
    txt = text.strip()
    length = len(txt)
    words = txt.split()
    word_count = len(words)
    exclamations = txt.count("!")
    questions = txt.count("?")
    caps_words = sum(1 for w in words if any(c.isalpha() for c in w) and w.isupper())
    caps_ratio = (caps_words / word_count) if word_count else 0.0
    has_number = any(char.isdigit() for char in txt)

    power_words = [
        # Urgency / scarcity
        "urgent", "limited", "exclusive", "expires", "deadline", "now", "today",
        # Money / results
        "free", "guaranteed", "money", "profit", "income", "revenue", "earn",
        "cash", "rich", "wealth", "savings", "roi", "returns",
        # Social proof / authority
        "proven", "tested", "experts", "trusted", "endorsed", "award",
        "official", "certified",
        # Curiosity / mystery
        "secret", "hidden", "unknown", "revealed", "discover", "inside",
        "truth", "expose", "uncover", "mystery", "forbidden",
        # Ease / speed
        "easy", "instant", "simple", "fast", "quick", "effortless", "done",
        "automated", "no-effort", "hands-off",
        # Superlatives / intensity
        "ultimate", "best", "top", "new", "breakthrough", "massive", "powerful",
        "essential", "critical", "shocking", "surprising", "incredible",
        "unbelievable", "insane", "mind-blowing",
        # Negative hooks
        "mistake", "wrong", "avoid", "warning", "danger", "failed", "lose",
        "never", "stop", "quit",
        # Positive hooks
        "hack", "trick", "tip", "strategy", "system", "formula", "blueprint",
        "insider", "cheat", "shortcut", "boost",
    ]
    pw_found = [w for w in power_words if w in txt.lower()]

    score = 50
    if 30 <= length <= 80:
        score += 20
    else:
        score -= max(0, (abs(55 - length) // 5))
    if has_number:
        score += 10
    if questions == 1:
        score += 5
    score -= min(20, exclamations * 8)
    if 0 < caps_ratio < 0.4:
        score += 5
    if caps_ratio >= 0.6:
        score -= 15
    score += min(15, len(pw_found) * 5)
    score = max(0, min(100, int(score)))

    grade = "A" if score >= 80 else "B" if score >= 60 else "C" if score >= 40 else "D"

    suggestions = []
    if length < 30:
        suggestions.append("Make the headline longer and more specific.")
    if length > 120:
        suggestions.append("Shorten to the core message (under 80 chars ideal).")
    if exclamations > 1:
        suggestions.append("Drop extra exclamation marks — they look spammy.")
    if caps_ratio >= 0.6:
        suggestions.append("Avoid ALL-CAPS — it reduces credibility.")
    if not has_number:
        suggestions.append("Add a number for specificity (e.g. '5 ways', '$6K/mo').")
    if not pw_found:
        suggestions.append("Add a power word (e.g. 'proven', 'secret', 'simple').")
    if questions == 0 and not has_number:
        suggestions.append("Try framing as a question to boost curiosity.")

    return {
        "text": txt,
        "score": score,
        "grade": grade,
        "length": length,
        "word_count": word_count,
        "has_number": has_number,
        "question_mark": questions > 0,
        "power_words_found": pw_found,
        "caps_ratio": round(caps_ratio, 2),
        "suggestions": suggestions,
    }


@app.route("/v1/analyze_headline", methods=["GET", "POST"])
def endpoint_analyze_headline():
    if not _verify_rapidapi_request():
        return jsonify({"error": "forbidden"}), 403
    allowed, remaining = _check_rate_limit()
    if not allowed:
        return jsonify({"error": "rate limit exceeded (30/min)"}), 429

    start = time.time()
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        text = payload.get("text") or payload.get("headline")
    else:
        text = request.args.get("text") or request.args.get("headline")

    if not text:
        return jsonify({"error": "missing 'text' parameter"}), 400
    if len(text) > 500:
        return jsonify({"error": "text too long (max 500 chars)"}), 400

    result = analyze_headline(text)
    _log_usage("analyze_headline", int((time.time() - start) * 1000))
    return _add_rate_headers(jsonify(result), remaining)


# Keep old path working for backwards compat
@app.route("/analyze_headline", methods=["GET", "POST"])
def endpoint_analyze_headline_legacy():
    return endpoint_analyze_headline()


# ---------------------------------------------------------------------------
# 2. Generate Hooks (AI-powered)
# ---------------------------------------------------------------------------
@app.route("/v1/generate_hooks", methods=["POST"])
def endpoint_generate_hooks():
    if not _verify_rapidapi_request():
        return jsonify({"error": "forbidden"}), 403
    allowed, remaining = _check_rate_limit()
    if not allowed:
        return jsonify({"error": "rate limit exceeded (30/min)"}), 429

    start = time.time()
    payload = request.get_json(silent=True) or {}
    topic = payload.get("topic", "").strip()
    try:
        count = min(int(payload.get("count", 5)), 10)
    except (ValueError, TypeError):
        return jsonify({"error": "'count' must be an integer"}), 400
    style = payload.get("style", "viral")  # viral, professional, casual

    if not topic:
        return jsonify({"error": "missing 'topic' parameter"}), 400
    if len(topic) > 300:
        return jsonify({"error": "topic too long (max 300 chars)"}), 400

    prompt = (
        f"Generate exactly {count} scroll-stopping hooks/headlines for this topic: {topic}\n"
        f"Style: {style}\n"
        f"Rules:\n"
        f"- Each hook should be 1 sentence, under 80 characters\n"
        f"- Use power words, numbers, or curiosity gaps\n"
        f"- No generic filler\n"
        f"- Return ONLY a JSON array of strings, nothing else\n"
        f"Example: [\"Hook 1\", \"Hook 2\"]"
    )

    try:
        raw = _llm_generate(prompt)
        match = re.search(r'\[.*?\]', raw, re.DOTALL)
        if match:
            try:
                hooks = json.loads(match.group(0))
            except json.JSONDecodeError:
                hooks = None
        else:
            hooks = None

        if not hooks:
            hooks = [
                re.sub(r'^[\d.\-\)\]]+\s*', '', line).strip().strip('"')
                for line in raw.strip().split("\n")
                if line.strip() and len(line.strip()) > 5
            ]
        hooks = [h for h in hooks if isinstance(h, str) and len(h) > 5][:count]
    except Exception as e:
        return jsonify({"error": f"LLM generation failed: {e}"}), 503

    _log_usage("generate_hooks", int((time.time() - start) * 1000))
    return _add_rate_headers(jsonify({"topic": topic, "style": style, "hooks": hooks}), remaining)


# ---------------------------------------------------------------------------
# 3. Rewrite (AI-powered)
# ---------------------------------------------------------------------------
@app.route("/v1/rewrite", methods=["POST"])
def endpoint_rewrite():
    if not _verify_rapidapi_request():
        return jsonify({"error": "forbidden"}), 403
    allowed, remaining = _check_rate_limit()
    if not allowed:
        return jsonify({"error": "rate limit exceeded (30/min)"}), 429

    start = time.time()
    payload = request.get_json(silent=True) or {}
    text = payload.get("text", "").strip()
    platform = payload.get("platform", "twitter")  # twitter, linkedin, email, blog
    tone = payload.get("tone", "engaging")  # engaging, professional, casual, humorous

    if not text:
        return jsonify({"error": "missing 'text' parameter"}), 400
    if len(text) > 2000:
        return jsonify({"error": "text too long (max 2000 chars)"}), 400

    char_limits = {"twitter": 280, "linkedin": 700, "instagram": 2200, "tiktok": 150, "email": 500, "blog": 1000}
    limit = char_limits.get(platform, 500)

    prompt = (
        f"Rewrite this text for {platform} in a {tone} tone.\n"
        f"Keep it under {limit} characters.\n"
        f"Return ONLY the rewritten text, nothing else.\n\n"
        f"Original: {text}"
    )

    try:
        rewritten = _llm_generate(prompt).strip().strip('"')
    except Exception as e:
        return jsonify({"error": f"LLM generation failed: {e}"}), 503

    _log_usage("rewrite", int((time.time() - start) * 1000))
    return _add_rate_headers(jsonify({
        "original": text,
        "rewritten": rewritten,
        "platform": platform,
        "tone": tone,
        "char_count": len(rewritten),
    }), remaining)


# ---------------------------------------------------------------------------
# 4. Tweet Ideas (AI-powered)
# ---------------------------------------------------------------------------
@app.route("/v1/tweet_ideas", methods=["POST"])
def endpoint_tweet_ideas():
    if not _verify_rapidapi_request():
        return jsonify({"error": "forbidden"}), 403
    allowed, remaining = _check_rate_limit()
    if not allowed:
        return jsonify({"error": "rate limit exceeded (30/min)"}), 429

    start = time.time()
    payload = request.get_json(silent=True) or {}
    niche = payload.get("niche", "").strip()
    try:
        count = min(int(payload.get("count", 5)), 10)
    except (ValueError, TypeError):
        return jsonify({"error": "'count' must be an integer"}), 400
    include_hashtags = payload.get("hashtags", True)

    if not niche:
        return jsonify({"error": "missing 'niche' parameter"}), 400
    if len(niche) > 200:
        return jsonify({"error": "niche too long (max 200 chars)"}), 400

    prompt = (
        f"Generate {count} tweet ideas for someone in the '{niche}' niche.\n"
        f"Rules:\n"
        f"- Each tweet under 280 characters\n"
        f"- Mix formats: hot take, tip, question, story hook, list\n"
        f"{'- Include 1-2 relevant hashtags per tweet' if include_hashtags else '- No hashtags'}\n"
        f"- Return ONLY a JSON array of strings\n"
        f"Example: [\"Tweet 1\", \"Tweet 2\"]"
    )

    try:
        raw = _llm_generate(prompt)
        # Try to extract JSON array, handling LLM adding extra text
        match = re.search(r'\[.*?\]', raw, re.DOTALL)
        if match:
            try:
                tweets = json.loads(match.group(0))
            except json.JSONDecodeError:
                tweets = None
        else:
            tweets = None

        if not tweets:
            # Fallback: split by newlines, clean up numbering
            tweets = [
                re.sub(r'^[\d.\-\)\]]+\s*', '', line).strip().strip('"')
                for line in raw.strip().split("\n")
                if line.strip() and len(line.strip()) > 10
            ]
        tweets = [t for t in tweets if isinstance(t, str) and 10 < len(t) <= 300][:count]
    except Exception as e:
        return jsonify({"error": f"LLM generation failed: {e}"}), 503

    _log_usage("tweet_ideas", int((time.time() - start) * 1000))
    return _add_rate_headers(jsonify({"niche": niche, "count": len(tweets), "tweets": tweets}), remaining)


# ---------------------------------------------------------------------------
# 5. Tweet Scorer (heuristic — instant, no LLM)
# ---------------------------------------------------------------------------
def score_tweet(text: str) -> dict:
    """Score a tweet draft 0-100 for engagement potential."""
    if not isinstance(text, str):
        text = str(text or "")
    txt = text.strip()
    char_count = len(txt)
    words = txt.split()
    word_count = len(words)

    # Extract hashtags and mentions
    hashtags = re.findall(r'#\w+', txt)
    mentions = re.findall(r'@\w+', txt)
    urls = re.findall(r'https?://\S+', txt)

    # Detect emojis (simple unicode range check)
    emoji_count = sum(1 for c in txt if ord(c) > 0x1F300)

    # Readability: avg word length
    clean_words = [re.sub(r'[^a-zA-Z0-9]', '', w) for w in words if w and not w.startswith(('#', '@', 'http'))]
    avg_word_len = (sum(len(w) for w in clean_words) / len(clean_words)) if clean_words else 0

    # Power words from the headline analyzer pool
    power_word_set = {
        "secret", "proven", "free", "new", "easy", "instant", "guaranteed",
        "discover", "shocking", "ultimate", "exclusive", "limited", "urgent",
        "massive", "breakthrough", "insider", "hack", "mistake", "simple",
        "powerful", "surprising", "essential", "critical", "warning", "hidden",
        "revealed", "truth", "best", "money", "earn", "fast", "quick", "boost",
        "strategy", "tip", "formula", "blueprint",
    }
    pw_found = [w for w in power_word_set if w in txt.lower()]

    # Scoring
    score = 40  # baseline

    # Character count sweet spot: 71-100 for engagement per studies
    if 71 <= char_count <= 100:
        score += 20
    elif 50 <= char_count <= 140:
        score += 12
    elif char_count <= 30:
        score -= 15
    elif char_count > 240:
        score -= 8

    # Hashtags: 1-2 is optimal
    if len(hashtags) == 1:
        score += 8
    elif len(hashtags) == 2:
        score += 6
    elif len(hashtags) >= 4:
        score -= 12  # over-hashtagging looks spammy

    # Emojis moderate use
    if 1 <= emoji_count <= 3:
        score += 8
    elif emoji_count > 5:
        score -= 5

    # Has a URL (link tweets often do well)
    if urls:
        score += 5

    # Power words
    score += min(12, len(pw_found) * 4)

    # Question mark (curiosity hook)
    if '?' in txt:
        score += 7

    # Starts with a number (list-style)
    if txt and txt[0].isdigit():
        score += 6

    # Excessive caps
    caps_words = sum(1 for w in words if any(c.isalpha() for c in w) and w.isupper())
    caps_ratio = (caps_words / word_count) if word_count else 0
    if caps_ratio >= 0.5:
        score -= 15

    # Multiple mentions (reply-bait penalty)
    if len(mentions) >= 3:
        score -= 8

    # Readability: short avg word length = more readable
    if avg_word_len < 5:
        score += 5

    score = max(0, min(100, int(score)))
    grade = "A" if score >= 80 else "B" if score >= 60 else "C" if score >= 40 else "D"

    suggestions = []
    if char_count > 240:
        suggestions.append("Shorten to under 240 chars — shorter tweets get more engagement.")
    if char_count < 40:
        suggestions.append("Add more context — very short tweets get overlooked.")
    if len(hashtags) == 0:
        suggestions.append("Add 1-2 relevant hashtags to reach more people.")
    if len(hashtags) >= 4:
        suggestions.append("Use at most 2 hashtags — more looks spammy.")
    if emoji_count == 0:
        suggestions.append("Add 1-2 emojis to make the tweet more visually engaging.")
    if not pw_found:
        suggestions.append("Add a power word (e.g. 'secret', 'proven', 'hack') to grab attention.")
    if caps_ratio >= 0.5:
        suggestions.append("Avoid ALL CAPS — it reduces credibility.")
    if '?' not in txt and not txt[0:1].isdigit():
        suggestions.append("Try starting with a number or a question for a stronger hook.")

    return {
        "text": txt,
        "score": score,
        "grade": grade,
        "char_count": char_count,
        "word_count": word_count,
        "hashtag_count": len(hashtags),
        "hashtags": hashtags,
        "mention_count": len(mentions),
        "emoji_count": emoji_count,
        "has_url": bool(urls),
        "power_words_found": pw_found,
        "suggestions": suggestions,
    }


@app.route("/v1/score_tweet", methods=["GET", "POST"])
@app.route("/score-tweet", methods=["GET", "POST"])
@app.route("/score_tweet", methods=["GET", "POST"])
def endpoint_score_tweet():
    # GET requests: return helpful usage info instead of "Method Not Allowed"
    if request.method == "GET":
        return jsonify({
            "endpoint": "score-tweet",
            "method": "POST",
            "description": "Score any tweet draft 0-100 with grade and improvement tips.",
            "usage": {
                "url": "https://contentforge-api-lpp9.onrender.com/score-tweet",
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "body": {"tweet": "your tweet text here"},
            },
            "example_curl": (
                'curl -X POST https://contentforge-api-lpp9.onrender.com/score-tweet '
                '-H "Content-Type: application/json" '
                '-d \'{"tweet": "Want to boost your headline? Try ContentForge free."}\''
            ),
            "note": "No API key needed for direct access. Free tier on RapidAPI: 50 calls/month.",
        }), 200

    if not _verify_rapidapi_request():
        return jsonify({"error": "forbidden"}), 403
    allowed, remaining = _check_rate_limit()
    if not allowed:
        return jsonify({"error": "rate limit exceeded (30/min)"}), 429

    start = time.time()
    payload = request.get_json(silent=True) or {}
    # Accept both "tweet" and "text" as parameter names
    text = (payload.get("tweet") or payload.get("text") or "").strip()

    if not text:
        return jsonify({"error": "missing 'tweet' parameter. Send JSON body: {\"tweet\": \"your text\"}"}), 400
    if len(text) > 1000:
        return jsonify({"error": "text too long (max 1000 chars)"}), 400

    result = score_tweet(text)
    _log_usage("score_tweet", int((time.time() - start) * 1000))
    return _add_rate_headers(jsonify(result), remaining)


# ---------------------------------------------------------------------------
# 5b. LinkedIn Post Scorer (heuristic -- instant, no LLM)
# ---------------------------------------------------------------------------
def score_linkedin_post(text: str) -> dict:
    """Score a LinkedIn post draft 0-100 for engagement and reach potential.

    LinkedIn algorithm and audience differ from Twitter:
      - Longer content performs better (800-1500 chars is the sweet spot)
      - Personal stories and first-person hooks outperform generic advice
      - Short paragraphs with line breaks improve readability
      - 3-5 hashtags is optimal (not 1-2 like Twitter)
      - External URLs suppress reach (LinkedIn wants to keep you on platform)
      - Lists and bullet points get more saves and shares
      - Questions and CTAs at the end drive comments, which boost reach
    """
    if not isinstance(text, str):
        text = str(text or "")
    txt = text.strip()
    char_count = len(txt)
    words = txt.split()
    word_count = len(words)

    # ---- extract features ----
    hashtags = re.findall(r'#\w+', txt)
    mentions = re.findall(r'@\w+', txt)
    urls = re.findall(r'https?://\S+', txt)
    emoji_count = sum(1 for c in txt if ord(c) > 0x1F300)

    # Paragraphs: split on double newlines
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', txt) if p.strip()]
    paragraph_count = len(paragraphs)
    avg_paragraph_len = (
        sum(len(p) for p in paragraphs) / paragraph_count
    ) if paragraph_count else char_count

    # Hook: first paragraph (what shows before "see more")
    hook = paragraphs[0] if paragraphs else txt
    hook_len = len(hook)

    # Bullet / list detection
    list_lines = [
        ln for ln in txt.splitlines()
        if re.match(r'^\s*[-*\u2022\u2023\u25E6\u25CF\u25CB\u2013\u2014]\s', ln)
        or re.match(r'^\s*\d+[.)]\s', ln)
    ]
    has_list = len(list_lines) >= 2

    # CTA detection (last 200 chars)
    tail = txt[-200:].lower() if len(txt) >= 200 else txt.lower()
    cta_phrases = [
        "what do you think", "agree or disagree", "comment below",
        "share this", "thoughts?", "drop a comment", "let me know",
        "would you", "do you agree", "save this", "repost",
        "tag someone", "follow me", "hit follow", "ring the bell",
        "what would you", "your turn", "am i wrong",
    ]
    has_cta = any(phrase in tail for phrase in cta_phrases)
    has_question_at_end = '?' in tail

    # Clean words for readability analysis
    clean_words = [
        re.sub(r'[^a-zA-Z0-9]', '', w)
        for w in words
        if w and not w.startswith(('#', '@', 'http'))
    ]
    avg_word_len = (
        sum(len(w) for w in clean_words) / len(clean_words)
    ) if clean_words else 0

    # Power words (professional/LinkedIn tone)
    power_word_set = {
        "strategy", "proven", "secret", "mistake", "insight", "lesson",
        "discovered", "revealed", "transform", "boost", "growth", "results",
        "data", "framework", "leadership", "career", "opportunity", "mindset",
        "productivity", "hack", "tip", "breakthrough", "surprising", "truth",
        "hidden", "success", "failure", "learned", "changed", "journey",
        "honest", "unpopular", "controversial", "reality", "myth", "warning",
        "free", "simple", "powerful", "essential", "critical",
    }
    pw_found = [w for w in power_word_set if w in txt.lower()]

    # ---- scoring ----
    score = 40  # baseline

    # -- Length (most important factor on LinkedIn) --
    if char_count < 100:
        score -= 10
    elif 100 <= char_count < 300:
        score += 5
    elif 300 <= char_count < 800:
        score += 12
    elif 800 <= char_count <= 1500:
        score += 20  # optimal sweet spot
    elif 1500 < char_count <= 2500:
        score += 15
    elif 2500 < char_count <= 3000:
        score += 8
    else:
        score += 3  # very long, may lose readers

    # -- Hook strength (the first paragraph decides if people click "see more") --
    if hook_len <= 150:
        score += 4  # fits in preview
    if hook and hook[0:1] == "I":
        score += 5  # personal story opener
    if hook and hook[0:1].isdigit():
        score += 5  # number hook
    if '?' in hook:
        score += 4  # curiosity in the hook

    # -- Paragraph structure --
    if paragraph_count >= 3:
        score += 5
    if paragraph_count >= 5:
        score += 3  # well-structured long form
    if avg_paragraph_len < 150:
        score += 4  # short, scannable paragraphs

    # -- List/bullet points --
    if has_list:
        score += 5

    # -- Hashtags (3-5 is LinkedIn optimal) --
    ht_count = len(hashtags)
    if ht_count == 0:
        pass  # no penalty but no discovery boost
    elif 1 <= ht_count <= 2:
        score += 4
    elif 3 <= ht_count <= 5:
        score += 8  # optimal range
    elif ht_count > 5:
        score -= 8  # spammy

    # -- Emoji (professional context: moderate is fine) --
    if 1 <= emoji_count <= 3:
        score += 4
    elif 4 <= emoji_count <= 6:
        score += 2
    elif emoji_count > 6:
        score -= 5

    # -- Engagement drivers --
    if has_question_at_end:
        score += 7
    if has_cta:
        score += 5

    # -- Power words --
    score += min(12, len(pw_found) * 3)

    # -- URL penalty (LinkedIn suppresses posts with outbound links) --
    if urls:
        score -= 5

    # -- ALL CAPS abuse (exclude common acronyms) --
    _acronyms = {
        "API", "AI", "CTA", "CEO", "CTO", "CFO", "COO", "CMO", "HR", "PR",
        "SEO", "SEM", "URL", "DNS", "CSS", "HTML", "JSON", "SQL", "AWS",
        "GCP", "SaaS", "SAAS", "B2B", "B2C", "ROI", "KPI", "OKR", "MVP",
        "IPO", "VC", "YC", "USA", "LLC", "INC", "ETF", "NFT", "DM", "PM",
    }
    caps_words = sum(
        1 for w in words
        if len(w) > 2
        and w.isupper()
        and any(c.isalpha() for c in w)
        and w.strip(".,!?:;") not in _acronyms
    )
    if caps_words >= 3:
        score -= 5

    # -- Excessive exclamation marks --
    if txt.count('!') >= 4:
        score -= 3

    # -- Line break style (single newlines for readability) --
    single_breaks = txt.count('\n') - txt.count('\n\n')
    if single_breaks >= 3:
        score += 3  # LinkedIn-style line spacing

    score = max(0, min(100, int(score)))
    grade = (
        "A" if score >= 80 else
        "B" if score >= 60 else
        "C" if score >= 40 else
        "D" if score >= 20 else
        "F"
    )

    # ---- suggestions ----
    suggestions = []

    if char_count < 300:
        suggestions.append(
            "LinkedIn rewards longer posts. Aim for 800-1500 characters "
            "for maximum reach."
        )
    elif char_count > 2500:
        suggestions.append(
            "Your post is quite long. Consider trimming to under 1500 "
            "characters for better read-through rates."
        )

    if paragraph_count <= 1:
        suggestions.append(
            "Break your post into short paragraphs (2-3 sentences each). "
            "Walls of text get skipped on LinkedIn."
        )
    elif avg_paragraph_len > 200:
        suggestions.append(
            "Your paragraphs are long. Keep each one under 150 characters "
            "for easier scanning on mobile."
        )

    if hook_len > 200:
        suggestions.append(
            "Your opening is too long for the preview. Keep the first "
            "paragraph under 150 characters so people see the hook "
            "before clicking 'see more'."
        )

    if not (hook and hook[0:1] in ("I", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9")):
        if '?' not in hook:
            suggestions.append(
                "Start with a personal story ('I ...'), a number ('3 things...'), "
                "or a question to grab attention in the feed."
            )

    if ht_count == 0:
        suggestions.append(
            "Add 3-5 relevant hashtags at the end. LinkedIn uses them for "
            "topic distribution."
        )
    elif ht_count < 3:
        suggestions.append(
            "Add more hashtags (3-5 total). LinkedIn distributes posts to "
            "hashtag followers."
        )
    elif ht_count > 5:
        suggestions.append(
            "Too many hashtags. Stick to 3-5 relevant ones at the end."
        )

    if not has_list and char_count > 500:
        suggestions.append(
            "Consider adding a bulleted or numbered list. Lists get more "
            "saves and shares."
        )

    if not has_question_at_end and not has_cta:
        suggestions.append(
            "End with a question or call to action (e.g. 'What do you think?' "
            "or 'Save this for later'). Comments drive reach on LinkedIn."
        )

    if urls:
        suggestions.append(
            "LinkedIn suppresses posts with external links. Put the URL in "
            "the first comment instead of the post body for better reach."
        )

    if emoji_count == 0 and char_count > 200:
        suggestions.append(
            "Add 1-2 emojis to break up the text and draw the eye."
        )

    if not pw_found:
        suggestions.append(
            "Add a power word (e.g. 'proven', 'strategy', 'mistake', "
            "'discovered') to make the post more compelling."
        )

    if caps_words >= 3:
        suggestions.append(
            "Tone down the ALL CAPS words. It comes across as shouting "
            "in a professional context."
        )

    return {
        "text": txt,
        "platform": "linkedin",
        "score": score,
        "grade": grade,
        "char_count": char_count,
        "word_count": word_count,
        "paragraph_count": paragraph_count,
        "avg_paragraph_length": round(avg_paragraph_len),
        "hook_length": hook_len,
        "hook_preview": hook[:150] + ("..." if hook_len > 150 else ""),
        "has_list": has_list,
        "list_items_detected": len(list_lines),
        "hashtag_count": ht_count,
        "hashtags": hashtags,
        "mention_count": len(mentions),
        "emoji_count": emoji_count,
        "has_url": bool(urls),
        "url_penalty_applied": bool(urls),
        "has_cta": has_cta,
        "has_question_at_end": has_question_at_end,
        "power_words_found": pw_found,
        "suggestions": suggestions,
    }


@app.route("/v1/score_linkedin_post", methods=["GET", "POST"])
@app.route("/score-linkedin-post", methods=["GET", "POST"])
@app.route("/score_linkedin_post", methods=["GET", "POST"])
def endpoint_score_linkedin_post():
    # GET: return usage doc
    if request.method == "GET":
        return jsonify({
            "endpoint": "score-linkedin-post",
            "method": "POST",
            "description": (
                "Score a LinkedIn post draft 0-100 for reach and engagement. "
                "Analyzes hook strength, paragraph structure, hashtag count, "
                "CTA presence, URL penalties, and more."
            ),
            "usage": {
                "url": "https://contentforge-api-lpp9.onrender.com/score-linkedin-post",
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "body": {"post": "your linkedin post text here"},
            },
            "example_curl": (
                'curl -X POST https://contentforge-api-lpp9.onrender.com/score-linkedin-post '
                '-H "Content-Type: application/json" '
                "-d '{\"post\": \"I spent 3 years building tools nobody used."
                "\\n\\nThen I changed one thing: I started scoring my own content "
                "before posting.\\n\\n#buildinpublic #contentcreation #linkedin\"}'"
            ),
            "scoring_factors": [
                "Post length (sweet spot: 800-1500 chars)",
                "Hook strength (first paragraph, under 150 chars)",
                "Paragraph structure (short, scannable blocks)",
                "Hashtag count (optimal: 3-5)",
                "Bullet/list detection",
                "Call to action or question at end",
                "Power words (professional context)",
                "Emoji usage (moderate is positive)",
                "URL penalty (LinkedIn suppresses external links)",
            ],
            "note": (
                "No API key needed for direct access. "
                "Free tier on RapidAPI: 50 calls/month."
            ),
        }), 200

    if not _verify_rapidapi_request():
        return jsonify({"error": "forbidden"}), 403
    allowed, remaining = _check_rate_limit()
    if not allowed:
        return jsonify({"error": "rate limit exceeded (30/min)"}), 429

    start = time.time()
    payload = request.get_json(silent=True) or {}
    text = (
        payload.get("post")
        or payload.get("text")
        or payload.get("content")
        or ""
    ).strip()

    if not text:
        return jsonify({
            "error": (
                "missing 'post' parameter. "
                'Send JSON body: {"post": "your linkedin post text"}'
            )
        }), 400
    if len(text) > 5000:
        return jsonify({"error": "text too long (max 5000 chars)"}), 400

    result = score_linkedin_post(text)
    _log_usage("score_linkedin_post", int((time.time() - start) * 1000))
    return _add_rate_headers(jsonify(result), remaining)


# ---------------------------------------------------------------------------
# 5c. Instagram Caption Scorer (heuristic -- instant, no LLM)
# ---------------------------------------------------------------------------
def score_instagram_caption(text: str) -> dict:
    """Score an Instagram caption draft 0-100 for engagement potential.

    Instagram-specific signals:
      - Caption length: 138-150 chars is highest engagement, but longer
        captions (up to 2200) work for storytelling niches.
      - Hashtags: 5-15 is optimal (research varies; 11 is the cited sweet
        spot, but 5-15 is broadly safe).  Instagram allows up to 30.
      - Emojis strongly correlate with higher engagement (2-6 is ideal).
      - Call-to-action ("save this", "tag a friend", "double tap") drives
        interaction signals the algorithm rewards.
      - Line breaks improve readability in captions (the "dot spacer" trick
        or simply \\n\\n).
      - Mentions can boost reach via shares.
      - First line is the hook (only ~125 chars show before "more").
    """
    if not isinstance(text, str):
        text = str(text or "")
    txt = text.strip()
    char_count = len(txt)
    words = txt.split()
    word_count = len(words)

    # ---- extract features ----
    hashtags = re.findall(r'#\w+', txt)
    mentions = re.findall(r'@\w+', txt)
    urls = re.findall(r'https?://\S+', txt)
    emoji_count = sum(1 for c in txt if ord(c) > 0x1F300)

    # Hook: first line (before first newline, or first 125 chars)
    first_line = txt.split('\n')[0].strip()
    hook = first_line[:125]
    hook_len = len(first_line)

    # Line breaks (readability)
    line_break_count = txt.count('\n')

    # CTA detection
    tail = txt[-250:].lower() if len(txt) >= 250 else txt.lower()
    cta_phrases = [
        "save this", "tag a friend", "double tap", "comment below",
        "share this", "link in bio", "tap the link", "follow for more",
        "what do you think", "which one", "would you", "tell me",
        "drop a", "let me know", "agree or disagree", "thoughts?",
        "dm me", "check the link", "swipe", "bookmark this",
    ]
    has_cta = any(phrase in tail for phrase in cta_phrases)
    has_question = '?' in tail

    # Power words (Instagram / lifestyle context)
    power_word_set = {
        "free", "secret", "hack", "tip", "proven", "easy", "simple",
        "transform", "boost", "best", "ultimate", "exclusive", "limited",
        "discover", "amazing", "stunning", "beautiful", "inspiring",
        "powerful", "essential", "guide", "tutorial", "results",
        "mistake", "honest", "real", "authentic", "truth", "game-changer",
    }
    pw_found = [w for w in power_word_set if w in txt.lower()]

    # ---- scoring ----
    score = 40  # baseline

    # -- Length --
    if char_count < 20:
        score -= 10  # too short, no context
    elif 20 <= char_count < 70:
        score += 2
    elif 70 <= char_count <= 150:
        score += 15  # optimal engagement sweet spot
    elif 150 < char_count <= 300:
        score += 12
    elif 300 < char_count <= 1000:
        score += 10
    elif 1000 < char_count <= 2200:
        score += 6  # long-form storytelling
    else:
        score -= 5  # over Instagram's 2200 char limit

    # -- Hashtags (5-15 optimal, max 30) --
    ht_count = len(hashtags)
    if ht_count == 0:
        pass  # no discovery boost
    elif 1 <= ht_count <= 4:
        score += 4
    elif 5 <= ht_count <= 15:
        score += 10  # optimal range
    elif 16 <= ht_count <= 30:
        score += 3  # works but may look spammy
    else:
        score -= 10  # over 30 = Instagram may hide the post

    # -- Emojis (Instagram loves them) --
    if emoji_count == 0:
        pass  # no penalty but missed opportunity
    elif 1 <= emoji_count <= 2:
        score += 4
    elif 3 <= emoji_count <= 6:
        score += 8  # optimal
    elif 7 <= emoji_count <= 10:
        score += 4
    elif emoji_count > 10:
        score -= 4

    # -- CTA / engagement prompt --
    if has_cta:
        score += 7
    if has_question:
        score += 5

    # -- Hook strength --
    if hook_len <= 125:
        score += 4  # full hook visible before "more"
    if hook and hook[0:1].isdigit():
        score += 3  # numbered hook

    # -- Line breaks (readability) --
    if line_break_count >= 2:
        score += 4

    # -- Mentions --
    if 1 <= len(mentions) <= 3:
        score += 3

    # -- Power words --
    score += min(10, len(pw_found) * 3)

    # -- URL penalty (Instagram captions don't support clickable links) --
    if urls:
        score -= 5

    # -- ALL CAPS abuse --
    caps_words = sum(
        1 for w in words
        if len(w) > 2 and w.isupper() and any(c.isalpha() for c in w)
    )
    if caps_words >= 3:
        score -= 5

    # -- Excessive exclamation --
    if txt.count('!') >= 5:
        score -= 3

    score = max(0, min(100, int(score)))
    grade = (
        "A" if score >= 80 else
        "B" if score >= 60 else
        "C" if score >= 40 else
        "D" if score >= 20 else
        "F"
    )

    # ---- suggestions ----
    suggestions = []

    if char_count < 50:
        suggestions.append(
            "Your caption is very short. Add more context or a story "
            "to engage your audience."
        )
    if char_count > 2200:
        suggestions.append(
            "Instagram caps captions at 2,200 characters. Trim it down."
        )

    if ht_count == 0:
        suggestions.append(
            "Add 5-15 relevant hashtags for discoverability. Mix popular "
            "and niche-specific tags."
        )
    elif ht_count < 5:
        suggestions.append(
            f"You have {ht_count} hashtag(s). Aim for 5-15 for optimal "
            "Instagram reach."
        )
    elif ht_count > 30:
        suggestions.append(
            "Instagram allows a max of 30 hashtags. Remove the extras "
            "or your post may be hidden."
        )

    if emoji_count == 0:
        suggestions.append(
            "Add 2-6 emojis. Instagram posts with emojis get measurably "
            "higher engagement."
        )

    if not has_cta and not has_question:
        suggestions.append(
            "End with a CTA ('Save this', 'Tag a friend', 'What do you "
            "think?') to drive comments and saves."
        )

    if hook_len > 125:
        suggestions.append(
            "Keep the first line under 125 characters — that's all users "
            "see before tapping 'more'."
        )

    if line_break_count == 0 and char_count > 100:
        suggestions.append(
            "Add line breaks to make the caption scannable. Use blank "
            "lines or dot spacers between sections."
        )

    if urls:
        suggestions.append(
            "Links in Instagram captions aren't clickable. Move the URL "
            "to your bio and say 'link in bio'."
        )

    if not pw_found:
        suggestions.append(
            "Add a power word (e.g. 'secret', 'hack', 'transform', "
            "'authentic') to make the caption pop."
        )

    return {
        "text": txt,
        "platform": "instagram",
        "score": score,
        "grade": grade,
        "char_count": char_count,
        "word_count": word_count,
        "hook_length": hook_len,
        "hook_preview": hook + ("..." if hook_len > 125 else ""),
        "line_break_count": line_break_count,
        "hashtag_count": ht_count,
        "hashtags": hashtags,
        "mention_count": len(mentions),
        "emoji_count": emoji_count,
        "has_url": bool(urls),
        "has_cta": has_cta,
        "has_question": has_question,
        "power_words_found": pw_found,
        "suggestions": suggestions,
    }


@app.route("/v1/score_instagram", methods=["GET", "POST"])
@app.route("/score-instagram", methods=["GET", "POST"])
@app.route("/score_instagram", methods=["GET", "POST"])
def endpoint_score_instagram():
    # GET: return usage doc
    if request.method == "GET":
        return jsonify({
            "endpoint": "score-instagram",
            "method": "POST",
            "description": (
                "Score an Instagram caption draft 0-100 for engagement. "
                "Analyzes caption length, hashtag count, emoji usage, "
                "CTA detection, hook strength, and more."
            ),
            "usage": {
                "url": "https://contentforge-api-lpp9.onrender.com/score-instagram",
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "body": {"caption": "your instagram caption here"},
            },
            "example_curl": (
                'curl -X POST https://contentforge-api-lpp9.onrender.com/score-instagram '
                '-H "Content-Type: application/json" '
                "-d '{\"caption\": \"Stop scrolling. This changed my morning routine forever."
                "\\n\\nI tried 30 days of cold showers and here's what happened.\\n\\n"
                "#morningroutine #coldshower #productivity #selfimprovement #lifehacks\"}'"
            ),
            "scoring_factors": [
                "Caption length (sweet spot: 70-150 chars for engagement)",
                "Hashtag count (optimal: 5-15)",
                "Emoji usage (2-6 is ideal on Instagram)",
                "Hook strength (first 125 chars show before 'more')",
                "Call to action (save, tag, comment, etc.)",
                "Line breaks and readability",
                "Power words (lifestyle/engagement context)",
                "URL penalty (links aren't clickable in captions)",
            ],
            "note": (
                "No API key needed for direct access. "
                "Free tier on RapidAPI: 50 calls/month."
            ),
        }), 200

    if not _verify_rapidapi_request():
        return jsonify({"error": "forbidden"}), 403
    allowed, remaining = _check_rate_limit()
    if not allowed:
        return jsonify({"error": "rate limit exceeded (30/min)"}), 429

    start = time.time()
    payload = request.get_json(silent=True) or {}
    text = (
        payload.get("caption")
        or payload.get("text")
        or payload.get("post")
        or ""
    ).strip()

    if not text:
        return jsonify({
            "error": (
                "missing 'caption' parameter. "
                'Send JSON body: {"caption": "your instagram caption text"}'
            )
        }), 400
    if len(text) > 5000:
        return jsonify({"error": "text too long (max 5000 chars)"}), 400

    result = score_instagram_caption(text)
    _log_usage("score_instagram", int((time.time() - start) * 1000))
    return _add_rate_headers(jsonify(result), remaining)


# ---------------------------------------------------------------------------
# 5d. YouTube Title & Thumbnail Text Scorer (heuristic -- instant, no LLM)
# ---------------------------------------------------------------------------
def score_youtube_title(text: str, thumbnail_text: str = "") -> dict:
    """Score a YouTube title (and optional thumbnail text) 0-100 for CTR.

    YouTube-specific signals:
      - Title length: 40-60 chars is optimal for CTR (shows fully in search
        and suggested). Under 70 to avoid truncation.
      - Numbers in titles boost CTR (listicles, years, amounts).
      - Emotional/curiosity words drive clicks.
      - Brackets/parentheses add perceived value: [Tutorial], (2026).
      - ALL CAPS in 1-2 words is acceptable for emphasis; full caps = spam.
      - Thumbnail text should be short (3-5 words max), readable, and not
        repeat the title verbatim.
    """
    if not isinstance(text, str):
        text = str(text or "")
    title = text.strip()
    thumb = (thumbnail_text or "").strip()
    char_count = len(title)
    words = title.split()
    word_count = len(words)

    # ---- extract features ----
    has_number = bool(re.search(r'\d', title))
    has_year = bool(re.search(r'20\d{2}', title))
    has_bracket = bool(re.search(r'[\[\(]', title))
    has_question = '?' in title
    has_pipe_or_dash = bool(re.search(r'[|—–-]', title))
    has_colon = ':' in title

    # Power words (YouTube CTR drivers)
    power_word_set = {
        "how", "why", "best", "worst", "top", "secret", "proven", "free",
        "ultimate", "complete", "guide", "tutorial", "review", "honest",
        "truth", "mistake", "avoid", "hack", "easy", "fast", "simple",
        "shocking", "insane", "unbelievable", "never", "always", "stop",
        "need", "must", "watch", "revealed", "warning", "finally",
        "changed", "updated", "new", "real", "actual", "exactly",
        "tried", "tested", "results", "money", "making", "earn",
    }
    pw_found = [w for w in power_word_set if w in title.lower().split()]

    # Emoji in title (generally discouraged on YT)
    emoji_count = sum(1 for c in title if ord(c) > 0x1F300)

    # ALL CAPS analysis
    caps_words = [w for w in words if w.isupper() and len(w) > 1 and any(c.isalpha() for c in w)]
    caps_count = len(caps_words)

    # ---- scoring ----
    score = 40  # baseline

    # -- Length --
    if char_count < 20:
        score -= 5
    elif 20 <= char_count < 40:
        score += 8
    elif 40 <= char_count <= 60:
        score += 18  # optimal CTR range
    elif 60 < char_count <= 70:
        score += 12  # still shows fully
    elif 70 < char_count <= 100:
        score += 3  # starts truncating
    else:
        score -= 8  # heavily truncated

    # -- Numbers --
    if has_number:
        score += 6
    if has_year:
        score += 3  # current year signals freshness

    # -- Brackets/Parentheses --
    if has_bracket:
        score += 5

    # -- Question --
    if has_question:
        score += 5

    # -- Structural separators (Title | Category or Title: Subtitle) --
    if has_pipe_or_dash or has_colon:
        score += 3

    # -- Power words --
    score += min(12, len(pw_found) * 3)

    # -- Emoji (mild penalty on YouTube) --
    if emoji_count == 1:
        score += 1
    elif emoji_count >= 2:
        score -= 3

    # -- CAPS emphasis (1-2 words = emphasis, 3+ = spammy) --
    if 1 <= caps_count <= 2:
        score += 4
    elif caps_count >= 3:
        score -= 8

    # -- Word count sweet spot --
    if 5 <= word_count <= 10:
        score += 3

    # -- Thumbnail text analysis --
    thumb_score_detail = {}
    if thumb:
        thumb_words = thumb.split()
        thumb_word_count = len(thumb_words)
        thumb_char_count = len(thumb)

        thumb_bonus = 0
        if 1 <= thumb_word_count <= 5:
            thumb_bonus += 5  # short and readable
        elif thumb_word_count > 7:
            thumb_bonus -= 5  # too cluttered

        # Penalize if thumbnail text duplicates the title
        title_lower = title.lower()
        thumb_lower = thumb.lower()
        overlap_words = set(thumb_lower.split()) & set(title_lower.split())
        filler_words = {"the", "a", "an", "is", "to", "for", "and", "of", "in", "on", "it", "my", "i", "you", "your"}
        meaningful_overlap = overlap_words - filler_words
        if len(meaningful_overlap) >= 3:
            thumb_bonus -= 5  # too much repetition

        # Thumb caps (acceptable for thumbnails)
        if thumb.isupper() and thumb_word_count <= 4:
            thumb_bonus += 2  # ALL CAPS thumbnail text is fine for short text

        score += thumb_bonus
        thumb_score_detail = {
            "thumbnail_text": thumb,
            "thumbnail_word_count": thumb_word_count,
            "thumbnail_char_count": thumb_char_count,
            "thumbnail_title_overlap": list(meaningful_overlap),
            "thumbnail_bonus": thumb_bonus,
        }

    score = max(0, min(100, int(score)))
    grade = (
        "A" if score >= 80 else
        "B" if score >= 60 else
        "C" if score >= 40 else
        "D" if score >= 20 else
        "F"
    )

    # ---- suggestions ----
    suggestions = []

    if char_count < 30:
        suggestions.append(
            "Your title is very short. Aim for 40-60 characters for "
            "optimal CTR in YouTube search and suggested."
        )
    elif char_count > 70:
        suggestions.append(
            "Your title may be truncated in search results. Keep it "
            "under 70 characters (40-60 is the sweet spot)."
        )

    if not has_number:
        suggestions.append(
            "Add a number to your title (e.g. '5 Ways...', '$1,000', "
            "'in 30 Days'). Numbered titles get higher CTR."
        )

    if not has_bracket:
        suggestions.append(
            "Consider adding brackets like [Tutorial], [2026], or "
            "(Step by Step) — they boost perceived value."
        )

    if not pw_found:
        suggestions.append(
            "Add a power word (e.g. 'best', 'secret', 'proven', "
            "'honest', 'ultimate') to drive curiosity."
        )

    if not has_question and word_count < 8:
        suggestions.append(
            "Try phrasing as a question ('How to...?', 'Why does...?') "
            "for a curiosity-driven hook."
        )

    if caps_count >= 3:
        suggestions.append(
            "Too many ALL CAPS words. Use 1-2 for emphasis (e.g. "
            "'NEVER Do This') — more looks clickbaity."
        )

    if emoji_count >= 2:
        suggestions.append(
            "Minimize emojis in YouTube titles. One max — save emojis "
            "for the description."
        )

    if thumb:
        if len(thumb.split()) > 5:
            suggestions.append(
                "Thumbnail text is too long. Keep it to 3-5 words max "
                "for readability at small sizes."
            )
        if thumb_score_detail.get("thumbnail_title_overlap"):
            suggestions.append(
                "Your thumbnail text repeats title words "
                f"({', '.join(thumb_score_detail['thumbnail_title_overlap'])}). "
                "Use complementary text that adds context, not repetition."
            )

    result = {
        "text": title,
        "platform": "youtube",
        "score": score,
        "grade": grade,
        "char_count": char_count,
        "word_count": word_count,
        "has_number": has_number,
        "has_year": has_year,
        "has_bracket": has_bracket,
        "has_question": has_question,
        "caps_words": caps_count,
        "emoji_count": emoji_count,
        "power_words_found": pw_found,
        "suggestions": suggestions,
    }
    result.update(thumb_score_detail)
    return result


@app.route("/v1/score_youtube_title", methods=["GET", "POST"])
@app.route("/score-youtube-title", methods=["GET", "POST"])
@app.route("/score_youtube_title", methods=["GET", "POST"])
def endpoint_score_youtube_title():
    # GET: return usage doc
    if request.method == "GET":
        return jsonify({
            "endpoint": "score-youtube-title",
            "method": "POST",
            "description": (
                "Score a YouTube title (and optional thumbnail text) 0-100 "
                "for click-through rate potential. Analyzes title length, "
                "numbers, power words, brackets, caps emphasis, and more."
            ),
            "usage": {
                "url": "https://contentforge-api-lpp9.onrender.com/score-youtube-title",
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "body": {
                    "title": "your youtube title here",
                    "thumbnail_text": "(optional) text on the thumbnail",
                },
            },
            "example_curl": (
                'curl -X POST https://contentforge-api-lpp9.onrender.com/score-youtube-title '
                '-H "Content-Type: application/json" '
                "-d '{\"title\": \"I Tried Making $1,000 in 24 Hours [Realistic Results]\", "
                "\"thumbnail_text\": \"$1K IN 24H??\"}'"
            ),
            "scoring_factors": [
                "Title length (sweet spot: 40-60 chars)",
                "Numbers in title (boost CTR)",
                "Power words (curiosity, emotion)",
                "Brackets/parentheses ([Tutorial], (2026))",
                "Question format (curiosity hook)",
                "CAPS emphasis (1-2 words good, 3+ bad)",
                "Thumbnail text (short, complementary, not repetitive)",
            ],
            "note": (
                "No API key needed for direct access. "
                "Free tier on RapidAPI: 50 calls/month."
            ),
        }), 200

    if not _verify_rapidapi_request():
        return jsonify({"error": "forbidden"}), 403
    allowed, remaining = _check_rate_limit()
    if not allowed:
        return jsonify({"error": "rate limit exceeded (30/min)"}), 429

    start = time.time()
    payload = request.get_json(silent=True) or {}
    title = (
        payload.get("title")
        or payload.get("text")
        or ""
    ).strip()
    thumbnail_text = (payload.get("thumbnail_text") or "").strip()

    if not title:
        return jsonify({
            "error": (
                "missing 'title' parameter. "
                'Send JSON body: {"title": "your youtube title"}'
            )
        }), 400
    if len(title) > 500:
        return jsonify({"error": "title too long (max 500 chars)"}), 400

    result = score_youtube_title(title, thumbnail_text)
    _log_usage("score_youtube_title", int((time.time() - start) * 1000))
    return _add_rate_headers(jsonify(result), remaining)


# ---------------------------------------------------------------------------
# 5e. Email Subject Line Scorer (heuristic -- instant, no LLM)
# ---------------------------------------------------------------------------
def score_email_subject(text: str, preview_text: str = "") -> dict:
    """Score an email subject line 0-100 for open rate potential.

    Email-specific signals:
      - Length: 30-50 chars is optimal (fully visible on mobile and desktop).
        Under 20 feels incomplete, over 60 gets truncated on mobile.
      - Personalization tokens (e.g. {first_name}) boost open rates ~26%.
      - Numbers boost opens (specificity).
      - Urgency/scarcity words work but overuse triggers spam filters.
      - ALL CAPS is a major spam signal.
      - Excessive punctuation (!!! or ???) hurts deliverability.
      - Spam trigger words lower inbox placement.
      - Preview/preheader text should complement, not repeat the subject.
      - Emojis: one well-placed emoji boosts mobile open rates.
    """
    if not isinstance(text, str):
        text = str(text or "")
    subj = text.strip()
    preview = (preview_text or "").strip()
    char_count = len(subj)
    words = subj.split()
    word_count = len(words)

    # ---- extract features ----
    has_number = bool(re.search(r'\d', subj))
    has_question = '?' in subj
    emoji_count = sum(1 for c in subj if ord(c) > 0x1F300)

    # Personalization tokens like {first_name}, {{name}}, [NAME]
    personalization_tokens = re.findall(
        r'\{+\w+\}+|\[\w+\]', subj
    )
    has_personalization = bool(personalization_tokens)

    # Urgency/scarcity words
    urgency_words = {
        "urgent", "limited", "expires", "deadline", "last chance",
        "final", "hurry", "now", "today", "ending", "don't miss",
        "act now", "only", "hours left", "closing",
    }
    uw_found = [w for w in urgency_words if w in subj.lower()]

    # Power words (email context)
    power_word_set = {
        "free", "new", "exclusive", "proven", "secret", "insider",
        "important", "update", "announcement", "invitation", "breaking",
        "confirmed", "discover", "unlock", "introducing", "save",
        "results", "quick", "easy", "guide", "mistake", "warning",
        "alert", "you", "your",
    }
    pw_found = [w for w in power_word_set if w in subj.lower().split()]

    # Spam trigger words (common in email marketing)
    spam_triggers = {
        "buy now", "click here", "order now", "subscribe now",
        "100% free", "act now", "apply now", "as seen on",
        "billion", "cash", "cheap", "congratulations", "credit",
        "dear friend", "discount", "double your", "earn money",
        "fast cash", "get rich", "guarantee", "incredible deal",
        "info you requested", "investment", "lottery", "make money",
        "million", "no obligation", "offer", "once in a lifetime",
        "opt in", "please read", "prize", "promise", "risk free",
        "satisfaction guaranteed", "special promotion", "this isn't spam",
        "unsolicited", "winner", "you have been selected", "$$",
    }
    spam_found = [t for t in spam_triggers if t in subj.lower()]

    # ALL CAPS detection
    caps_words = sum(
        1 for w in words
        if len(w) > 1 and w.isupper() and any(c.isalpha() for c in w)
    )

    # Excessive punctuation
    exclamation_count = subj.count('!')
    question_count = subj.count('?')

    # ---- scoring ----
    score = 40  # baseline

    # -- Length --
    if char_count < 10:
        score -= 10
    elif 10 <= char_count < 20:
        score += 3
    elif 20 <= char_count < 30:
        score += 10
    elif 30 <= char_count <= 50:
        score += 18  # optimal
    elif 50 < char_count <= 60:
        score += 12
    elif 60 < char_count <= 80:
        score += 5
    else:
        score -= 5  # too long

    # -- Personalization --
    if has_personalization:
        score += 8

    # -- Numbers --
    if has_number:
        score += 5

    # -- Question --
    if has_question and question_count <= 1:
        score += 5

    # -- Power words --
    score += min(12, len(pw_found) * 3)

    # -- Urgency words (small boost, but penalize excess) --
    if 1 <= len(uw_found) <= 2:
        score += 5
    elif len(uw_found) >= 3:
        score -= 5  # feels like spam

    # -- Emoji --
    if emoji_count == 1:
        score += 4
    elif emoji_count >= 2:
        score -= 3

    # -- Spam triggers --
    score -= min(20, len(spam_found) * 5)

    # -- ALL CAPS --
    if caps_words >= 2:
        score -= 10  # major spam signal
    elif caps_words == 1:
        score -= 3

    # -- Excessive punctuation --
    if exclamation_count >= 2:
        score -= 6
    elif exclamation_count == 1:
        score -= 1
    if question_count >= 2:
        score -= 3

    # -- Word count sweet spot --
    if 4 <= word_count <= 8:
        score += 3

    # -- Preview text analysis --
    preview_detail = {}
    if preview:
        preview_bonus = 0
        preview_len = len(preview)
        if 40 <= preview_len <= 100:
            preview_bonus += 5  # optimal preheader length
        elif preview_len < 20:
            preview_bonus += 1

        # Penalize if preview repeats subject
        subj_words_set = set(subj.lower().split())
        preview_words_set = set(preview.lower().split())
        filler = {"the", "a", "an", "is", "to", "for", "and", "of", "in", "on", "it", "i", "you", "your", "we"}
        overlap = (subj_words_set & preview_words_set) - filler
        if len(overlap) >= 3:
            preview_bonus -= 4

        score += preview_bonus
        preview_detail = {
            "preview_text": preview,
            "preview_char_count": preview_len,
            "preview_subject_overlap": list(overlap),
            "preview_bonus": preview_bonus,
        }

    score = max(0, min(100, int(score)))
    grade = (
        "A" if score >= 80 else
        "B" if score >= 60 else
        "C" if score >= 40 else
        "D" if score >= 20 else
        "F"
    )

    # ---- suggestions ----
    suggestions = []

    if char_count < 20:
        suggestions.append(
            "Your subject line is very short. Aim for 30-50 characters "
            "to give recipients enough context to open."
        )
    elif char_count > 60:
        suggestions.append(
            "Your subject line will be truncated on mobile. Keep it "
            "under 50 characters (30-50 is optimal)."
        )

    if not has_personalization:
        suggestions.append(
            "Add personalization like {first_name} — personalized subject "
            "lines increase open rates by ~26%."
        )

    if not has_number:
        suggestions.append(
            "Add a number for specificity (e.g. '5 tips', 'in 3 minutes', "
            "'save $200'). Numbers signal concrete value."
        )

    if not pw_found and not uw_found:
        suggestions.append(
            "Add a power word (e.g. 'exclusive', 'proven', 'quick', "
            "'free', 'new') to drive curiosity."
        )

    if spam_found:
        suggestions.append(
            f"Spam trigger(s) detected: {', '.join(spam_found)}. These "
            "can land you in the spam folder."
        )

    if caps_words >= 2:
        suggestions.append(
            "Avoid ALL CAPS words in email subjects — it's a spam signal "
            "that hurts deliverability."
        )

    if exclamation_count >= 2:
        suggestions.append(
            "Reduce exclamation marks. Multiple !!! triggers spam "
            "filters in most email clients."
        )

    if emoji_count == 0:
        suggestions.append(
            "Consider adding one emoji — it can boost open rates on "
            "mobile by making your subject stand out."
        )
    elif emoji_count >= 2:
        suggestions.append(
            "Use at most 1 emoji. Multiple emojis in subjects reduce "
            "perceived professionalism."
        )

    if preview and preview_detail.get("preview_subject_overlap"):
        suggestions.append(
            "Your preview text repeats the subject. Use it to add context "
            "or a teaser that complements the subject line."
        )
    elif not preview:
        suggestions.append(
            "Add preview/preheader text (40-100 chars) to complement "
            "the subject line. It shows next to the subject in inbox."
        )

    result = {
        "text": subj,
        "platform": "email",
        "score": score,
        "grade": grade,
        "char_count": char_count,
        "word_count": word_count,
        "has_number": has_number,
        "has_question": has_question,
        "has_personalization": has_personalization,
        "personalization_tokens": personalization_tokens,
        "emoji_count": emoji_count,
        "urgency_words_found": uw_found,
        "power_words_found": pw_found,
        "spam_triggers_found": spam_found,
        "caps_word_count": caps_words,
        "exclamation_count": exclamation_count,
        "suggestions": suggestions,
    }
    result.update(preview_detail)
    return result


@app.route("/v1/score_email_subject", methods=["GET", "POST"])
@app.route("/score-email-subject", methods=["GET", "POST"])
@app.route("/score_email_subject", methods=["GET", "POST"])
def endpoint_score_email_subject():
    # GET: return usage doc
    if request.method == "GET":
        return jsonify({
            "endpoint": "score-email-subject",
            "method": "POST",
            "description": (
                "Score an email subject line (and optional preview/preheader) "
                "0-100 for open rate potential. Analyzes length, personalization, "
                "power words, spam triggers, ALL CAPS, and more."
            ),
            "usage": {
                "url": "https://contentforge-api-lpp9.onrender.com/score-email-subject",
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "body": {
                    "subject": "your email subject line here",
                    "preview_text": "(optional) preheader/preview text",
                },
            },
            "example_curl": (
                'curl -X POST https://contentforge-api-lpp9.onrender.com/score-email-subject '
                '-H "Content-Type: application/json" '
                "-d '{\"subject\": \"{first_name}, your 3-step plan is ready\", "
                "\"preview_text\": \"Open to see the strategy top creators use\"}'"
            ),
            "scoring_factors": [
                "Subject length (sweet spot: 30-50 chars)",
                "Personalization tokens ({first_name}, etc.)",
                "Numbers (specificity boosts opens)",
                "Power words (exclusive, proven, new, etc.)",
                "Urgency words (limited, deadline, etc.)",
                "Spam trigger detection (buy now, click here, etc.)",
                "ALL CAPS penalty (spam signal)",
                "Excessive punctuation penalty",
                "Emoji (1 is good, 2+ is risky)",
                "Preview text (complementary, not repetitive)",
            ],
            "note": (
                "No API key needed for direct access. "
                "Free tier on RapidAPI: 50 calls/month."
            ),
        }), 200

    if not _verify_rapidapi_request():
        return jsonify({"error": "forbidden"}), 403
    allowed, remaining = _check_rate_limit()
    if not allowed:
        return jsonify({"error": "rate limit exceeded (30/min)"}), 429

    start = time.time()
    payload = request.get_json(silent=True) or {}
    subject = (
        payload.get("subject")
        or payload.get("text")
        or ""
    ).strip()
    preview_text = (payload.get("preview_text") or payload.get("preview") or "").strip()

    if not subject:
        return jsonify({
            "error": (
                "missing 'subject' parameter. "
                'Send JSON body: {"subject": "your email subject line"}'
            )
        }), 400
    if len(subject) > 500:
        return jsonify({"error": "subject too long (max 500 chars)"}), 400

    result = score_email_subject(subject, preview_text)
    _log_usage("score_email_subject", int((time.time() - start) * 1000))
    return _add_rate_headers(jsonify(result), remaining)


# ---------------------------------------------------------------------------
# 5f. Readability Score (heuristic — instant, no LLM)
# ---------------------------------------------------------------------------
def score_readability(text: str) -> dict:
    """Score any text for readability using Flesch-Kincaid metrics.

    Returns 0-100 score, grade, Flesch Reading Ease, Flesch-Kincaid Grade
    Level, average sentence length, average syllables per word, and
    suggestions for improving readability.
    """
    import re as _re
    import math

    text = (text or "").strip()
    if not text:
        return {
            "text": "",
            "score": 0,
            "grade": "F",
            "flesch_reading_ease": 0,
            "flesch_kincaid_grade": 0,
            "avg_sentence_length": 0,
            "avg_syllables_per_word": 0,
            "sentence_count": 0,
            "word_count": 0,
            "char_count": 0,
            "suggestions": ["No text provided."],
        }

    char_count = len(text)

    # --- sentence splitting ---------------------------------------------------
    sentences = _re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    sentence_count = max(len(sentences), 1)

    # --- word splitting -------------------------------------------------------
    words = _re.findall(r"[a-zA-Z']+", text)
    word_count = max(len(words), 1)

    # --- syllable counter (approximation) ------------------------------------
    def _count_syllables(word):
        word = word.lower().strip()
        if len(word) <= 2:
            return 1
        # remove trailing e
        if word.endswith("e"):
            word = word[:-1]
        vowels = "aeiouy"
        count = 0
        prev_vowel = False
        for ch in word:
            is_vowel = ch in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        return max(count, 1)

    total_syllables = sum(_count_syllables(w) for w in words)
    avg_sentence_length = round(word_count / sentence_count, 1)
    avg_syllables_per_word = round(total_syllables / word_count, 2)

    # --- Flesch Reading Ease (0-100, higher = easier) -------------------------
    fre = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
    fre = round(max(0, min(100, fre)), 1)

    # --- Flesch-Kincaid Grade Level (US school grade) -------------------------
    fkgl = (0.39 * avg_sentence_length) + (11.8 * avg_syllables_per_word) - 15.59
    fkgl = round(max(0, fkgl), 1)

    # --- Build 0-100 composite score ------------------------------------------
    # Goal: most web/social content should target grade 6-9 (easy to read)
    score = 40  # base

    # Flesch Reading Ease mapping (higher FRE = better for general audiences)
    if fre >= 70:
        score += 25  # very easy
    elif fre >= 60:
        score += 20  # standard
    elif fre >= 50:
        score += 12  # fairly difficult
    elif fre >= 30:
        score += 5   # difficult
    # else: 0 bonus (very difficult)

    # Grade level targeting (6-9 is ideal for most online content)
    if 5 <= fkgl <= 9:
        score += 20  # ideal range
    elif 3 <= fkgl <= 12:
        score += 10  # acceptable
    elif fkgl <= 15:
        score += 3   # academic level
    # else: 0 (too complex)

    # Sentence length variety (not all same length = more engaging)
    if sentence_count >= 3:
        lens = [len(_re.findall(r"[a-zA-Z']+", s)) for s in sentences]
        variance = sum((l - avg_sentence_length) ** 2 for l in lens) / len(lens)
        std_dev = math.sqrt(variance)
        if std_dev >= 4:
            score += 8  # good variety
        elif std_dev >= 2:
            score += 4
        # monotone sentences get no bonus

    # Short paragraphs bonus (line breaks suggest formatting)
    line_breaks = text.count("\n")
    if line_breaks >= 2:
        score += 5
    elif line_breaks >= 1:
        score += 2

    # Penalize excessively long sentences
    if avg_sentence_length > 25:
        score -= 8
    elif avg_sentence_length > 20:
        score -= 3

    # Penalize very short content (< 50 chars)
    if char_count < 50:
        score -= 5

    score = max(0, min(100, score))

    # --- Grade ---------------------------------------------------------------
    if score >= 80:
        grade = "A"
    elif score >= 65:
        grade = "B"
    elif score >= 50:
        grade = "C"
    elif score >= 35:
        grade = "D"
    else:
        grade = "F"

    # --- Suggestions -----------------------------------------------------------
    suggestions = []
    if fre < 50:
        suggestions.append("Text is hard to read. Use shorter words and simpler sentences.")
    if fkgl > 12:
        suggestions.append(f"Grade level {fkgl} is above college level. Aim for grade 6-9 for online audiences.")
    elif fkgl > 9:
        suggestions.append(f"Grade level {fkgl} is a bit high. Consider simplifying for broader reach.")
    if avg_sentence_length > 25:
        suggestions.append(f"Average sentence length is {avg_sentence_length} words. Try keeping sentences under 20 words.")
    elif avg_sentence_length > 20:
        suggestions.append(f"Sentences average {avg_sentence_length} words. Mixing in shorter sentences improves flow.")
    if sentence_count < 3 and char_count > 100:
        suggestions.append("Consider breaking your text into more sentences for easier scanning.")
    if line_breaks == 0 and char_count > 200:
        suggestions.append("Add line breaks or paragraphs to improve visual readability.")
    if avg_syllables_per_word > 1.8:
        suggestions.append("Many multi-syllable words. Replace complex words with simpler alternatives where possible.")
    if not suggestions:
        if score >= 80:
            suggestions.append("Excellent readability! This text is well-suited for a general audience.")
        else:
            suggestions.append("Readability is acceptable. Minor simplification could improve clarity.")

    # --- Reading level description -------------------------------------------
    if fkgl <= 5:
        reading_level = "elementary"
    elif fkgl <= 8:
        reading_level = "middle school"
    elif fkgl <= 12:
        reading_level = "high school"
    elif fkgl <= 16:
        reading_level = "college"
    else:
        reading_level = "graduate"

    return {
        "text": text[:500] + ("..." if len(text) > 500 else ""),
        "score": score,
        "grade": grade,
        "flesch_reading_ease": fre,
        "flesch_kincaid_grade": fkgl,
        "reading_level": reading_level,
        "avg_sentence_length": avg_sentence_length,
        "avg_syllables_per_word": avg_syllables_per_word,
        "sentence_count": sentence_count,
        "word_count": word_count,
        "char_count": char_count,
        "suggestions": suggestions,
    }


@app.route("/v1/score_readability", methods=["GET", "POST"])
@app.route("/score-readability", methods=["GET", "POST"])
@app.route("/score_readability", methods=["GET", "POST"])
def endpoint_score_readability():
    if not _verify_rapidapi_request():
        return jsonify({"error": "forbidden"}), 403

    # --- GET: usage docs ---
    if request.method == "GET":
        return jsonify({
            "endpoint": "/v1/score_readability",
            "method": "POST",
            "description": (
                "Score any text for readability 0-100. Returns Flesch Reading Ease, "
                "Flesch-Kincaid Grade Level, reading level label, sentence/word stats, "
                "and actionable improvement suggestions. Instant, no AI needed."
            ),
            "parameters": {
                "text": "(required) the text to analyze — any length",
            },
            "example_body": {"text": "Short sentences work best. They keep the reader engaged. Use simple words too."},
            "try_it": "POST this endpoint with a JSON body to score your text.",
        })

    allowed, remaining = _check_rate_limit()
    if not allowed:
        return jsonify({"error": "rate limit exceeded"}), 429

    start = time.time()
    data = request.get_json(silent=True) or {}
    text = data.get("text") or data.get("content") or data.get("body") or ""
    text = text.strip()

    if not text:
        return jsonify({
            "error": (
                "missing 'text' parameter. "
                'Send JSON body: {"text": "your content to analyze"}'
            )
        }), 400

    result = score_readability(text)
    _log_usage("score_readability", int((time.time() - start) * 1000))
    return _add_rate_headers(jsonify(result), remaining)


# ---------------------------------------------------------------------------
# 5g2. Threads Post Score (heuristic — instant, no LLM)
# ---------------------------------------------------------------------------
def score_threads_post(text: str) -> dict:
    """Score a Meta Threads post 0-100 for reach and engagement.

    Threads-specific signals (as of 2024-2026 Meta guidance):
    - Length: 50-250 is conversational sweet spot (+15). 251-400 (+8). <50 or >400 (-5)
    - Hashtags: Threads penalizes hashtag stuffing. 0 = neutral. 1 = -3. 2+ = -5 each.
    - Emojis: 1-2 is natural (+8). 3-4 is OK (+4). 5+ feels spammy (-4).
    - Question hook: conversational and reply-baiting (+10)
    - Personal pronouns (I/me/my/we): first-person authenticity (+6)
    - CTA keywords: "agree", "thoughts", "comment", "reply", "share", "follow" (+7)
    - Power words: same broad set as tweet scorer (max +12)
    - Number/digit in text: +4
    - Links in the post: -6 (Meta removes links; bad for reach)
    - ALL CAPS word abuse: -6
    """
    _THREADS_POWER_WORDS = {
        "secret", "hack", "revealed", "proven", "instant", "boost", "simple",
        "free", "discover", "strategy", "tip", "now", "fast", "quick",
        "powerful", "result", "growth", "worth", "better", "mistake",
        "change", "never", "always", "only", "real", "truth", "honest",
        "exactly", "finally", "stop", "start",
    }
    _THREADS_CTA_WORDS = {
        "agree", "disagree", "thoughts", "comment", "reply",
        "share", "follow", "drop", "tell me", "what do you",
    }

    text = (text or "").strip()
    if not text:
        return {
            "text": text, "score": 0, "grade": "F",
            "char_count": 0, "word_count": 0, "hashtag_count": 0,
            "emoji_count": 0, "has_cta": False, "has_question": False,
            "has_number": False, "has_link": False, "has_personal_pronoun": False,
            "caps_abuse": False, "hashtags": [], "power_words_found": [], "caps_words": [],
        }

    char_count = len(text)
    words = text.split()
    word_count = len(words)
    hashtags = re.findall(r'#\w+', text)
    hashtag_count = len(hashtags)
    emojis = re.findall(
        r'[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0001FA00-\U0001FA9F]',
        text, re.UNICODE,
    )
    emoji_count = len(emojis)
    has_question = "?" in text
    has_number = bool(re.search(r'\b\d+\b', text))
    has_link = bool(re.search(r'https?://', text, re.IGNORECASE))

    text_lower = text.lower()
    has_cta = any(cta in text_lower for cta in _THREADS_CTA_WORDS)
    has_personal_pronoun = bool(re.search(r'\b(i|me|my|we|our)\b', text_lower))

    caps_words = [w for w in words if w.isupper() and len(w) > 2 and w.lstrip("#@").isalpha()]
    caps_abuse = len(caps_words) >= 3

    power_words_found = sorted({w for w in _THREADS_POWER_WORDS if re.search(rf'\b{re.escape(w)}\b', text_lower)})

    score = 40

    # Length bonus
    if 50 <= char_count <= 250:
        score += 15
    elif 251 <= char_count <= 400:
        score += 8
    elif char_count < 50 or char_count > 400:
        score -= 5

    # Hashtag: Threads discourages hashtags
    if hashtag_count == 1:
        score -= 3
    elif hashtag_count >= 2:
        score -= 5 * hashtag_count

    # Emojis
    if 1 <= emoji_count <= 2:
        score += 8
    elif 3 <= emoji_count <= 4:
        score += 4
    elif emoji_count > 4:
        score -= 4

    # Quality signals
    if has_question:
        score += 10
    if has_personal_pronoun:
        score += 6
    if has_cta:
        score += 7
    if has_number:
        score += 4
    if has_link:
        score -= 6

    # Power words (capped at 4)
    pw_bonus = min(len(power_words_found), 4) * 3
    score += pw_bonus

    # Caps abuse
    if caps_abuse:
        score -= 6

    score = max(0, min(100, score))
    grade_map = [(90, "A"), (75, "B"), (60, "C"), (45, "D")]
    grade = next((g for t, g in grade_map if score >= t), "F")

    return {
        "text": text,
        "score": score,
        "grade": grade,
        "char_count": char_count,
        "word_count": word_count,
        "hashtag_count": hashtag_count,
        "emoji_count": emoji_count,
        "has_cta": has_cta,
        "has_question": has_question,
        "has_number": has_number,
        "has_link": has_link,
        "has_personal_pronoun": has_personal_pronoun,
        "caps_abuse": caps_abuse,
        "hashtags": hashtags,
        "power_words_found": power_words_found,
        "caps_words": caps_words,
    }


@app.route("/v1/score_threads", methods=["GET", "POST"])
@app.route("/score-threads", methods=["GET", "POST"])
@app.route("/score_threads", methods=["GET", "POST"])
def endpoint_score_threads():
    """Score a Meta Threads post for engagement and reach."""
    if request.method == "GET":
        return jsonify({
            "endpoint": "score-threads",
            "method": "POST",
            "description": (
                "Score a Meta Threads post 0-100 for reach and engagement. "
                "Threads rewards conversational short-form text, personal voice, "
                "and questions. Unlike other platforms, hashtags actually penalize "
                "reach on Threads — and links are stripped by Meta. "
                "Returns score, grade, and all signal breakdowns."
            ),
            "usage": {
                "url": "https://contentforge-api-lpp9.onrender.com/score-threads",
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "body": {"text": "your Threads post draft here"},
            },
            "scoring_weights": {
                "length_50_to_250_chars": "+15",
                "question_hook": "+10",
                "personal_pronoun_I_me_my": "+6",
                "cta_agree_thoughts_reply": "+7",
                "emojis_1_or_2": "+8",
                "power_words_max_4": "+12",
                "number_in_text": "+4",
                "hashtags": "-3 to -5 each (Threads penalizes hashtags)",
                "link_in_text": "-6 (Meta removes links)",
                "caps_abuse_3plus_caps_words": "-6",
            },
            "example_curl": (
                'curl -X POST https://contentforge-api-lpp9.onrender.com/score-threads '
                '-H "Content-Type: application/json" '
                "-d '{\"text\": \"I spent 3 years building the wrong thing.\\n\\nHere's what I wish I knew on day 1:\\n\\nTalk to 10 customers before writing a single line of code.\\n\\nAgree?\"}'"
            ),
            "note": "No API key needed for direct access. Free tier on RapidAPI: 50 calls/month.",
        }), 200

    if not _verify_rapidapi_request():
        return jsonify({"error": "forbidden"}), 403
    allowed, remaining = _check_rate_limit()
    if not allowed:
        return jsonify({"error": "rate limit exceeded (30/min)"}), 429

    start = time.time()
    payload = request.get_json(silent=True) or {}
    text = (payload.get("text") or payload.get("post") or payload.get("content") or "").strip()

    if not text:
        return jsonify({
            "error": "missing 'text' parameter. Send JSON body: {\"text\": \"your Threads post\"}"
        }), 400
    if len(text) > 500:
        return jsonify({"error": "text too long (Threads max is 500 chars)"}), 400

    result = score_threads_post(text)
    _log_usage("score_threads", int((time.time() - start) * 1000))
    return _add_rate_headers(jsonify(result), remaining)


# ---------------------------------------------------------------------------
# 5g3. Facebook Post Score (heuristic — instant, no LLM)
# ---------------------------------------------------------------------------
def score_facebook_post(text: str) -> dict:
    """Score a Facebook organic post 0-100 for reach and engagement.

    Facebook-specific signals:
    - Length: 40-300 chars is conversational sweet spot (+15). 301-500 (+8). <40 or 500+ (-5).
    - Hashtags: 1-2 is reasonable on Facebook (+5). 3-5 neutral. 6+ penalizes (-5).
    - Emojis: 1-4 (+8). 5-7 (+4). 8+ (-4).
    - Question hook: drives comment engagement (+8).
    - CTA: share/comment/tag/click/join/follow (+7).
    - Personal pronouns (I/me/my/we/our): community voice (+4).
    - Power words: standard set (max +12).
    - Number/digit: +4.
    - Links: mild penalty (-3); Facebook downranks external links in organic feed.
    - ALL CAPS word abuse: -6.
    """
    _FACEBOOK_POWER_WORDS = {
        "secret", "hack", "revealed", "proven", "instant", "boost", "simple",
        "free", "discover", "strategy", "tip", "now", "fast", "quick",
        "powerful", "result", "growth", "worth", "better", "mistake",
        "change", "never", "always", "only", "real", "truth", "honest",
        "exactly", "finally", "stop", "start",
    }
    _FACEBOOK_CTA_WORDS = {
        "share", "comment", "tag", "click", "join", "follow",
        "like", "react", "save", "link in bio", "sign up",
    }

    text = (text or "").strip()
    if not text:
        return {
            "text": text, "score": 0, "grade": "F",
            "char_count": 0, "word_count": 0, "hashtag_count": 0,
            "emoji_count": 0, "has_cta": False, "has_question": False,
            "has_number": False, "has_link": False, "has_personal_pronoun": False,
            "caps_abuse": False, "hashtags": [], "power_words_found": [], "caps_words": [],
        }

    char_count = len(text)
    words = text.split()
    word_count = len(words)
    hashtags = re.findall(r'#\w+', text)
    hashtag_count = len(hashtags)
    emojis = re.findall(
        r'[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0001FA00-\U0001FA9F]',
        text, re.UNICODE,
    )
    emoji_count = len(emojis)
    has_question = "?" in text
    has_number = bool(re.search(r'\b\d+\b', text))
    has_link = bool(re.search(r'https?://', text, re.IGNORECASE))

    text_lower = text.lower()
    has_cta = any(cta in text_lower for cta in _FACEBOOK_CTA_WORDS)
    has_personal_pronoun = bool(re.search(r'\b(i|me|my|we|our)\b', text_lower))

    caps_words = [w for w in words if w.isupper() and len(w) > 2 and w.lstrip("#@").isalpha()]
    caps_abuse = len(caps_words) >= 3

    power_words_found = sorted({w for w in _FACEBOOK_POWER_WORDS if re.search(rf'\b{re.escape(w)}\b', text_lower)})

    score = 40

    # Length bonus
    if 40 <= char_count <= 300:
        score += 15
    elif 301 <= char_count <= 500:
        score += 8
    elif char_count < 40 or char_count > 500:
        score -= 5

    # Hashtags (1-2 OK on Facebook, too many hurts organic reach)
    if 1 <= hashtag_count <= 2:
        score += 5
    elif hashtag_count >= 6:
        score -= 5

    # Emojis
    if 1 <= emoji_count <= 4:
        score += 8
    elif 5 <= emoji_count <= 7:
        score += 4
    elif emoji_count > 7:
        score -= 4

    # Quality signals
    if has_question:
        score += 8
    if has_personal_pronoun:
        score += 4
    if has_cta:
        score += 7
    if has_number:
        score += 4
    if has_link:
        score -= 3  # Facebook mildly downranks external links in organic feed

    # Power words (capped at 4)
    pw_bonus = min(len(power_words_found), 4) * 3
    score += pw_bonus

    # Caps abuse
    if caps_abuse:
        score -= 6

    score = max(0, min(100, score))
    grade_map = [(90, "A"), (75, "B"), (60, "C"), (45, "D")]
    grade = next((g for t, g in grade_map if score >= t), "F")

    return {
        "text": text,
        "score": score,
        "grade": grade,
        "char_count": char_count,
        "word_count": word_count,
        "hashtag_count": hashtag_count,
        "emoji_count": emoji_count,
        "has_cta": has_cta,
        "has_question": has_question,
        "has_number": has_number,
        "has_link": has_link,
        "has_personal_pronoun": has_personal_pronoun,
        "caps_abuse": caps_abuse,
        "hashtags": hashtags,
        "power_words_found": power_words_found,
        "caps_words": caps_words,
    }


@app.route("/v1/score_facebook", methods=["GET", "POST"])
@app.route("/score-facebook", methods=["GET", "POST"])
@app.route("/score_facebook", methods=["GET", "POST"])
def endpoint_score_facebook():
    """GET → docs  |  POST /v1/score_facebook — score a Facebook post 0-100."""
    if request.method == "GET":
        return jsonify({
            "endpoint": "POST /v1/score_facebook",
            "description": "Score a Facebook organic post for reach and engagement 0-100. Instant heuristic, no AI.",
            "input": {"text": "string (required)"},
            "output": {"score": "0-100", "grade": "A-F", "char_count": "int",
                       "hashtag_count": "int", "emoji_count": "int",
                       "has_cta": "bool", "has_question": "bool",
                       "has_personal_pronoun": "bool", "has_link": "bool",
                       "power_words_found": "array", "caps_abuse": "bool"},
            "example": {"text": "We just hit 10,000 customers \ud83c\udf89 — and it's all because of you. What's one thing you'd like us to build next? Drop a comment below!"},
        })
    if not _verify_rapidapi_request():
        return jsonify({"error": "forbidden"}), 403
    allowed, remaining = _check_rate_limit()
    if not allowed:
        return jsonify({"error": "rate limit exceeded (30/min)"}), 429
    start = time.time()
    payload = request.get_json(silent=True) or {}
    text = (payload.get("text") or payload.get("post") or payload.get("content") or "").strip()
    if not text:
        return jsonify({"error": "missing 'text' parameter. Send JSON body: {\"text\": \"your Facebook post\"}"}), 400
    if len(text) > 5000:
        return jsonify({"error": "text too long (max 5000 chars)"}), 400
    result = score_facebook_post(text)
    _log_usage("score_facebook", int((time.time() - start) * 1000))
    return _add_rate_headers(jsonify(result), remaining)


# ---------------------------------------------------------------------------
# 5h. TikTok Caption Score (heuristic — instant, no LLM)
# ---------------------------------------------------------------------------
def score_tiktok_caption(text: str) -> dict:
    """Score a TikTok caption 0-100 for reach and engagement.

    TikTok-specific signals:
    - Caption length: 1-150 chars is sweet spot (captions are secondary; hook is in the video)
    - Hashtags: 3-6 is optimal (more selective than Instagram)
    - Hook (first 100 chars): starts with question, number, or power word
    - Emojis: 1-3 ideal (less is more on TikTok vs Instagram)
    - CTA: 'follow', 'save', 'share', 'comment', 'duet', 'stitch'
    - Trending sounds mention: not scoreable but context tip
    - Power words tuned for TikTok discovery
    """
    import re as _re

    text = (text or "").strip()
    if not text:
        return {
            "text": "",
            "platform": "tiktok",
            "score": 0,
            "grade": "F",
            "char_count": 0,
            "word_count": 0,
            "hashtag_count": 0,
            "hashtags": [],
            "emoji_count": 0,
            "has_question": False,
            "has_cta": False,
            "hook_length": 0,
            "power_words_found": [],
            "suggestions": ["No caption provided."],
        }

    TIKTOK_POWER_WORDS = [
        "viral", "hack", "secret", "transform", "instant", "proven", "simple",
        "easy", "fast", "quick", "real", "honest", "truth", "warning",
        "pov", "trend", "trending", "watch", "boost", "free", "discover",
        "reveal", "exposed", "stop", "mistake", "results", "works", "change",
        "this", "why", "how", "do", "try", "omg", "wait", "wild",
    ]

    TIKTOK_CTA_WORDS = [
        "follow", "save", "share", "comment", "duet", "stitch",
        "like", "subscribe", "link in bio", "link bio", "click", "tap",
    ]

    char_count = len(text)
    words = _re.findall(r"[a-zA-Z']+", text)
    word_count = len(words)

    # hashtags
    hashtags = _re.findall(r"#\w+", text.lower())
    hashtag_count = len(hashtags)

    # emojis
    emoji_count = sum(1 for ch in text
                      if ord(ch) > 127000 or (0x1F300 <= ord(ch) <= 0x1FAFF)
                      or (0x2600 <= ord(ch) <= 0x27BF))

    # hook = first 100 characters
    hook = text[:100]
    hook_length = len(hook.strip())
    has_question = "?" in hook

    # power words
    lower_words = [w.lower() for w in words]
    power_words_found = list({w for w in lower_words if w in TIKTOK_POWER_WORDS})

    # CTA
    text_lower = text.lower()
    has_cta = any(cta in text_lower for cta in TIKTOK_CTA_WORDS)

    # CAPS abuse (whole words)
    caps_words = [w for w in words if w.isupper() and len(w) > 1]

    # numbers in caption
    has_number = bool(_re.search(r'\d', text))

    # --- Score ---
    score = 40  # base

    # Length: TikTok captions are secondary; 50-150 is sweet spot
    if 50 <= char_count <= 150:
        score += 18
    elif 20 <= char_count <= 200:
        score += 12
    elif char_count <= 300:
        score += 5
    elif char_count > 500:
        score -= 5  # too long, harder to read

    # Hashtags: 3-6 optimal (TikTok prefers focused tags)
    if 3 <= hashtag_count <= 6:
        score += 12
    elif hashtag_count == 2:
        score += 7
    elif hashtag_count == 1 or hashtag_count == 7:
        score += 4
    elif hashtag_count > 10:
        score -= 6  # over-tagging penalty on TikTok

    # Emojis: 1-3 ideal
    if 1 <= emoji_count <= 3:
        score += 8
    elif 4 <= emoji_count <= 5:
        score += 3
    elif emoji_count > 6:
        score -= 3

    # CTA
    if has_cta:
        score += 8

    # Question hook
    if has_question:
        score += 5

    # Power words (max +12)
    pw_bonus = min(len(power_words_found) * 4, 12)
    score += pw_bonus

    # Number in caption
    if has_number:
        score += 4

    # Hook starts strong (> 10 chars, signals caption isn't just hashtags)
    if hook_length >= 20:
        score += 5

    # Caps abuse penalty
    if len(caps_words) >= 3:
        score -= 6
    elif len(caps_words) >= 2:
        score -= 2

    score = max(0, min(100, score))

    # Grade
    if score >= 80:
        grade = "A"
    elif score >= 65:
        grade = "B"
    elif score >= 50:
        grade = "C"
    elif score >= 35:
        grade = "D"
    else:
        grade = "F"

    # Suggestions
    suggestions = []
    if char_count < 20:
        suggestions.append("Caption is very short. Add context or a hook to entice viewers to engage.")
    elif char_count > 300:
        suggestions.append("Caption is long. TikTok users typically engage with captions under 150 characters.")
    if hashtag_count < 3:
        suggestions.append(f"Only {hashtag_count} hashtag(s). TikTok discovery works best with 3-6 focused hashtags.")
    elif hashtag_count > 8:
        suggestions.append(f"{hashtag_count} hashtags is too many. Stick to 3-6 niche-specific tags for better distribution.")
    if emoji_count == 0:
        suggestions.append("Add 1-3 emojis to make the caption more eye-catching in the feed.")
    elif emoji_count > 5:
        suggestions.append(f"{emoji_count} emojis may look spammy. 1-3 is usually optimal on TikTok.")
    if not has_cta:
        suggestions.append("Add a CTA like 'save this', 'follow for more', or 'duet this' to drive interaction.")
    if not has_question and not has_number:
        suggestions.append("Start with a question or a number to hook viewers into reading the caption.")
    if not power_words_found:
        suggestions.append("Include power words like 'viral', 'hack', 'secret', or 'POV' to boost discovery.")
    if not suggestions:
        suggestions.append("Well-optimized TikTok caption! Strong hashtag mix, hook, and CTA detected.")

    return {
        "text": text[:500] + ("..." if len(text) > 500 else ""),
        "platform": "tiktok",
        "score": score,
        "grade": grade,
        "char_count": char_count,
        "word_count": word_count,
        "hashtag_count": hashtag_count,
        "hashtags": hashtags[:20],
        "emoji_count": emoji_count,
        "has_question": has_question,
        "has_cta": has_cta,
        "has_number": has_number,
        "hook_length": hook_length,
        "power_words_found": power_words_found,
        "caps_words": caps_words[:10],
        "suggestions": suggestions,
    }


@app.route("/v1/score_tiktok", methods=["GET", "POST"])
@app.route("/score-tiktok", methods=["GET", "POST"])
@app.route("/score_tiktok", methods=["GET", "POST"])
def endpoint_score_tiktok():
    if not _verify_rapidapi_request():
        return jsonify({"error": "forbidden"}), 403

    # --- GET: usage docs ---
    if request.method == "GET":
        return jsonify({
            "endpoint": "/v1/score_tiktok",
            "method": "POST",
            "description": (
                "Score a TikTok caption 0-100 for reach and engagement. "
                "Checks caption length (50-150 ideal), hashtag count (3-6 optimal), "
                "emojis (1-3 ideal), question hooks, CTA detection, and TikTok-specific power words. "
                "Instant, no AI needed."
            ),
            "parameters": {
                "caption": "(required) the TikTok caption to score",
            },
            "aliases": ["text", "post", "content"],
            "example_body": {
                "caption": "POV: you stop guessing and start scoring your content 🎯 Try this free #contenttips #tiktokmarketing #growthhack"
            },
            "try_it": "POST this endpoint with a JSON body to score your TikTok caption.",
        })

    allowed, remaining = _check_rate_limit()
    if not allowed:
        return jsonify({"error": "rate limit exceeded"}), 429

    start = time.time()
    data = request.get_json(silent=True) or {}
    caption = (
        data.get("caption") or data.get("text") or
        data.get("post") or data.get("content") or ""
    ).strip()

    if not caption:
        return jsonify({
            "error": (
                "missing 'caption' parameter. "
                'Send JSON body: {"caption": "your TikTok caption"}'
            )
        }), 400
    if len(caption) > 2200:
        return jsonify({"error": "caption too long (TikTok max is 2200 chars)"}), 400

    result = score_tiktok_caption(caption)
    _log_usage("score_tiktok", int((time.time() - start) * 1000))
    return _add_rate_headers(jsonify(result), remaining)


# ---------------------------------------------------------------------------
# 5i. Hashtag Analyzer (heuristic — instant, no LLM)
# ---------------------------------------------------------------------------
def analyze_hashtags(hashtags_input: str, platform: str = "twitter") -> dict:
    """Analyze a set of hashtags for quality, diversity, and platform fit.

    Checks: count vs platform ideal, individual tag length, ALL CAPS tags,
    banned/spam-risk patterns, duplicate detection, specificity variety
    (mega/large/niche/micro), and mixed_case usage.
    """
    import re as _re

    platform = (platform or "twitter").lower().strip()
    hashtags_input = (hashtags_input or "").strip()

    if not hashtags_input:
        return {
            "platform": platform,
            "input": "",
            "score": 0,
            "grade": "F",
            "hashtag_count": 0,
            "hashtags": [],
            "platform_ideal_range": "1-5",
            "duplicates": [],
            "spam_risk_tags": [],
            "caps_tags": [],
            "long_tags": [],
            "camel_case_tags": [],
            "specificity": {"broad": 0, "niche": 0, "micro": 0},
            "suggestions": ["No hashtags provided."],
        }

    # Extract hashtags — allow input as "tag1 tag2 #tag3" or "#tag1 #tag2"
    raw = _re.findall(r"#?(\w+)", hashtags_input)
    tags = [t.lower() for t in raw if len(t) >= 2]
    tags_original = [t for t in _re.findall(r"#?(\w+)", hashtags_input) if len(t) >= 2]
    unique_tags = list(dict.fromkeys(tags))  # deduplicated, order preserved
    duplicates = [t for t in tags if tags.count(t) > 1]
    duplicates = list(set(duplicates))
    hashtag_count = len(unique_tags)

    # Platform-specific ideal counts
    _PLATFORM_IDEAL = {
        "twitter": (1, 3),
        "tweet": (1, 3),
        "instagram": (5, 15),
        "tiktok": (3, 6),
        "linkedin": (3, 5),
        "youtube": (3, 8),
        "facebook": (1, 3),
    }
    lo, hi = _PLATFORM_IDEAL.get(platform, (1, 5))

    # Tag length analysis (chars)
    short_tags = [t for t in unique_tags if len(t) <= 3]
    long_tags = [t for t in unique_tags if len(t) > 25]
    caps_tags = [t for t in tags_original if t.isupper() and len(t) > 2]

    # Spam/banned pattern detection
    _SPAM_PATTERNS = [
        "followme", "follow4follow", "f4f", "likeforlike", "l4l",
        "followback", "spammerfollow", "spam", "bot", "fake",
        "tagforlikes", "likeall", "followall",
    ]
    spam_tags = [t for t in unique_tags if t in _SPAM_PATTERNS]

    # Rough specificity tier (by tag length as proxy — longer tags tend to be more niche)
    mega_tags = [t for t in unique_tags if len(t) <= 6]       # e.g. #love, #food
    niche_tags = [t for t in unique_tags if 12 <= len(t) <= 22]  # e.g. #webdevelopment
    micro_tags = [t for t in unique_tags if len(t) > 22]         # very specific

    # Mixed case presence (camelCase is good UX — screen readers)
    camel_tags = [t for t in tags_original if any(c.isupper() for c in t[1:])]

    # --- Score ---
    score = 40

    # Count relative to ideal for platform
    if lo <= hashtag_count <= hi:
        score += 25
    elif hashtag_count == lo - 1 or hashtag_count == hi + 1:
        score += 15
    elif hashtag_count < lo:
        score += 5
    elif hashtag_count <= hi + 5:
        score += 8
    else:
        score -= 5  # way too many

    # Duplicate penalty
    if duplicates:
        score -= len(duplicates) * 5

    # Spam tags penalty
    score -= len(spam_tags) * 8

    # Long tag penalty (over 25 chars is likely typo/noise)
    score -= len(long_tags) * 3

    # Short tag penalty (≤3 chars, usually too broad e.g. #ai, #go, #js)
    if len(short_tags) > 2:
        score -= (len(short_tags) - 2) * 3

    # Specificity variety bonus: mix of broad + niche = good
    has_variety = (len(mega_tags) >= 1 and len(niche_tags) >= 1)
    if has_variety:
        score += 10

    # Mixed case (accessibility) bonus
    if camel_tags:
        score += 5

    # Caps abuse penalty
    if len(caps_tags) > 1:
        score -= len(caps_tags) * 3

    score = max(0, min(100, score))

    # Grade
    if score >= 80:
        grade = "A"
    elif score >= 65:
        grade = "B"
    elif score >= 50:
        grade = "C"
    elif score >= 35:
        grade = "D"
    else:
        grade = "F"

    # Suggestions
    suggestions = []
    if hashtag_count < lo:
        suggestions.append(f"Only {hashtag_count} hashtag(s). For {platform}, aim for {lo}-{hi} hashtags.")
    elif hashtag_count > hi + 3:
        suggestions.append(f"{hashtag_count} hashtags is too many for {platform}. Trim to {lo}-{hi} for best reach.")
    if duplicates:
        suggestions.append(f"Duplicate hashtags found: {', '.join('#' + t for t in duplicates)}. Remove duplicates.")
    if spam_tags:
        suggestions.append(f"Spam-risk tags detected: {', '.join('#' + t for t in spam_tags)}. Remove these for better reach.")
    if long_tags:
        suggestions.append(f"Very long tag(s): {', '.join('#' + t for t in long_tags)}. Keep hashtags under 25 characters.")
    if len(short_tags) > 2:
        suggestions.append(f"Many very short tags ({', '.join('#' + t for t in short_tags)}). Mix in more specific niche tags.")
    if not has_variety:
        suggestions.append("Mix broad/trending tags with niche-specific ones for better discovery at multiple levels.")
    if not camel_tags and hashtag_count > 1:
        suggestions.append("Consider CamelCase hashtags (e.g., #BuildInPublic) for better accessibility and readability.")
    if len(caps_tags) > 1:
        suggestions.append(f"ALL CAPS hashtags look aggressive: {', '.join('#' + t for t in caps_tags)}. Use CamelCase instead.")
    if not suggestions:
        suggestions.append(f"Well-balanced hashtag set for {platform}. Good mix and appropriate count.")

    return {
        "platform": platform,
        "input": hashtags_input[:500],
        "score": score,
        "grade": grade,
        "hashtag_count": hashtag_count,
        "hashtags": [f"#{t}" for t in unique_tags],
        "platform_ideal_range": f"{lo}-{hi}",
        "duplicates": [f"#{t}" for t in duplicates],
        "spam_risk_tags": [f"#{t}" for t in spam_tags],
        "caps_tags": [f"#{t}" for t in caps_tags],
        "long_tags": [f"#{t}" for t in long_tags],
        "camel_case_tags": [f"#{t}" for t in camel_tags],
        "specificity": {
            "broad": len(mega_tags),
            "niche": len(niche_tags),
            "micro": len(micro_tags),
        },
        "suggestions": suggestions,
    }


@app.route("/v1/analyze_hashtags", methods=["GET", "POST"])
@app.route("/analyze-hashtags", methods=["GET", "POST"])
@app.route("/analyze_hashtags", methods=["GET", "POST"])
def endpoint_analyze_hashtags():
    if not _verify_rapidapi_request():
        return jsonify({"error": "forbidden"}), 403

    # --- GET: usage docs ---
    if request.method == "GET":
        return jsonify({
            "endpoint": "/v1/analyze_hashtags",
            "method": "POST",
            "description": (
                "Analyze a set of hashtags for quality, diversity, and platform fit. "
                "Checks count vs platform ideal, duplicates, spam-risk tags, tag length, "
                "specificity variety (broad/niche/micro), and CamelCase accessibility. "
                "Instant, no AI needed."
            ),
            "parameters": {
                "hashtags": "(required) space or comma-separated hashtags (with or without #)",
                "platform": "(optional) twitter/instagram/tiktok/linkedin/youtube. Default: twitter",
            },
            "example_body": {
                "hashtags": "#buildinpublic #indiehackers #saas #contentmarketing",
                "platform": "twitter"
            },
            "try_it": "POST this endpoint with a JSON body to analyze your hashtags.",
        })

    allowed, remaining = _check_rate_limit()
    if not allowed:
        return jsonify({"error": "rate limit exceeded"}), 429

    start = time.time()
    data = request.get_json(silent=True) or {}
    hashtags = (
        data.get("hashtags") or data.get("tags") or data.get("text") or ""
    ).strip()
    platform = (data.get("platform") or "twitter").strip().lower()

    if not hashtags:
        return jsonify({
            "error": (
                "missing 'hashtags' parameter. "
                'Send JSON body: {"hashtags": "#tag1 #tag2 #tag3", "platform": "twitter"}'
            )
        }), 400
    if len(hashtags) > 1000:
        return jsonify({"error": "hashtags input too long (max 1000 chars)"}), 400

    result = analyze_hashtags(hashtags, platform)
    _log_usage("analyze_hashtags", int((time.time() - start) * 1000))
    return _add_rate_headers(jsonify(result), remaining)


# ---------------------------------------------------------------------------
# 5j. Pinterest Pin Description Scorer (heuristic — instant, no LLM)
# ---------------------------------------------------------------------------
def score_pinterest_pin(text: str) -> dict:
    """Score a Pinterest pin description 0-100 for reach and saves.

    Pinterest-specific signals (2024-2026):
    - Length: 150-500 chars is the sweet spot (more keyword surface area).
      Under 50 = weak SEO; over 500 chars OK but diminishing returns.
    - Pinterest is a search engine — keyword phrases drive discovery.
    - Hashtags: 2-5 at the end. More than 20 triggers spam flags.
    - No promotional language ('buy now', 'click here') — Pinterest
      deprioritises posts with hard-sell phrases.
    - Story/first-person format earns more saves.
    - CTA: 'save', 'pin', 'try', 'read', 'visit', 'find out', 'get the recipe'
    - Emojis: 0-3 is fine (Pinterest is less emoji-driven than Instagram).
    - Links: neutral — Pinterest is inherently link-driven.
    - ALL CAPS word abuse signals spam.
    """
    text = (text or "").strip()
    if not text:
        return {
            "text": text, "platform": "pinterest", "score": 0, "grade": "F",
            "char_count": 0, "word_count": 0, "hashtag_count": 0,
            "emoji_count": 0, "has_cta": False, "has_personal_pronoun": False,
            "has_number": False, "has_link": False,
            "spam_language_found": [], "power_words_found": [],
            "caps_abuse": False, "hashtags": [], "suggestions": [],
        }

    char_count = len(text)
    words = text.split()
    word_count = len(words)
    hashtags = re.findall(r'#\w+', text)
    hashtag_count = len(hashtags)
    emoji_count = sum(1 for c in text if ord(c) > 0x1F300)
    has_number = bool(re.search(r'\d', text))
    has_link = bool(re.search(r'https?://', text, re.IGNORECASE))

    text_lower = text.lower()
    has_personal_pronoun = bool(re.search(r'\b(i|me|my|we|our)\b', text_lower))

    _SPAM_PHRASES = {
        "buy now", "click here", "order now", "act now", "limited time",
        "free gift", "discount code", "promo code", "coupon", "sale ends",
        "don't miss out", "spam", "ad:", "sponsored", "affiliate",
    }
    spam_found = [p for p in _SPAM_PHRASES if p in text_lower]

    _CTA_PHRASES = {
        "save", "pin", "try", "read", "visit", "find out", "get the recipe",
        "learn how", "see how", "discover", "click to", "tap to",
        "download", "grab", "sign up", "follow for",
    }
    has_cta = any(p in text_lower for p in _CTA_PHRASES)

    _POWER_WORDS = {
        "easy", "simple", "quick", "best", "ultimate", "guide", "tutorial",
        "hack", "tip", "secret", "proven", "natural", "diy", "how to",
        "recipe", "idea", "inspiration", "beautiful", "stunning", "perfect",
        "essential", "must", "love", "amazing", "free", "fast", "step by step",
        "beginner", "complete", "creative",
    }
    power_words_found = sorted({w for w in _POWER_WORDS if w in text_lower})

    caps_words = [w for w in words if w.isupper() and len(w) > 2 and w.lstrip("#@").isalpha()]
    caps_abuse = len(caps_words) >= 3

    # --- Score ---
    score = 40

    # Length
    if char_count < 30:
        score -= 10
    elif 30 <= char_count < 100:
        score += 5
    elif 100 <= char_count < 150:
        score += 10
    elif 150 <= char_count <= 500:
        score += 18  # sweet spot
    elif 500 < char_count <= 800:
        score += 12
    else:
        score += 6  # long but not penalised — more keyword surface

    # Hashtags (2-5 optimal)
    if hashtag_count == 0:
        pass  # neutral — Pinterest doesn't require them
    elif 2 <= hashtag_count <= 5:
        score += 10
    elif hashtag_count == 1:
        score += 5
    elif 6 <= hashtag_count <= 10:
        score += 4
    elif 11 <= hashtag_count <= 20:
        score += 0  # no benefit
    else:
        score -= 8  # spam risk

    # Promotional spam
    score -= min(20, len(spam_found) * 7)

    # Personal story
    if has_personal_pronoun:
        score += 6

    # CTA
    if has_cta:
        score += 7

    # Number (specificity)
    if has_number:
        score += 4

    # Power words (max +12)
    score += min(12, len(power_words_found) * 3)

    # Emojis: mild boost for 1-3
    if 1 <= emoji_count <= 3:
        score += 4
    elif emoji_count > 6:
        score -= 3

    # ALL CAPS abuse
    if caps_abuse:
        score -= 6

    score = max(0, min(100, score))
    grade_map = [(90, "A"), (75, "B"), (60, "C"), (45, "D")]
    grade = next((g for t, g in grade_map if score >= t), "F")

    # Suggestions
    suggestions = []
    if char_count < 100:
        suggestions.append(
            "Description is very short. Add 150-500 characters with relevant "
            "keyword phrases — Pinterest is a search engine."
        )
    if hashtag_count == 0:
        suggestions.append(
            "Add 2-5 relevant hashtags at the end of the description to improve "
            "topic discovery on Pinterest."
        )
    elif hashtag_count > 10:
        suggestions.append(
            f"{hashtag_count} hashtags is too many. Stick to 2-5 targeted tags."
        )
    if spam_found:
        suggestions.append(
            f"Promotional language detected: {', '.join(spam_found)}. Pinterest "
            "deprioritises hard-sell posts — describe the value instead."
        )
    if not has_personal_pronoun:
        suggestions.append(
            "Add a personal story angle ('I tried...', 'We love...'). "
            "First-person posts earn more saves on Pinterest."
        )
    if not has_cta:
        suggestions.append(
            "Add a soft CTA like 'Save this for later', 'Try this recipe', "
            "or 'Visit the link for the full tutorial'."
        )
    if not power_words_found:
        suggestions.append(
            "Add a power word (e.g. 'easy', 'ultimate', 'how to', 'beginner') "
            "to improve keyword relevance and click appeal."
        )
    if caps_abuse:
        suggestions.append(
            "Avoid ALL CAPS words — they signal spam on Pinterest."
        )
    if not suggestions:
        suggestions.append("Well-optimised Pinterest description. Strong keywords, CTA, and story format detected.")

    return {
        "text": text[:500] + ("..." if char_count > 500 else ""),
        "platform": "pinterest",
        "score": score,
        "grade": grade,
        "char_count": char_count,
        "word_count": word_count,
        "hashtag_count": hashtag_count,
        "hashtags": hashtags,
        "emoji_count": emoji_count,
        "has_cta": has_cta,
        "has_personal_pronoun": has_personal_pronoun,
        "has_number": has_number,
        "has_link": has_link,
        "spam_language_found": spam_found,
        "power_words_found": power_words_found,
        "caps_abuse": caps_abuse,
        "suggestions": suggestions,
    }


@app.route("/v1/score_pinterest", methods=["GET", "POST"])
@app.route("/score-pinterest", methods=["GET", "POST"])
@app.route("/score_pinterest", methods=["GET", "POST"])
def endpoint_score_pinterest():
    """Score a Pinterest pin description for reach, saves, and SEO."""
    if request.method == "GET":
        return jsonify({
            "endpoint": "score-pinterest",
            "method": "POST",
            "description": (
                "Score a Pinterest pin description 0-100 for reach and saves. "
                "Pinterest functions as a search engine — keyword density, "
                "description length (150-500 chars), CTA, and avoiding "
                "promotional language are the key signals. Instant, no AI."
            ),
            "usage": {
                "url": "https://contentforge-api-lpp9.onrender.com/score-pinterest",
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "body": {"text": "your Pinterest pin description here"},
            },
            "scoring_factors": [
                "Description length (sweet spot: 150-500 chars)",
                "Hashtag count (2-5 optimal at end)",
                "Spam/promotional language penalty (buy now, click here, etc.)",
                "Personal story angle (I/we boosts saves)",
                "CTA presence (save, try, read, visit)",
                "Power words (easy, ultimate, how to, beginner, etc.)",
                "Emoji usage (0-3 is fine, 7+ is risky)",
                "ALL CAPS abuse penalty",
            ],
            "example_curl": (
                'curl -X POST https://contentforge-api-lpp9.onrender.com/score-pinterest '
                '-H "Content-Type: application/json" '
                "-d '{\"text\": \"I tried batch-cooking every Sunday for 30 days and it completely changed my week. "
                "Here are the 5 easiest make-ahead meals for busy families. Save this for your next meal prep day! "
                "#mealprep #healthyeating #busyfamilies #dinnerideas\"}'"
            ),
            "note": "No API key needed for direct access. Free tier on RapidAPI: 50 calls/month.",
        }), 200

    if not _verify_rapidapi_request():
        return jsonify({"error": "forbidden"}), 403
    allowed, remaining = _check_rate_limit()
    if not allowed:
        return jsonify({"error": "rate limit exceeded (30/min)"}), 429

    start = time.time()
    payload = request.get_json(silent=True) or {}
    text = (
        payload.get("text") or payload.get("description")
        or payload.get("pin") or payload.get("content") or ""
    ).strip()

    if not text:
        return jsonify({
            "error": "missing 'text' parameter. Send JSON body: {\"text\": \"your pin description\"}"
        }), 400
    if len(text) > 5000:
        return jsonify({"error": "text too long (max 5000 chars)"}), 400

    result = score_pinterest_pin(text)
    _log_usage("score_pinterest", int((time.time() - start) * 1000))
    return _add_rate_headers(jsonify(result), remaining)


# ---------------------------------------------------------------------------
# 5k. YouTube Video Description Scorer (heuristic — instant, no LLM)
# ---------------------------------------------------------------------------
def score_youtube_description(text: str) -> dict:
    """Score a YouTube video description 0-100 for SEO and viewer value.

    YouTube description signals:
    - Length: 200-1000 chars is optimal (provides keyword surface without bloat).
      Under 100 = SEO opportunity missed. Over 2000 = fine but may dilute.
    - First 125 chars are the search-snippet hook (visible before 'Show more').
      Should contain the primary keyword and a compelling line.
    - Timestamps/chapters ([00:00] format) improve watch-time and search rankings.
    - CTA near the top: subscribe, like, comment, or link-to-resource.
    - 3-5 hashtags at the end boost topic discovery (YouTube shows them above title).
    - Link section: channel links, social, merch — presence signals professionalism.
    - Keyword repetition: target keyword appearing 2-3x naturally is a positive signal.
    """
    text = (text or "").strip()
    if not text:
        return {
            "text": text, "platform": "youtube_description", "score": 0, "grade": "F",
            "char_count": 0, "word_count": 0, "hashtag_count": 0, "emoji_count": 0,
            "has_timestamps": False, "has_cta": False, "has_links": False,
            "hook_length": 0, "hook_preview": "", "keyword_density_hint": False,
            "power_words_found": [], "suggestions": [],
        }

    char_count = len(text)
    words = text.split()
    word_count = len(words)
    hashtags = re.findall(r'#\w+', text)
    hashtag_count = len(hashtags)
    emoji_count = sum(1 for c in text if ord(c) > 0x1F300)

    # First 125 chars (search snippet)
    first_line = text.split('\n')[0].strip()
    hook = first_line[:125]
    hook_length = len(first_line)

    # Timestamps detection (e.g. 0:00 or 00:00 or 1:23:45)
    has_timestamps = bool(re.search(r'\b\d{1,2}:\d{2}(?::\d{2})?\b', text))

    # Links
    has_links = bool(re.search(r'https?://', text, re.IGNORECASE))

    # CTA
    text_lower = text.lower()
    _CTA_PHRASES = {
        "subscribe", "hit the bell", "ring the bell", "like this video",
        "leave a comment", "comment below", "join", "follow", "patreon",
        "link in description", "check out", "visit", "download",
    }
    has_cta = any(p in text_lower for p in _CTA_PHRASES)

    # Keyword density hint: any word appearing 3+ times (excluding stopwords)
    _STOPWORDS = {"the", "a", "an", "is", "to", "for", "and", "of", "in", "on",
                  "at", "by", "as", "be", "or", "my", "me", "we", "i", "this",
                  "that", "it", "with", "your", "you", "from", "how", "what",
                  "why", "who", "all", "not", "but", "so", "if", "its", "our"}
    clean_words = [re.sub(r'[^a-z]', '', w.lower()) for w in words if len(w) > 3]
    clean_words = [w for w in clean_words if w not in _STOPWORDS]
    word_freq = {}
    for w in clean_words:
        word_freq[w] = word_freq.get(w, 0) + 1
    keyword_density_hint = any(v >= 3 for v in word_freq.values())

    _POWER_WORDS = {
        "best", "ultimate", "complete", "guide", "tutorial", "how to", "review",
        "honest", "top", "new", "updated", "secret", "proven", "step by step",
        "beginners", "advanced", "free", "easy", "fast", "results", "tips",
    }
    power_words_found = sorted({w for w in _POWER_WORDS if w in text_lower})

    # --- Score ---
    score = 40

    # Length
    if char_count < 50:
        score -= 10
    elif 50 <= char_count < 100:
        score += 3
    elif 100 <= char_count < 200:
        score += 8
    elif 200 <= char_count <= 1000:
        score += 18  # sweet spot
    elif 1000 < char_count <= 2000:
        score += 12
    else:
        score += 6

    # Hook (first 125 chars)
    if hook_length <= 125:
        score += 5  # full hook visible in search snippet
    if hook and hook[0:1].isdigit():
        score += 3  # number hook

    # Timestamps/chapters
    if has_timestamps:
        score += 12  # strong SEO + UX signal

    # CTA
    if has_cta:
        score += 7

    # Links
    if has_links:
        score += 5  # links = professional, expected in YT descriptions

    # Hashtags (3-5 at end is ideal)
    if 3 <= hashtag_count <= 5:
        score += 8
    elif 1 <= hashtag_count <= 7:
        score += 4
    elif hashtag_count > 15:
        score -= 5

    # Keyword density signal
    if keyword_density_hint:
        score += 5

    # Power words
    score += min(10, len(power_words_found) * 3)

    # Emoji (tasteful use in YT descriptions is fine, excessive is not)
    if 1 <= emoji_count <= 5:
        score += 3
    elif emoji_count > 10:
        score -= 3

    score = max(0, min(100, score))
    grade_map = [(90, "A"), (75, "B"), (60, "C"), (45, "D")]
    grade = next((g for t, g in grade_map if score >= t), "F")

    # Suggestions
    suggestions = []
    if char_count < 100:
        suggestions.append(
            "Description is very short. Aim for 200-1000 characters with "
            "relevant keywords and a CTA."
        )
    if hook_length > 125:
        suggestions.append(
            "The first line is longer than 125 characters — only the first "
            "~125 chars show in YouTube search results. Put your hook there."
        )
    if not has_timestamps:
        suggestions.append(
            "Add timestamps/chapters (e.g. '0:00 Intro'). They improve watch "
            "time, help viewers navigate, and boost search rankings."
        )
    if not has_cta:
        suggestions.append(
            "Add a CTA near the top: 'Subscribe for more', 'Leave a comment', "
            "or a link to a related resource."
        )
    if hashtag_count == 0:
        suggestions.append(
            "Add 3-5 relevant hashtags at the very end of the description. "
            "YouTube displays them above the title in the feed."
        )
    elif hashtag_count > 10:
        suggestions.append(
            f"{hashtag_count} hashtags is too many. Stick to 3-5 focused tags."
        )
    if not has_links:
        suggestions.append(
            "Add relevant links (channel, social, resources) in the description. "
            "Viewers and YouTube's algorithm expect them."
        )
    if not keyword_density_hint:
        suggestions.append(
            "Repeat your main keyword 2-3 times naturally. "
            "YouTube uses description text as an SEO signal."
        )
    if not suggestions:
        suggestions.append(
            "Well-optimised YouTube description! Timestamps, CTA, links, "
            "and keywords all detected."
        )

    return {
        "text": text[:500] + ("..." if char_count > 500 else ""),
        "platform": "youtube_description",
        "score": score,
        "grade": grade,
        "char_count": char_count,
        "word_count": word_count,
        "hashtag_count": hashtag_count,
        "hashtags": hashtags[:10],
        "emoji_count": emoji_count,
        "hook_length": hook_length,
        "hook_preview": hook + ("..." if hook_length > 125 else ""),
        "has_timestamps": has_timestamps,
        "has_cta": has_cta,
        "has_links": has_links,
        "keyword_density_hint": keyword_density_hint,
        "power_words_found": power_words_found,
        "suggestions": suggestions,
    }


@app.route("/v1/score_youtube_description", methods=["GET", "POST"])
@app.route("/score-youtube-description", methods=["GET", "POST"])
@app.route("/score_youtube_description", methods=["GET", "POST"])
def endpoint_score_youtube_description():
    """Score a YouTube video description for SEO and viewer value."""
    if request.method == "GET":
        return jsonify({
            "endpoint": "score-youtube-description",
            "method": "POST",
            "description": (
                "Score a YouTube video description 0-100 for SEO and viewer value. "
                "Checks description length (200-1000 ideal), first-125-char search "
                "hook, timestamps/chapters, CTA, links, hashtag count, and keyword "
                "density. Instant, no AI."
            ),
            "usage": {
                "url": "https://contentforge-api-lpp9.onrender.com/score-youtube-description",
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "body": {"text": "your YouTube description here"},
            },
            "scoring_factors": [
                "Description length (sweet spot: 200-1000 chars)",
                "First 125 chars visible in search snippet (hook strength)",
                "Timestamps/chapters (major watch-time + SEO signal)",
                "CTA near the top",
                "Links (social, resources, channel)",
                "Hashtags at end (3-5 optimal)",
                "Keyword density (2-3x repetition is positive)",
                "Power words",
            ],
            "example_curl": (
                'curl -X POST https://contentforge-api-lpp9.onrender.com/score-youtube-description '
                '-H "Content-Type: application/json" '
                '-d \'{"text": "Learn the 5 passive income strategies I used to hit $5K/mo in 2026. '
                'Subscribe for weekly income reports!\\n\\n0:00 Intro\\n1:30 Strategy 1\\n5:00 Strategy 2\\n\\n'
                'Free download: https://example.com\\n\\n#passiveincome #sidehustle #money"}\''
            ),
            "note": "No API key needed for direct access. Free tier on RapidAPI: 50 calls/month.",
        }), 200

    if not _verify_rapidapi_request():
        return jsonify({"error": "forbidden"}), 403
    allowed, remaining = _check_rate_limit()
    if not allowed:
        return jsonify({"error": "rate limit exceeded (30/min)"}), 429

    start = time.time()
    payload = request.get_json(silent=True) or {}
    text = (
        payload.get("text") or payload.get("description") or payload.get("content") or ""
    ).strip()

    if not text:
        return jsonify({
            "error": "missing 'text' parameter. Send JSON body: {\"text\": \"your YouTube description\"}"
        }), 400
    if len(text) > 10000:
        return jsonify({"error": "text too long (max 10000 chars — YouTube description limit)"}), 400

    result = score_youtube_description(text)
    _log_usage("score_youtube_description", int((time.time() - start) * 1000))
    return _add_rate_headers(jsonify(result), remaining)


# ---------------------------------------------------------------------------
# 5l. Ad Copy Scorer (heuristic — instant, no LLM)
# ---------------------------------------------------------------------------
def score_ad_copy(headline: str, description: str = "", platform: str = "google") -> dict:
    """Score ad copy 0-100 for Google Ads or Meta (Facebook/Instagram) Ads.

    Ad copy rules:
    Google Ads:
      - Headline: ideal ≤30 chars (hard limit). Score penalises over 30.
      - Description: ideal ≤90 chars.
    Meta Ads (facebook/instagram):
      - Headline: ≤27 chars ideal.
      - Primary text: 125 chars visible before 'See more'; ≤90 chars ideal.

    Quality signals:
    - CTA: 'buy', 'get', 'start', 'try', 'sign up', 'learn more', etc.
    - Benefit-first framing (what the customer gains)
    - Number/stat presence ('save 50%', '$0 setup', '3-minute')
    - You-language ('you', 'your') for second-person connection
    - Urgency/scarcity ('limited', 'today only', 'expires')
    - Power words
    - Headline + description are scored independently and combined.
    """
    _PLATFORM_LIMITS = {
        "google": {"headline": 30, "description": 90},
        "meta": {"headline": 27, "description": 125},
        "facebook": {"headline": 27, "description": 125},
        "instagram": {"headline": 27, "description": 125},
    }
    limits = _PLATFORM_LIMITS.get(platform.lower(), _PLATFORM_LIMITS["google"])
    hl_limit = limits["headline"]
    desc_limit = limits["description"]

    headline = (headline or "").strip()
    description = (description or "").strip()

    if not headline:
        return {
            "headline": headline, "description": description,
            "platform": platform, "score": 0, "grade": "F",
            "headline_char_count": 0, "headline_within_limit": False,
            "description_char_count": 0, "description_within_limit": False,
            "has_cta": False, "has_number": False, "has_you_language": False,
            "urgency_words_found": [], "power_words_found": [],
            "suggestions": ["Headline is required."],
        }

    hl_len = len(headline)
    desc_len = len(description)
    hl_within = hl_len <= hl_limit
    desc_within = desc_len <= desc_limit or not description

    combined = (headline + " " + description).lower()
    words = combined.split()

    has_number = bool(re.search(r'\d', combined))
    has_you = bool(re.search(r'\byou\b|\byour\b', combined))

    _CTA_WORDS = {
        "buy", "get", "start", "try", "sign up", "signup", "register",
        "learn more", "discover", "shop", "order", "book", "claim",
        "download", "grab", "join", "see", "watch", "read", "access",
        "unlock", "save", "find", "explore",
    }
    has_cta = any(cta in combined for cta in _CTA_WORDS)

    _URGENCY_WORDS = {
        "limited", "today only", "expires", "deadline", "last chance",
        "hurry", "now", "ending", "don't miss", "only", "act now",
        "sale ends", "for a limited time", "while supplies last",
    }
    urgency_found = sorted({w for w in _URGENCY_WORDS if w in combined})

    _POWER_WORDS = {
        "free", "new", "exclusive", "proven", "guaranteed", "instant",
        "simple", "easy", "fast", "best", "top", "ultimate", "save",
        "bonus", "secret", "powerful", "amazing", "results", "boost",
        "without", "no risk", "trusted",
    }
    power_words_found = sorted({w for w in _POWER_WORDS if w in combined})

    # --- Headline sub-score (0-50) ---
    hl_score = 0
    if hl_within:
        hl_score += 15  # meets platform limit
    else:
        hl_score -= 5   # over limit is a hard fail in real ad platforms

    if 10 <= hl_len <= hl_limit:
        hl_score += 10  # good length
    elif hl_len < 10:
        hl_score += 3   # too short

    hl_lower = headline.lower()
    if any(cta in hl_lower for cta in _CTA_WORDS):
        hl_score += 8
    if bool(re.search(r'\d', headline)):
        hl_score += 6  # stat/number in headline = stronger click
    if bool(re.search(r'\byou\b|\byour\b', hl_lower)):
        hl_score += 5
    if any(w in hl_lower for w in _POWER_WORDS):
        hl_score += 6
    hl_score = max(0, min(50, hl_score))

    # --- Description sub-score (0-40) ---
    desc_score = 0
    if description:
        if desc_within:
            desc_score += 10
        if 20 <= desc_len <= desc_limit:
            desc_score += 8
        if has_cta:
            desc_score += 7
        if has_number:
            desc_score += 5
        if has_you:
            desc_score += 5
        if urgency_found:
            desc_score += 5
        desc_score = max(0, min(40, desc_score))
    else:
        desc_score = 5  # description is optional but helpful

    score = 10 + hl_score + desc_score
    score = max(0, min(100, score))
    grade_map = [(90, "A"), (75, "B"), (60, "C"), (45, "D")]
    grade = next((g for t, g in grade_map if score >= t), "F")

    # Suggestions
    suggestions = []
    if not hl_within:
        suggestions.append(
            f"Headline is {hl_len} chars but the {platform} limit is {hl_limit}. "
            f"Trim to ≤{hl_limit} chars or it will be cut off."
        )
    if hl_len < 15:
        suggestions.append(
            "Headline is very short. Use the full character allowance to convey "
            "maximum value in the limited space."
        )
    if not has_cta:
        suggestions.append(
            "Add a clear CTA — 'Get Started', 'Try Free', 'Learn More', 'Shop Now'. "
            "Ads without CTAs underperform consistently."
        )
    if not has_number:
        suggestions.append(
            "Include a number or stat (e.g. 'Save 50%', '$0 to start', 'In 5 minutes'). "
            "Specific numbers boost CTR in ad copy."
        )
    if not has_you:
        suggestions.append(
            "Use 'you' or 'your' to speak directly to the reader. "
            "Second-person framing makes ads feel personal and relevant."
        )
    if not urgency_found and not description:
        suggestions.append(
            "Add a description with urgency ('Limited time', 'Today only') or a benefit "
            "statement to give reasons to click beyond the headline."
        )
    if description and not desc_within:
        suggestions.append(
            f"Description is {desc_len} chars but the visible preview is ~{desc_limit} chars on {platform}. "
            "Put your strongest message in the first part."
        )
    if not suggestions:
        suggestions.append(
            "Solid ad copy! CTA, number, you-language, and character limits all look good."
        )

    return {
        "headline": headline,
        "description": description,
        "platform": platform,
        "score": score,
        "grade": grade,
        "headline_char_count": hl_len,
        "headline_limit": hl_limit,
        "headline_within_limit": hl_within,
        "description_char_count": desc_len,
        "description_limit": desc_limit,
        "description_within_limit": desc_within,
        "has_cta": has_cta,
        "has_number": has_number,
        "has_you_language": has_you,
        "urgency_words_found": urgency_found,
        "power_words_found": power_words_found,
        "suggestions": suggestions,
    }


@app.route("/v1/score_ad_copy", methods=["GET", "POST"])
@app.route("/score-ad-copy", methods=["GET", "POST"])
@app.route("/score_ad_copy", methods=["GET", "POST"])
def endpoint_score_ad_copy():
    """Score Google Ads or Meta ad copy for CTR potential."""
    if request.method == "GET":
        return jsonify({
            "endpoint": "score-ad-copy",
            "method": "POST",
            "description": (
                "Score ad copy (headline + description) 0-100 for Google Ads or "
                "Meta Ads. Checks character limits, CTA presence, number/stat usage, "
                "you-language, urgency words, and power words. Instant, no AI."
            ),
            "usage": {
                "url": "https://contentforge-api-lpp9.onrender.com/score-ad-copy",
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "body": {
                    "headline": "your ad headline (required)",
                    "description": "your ad description (optional)",
                    "platform": "google or meta (default: google)",
                },
            },
            "character_limits": {
                "google": {"headline": "30 chars", "description": "90 chars"},
                "meta": {"headline": "27 chars", "description": "125 chars visible"},
            },
            "scoring_factors": [
                "Headline length vs platform limit",
                "CTA presence (Buy, Get, Start, Try, etc.)",
                "Number/stat (Save 50%, in 3 minutes, $0 setup)",
                "You-language (you/your for personal relevance)",
                "Urgency/scarcity (limited, today only, expires)",
                "Power words (free, proven, instant, results, etc.)",
                "Description completeness and length",
            ],
            "example_curl": (
                'curl -X POST https://contentforge-api-lpp9.onrender.com/score-ad-copy '
                '-H "Content-Type: application/json" '
                '-d \'{"headline": "Score Your Content in 5 Seconds", '
                '"description": "Try ContentForge free — instant scores for tweets, LinkedIn, TikTok and more.", '
                '"platform": "google"}\''
            ),
            "note": "No API key needed for direct access. Free tier on RapidAPI: 50 calls/month.",
        }), 200

    if not _verify_rapidapi_request():
        return jsonify({"error": "forbidden"}), 403
    allowed, remaining = _check_rate_limit()
    if not allowed:
        return jsonify({"error": "rate limit exceeded (30/min)"}), 429

    start = time.time()
    payload = request.get_json(silent=True) or {}
    headline = (
        payload.get("headline") or payload.get("title") or payload.get("text") or ""
    ).strip()
    description = (payload.get("description") or payload.get("body") or "").strip()
    platform_param = (payload.get("platform") or "google").strip().lower()

    if platform_param not in ("google", "meta", "facebook", "instagram"):
        platform_param = "google"

    if not headline:
        return jsonify({
            "error": "missing 'headline' parameter. Send JSON body: {\"headline\": \"your ad headline\"}"
        }), 400
    if len(headline) > 200:
        return jsonify({"error": "headline too long (max 200 chars for scoring)"}), 400
    if len(description) > 500:
        return jsonify({"error": "description too long (max 500 chars for scoring)"}), 400

    result = score_ad_copy(headline, description, platform_param)
    _log_usage("score_ad_copy", int((time.time() - start) * 1000))
    return _add_rate_headers(jsonify(result), remaining)


# ---------------------------------------------------------------------------
# 5g. Multi-Platform Score (heuristic — instant, no LLM)
# ---------------------------------------------------------------------------
_PLATFORM_SCORERS = {
    "tweet": lambda text, _opts: score_tweet(text),
    "twitter": lambda text, _opts: score_tweet(text),
    "linkedin": lambda text, _opts: score_linkedin_post(text),
    "instagram": lambda text, _opts: score_instagram_caption(text),
    "tiktok": lambda text, _opts: score_tiktok_caption(text),
    "threads": lambda text, _opts: score_threads_post(text),
    "facebook": lambda text, _opts: score_facebook_post(text),
    "pinterest": lambda text, _opts: score_pinterest_pin(text),
    "youtube": lambda text, opts: score_youtube_title(
        text, opts.get("thumbnail_text", "")
    ),
    "youtube_description": lambda text, _opts: score_youtube_description(text),
    "email": lambda text, opts: score_email_subject(
        text, opts.get("preview_text", "")
    ),
}


@app.route("/v1/score_multi", methods=["GET", "POST"])
@app.route("/score-multi", methods=["GET", "POST"])
@app.route("/score_multi", methods=["GET", "POST"])
def endpoint_score_multi():
    """Score one piece of text across multiple platforms in a single call."""
    if request.method == "GET":
        return jsonify({
            "endpoint": "score-multi",
            "method": "POST",
            "description": (
                "Score one piece of text across multiple platforms in a single "
                "API call. Returns per-platform scores, grades, and suggestions. "
                "Instant heuristic analysis, no AI needed."
            ),
            "usage": {
                "url": "https://contentforge-api-lpp9.onrender.com/score-multi",
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "body": {
                    "text": "your content text here",
                    "platforms": ["tweet", "linkedin", "instagram"],
                },
            },
            "available_platforms": list(_PLATFORM_SCORERS.keys()),
            "example_curl": (
                'curl -X POST https://contentforge-api-lpp9.onrender.com/score-multi '
                '-H "Content-Type: application/json" '
                "-d '{\"text\": \"I built a free tool that scores your content "
                "before you post it.\", \"platforms\": [\"tweet\", \"linkedin\", \"instagram\"]}'"
            ),
            "note": (
                "No API key needed for direct access. "
                "Free tier on RapidAPI: 50 calls/month."
            ),
        }), 200

    if not _verify_rapidapi_request():
        return jsonify({"error": "forbidden"}), 403
    allowed, remaining = _check_rate_limit()
    if not allowed:
        return jsonify({"error": "rate limit exceeded (30/min)"}), 429

    start = time.time()
    payload = request.get_json(silent=True) or {}
    text = (payload.get("text") or payload.get("content") or "").strip()
    platforms = payload.get("platforms", [])
    opts = payload  # pass full payload for thumbnail_text, preview_text

    if not text:
        return jsonify({
            "error": (
                "missing 'text' parameter. "
                'Send JSON: {"text": "...", "platforms": ["tweet", "linkedin"]}'
            )
        }), 400
    if len(text) > 5000:
        return jsonify({"error": "text too long (max 5000 chars)"}), 400

    if not platforms or not isinstance(platforms, list):
        # Default: score for all major platforms
        platforms = ["tweet", "linkedin", "instagram"]

    # Validate platforms
    valid = [p for p in platforms if p in _PLATFORM_SCORERS]
    if not valid:
        return jsonify({
            "error": (
                f"no valid platforms. Available: {list(_PLATFORM_SCORERS.keys())}"
            )
        }), 400

    results = {}
    best_platform = None
    best_score = -1

    for p in valid:
        try:
            r = _PLATFORM_SCORERS[p](text, opts)
            results[p] = {
                "score": r["score"],
                "grade": r["grade"],
                "suggestions": r.get("suggestions", []),
            }
            if r["score"] > best_score:
                best_score = r["score"]
                best_platform = p
        except Exception as e:
            results[p] = {"score": 0, "grade": "F", "error": str(e)}

    _log_usage("score_multi", int((time.time() - start) * 1000))
    return _add_rate_headers(jsonify({
        "text": text[:200] + ("..." if len(text) > 200 else ""),
        "platforms_scored": valid,
        "results": results,
        "best_platform": best_platform,
        "best_score": best_score,
    }), remaining)


# ---------------------------------------------------------------------------
# 6. Content Calendar (AI-powered)
# ---------------------------------------------------------------------------
@app.route("/v1/content_calendar", methods=["POST"])
def endpoint_content_calendar():
    if not _verify_rapidapi_request():
        return jsonify({"error": "forbidden"}), 403
    allowed, remaining = _check_rate_limit()
    if not allowed:
        return jsonify({"error": "rate limit exceeded (30/min)"}), 429

    start = time.time()
    payload = request.get_json(silent=True) or {}
    niche = payload.get("niche", "").strip()
    try:
        days = max(1, min(int(payload.get("days", 7)), 7))
    except (ValueError, TypeError):
        return jsonify({"error": "'days' must be an integer (1-7)"}), 400
    platform = payload.get("platform", "twitter")
    tone = payload.get("tone", "engaging")

    if not niche:
        return jsonify({"error": "missing 'niche' parameter"}), 400
    if len(niche) > 200:
        return jsonify({"error": "niche too long (max 200 chars)"}), 400

    day_labels = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][:days]

    prompt = (
        f"Create a {days}-day {platform} content calendar for the '{niche}' niche.\n"
        f"Tone: {tone}\n"
        f"Rules:\n"
        f"- One post idea per day\n"
        f"- Each day: a short topic/theme label and a ready-to-post draft\n"
        f"- Mix content types: tip, story, hot take, question, list\n"
        f"- Keep each draft under 280 characters for {platform}\n"
        f"- Return ONLY valid JSON in this exact format:\n"
        f'{{"calendar": [{{"day": "Monday", "theme": "...", "draft": "..."}}, ...]}}\n'
        f"Use these day labels in order: {', '.join(day_labels)}"
    )

    try:
        raw = _llm_generate(prompt)
        # Try to extract JSON object
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        calendar_data = None
        if match:
            try:
                calendar_data = json.loads(match.group(0))
            except json.JSONDecodeError:
                calendar_data = None

        if not calendar_data or "calendar" not in calendar_data:
            # Fallback: parse as line-by-line and build structure
            lines = [l.strip() for l in raw.strip().split("\n") if l.strip() and len(l.strip()) > 10]
            entries = []
            for i, label in enumerate(day_labels):
                draft = lines[i] if i < len(lines) else f"Post about {niche} today."
                draft = re.sub(r'^[\d.\-\)\]]+\s*', '', draft).strip().strip('"')
                entries.append({"day": label, "theme": niche, "draft": draft})
            calendar_data = {"calendar": entries}

        # Trim to requested days and label correctly
        entries = calendar_data.get("calendar", [])
        for i, entry in enumerate(entries):
            if i < len(day_labels):
                entry["day"] = day_labels[i]

        entries = entries[:days]

    except Exception as e:
        return jsonify({"error": f"LLM generation failed: {e}"}), 503

    _log_usage("content_calendar", int((time.time() - start) * 1000))
    return _add_rate_headers(jsonify({
        "niche": niche,
        "platform": platform,
        "tone": tone,
        "days": len(entries),
        "calendar": entries,
    }), remaining)


# ---------------------------------------------------------------------------
# 7. Improve Headline (AI-powered)
# ---------------------------------------------------------------------------
@app.route("/v1/improve_headline", methods=["POST"])
def endpoint_improve_headline():
    if not _verify_rapidapi_request():
        return jsonify({"error": "forbidden"}), 403
    allowed, remaining = _check_rate_limit()
    if not allowed:
        return jsonify({"error": "rate limit exceeded (30/min)"}), 429

    start = time.time()
    payload = request.get_json(silent=True) or {}
    text = payload.get("text", "").strip()
    try:
        count = max(1, min(int(payload.get("count", 3)), 5))
    except (ValueError, TypeError):
        return jsonify({"error": "'count' must be an integer (1-5)"}), 400

    if not text:
        return jsonify({"error": "missing 'text' parameter"}), 400
    if len(text) > 500:
        return jsonify({"error": "text too long (max 500 chars)"}), 400

    # First score the original to identify weaknesses
    original_analysis = analyze_headline(text)

    prompt = (
        f"Rewrite this headline into {count} improved versions that score higher on engagement.\n"
        f"Original: {text}\n"
        f"Current weaknesses to fix: {'; '.join(original_analysis.get('suggestions', [])) or 'none identified'}\n"
        f"Rules:\n"
        f"- Each version should be a significant improvement, not just minor word swaps\n"
        f"- Keep the core message/topic intact\n"
        f"- Use power words, numbers, questions, or curiosity gaps\n"
        f"- Each improved headline under 100 characters\n"
        f"- Return ONLY a JSON array of strings\n"
        f"Example: [\"Improved version 1\", \"Improved version 2\", \"Improved version 3\"]"
    )

    try:
        raw = _llm_generate(prompt)
        match = re.search(r'\[.*?\]', raw, re.DOTALL)
        improved = None
        if match:
            try:
                improved = json.loads(match.group(0))
            except json.JSONDecodeError:
                improved = None

        if not improved:
            improved = [
                re.sub(r'^[\d.\-\)\]]+\s*', '', line).strip().strip('"')
                for line in raw.strip().split("\n")
                if line.strip() and len(line.strip()) > 5
            ]
        improved = [h for h in improved if isinstance(h, str) and len(h) > 5][:count]

        # Score each improved version
        scored_versions = []
        for version in improved:
            analysis = analyze_headline(version)
            scored_versions.append({
                "text": version,
                "score": analysis["score"],
                "grade": analysis["grade"],
                "power_words_found": analysis["power_words_found"],
            })

        # Sort by score descending
        scored_versions.sort(key=lambda x: -x["score"])

    except Exception as e:
        return jsonify({"error": f"LLM generation failed: {e}"}), 503

    _log_usage("improve_headline", int((time.time() - start) * 1000))
    return _add_rate_headers(jsonify({
        "original": text,
        "original_score": original_analysis["score"],
        "original_grade": original_analysis["grade"],
        "original_suggestions": original_analysis["suggestions"],
        "improved_versions": scored_versions,
    }), remaining)


# ---------------------------------------------------------------------------
# 8. Thread Outline (AI-powered)
# ---------------------------------------------------------------------------
@app.route("/v1/thread_outline", methods=["POST"])
def endpoint_thread_outline():
    if not _verify_rapidapi_request():
        return jsonify({"error": "forbidden"}), 403
    allowed, remaining = _check_rate_limit()
    if not allowed:
        return jsonify({"error": "rate limit exceeded (30/min)"}), 429

    start = time.time()
    payload = request.get_json(silent=True) or {}
    topic = payload.get("topic", "").strip()
    try:
        tweet_count = max(3, min(int(payload.get("tweet_count", 7)), 10))
    except (ValueError, TypeError):
        return jsonify({"error": "'tweet_count' must be an integer (3-10)"}), 400
    tone = payload.get("tone", "informative").strip() or "informative"

    if not topic:
        return jsonify({"error": "missing 'topic' parameter"}), 400
    if len(topic) > 300:
        return jsonify({"error": "topic too long (max 300 chars)"}), 400

    body_count = tweet_count - 2  # subtract hook and CTA tweets

    prompt = (
        f"Write a Twitter thread outline about: {topic}\n"
        f"Tone: {tone}\n"
        f"Structure:\n"
        f"- 1 hook tweet (scroll-stopping opener, under 280 chars)\n"
        f"- {body_count} body tweets (one key insight each, under 280 chars)\n"
        f"- 1 CTA tweet (call to action — follow, bookmark, reply — under 280 chars)\n"
        f"Rules:\n"
        f"- Each tweet stands alone and delivers real value\n"
        f"- Number the body tweets in the content (e.g. '2/ ', '3/ ')\n"
        f"- Use concrete examples, numbers, or bold claims\n"
        f"- Return ONLY valid JSON in this exact format:\n"
        f'{{"hook": "...", "tweets": ["...", "...", ...], "cta": "..."}}\n'
        f"The 'tweets' array must have exactly {body_count} items."
    )

    try:
        raw = _llm_generate(prompt)
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        thread_data = None
        if match:
            try:
                thread_data = json.loads(match.group(0))
            except json.JSONDecodeError:
                thread_data = None

        if not thread_data or "hook" not in thread_data:
            # Fallback: split raw text into tweet-sized chunks
            lines = [
                re.sub(r'^[\d.\-\)\]]+\s*', '', l).strip().strip('"')
                for l in raw.strip().split("\n")
                if l.strip() and len(l.strip()) > 10
            ]
            hook = lines[0] if lines else f"Thread about {topic}:"
            cta = lines[-1] if len(lines) > 1 else "Follow for more insights like this 🧵"
            body = lines[1:-1][:body_count] if len(lines) > 2 else [f"Key insight about {topic}."] * body_count
            thread_data = {"hook": hook, "tweets": body, "cta": cta}

        hook = str(thread_data.get("hook", f"Thread: {topic}")).strip()
        tweets = [str(t).strip() for t in thread_data.get("tweets", []) if str(t).strip()][:body_count]
        # Pad if LLM returned fewer body tweets than requested
        while len(tweets) < body_count:
            tweets.append(f"{len(tweets) + 2}/ Key insight about {topic}.")
        cta = str(thread_data.get("cta", "Follow for more threads like this 🧵")).strip()

        all_tweets = [hook] + tweets + [cta]

    except Exception as e:
        return jsonify({"error": f"LLM generation failed: {e}"}), 503

    _log_usage("thread_outline", int((time.time() - start) * 1000))
    return _add_rate_headers(jsonify({
        "topic": topic,
        "tone": tone,
        "total_tweets": len(all_tweets),
        "hook": hook,
        "tweets": tweets,
        "cta": cta,
        "full_thread": all_tweets,
    }), remaining)


# ---------------------------------------------------------------------------
# 9. Generate Bio (AI-powered)
# ---------------------------------------------------------------------------
@app.route("/v1/generate_bio", methods=["POST"])
def endpoint_generate_bio():
    if not _verify_rapidapi_request():
        return jsonify({"error": "forbidden"}), 403
    allowed, remaining = _check_rate_limit()
    if not allowed:
        return jsonify({"error": "rate limit exceeded (30/min)"}), 429

    start = time.time()
    payload = request.get_json(silent=True) or {}
    name = payload.get("name", "").strip()
    niche = payload.get("niche", "").strip()
    keywords = payload.get("keywords", [])
    platform = payload.get("platform", "twitter").strip().lower() or "twitter"
    tone = payload.get("tone", "professional").strip() or "professional"

    if not name:
        return jsonify({"error": "missing 'name' parameter"}), 400
    if not niche:
        return jsonify({"error": "missing 'niche' parameter"}), 400
    if len(name) > 100:
        return jsonify({"error": "name too long (max 100 chars)"}), 400
    if len(niche) > 200:
        return jsonify({"error": "niche too long (max 200 chars)"}), 400

    # Platform-specific char limits
    char_limits = {"twitter": 160, "linkedin": 300, "instagram": 150}
    char_limit = char_limits.get(platform, 160)

    if isinstance(keywords, list):
        keywords_str = ", ".join(str(k) for k in keywords[:10] if k)
    else:
        keywords_str = str(keywords)[:200]

    prompt = (
        f"Write a {platform} bio for {name}.\n"
        f"Niche: {niche}\n"
        f"Tone: {tone}\n"
        f"{'Keywords to include: ' + keywords_str if keywords_str else ''}\n"
        f"Rules:\n"
        f"- Maximum {char_limit} characters\n"
        f"- Opening with what they do, not their name\n"
        f"- Include a clear value proposition\n"
        f"- End with a CTA or hook (e.g. 'DM me', 'Follow for daily tips', link placeholder)\n"
        f"- Friendly, punchy, human-sounding\n"
        f"- Return ONLY the bio text, no quotes, no explanation"
    )

    try:
        bio = _llm_generate(prompt).strip().strip('"').strip("'")
        # Trim to platform limit if LLM over-generated
        if len(bio) > char_limit * 1.2:
            bio = bio[:char_limit].rsplit(" ", 1)[0] + "…"
    except Exception as e:
        return jsonify({"error": f"LLM generation failed: {e}"}), 503

    is_valid = len(bio) <= char_limit

    _log_usage("generate_bio", int((time.time() - start) * 1000))
    return _add_rate_headers(jsonify({
        "name": name,
        "platform": platform,
        "tone": tone,
        "bio": bio,
        "char_count": len(bio),
        "char_limit": char_limit,
        "is_valid_length": is_valid,
    }), remaining)


# ---------------------------------------------------------------------------
# 8. Generate Caption (AI-powered) — Instagram / TikTok
# ---------------------------------------------------------------------------
@app.route("/v1/generate_caption", methods=["GET", "POST"])
@app.route("/generate-caption", methods=["GET", "POST"])
@app.route("/generate_caption", methods=["GET", "POST"])
def endpoint_generate_caption():
    """AI-generated caption for Instagram or TikTok, ready to score and post."""
    if request.method == "GET":
        return jsonify({
            "endpoint": "generate-caption",
            "method": "POST",
            "description": (
                "Generate an optimized caption for Instagram or TikTok. "
                "Includes hashtags, emojis, and a call-to-action engineered "
                "for the target platform's algorithm."
            ),
            "usage": {
                "url": "https://contentforge-api-lpp9.onrender.com/generate-caption",
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "body": {
                    "topic": "your post topic here",
                    "platform": "instagram",
                    "tone": "engaging",
                },
            },
            "parameters": {
                "topic": "What your post is about (required)",
                "platform": "instagram or tiktok (default: instagram)",
                "tone": "engaging, inspirational, educational, humorous (default: engaging)",
            },
            "example_curl": (
                'curl -X POST https://contentforge-api-lpp9.onrender.com/generate-caption '
                '-H "Content-Type: application/json" '
                "-d '{\"topic\": \"morning productivity routine\", \"platform\": \"instagram\"}'"
            ),
        }), 200

    if not _verify_rapidapi_request():
        return jsonify({"error": "forbidden"}), 403
    allowed, remaining = _check_rate_limit()
    if not allowed:
        return jsonify({"error": "rate limit exceeded (30/min)"}), 429

    start = time.time()
    payload = request.get_json(silent=True) or {}
    topic = (payload.get("topic") or payload.get("content") or "").strip()
    platform = payload.get("platform", "instagram").lower().strip()
    tone = payload.get("tone", "engaging").lower().strip()

    if not topic:
        return jsonify({
            "error": "missing 'topic' parameter. Send JSON: {\"topic\": \"your post topic\"}"
        }), 400
    if len(topic) > 500:
        return jsonify({"error": "topic too long (max 500 chars)"}), 400

    if platform not in ("instagram", "tiktok"):
        platform = "instagram"
    if tone not in ("engaging", "inspirational", "educational", "humorous"):
        tone = "engaging"

    if platform == "instagram":
        platform_rules = (
            "Instagram caption rules:\n"
            "- First line is the hook (scroll-stopper)\n"
            "- Body: 3-5 short lines\n"
            "- End with a question or call-to-action\n"
            "- Add 5-10 relevant hashtags at the end\n"
            "- Include 2-4 emojis throughout\n"
            "- Under 300 words total\n"
        )
    else:
        platform_rules = (
            "TikTok caption rules:\n"
            "- First line is a strong hook (POV / question / bold claim)\n"
            "- Keep total text under 150 characters (captions show truncated)\n"
            "- Add 3-5 relevant hashtags inline\n"
            "- Include 1-2 emojis\n"
            "- Add one clear CTA (follow, save, share, comment)\n"
        )

    prompt = (
        f"Write a {tone} {platform} caption about: {topic}\n\n"
        f"{platform_rules}\n"
        "Return ONLY the caption text, nothing else. No intro, no explanation."
    )

    try:
        caption = _llm_generate(prompt).strip().strip('"').strip("'")
    except Exception as e:
        return jsonify({"error": f"LLM generation failed: {e}"}), 503

    _log_usage("generate_caption", int((time.time() - start) * 1000))
    return _add_rate_headers(jsonify({
        "topic": topic,
        "platform": platform,
        "tone": tone,
        "caption": caption,
        "char_count": len(caption),
        "word_count": len(caption.split()),
    }), remaining)


# ---------------------------------------------------------------------------
# 9. Generate LinkedIn Post (AI-powered)
# ---------------------------------------------------------------------------
@app.route("/v1/generate_linkedin_post", methods=["GET", "POST"])
@app.route("/generate-linkedin-post", methods=["GET", "POST"])
@app.route("/generate_linkedin_post", methods=["GET", "POST"])
def endpoint_generate_linkedin_post():
    """AI-generated LinkedIn post with hook, body paragraphs, insight, and CTA."""
    if request.method == "GET":
        return jsonify({
            "endpoint": "generate-linkedin-post",
            "method": "POST",
            "description": (
                "Generate a full LinkedIn post for any topic. "
                "Returns a structured post with a scroll-stopping hook, "
                "story/insight body, and a closing call-to-action — "
                "formatted in LinkedIn's proven short-paragraph style."
            ),
            "usage": {
                "url": "https://contentforge-api-lpp9.onrender.com/generate-linkedin-post",
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "body": {
                    "topic": "your post topic here",
                    "tone": "storytelling",
                },
            },
            "parameters": {
                "topic": "What your post is about (required)",
                "tone": "storytelling, professional, motivational (default: storytelling)",
            },
            "example_curl": (
                'curl -X POST https://contentforge-api-lpp9.onrender.com/generate-linkedin-post '
                '-H "Content-Type: application/json" '
                "-d '{\"topic\": \"lessons from launching my first SaaS\"}'"
            ),
        }), 200

    if not _verify_rapidapi_request():
        return jsonify({"error": "forbidden"}), 403
    allowed, remaining = _check_rate_limit()
    if not allowed:
        return jsonify({"error": "rate limit exceeded (30/min)"}), 429

    start = time.time()
    payload = request.get_json(silent=True) or {}
    topic = (payload.get("topic") or "").strip()
    tone = payload.get("tone", "storytelling").lower().strip()

    if not topic:
        return jsonify({
            "error": "missing 'topic' parameter. Send JSON: {\"topic\": \"your post topic\"}"
        }), 400
    if len(topic) > 500:
        return jsonify({"error": "topic too long (max 500 chars)"}), 400

    if tone not in ("storytelling", "professional", "motivational"):
        tone = "storytelling"

    tone_instructions = {
        "storytelling": (
            "Use personal story-telling format. Start with a bold first-person statement. "
            "Tell a mini story. Extract a key lesson. End with an engaging question."
        ),
        "professional": (
            "Use a data-driven professional tone. Open with a strong insight or statistic. "
            "Give 3 concise concrete points. End with a professional call-to-action."
        ),
        "motivational": (
            "Use an inspirational motivational tone. Start with a powerful challenge or truth. "
            "Build with short punch lines. End with an empowering CTA that feels actionable."
        ),
    }[tone]

    prompt = (
        f"Write a LinkedIn post about: {topic}\n\n"
        f"{tone_instructions}\n\n"
        "LinkedIn formatting rules:\n"
        "- Short paragraphs (1-2 sentences max each)\n"
        "- Blank line between each paragraph\n"
        "- First line is the hook (must make someone stop scrolling)\n"
        "- Add 3-5 relevant hashtags at the very end\n"
        "- Total length 150-400 words\n"
        "- Do NOT use bullet points or numbered lists\n\n"
        "Return ONLY the post text, nothing else."
    )

    try:
        post = _llm_generate(prompt).strip().strip('"').strip("'")
    except Exception as e:
        return jsonify({"error": f"LLM generation failed: {e}"}), 503

    _log_usage("generate_linkedin_post", int((time.time() - start) * 1000))
    return _add_rate_headers(jsonify({
        "topic": topic,
        "tone": tone,
        "post": post,
        "char_count": len(post),
        "word_count": len(post.split()),
    }), remaining)


# ---------------------------------------------------------------------------
# 10. Generate Email Sequence (AI-powered)
# ---------------------------------------------------------------------------
@app.route("/v1/generate_email_sequence", methods=["GET", "POST"])
@app.route("/generate-email-sequence", methods=["GET", "POST"])
@app.route("/generate_email_sequence", methods=["GET", "POST"])
def endpoint_generate_email_sequence():
    """Generate a 3-email drip sequence: hook → value → CTA."""
    if request.method == "GET":
        return jsonify({
            "endpoint": "generate-email-sequence",
            "method": "POST",
            "description": (
                "Generate a 3-email drip sequence for any niche or offer. "
                "Returns a hook email (day 0), a value email (day 2-3), "
                "and a CTA/close email (day 5-7). Each email includes "
                "subject line, preview text, and body copy. AI-powered."
            ),
            "usage": {
                "url": "https://contentforge-api-lpp9.onrender.com/generate-email-sequence",
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "body": {
                    "niche": "your niche or audience (required)",
                    "offer": "what you're promoting (optional)",
                    "tone": "friendly, professional, or urgency (default: friendly)",
                },
            },
            "example_curl": (
                'curl -X POST https://contentforge-api-lpp9.onrender.com/generate-email-sequence '
                '-H "Content-Type: application/json" '
                '-d \'{"niche": "indie developers building SaaS", "offer": "ContentForge API free tier", "tone": "friendly"}\''
            ),
            "note": "Uses AI (Gemini 2.0 Flash). Free tier on RapidAPI: 50 calls/month.",
        }), 200

    if not _verify_rapidapi_request():
        return jsonify({"error": "forbidden"}), 403
    allowed, remaining = _check_rate_limit()
    if not allowed:
        return jsonify({"error": "rate limit exceeded (30/min)"}), 429

    start = time.time()
    payload = request.get_json(silent=True) or {}
    niche = (payload.get("niche") or payload.get("audience") or "").strip()
    offer = (payload.get("offer") or payload.get("product") or "").strip()
    tone = (payload.get("tone") or "friendly").strip().lower()

    if not niche:
        return jsonify({
            "error": "missing 'niche' parameter. Send JSON body: {\"niche\": \"your audience/niche\"}"
        }), 400
    if len(niche) > 300:
        return jsonify({"error": "niche too long (max 300 chars)"}), 400
    if tone not in ("friendly", "professional", "urgency"):
        tone = "friendly"

    offer_line = f"Offer/product: {offer}" if offer else ""

    prompt = (
        f"Write a 3-email drip sequence for this audience: {niche}\n"
        f"{offer_line}\n"
        f"Tone: {tone}\n\n"
        "Email structure:\n"
        "- Email 1 (Day 0): Hook/welcome — introduce the value, build curiosity, no hard sell\n"
        "- Email 2 (Day 3): Value — give a concrete tip, insight, or result they can use now\n"
        "- Email 3 (Day 6): CTA/close — clear call to action, urgency or reason to act today\n\n"
        "For each email write:\n"
        "- subject: a compelling subject line (30-50 chars)\n"
        "- preview: preheader text (40-80 chars, complements subject)\n"
        "- body: 100-200 words max, conversational, short paragraphs\n\n"
        "Return ONLY valid JSON in this exact format:\n"
        '{"emails": ['
        '{"email_number": 1, "send_day": "Day 0", "subject": "...", "preview": "...", "body": "..."},'
        '{"email_number": 2, "send_day": "Day 3", "subject": "...", "preview": "...", "body": "..."},'
        '{"email_number": 3, "send_day": "Day 6", "subject": "...", "preview": "...", "body": "..."}'
        ']}'
    )

    try:
        raw = _llm_generate(prompt)
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        seq_data = None
        if match:
            try:
                seq_data = json.loads(match.group(0))
            except json.JSONDecodeError:
                seq_data = None

        if not seq_data or "emails" not in seq_data or not seq_data["emails"]:
            # Fallback: build minimal structure
            lines = [l.strip() for l in raw.strip().split("\n") if l.strip() and len(l.strip()) > 15]
            chunk = max(1, len(lines) // 3)
            seq_data = {"emails": [
                {"email_number": 1, "send_day": "Day 0",
                 "subject": f"A quick note about {niche}",
                 "preview": "Something I think you'll find useful",
                 "body": "\n".join(lines[:chunk])},
                {"email_number": 2, "send_day": "Day 3",
                 "subject": f"The #1 thing I learned about {niche}",
                 "preview": "Here's the insight I wish I had sooner",
                 "body": "\n".join(lines[chunk:chunk * 2])},
                {"email_number": 3, "send_day": "Day 6",
                 "subject": "Last chance — don't miss this",
                 "preview": "One final thing before I let you go",
                 "body": "\n".join(lines[chunk * 2:]) or f"Ready to take action? Try {offer or niche} today."},
            ]}

        emails = seq_data["emails"][:3]

    except Exception as e:
        return jsonify({"error": f"LLM generation failed: {e}"}), 503

    _log_usage("generate_email_sequence", int((time.time() - start) * 1000))
    return _add_rate_headers(jsonify({
        "niche": niche,
        "offer": offer,
        "tone": tone,
        "email_count": len(emails),
        "emails": emails,
    }), remaining)


# ---------------------------------------------------------------------------
# 11. Generate Content Brief (AI-powered)
# ---------------------------------------------------------------------------
@app.route("/v1/generate_content_brief", methods=["GET", "POST"])
@app.route("/generate-content-brief", methods=["GET", "POST"])
@app.route("/generate_content_brief", methods=["GET", "POST"])
def endpoint_generate_content_brief():
    """Generate an AI research and content brief for any topic."""
    if request.method == "GET":
        return jsonify({
            "endpoint": "generate-content-brief",
            "method": "POST",
            "description": (
                "Generate a full content brief for any topic. Returns target "
                "audience, suggested angle, content outline, SEO keywords, "
                "and 5 hook ideas. Useful for blog posts, YouTube scripts, "
                "LinkedIn articles, and social campaigns. AI-powered."
            ),
            "usage": {
                "url": "https://contentforge-api-lpp9.onrender.com/generate-content-brief",
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "body": {
                    "topic": "your content topic (required)",
                    "platform": "blog, youtube, linkedin, twitter (default: blog)",
                    "tone": "informative, conversational, authoritative (default: informative)",
                },
            },
            "example_curl": (
                'curl -X POST https://contentforge-api-lpp9.onrender.com/generate-content-brief '
                '-H "Content-Type: application/json" '
                '-d \'{"topic": "how indie developers build passive income with APIs", "platform": "blog"}\''
            ),
            "note": "Uses AI (Gemini 2.0 Flash). Free tier on RapidAPI: 50 calls/month.",
        }), 200

    if not _verify_rapidapi_request():
        return jsonify({"error": "forbidden"}), 403
    allowed, remaining = _check_rate_limit()
    if not allowed:
        return jsonify({"error": "rate limit exceeded (30/min)"}), 429

    start = time.time()
    payload = request.get_json(silent=True) or {}
    topic = (payload.get("topic") or payload.get("subject") or "").strip()
    platform = (payload.get("platform") or "blog").strip().lower()
    tone = (payload.get("tone") or "informative").strip().lower()

    if not topic:
        return jsonify({
            "error": "missing 'topic' parameter. Send JSON body: {\"topic\": \"your content topic\"}"
        }), 400
    if len(topic) > 400:
        return jsonify({"error": "topic too long (max 400 chars)"}), 400

    if platform not in ("blog", "youtube", "linkedin", "twitter", "instagram", "tiktok"):
        platform = "blog"
    if tone not in ("informative", "conversational", "authoritative"):
        tone = "informative"

    prompt = (
        f"Create a content brief for this topic: {topic}\n"
        f"Platform: {platform}\n"
        f"Tone: {tone}\n\n"
        "Return ONLY valid JSON with this exact structure:\n"
        "{\n"
        '  "target_audience": "1-2 sentence description of the ideal reader",\n'
        '  "angle": "the unique angle or spin that makes this content stand out",\n'
        '  "outline": ["Section 1 title", "Section 2 title", "Section 3 title", "Section 4 title", "Section 5 title"],\n'
        '  "seo_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],\n'
        '  "hooks": ["Hook idea 1", "Hook idea 2", "Hook idea 3", "Hook idea 4", "Hook idea 5"],\n'
        '  "estimated_word_count": 800\n'
        "}\n"
        "The outline array must have 4-6 items. The seo_keywords and hooks arrays must have exactly 5 items each."
    )

    try:
        raw = _llm_generate(prompt)
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        brief = None
        if match:
            try:
                brief = json.loads(match.group(0))
            except json.JSONDecodeError:
                brief = None

        if not brief or "target_audience" not in brief:
            # Fallback structure
            brief = {
                "target_audience": f"People interested in {topic}.",
                "angle": f"A practical, actionable guide to {topic}.",
                "outline": [
                    f"What is {topic}?",
                    "Why it matters",
                    "Step-by-step guide",
                    "Common mistakes to avoid",
                    "Next steps",
                ],
                "seo_keywords": [
                    topic[:30],
                    f"how to {topic[:20]}",
                    f"{topic[:20]} guide",
                    f"{topic[:20]} tips",
                    f"best {topic[:20]}",
                ],
                "hooks": [
                    f"Everything you need to know about {topic}",
                    f"The truth about {topic} nobody tells you",
                    f"I wish I knew this about {topic} sooner",
                    f"{topic}: what actually works in 2026",
                    f"Stop guessing — here's the real guide to {topic}",
                ],
                "estimated_word_count": 800,
            }

    except Exception as e:
        return jsonify({"error": f"LLM generation failed: {e}"}), 503

    _log_usage("generate_content_brief", int((time.time() - start) * 1000))
    return _add_rate_headers(jsonify({
        "topic": topic,
        "platform": platform,
        "tone": tone,
        "brief": brief,
    }), remaining)


# ---------------------------------------------------------------------------
# Health + Root
# ---------------------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    gemini_configured = bool(os.environ.get("GEMINI_API_KEY", ""))
    ollama_reachable = False
    try:
        import urllib.request as _ureq
        _ureq.urlopen(
            os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434") + "/api/tags",
            timeout=1,
        )
        ollama_reachable = True
    except Exception:
        pass

    llm_backend = "none"
    if ollama_reachable:
        llm_backend = "ollama"
    elif gemini_configured:
        llm_backend = "gemini"

    # Pull quick usage stats from usage log
    total_requests = 0
    endpoint_counts: dict = {}
    try:
        if USAGE_LOG.exists():
            entries = json.loads(USAGE_LOG.read_text())
            total_requests = len(entries)
            for e in entries:
                ep = e.get("endpoint", "unknown")
                endpoint_counts[ep] = endpoint_counts.get(ep, 0) + 1
    except Exception:
        pass

    return jsonify({
        "status": "ok",
        "service": "contentforge",
        "version": "1.0.0",
        "llm_backend": llm_backend,
        "ai_endpoints_ready": llm_backend != "none",
        "total_requests_served": total_requests,
        "endpoint_usage": endpoint_counts,
    })


@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "service": "ContentForge API",
        "version": "1.0.0",
        "endpoints": {
            "POST /v1/analyze_headline": "Score & improve any headline (instant, no AI)",
            "POST /v1/score_tweet": "Score a tweet draft for engagement potential (instant, no AI)",
            "POST /v1/score_linkedin_post": "Score a LinkedIn post for reach and engagement (instant, no AI)",
            "POST /v1/score_instagram": "Score an Instagram caption for engagement (instant, no AI)",
            "POST /v1/score_youtube_title": "Score a YouTube title for CTR potential (instant, no AI)",
            "POST /v1/score_email_subject": "Score an email subject line for open rate (instant, no AI)",
            "POST /v1/score_multi": "Score text across multiple platforms in one call (instant, no AI)",
            "POST /v1/score_readability": "Score any text for readability with Flesch-Kincaid metrics (instant, no AI)",
            "POST /v1/score_tiktok": "Score a TikTok caption for engagement and reach (instant, no AI)",
            "POST /v1/score_threads": "Score a Meta Threads post for reach and engagement (instant, no AI)",
            "POST /v1/score_facebook": "Score a Facebook organic post for reach and engagement (instant, no AI)",
            "POST /v1/score_pinterest": "Score a Pinterest pin description for reach and saves (instant, no AI)",
            "POST /v1/score_youtube_description": "Score a YouTube video description for SEO and viewer value (instant, no AI)",
            "POST /v1/score_ad_copy": "Score Google or Meta ad copy for CTR potential (instant, no AI)",
            "POST /v1/analyze_hashtags": "Analyze hashtags for quality, diversity, and platform fit (instant, no AI)",
            "POST /v1/improve_headline": "AI-rewrite a headline into N better scored versions",
            "POST /v1/generate_hooks": "AI-generated scroll-stopping hooks",
            "POST /v1/rewrite": "Rewrite text for any platform/tone",
            "POST /v1/tweet_ideas": "Generate tweet ideas for any niche",
            "POST /v1/content_calendar": "AI-generated 7-day content calendar",
            "POST /v1/thread_outline": "AI-generated Twitter thread outline (hook + body + CTA)",
            "POST /v1/generate_bio": "AI-generated social media bio (Twitter/LinkedIn/Instagram)",
            "POST /v1/generate_caption": "AI-generated Instagram or TikTok caption (with hashtags + CTA)",
            "POST /v1/generate_linkedin_post": "AI-generated LinkedIn post (storytelling, professional, or motivational)",
            "POST /v1/generate_email_sequence": "AI-generated 3-email drip sequence (hook → value → CTA)",
            "POST /v1/generate_content_brief": "AI-generated content brief with outline, keywords, and hooks",
            "GET /health": "Service health check + usage stats",
        },
        "docs": "https://rapidapi.com/captainarmoreddude-default-default/api/contentforge1",
        "rapidapi": "https://rapidapi.com/captainarmoreddude-default-default/api/contentforge1",
    })


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------
def _run_test():
    import pprint
    with app.test_client() as c:
        print("=== Headline Analyzer ===")
        rv = c.post("/v1/analyze_headline", json={"text": "How I made $6,000 a month from a tiny weekend project"})
        pprint.pprint(rv.get_json())

        print("\n=== Tweet Scorer ===")
        rv = c.post("/v1/score_tweet", json={"text": "Built an API in 48 hours. It made $500 last month 💸 Here's how: #indiehacker #buildinpublic"})
        pprint.pprint(rv.get_json())

        print("\n=== LinkedIn Post Scorer ===")
        rv = c.post("/v1/score_linkedin_post", json={"post": "I spent 3 years building tools nobody used.\n\nThen I changed one thing.\n\nHere's what I learned:\n\n- Hook matters\n- Short paragraphs\n- Questions at the end\n\nWhat did you change?\n\n#buildinpublic #contentcreation #linkedin"})
        pprint.pprint(rv.get_json())

        print("\n=== Instagram Caption Scorer ===")
        rv = c.post("/v1/score_instagram", json={"caption": "Stop scrolling. This changed everything.\n\nI tried 30 days of cold showers and here's what happened 🧊💪\n\nSave this for later 👇\n\n#morningroutine #coldshower #productivity #selfimprovement #lifehacks"})
        pprint.pprint(rv.get_json())

        print("\n=== YouTube Title Scorer ===")
        rv = c.post("/v1/score_youtube_title", json={"title": "I Tried Making $1,000 in 24 Hours [Honest Results]", "thumbnail_text": "$1K IN 24H??"})
        pprint.pprint(rv.get_json())

        print("\n=== Email Subject Scorer ===")
        rv = c.post("/v1/score_email_subject", json={"subject": "{first_name}, your 3-step plan is ready", "preview_text": "Open to see the strategy top creators use"})
        pprint.pprint(rv.get_json())

        print("\n=== Readability Scorer ===")
        rv = c.post("/v1/score_readability", json={"text": "Short sentences work best. They keep the reader engaged. Use simple words too."})
        pprint.pprint(rv.get_json())

        print("\n=== TikTok Caption Scorer ===")
        rv = c.post("/v1/score_tiktok", json={"text": "POV: you stop guessing and start knowing if your content will go viral 🔥\n\nTry this free tool 👇\n\n#tiktok #viral #contentcreator"})
        pprint.pprint(rv.get_json())

        print("\n=== Hashtag Analyzer ===")
        rv = c.post("/v1/analyze_hashtags", json={"hashtags": "#coding #python #buildinpublic", "platform": "twitter"})
        pprint.pprint(rv.get_json())

        print("\n=== Threads Post Scorer ===")
        rv = c.post("/v1/score_threads", json={"text": "I spent 3 years building the wrong thing.\n\nHere's what I wish I knew on day 1: talk to 10 customers before writing a single line of code.\n\nAgree?"})
        pprint.pprint(rv.get_json())

        print("\n=== Facebook Post Scorer ===")
        rv = c.post("/v1/score_facebook", json={"text": "We just hit 10,000 customers 🎉 and it is all because of you!\n\nWhat is one thing you want us to build next? Drop a comment below!"})
        pprint.pprint(rv.get_json())

        print("\n=== Pinterest Pin Scorer ===")
        rv = c.post("/v1/score_pinterest", json={"text": "I batch-cooked every Sunday for 30 days and it changed my week completely! Here are the 5 easiest make-ahead meals for busy families. Save this for your next meal prep day! #mealprep #healthyeating #busyfamilies #dinnerideas"})
        pprint.pprint(rv.get_json())

        print("\n=== YouTube Description Scorer ===")
        rv = c.post("/v1/score_youtube_description", json={"text": "Learn the 5 passive income strategies I used to hit $5K/mo in 2026. Subscribe for weekly income reports!\n\n0:00 Intro\n1:30 Strategy 1 — APIs\n5:00 Strategy 2 — Content\n\nFree download: https://example.com/guide\n\n#passiveincome #sidehustle #money"})
        pprint.pprint(rv.get_json())

        print("\n=== Ad Copy Scorer ===")
        rv = c.post("/v1/score_ad_copy", json={"headline": "Score Your Content in 5 Seconds", "description": "Try ContentForge free — instant scores for tweets, LinkedIn, TikTok and more.", "platform": "google"})
        pprint.pprint(rv.get_json())

        print("\n=== Multi-Platform Scorer ===")
        rv = c.post("/v1/score_multi", json={"text": "Just shipped v2 of my SaaS. Revenue hit $5K MRR in 90 days #buildinpublic"})
        pprint.pprint(rv.get_json())

        print("\n=== Improve Headline ===")
        rv = c.post("/v1/improve_headline", json={"text": "How to make money online", "count": 3})
        pprint.pprint(rv.get_json())

        print("\n=== Generate Hooks ===")
        rv = c.post("/v1/generate_hooks", json={"topic": "passive income with APIs", "count": 3})
        pprint.pprint(rv.get_json())

        print("\n=== Rewrite ===")
        rv = c.post("/v1/rewrite", json={
            "text": "I built an API and now it makes me money every month without doing anything.",
            "platform": "twitter",
            "tone": "engaging",
        })
        pprint.pprint(rv.get_json())

        print("\n=== Tweet Ideas ===")
        rv = c.post("/v1/tweet_ideas", json={"niche": "developer tools", "count": 3})
        pprint.pprint(rv.get_json())

        print("\n=== Content Calendar ===")
        rv = c.post("/v1/content_calendar", json={"niche": "indie hacking", "days": 3, "platform": "twitter"})
        pprint.pprint(rv.get_json())

        print("\n=== Thread Outline ===")
        rv = c.post("/v1/thread_outline", json={"topic": "how to build a micro-SaaS in a weekend", "tweet_count": 5, "tone": "motivational"})
        pprint.pprint(rv.get_json())

        print("\n=== Generate Bio ===")
        rv = c.post("/v1/generate_bio", json={"name": "Alex Rivera", "niche": "indie developer building micro-SaaS tools", "platform": "twitter", "tone": "casual", "keywords": ["APIs", "side income", "buildinpublic"]})
        pprint.pprint(rv.get_json())

        print("\n=== Generate Caption ===")
        rv = c.post("/v1/generate_caption", json={"topic": "morning productivity routine", "platform": "instagram", "tone": "inspirational"})
        pprint.pprint(rv.get_json())

        print("\n=== Generate LinkedIn Post ===")
        rv = c.post("/v1/generate_linkedin_post", json={"topic": "lessons from launching my first SaaS", "tone": "storytelling"})
        pprint.pprint(rv.get_json())

        print("\n=== Generate Email Sequence ===")
        rv = c.post("/v1/generate_email_sequence", json={"niche": "indie developers building SaaS", "offer": "ContentForge API free tier", "tone": "friendly"})
        pprint.pprint(rv.get_json())

        print("\n=== Generate Content Brief ===")
        rv = c.post("/v1/generate_content_brief", json={"topic": "how to build passive income with APIs", "platform": "blog"})
        pprint.pprint(rv.get_json())

        print("\n=== Health ===")
        rv = c.get("/health")
        pprint.pprint(rv.get_json())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ContentForge API")
    parser.add_argument("--test", action="store_true", help="Run smoke test and exit")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8081)
    args = parser.parse_args()

    if args.test:
        _run_test()
    else:
        print(f"ContentForge API running on http://{args.host}:{args.port}")
        app.run(host=args.host, port=args.port)
