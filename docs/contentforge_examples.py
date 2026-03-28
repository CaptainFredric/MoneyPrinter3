"""
ContentForge API — Python Code Examples
========================================
Copy-paste examples for all 10 endpoints.
Replace YOUR_KEY_HERE with your RapidAPI key.
Install dependency: pip install requests
"""

import requests

BASE_URL = "https://contentforge-api-lpp9.onrender.com"
HEADERS = {
    "X-RapidAPI-Key": "YOUR_KEY_HERE",
    "X-RapidAPI-Host": "contentforge1.p.rapidapi.com",
    "Content-Type": "application/json",
}


# ── 1. Analyze Headline (instant, no AI) ───────────────────────────────────
def analyze_headline(text: str) -> dict:
    r = requests.post(f"{BASE_URL}/v1/analyze_headline", headers=HEADERS, json={"text": text})
    r.raise_for_status()
    return r.json()


# ── 2. Score Tweet Draft (instant, no AI) ──────────────────────────────────
def score_tweet(text: str) -> dict:
    r = requests.post(f"{BASE_URL}/v1/score_tweet", headers=HEADERS, json={"text": text})
    r.raise_for_status()
    return r.json()


# ── 3. Improve Headline with AI ────────────────────────────────────────────
def improve_headline(text: str, count: int = 3) -> dict:
    r = requests.post(
        f"{BASE_URL}/v1/improve_headline",
        headers=HEADERS,
        json={"text": text, "count": count},
    )
    r.raise_for_status()
    return r.json()


# ── 4. Generate Hooks (AI) ─────────────────────────────────────────────────
def generate_hooks(topic: str, count: int = 5, tone: str = "engaging") -> dict:
    r = requests.post(
        f"{BASE_URL}/v1/generate_hooks",
        headers=HEADERS,
        json={"topic": topic, "count": count, "tone": tone},
    )
    r.raise_for_status()
    return r.json()


# ── 5. Rewrite Text (AI) ───────────────────────────────────────────────────
def rewrite(text: str, platform: str = "twitter", tone: str = "engaging") -> dict:
    r = requests.post(
        f"{BASE_URL}/v1/rewrite",
        headers=HEADERS,
        json={"text": text, "platform": platform, "tone": tone},
    )
    r.raise_for_status()
    return r.json()


# ── 6. Tweet Ideas (AI) ────────────────────────────────────────────────────
def tweet_ideas(niche: str, count: int = 5) -> dict:
    r = requests.post(
        f"{BASE_URL}/v1/tweet_ideas",
        headers=HEADERS,
        json={"niche": niche, "count": count},
    )
    r.raise_for_status()
    return r.json()


# ── 7. Content Calendar (AI) ───────────────────────────────────────────────
def content_calendar(niche: str, days: int = 7, platform: str = "twitter", tone: str = "engaging") -> dict:
    r = requests.post(
        f"{BASE_URL}/v1/content_calendar",
        headers=HEADERS,
        json={"niche": niche, "days": days, "platform": platform, "tone": tone},
    )
    r.raise_for_status()
    return r.json()


# ── 8. Thread Outline (AI) ─────────────────────────────────────────────────
def thread_outline(topic: str, tweet_count: int = 7, tone: str = "informative") -> dict:
    r = requests.post(
        f"{BASE_URL}/v1/thread_outline",
        headers=HEADERS,
        json={"topic": topic, "tweet_count": tweet_count, "tone": tone},
    )
    r.raise_for_status()
    return r.json()


# ── 9. Generate Bio (AI) ───────────────────────────────────────────────────
def generate_bio(
    name: str,
    niche: str,
    platform: str = "twitter",
    tone: str = "professional",
    keywords: list = None,
) -> dict:
    r = requests.post(
        f"{BASE_URL}/v1/generate_bio",
        headers=HEADERS,
        json={
            "name": name,
            "niche": niche,
            "platform": platform,
            "tone": tone,
            "keywords": keywords or [],
        },
    )
    r.raise_for_status()
    return r.json()


# ── 10. Health Check ───────────────────────────────────────────────────────
def health() -> dict:
    r = requests.get(f"{BASE_URL}/health", headers=HEADERS)
    r.raise_for_status()
    return r.json()


# ── Demo ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import json

    print("=== Headline Analyzer ===")
    result = analyze_headline("5 Proven Ways to Double Your Newsletter Open Rate")
    print(json.dumps(result, indent=2))

    print("\n=== Tweet Scorer ===")
    result = score_tweet(
        "Built a side project. Got 100 signups in 24 hours 🚀 Here's the exact homepage copy I used: #buildinpublic"
    )
    print(f"Score: {result['score']}/100  Grade: {result['grade']}")

    print("\n=== Improve Headline ===")
    result = improve_headline("How to make money online", count=3)
    print(f"Original: {result['original_grade']} ({result['original_score']})")
    for v in result["improved_versions"]:
        print(f"  [{v['grade']}] {v['score']} — {v['text']}")

    print("\n=== Thread Outline ===")
    result = thread_outline("why most side projects fail", tweet_count=5)
    print("HOOK:", result["hook"])
    for t in result["tweets"]:
        print(" ", t[:80])
    print("CTA:", result["cta"])

    print("\n=== Generate Bio ===")
    result = generate_bio(
        name="Alex Rivera",
        niche="indie developer building micro-SaaS tools",
        platform="twitter",
        tone="casual",
        keywords=["APIs", "side income", "buildinpublic"],
    )
    print(result["bio"])
    print(f"({result['char_count']}/{result['char_limit']} chars)")
