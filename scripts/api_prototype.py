#!/usr/bin/env python3
"""ContentForge API — AI-powered content toolkit for creators and marketers.

Endpoints:
  POST /v1/analyze_headline    — Score & improve any headline (heuristic, instant)
  POST /v1/generate_hooks      — Generate scroll-stopping hooks for a topic (AI)
  POST /v1/rewrite             — Rewrite text for a target platform/tone (AI)
  POST /v1/tweet_ideas         — Generate tweet ideas for a niche/topic (AI)
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
# Rate limiting (simple in-memory, per-IP)
# ---------------------------------------------------------------------------
_rate_buckets: dict[str, list[float]] = {}
RATE_LIMIT = 30  # requests per minute per IP


def _check_rate_limit():
    ip = request.remote_addr or "unknown"
    now = time.time()
    bucket = _rate_buckets.setdefault(ip, [])
    bucket[:] = [t for t in bucket if now - t < 60]
    if len(bucket) >= RATE_LIMIT:
        return False
    bucket.append(now)
    return True


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
        "secret", "proven", "free", "new", "easy", "instant", "guaranteed",
        "discover", "shocking", "ultimate", "exclusive", "limited", "urgent",
        "massive", "breakthrough", "insider", "hack", "mistake", "simple",
        "powerful", "surprising", "essential", "critical", "warning",
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
    if not _check_rate_limit():
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
    return jsonify(result)


# Keep old path working for backwards compat
@app.route("/analyze_headline", methods=["GET", "POST"])
def endpoint_analyze_headline_legacy():
    return endpoint_analyze_headline()


# ---------------------------------------------------------------------------
# 2. Generate Hooks (AI-powered)
# ---------------------------------------------------------------------------
@app.route("/v1/generate_hooks", methods=["POST"])
def endpoint_generate_hooks():
    if not _check_rate_limit():
        return jsonify({"error": "rate limit exceeded (30/min)"}), 429

    start = time.time()
    payload = request.get_json(silent=True) or {}
    topic = payload.get("topic", "").strip()
    count = min(int(payload.get("count", 5)), 10)
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
    return jsonify({"topic": topic, "style": style, "hooks": hooks})


# ---------------------------------------------------------------------------
# 3. Rewrite (AI-powered)
# ---------------------------------------------------------------------------
@app.route("/v1/rewrite", methods=["POST"])
def endpoint_rewrite():
    if not _check_rate_limit():
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
    return jsonify({
        "original": text,
        "rewritten": rewritten,
        "platform": platform,
        "tone": tone,
        "char_count": len(rewritten),
    })


# ---------------------------------------------------------------------------
# 4. Tweet Ideas (AI-powered)
# ---------------------------------------------------------------------------
@app.route("/v1/tweet_ideas", methods=["POST"])
def endpoint_tweet_ideas():
    if not _check_rate_limit():
        return jsonify({"error": "rate limit exceeded (30/min)"}), 429

    start = time.time()
    payload = request.get_json(silent=True) or {}
    niche = payload.get("niche", "").strip()
    count = min(int(payload.get("count", 5)), 10)
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
    return jsonify({"niche": niche, "count": len(tweets), "tweets": tweets})


# ---------------------------------------------------------------------------
# Health + Root
# ---------------------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "contentforge", "version": "1.0.0"})


@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "service": "ContentForge API",
        "version": "1.0.0",
        "endpoints": {
            "POST /v1/analyze_headline": "Score & improve any headline (instant)",
            "POST /v1/generate_hooks": "AI-generated scroll-stopping hooks",
            "POST /v1/rewrite": "Rewrite text for any platform/tone",
            "POST /v1/tweet_ideas": "Generate tweet ideas for any niche",
            "GET /health": "Service health check",
        },
        "docs": "https://rapidapi.com/contentforge/api/contentforge",
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
