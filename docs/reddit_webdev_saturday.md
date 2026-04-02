# r/webdev Saturday Post — "Showoff Saturday" Draft

**Subreddit**: r/webdev
**Flair**: Showoff Saturday
**Post day**: Saturday morning (aim for 9–11 AM local time for max engagement)

---

## Title options (pick one — test both mentally for "r/webdev smell")

**Option A (Anti-pattern hook — recommended):**
> Why I wrote a 7,000-line Flask monolith instead of microservices

**Option B (Architecture + constraint hook):**
> I needed <50ms latency for content scoring so I threw out all the LLMs

**Option C (Direct engineer angle):**
> Built a content scoring API with pure heuristics — no ML, no model calls, deterministic output

---

## Post Body (Option A — Anti-Pattern hook)

---

About six months ago I decided to build a content scoring API. The idea was simple: before you post a tweet or LinkedIn update, run it through a quality gate and get a grade (A–F) back.

The "obvious" 2024 move would be: wrap GPT-4, call it done, ship.

I didn't do that.

**The Problem With LLM Scoring**

LLMs are stochastic. Score the same tweet twice and you'll get 74, then 79. For a *workflow tool* — something you run on every piece of content you produce — that inconsistency is fatal. You can't build a quality gate on a foundation that argues with itself.

I also couldn't justify the latency. A round-trip to any hosted LLM is 1–3 seconds minimum. I wanted sub-50ms. That means no network calls in the hot path.

**The Monolith Decision**

I made the call early: one Flask file, all endpoints, deploy to Render. No service mesh, no message queues, no Kubernetes. Just a single process that can answer a scoring request before the user blinks.

It's now ~7,000 lines. People who see it will have opinions. Those people are probably correct about how I *should* have built it. But it:

- Deploys in one command (`git push`)
- Has zero inter-service latency
- Is trivially debuggable (one file, one log stream)
- Costs $0/month to host on Render free tier

The constraints shaped the architecture. <50ms latency + $0 infra + solo developer = monolith.

**How the Scoring Works**

Each platform scorer is a pure Python function. No ML. No model. Just heuristics:

```python
def _score_tweet(text: str) -> dict:
    score = 50
    suggestions = []

    # Length check (sweet spot: 71–140 chars)
    length = len(text)
    if 71 <= length <= 140:
        score += 15
    elif length < 40:
        score -= 20
        suggestions.append("Too short — add context or a hook.")

    # Emoji signal (1–3 is optimal)
    emoji_count = sum(1 for c in text if c in EMOJI_SET)
    if 1 <= emoji_count <= 3:
        score += 8
    elif emoji_count > 5:
        score -= 10
        suggestions.append("Too many emojis — reduces professional credibility.")

    # Power words
    power_hits = [w for w in POWER_WORDS if w.lower() in text.lower()]
    score += min(len(power_hits) * 5, 15)

    # ... 20+ more signals

    grade = "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 50 else "D" if score >= 35 else "F"
    quality_gate = "PASSED" if score >= 70 else "REVIEW" if score >= 50 else "FAILED"

    return {"score": min(score, 100), "grade": grade, "quality_gate": quality_gate, "suggestions": suggestions}
```

Same input → same output, every time. No variance. No hallucinations. The scoring logic is entirely open source — you can read exactly why a post scored 74 instead of 80.

**The LLM Fallback Chain**

LLMs *do* appear in the API — but only for generation endpoints (rewrites, hook generation, subject lines). The chain is:

```
Ollama (local, free) → Gemini 2.5 Flash (cloud fallback) → model rotation
```

If you self-host with Ollama running locally, nothing leaves your machine for AI calls. Scoring is always local and free.

**The QOps Layer**

One thing that emerged organically: a quality operations layer. Three endpoints built around the concept of a "pre-publish gate":

- `POST /v1/quality_gate` — batch verdict (`PASSED | REVIEW | FAILED`) for up to 10 posts
- `GET /v1/platform_friction` — real-time platform health signals
- `POST /v1/proof_export` — export score → engagement delta as proof (for A/B tracking)

The proof system is the part I'm most interested in long-term. If you can track "score given" vs "actual engagement" across enough posts, you can start calibrating the heuristic weights empirically. It's essentially building a ruler and then verifying it against reality.

**Current State**

45 endpoints across 12 platforms. Self-hostable. AGPL-3.0.

GitHub: https://github.com/CaptainFredric/ContentForge

Feedback welcome — particularly on the scoring heuristics. Some are solid, some are educated guesses that need real engagement data to validate.

---

## Post notes

- **DO NOT mention RapidAPI in the post body.** GitHub link only. Let the README do the funnel work.
- **DO NOT say "free to use" or "check it out on RapidAPI"** — this triggers downvote reflex
- **DO engage with every comment** — when someone asks "how does X work" → reference the specific endpoint and explain the heuristic
- Ideal response to "why not just use GPT-4?": *"GPT-4 is stochastic and slow — it gives different scores to the same text and takes 2 seconds to respond. This is deterministic and takes 50ms. For a professional workflow, consistency and speed beat 'vibes' every time."*
- Ideal response to "this is just regex" or "these heuristics are wrong": *"Probably. That's exactly what I'm trying to fix — if you want to share actual engagement data from posts you've scored, I'll calibrate the weights against real numbers."* (Founding Users funnel)

---

## Timing

Post Saturday between **9:00 AM – 11:00 AM** your local time. r/webdev peaks mid-morning on weekends.
Set a reminder to check back at 3h, 6h, 12h intervals.
