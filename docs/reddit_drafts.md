# Reddit Post Drafts — ContentForge v1.9.0

Copy-paste ready. Post these while logged in.

---

## r/SideProject

**Title:**
I built a content scoring API so you know if a post will flop *before* you hit publish

**Body:**
Been building ContentForge for a few months — it scores your content before you post it.

The idea: analytics tell you what happened *after*. I wanted something that tells you what's wrong *before*.

**What it does:**
- 45 endpoints across 12 platforms (Twitter, LinkedIn, YouTube, Reddit, TikTok, Instagram, email, etc.)
- Deterministic heuristics — no LLM call, always <50ms, free to run
- Returns a score, grade (A–F), quality gate (PASSED / REVIEW / FAILED), and actionable suggestions
- AI generation endpoints for hooks, ad copy, rewrites, bios, CTAs — using Ollama locally or Gemini as fallback
- Proof dashboard — log what you posted and what happened, track score-to-outcome deltas

**Quick example:**
```
POST /v1/score_content
{ "content": "5 habits that doubled my Twitter following", "platform": "twitter" }

→ { "score": 84, "grade": "B+", "quality_gate": "PASSED", "suggestions": [...] }
```

Free tier on RapidAPI — 30 req/min, no credit card.

Landing page: https://captainfredric.github.io/ContentForge
HN thread (more technical detail): https://news.ycombinator.com/item?id=47614618

Happy to answer questions — especially about the scoring heuristics if anyone's curious how platform-specific rules work.

---

## r/webdev

**Title:**
Show r/webdev: ContentForge API — score content for 12 platforms before publishing (<50ms, deterministic, no AI cost)

**Body:**
Built a REST API that scores content before you post it — no LLM required for scoring, so it's fast and free to call.

**Technical overview:**
- Flask app deployed on Render free tier
- 12 platform-specific scoring modules (Twitter, LinkedIn, YouTube, Reddit, TikTok, Instagram, Pinterest, Facebook, Email, Blog, Product Hunt, General)
- Each scorer runs pure heuristics: word count, readability (Flesch-Kincaid), hashtag density, emoji usage, CTA presence, hook strength, platform-specific keyword signals
- Every response includes `quality_gate` (PASSED/REVIEW/FAILED) + `operational_risk` (LOW/MEDIUM/HIGH)
- AI generation via Ollama → Gemini 2.5 Flash fallback chain
- In-memory rate limiting, flat JSON persistence, RapidAPI proxy auth

**New in v1.9.0:**
- `score_content` — unified single-platform scorer (the main entry point)
- `score_reddit` — Reddit-specific upvote potential scorer (specificity, anti-clickbait, hashtag penalty)
- `generate_subject_line` — AI email subject lines, each scored and ranked
- `generate_ad_copy` — N ad copy variants, auto-scored and ranked

**45 endpoints total.** OpenAPI spec in the repo.

GitHub: https://github.com/CaptainFredric/ContentForge
RapidAPI: https://rapidapi.com/captainfredric/api/contentforge (free tier)
Live: https://contentforge-api-lpp9.onrender.com/health

Feedback welcome — particularly on the scoring heuristics. Some are solid, some are educated guesses.

---

## r/selfhosted

**Title:**
ContentForge — self-hostable content scoring API, runs on Ollama locally, no external AI calls needed for scoring

**Body:**
ContentForge is a Flask API that scores social media content before posting. Designed to run self-hosted with Ollama for the AI generation endpoints — the scoring itself is pure heuristics with no AI cost.

**Self-host setup:**
```bash
git clone https://github.com/CaptainFredric/ContentForge
pip install -r requirements.txt
# configure Ollama endpoint in config
python scripts/api_prototype.py
```

**What runs locally (no external calls):**
- All 12 platform scorers — deterministic, <50ms
- Quality gate evaluation
- Rate limiting and proof dashboard

**What uses Ollama (local) or falls back to Gemini:**
- Hook generation, ad copy, rewrites, bio generation, subject lines

The LLM chain is: Ollama first → Gemini 2.5 Flash if Ollama unavailable → model rotation. If you have Ollama running locally, nothing leaves your machine for AI calls.

AGPL-3.0 licensed. Also available on RapidAPI if you just want to hit an endpoint without self-hosting.

GitHub: https://github.com/CaptainFredric/ContentForge
