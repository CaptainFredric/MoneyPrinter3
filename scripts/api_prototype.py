#!/usr/bin/env python3
"""ContentForge API — AI-powered content toolkit for creators and marketers.

Endpoints:
  POST /v1/analyze_headline    — Score & improve any headline (heuristic, instant)
  POST /v1/score_tweet         — Score a tweet draft before posting (heuristic, instant)
  POST /v1/improve_headline    — AI-rewrites a headline into N better scored versions (AI)
  POST /v1/generate_hooks      — Generate scroll-stopping hooks for a topic (AI)
  POST /v1/rewrite             — Rewrite text for a target platform/tone (AI)
  POST /v1/tweet_ideas         — Generate tweet ideas for a niche/topic (AI)
  POST /v1/content_calendar    — AI-generated 7-day content calendar for any niche (AI)
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

    char_limits = {"twitter": 280, "linkedin": 700, "email": 500, "blog": 1000}
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
            "POST /v1/improve_headline": "AI-rewrite a headline into N better scored versions",
            "POST /v1/generate_hooks": "AI-generated scroll-stopping hooks",
            "POST /v1/rewrite": "Rewrite text for any platform/tone",
            "POST /v1/tweet_ideas": "Generate tweet ideas for any niche",
            "POST /v1/content_calendar": "AI-generated 7-day content calendar",
            "POST /v1/thread_outline": "AI-generated Twitter thread outline (hook + body + CTA)",
            "POST /v1/generate_bio": "AI-generated social media bio (Twitter/LinkedIn/Instagram)",
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
