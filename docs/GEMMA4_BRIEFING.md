# ContentForge — Project Briefing for Gemma 4 27B
## Context Document for AI Assistant Onboarding

This document brings you fully up to speed on ContentForge so you can assist
with development, marketing, and strategy decisions without needing extra
explanation each session. Read it completely before responding to any task.

---

## 1. What ContentForge Is

ContentForge is a **before-publish content intelligence REST API**. It scores
social media posts, email subject lines, headlines, and ad copy *before* they
are published, so creators know what to fix rather than finding out after a
flop. It does not replace analytics — it runs upstream of them.

The core insight driving the product: every analytics tool tells you what
happened after. ContentForge tells you what is wrong before you post.

**Live API:** https://contentforge-api-lpp9.onrender.com
**GitHub:** https://github.com/CaptainFredric/ContentForge
**RapidAPI listing:** https://rapidapi.com/captainfredric/api/contentforge
**Landing page:** https://captainfredric.github.io/ContentForge
**HN thread:** https://news.ycombinator.com/item?id=47614618

---

## 2. Technical Architecture

### Runtime
- **Language:** Python 3.12
- **Framework:** Flask (single-file app: `scripts/api_prototype.py`, ~7000 lines)
- **Deployment:** Render free tier web service (~30s cold start)
- **Auth:** RapidAPI proxy secret (`X-RapidAPI-Proxy-Secret` header); all public
  endpoints verified against it
- **Rate limiting:** In-memory, 30 req/min per IP; resets on cold start
- **Persistence:** Flat JSON files in `.mp/` directory (no database)

### The Heuristic Engine
The scoring layer is entirely deterministic — no AI call, no external dependency,
always under 50ms. Each platform has its own scorer function with hand-tuned
signal weights:

```
score_tweet()              Twitter/X
score_linkedin_post()      LinkedIn
score_instagram_caption()  Instagram
score_tiktok_caption()     TikTok
score_threads_post()       Meta Threads
score_reddit_post()        Reddit
score_facebook_post()      Facebook
score_pinterest_pin()      Pinterest
score_youtube_title()      YouTube (title)
score_youtube_description() YouTube (description)
score_email_subject()      Email
score_ad_copy()            Google/Meta ads
analyze_headline()         General SEO headlines
score_readability()        Flesch-Kincaid readability
```

All scorers return: `score` (0-100), `grade` (A+ through F), `breakdown` dict,
`suggestions` list.

### Quality Gate (QOps Layer)
Every scoring endpoint passes its result through `_quality_gate(score)`:

```
score >= 75  →  PASSED  +  LOW risk
score >= 55  →  REVIEW  +  MEDIUM risk
score <  55  →  FAILED  +  HIGH risk
```

This makes ContentForge actionable, not just informational.

### LLM Generation Chain
AI generation endpoints use `_llm_generate(prompt)` with this fallback chain:
1. Ollama (local, free, zero cost) — checked first
2. Gemini 2.5 Flash (Google AI Studio API key) — fallback
3. Model rotation — further fallback

If self-hosted with Ollama running, nothing leaves the machine for generation.

### Proof Dashboard (8 endpoints)
An append-only log (`proof.json`, max 5000 events) that records:
- Score deltas (before/after edits)
- Publish outcomes (engagement results)
- Revenue attribution
- Cohort benchmarks and recommendations

This closes the feedback loop: score → post → measure → improve.

### Platform Friction Monitor
`GET /v1/platform_friction` aggregates account state machine data
(ACTIVE / COOLDOWN / DEGRADED / BLOCKED / PAUSED) and returns a single
LOW / MEDIUM / HIGH friction level for the entire automation network.

---

## 3. Current State: v1.9.0, 45 Endpoints

### Heuristic Scorers (19 endpoints — instant, no AI)
- `/v1/score_content` — **primary entry point**, unified single-platform scorer
- `/v1/score_tweet`
- `/v1/score_linkedin_post`
- `/v1/score_instagram`
- `/v1/score_youtube_title`
- `/v1/score_youtube_description`
- `/v1/score_email_subject`
- `/v1/score_tiktok`
- `/v1/score_threads`
- `/v1/score_reddit` — **new in v1.9.0**
- `/v1/score_facebook`
- `/v1/score_pinterest`
- `/v1/score_ad_copy`
- `/v1/score_readability`
- `/v1/analyze_headline`
- `/v1/analyze_hashtags`
- `/v1/score_multi` — score one text across multiple platforms at once
- `/v1/batch_score` — score up to 20 drafts against one platform
- `/v1/compare` — head-to-head comparison

### Analysis & Optimization (2 endpoints)
- `/v1/ab_test`
- `/v1/compare`

### AI Generators (13 endpoints — ~1-3s, uses LLM)
- `/v1/generate_hooks`
- `/v1/rewrite`
- `/v1/compose_assist`
- `/v1/improve_headline`
- `/v1/tweet_ideas`
- `/v1/content_calendar`
- `/v1/thread_outline`
- `/v1/generate_bio`
- `/v1/generate_subject_line` — **new in v1.9.0**
- `/v1/generate_ad_copy` — **new in v1.8.0**
- `/v1/generate_caption`
- `/v1/generate_linkedin_post`
- `/v1/generate_email_sequence`
- `/v1/generate_content_brief`

### Proof Dashboard (8 endpoints)
- `/v1/record_score_delta`
- `/v1/record_publish_outcome`
- `/v1/record_revenue`
- `/v1/dashboard_stats`
- `/v1/proof_timeline`
- `/v1/export_proof_report`
- `/v1/proof_recommendations`
- `/v1/cohort_benchmarks`

### System (3 endpoints)
- `/v1/platform_friction`
- `/v1/status`
- `/health`

---

## 4. Business Context

### Revenue Model
- **Primary channel:** RapidAPI marketplace (free tier + paid tiers)
- Free tier: 30 req/min, no credit card
- RapidAPI is described by the owner as "our main money-making goal"
- Secondary: self-hosting via GitHub (AGPL-3.0 license)

### Current Launch Status (as of April 2, 2026)
- RapidAPI listing: **live**, short and long descriptions updated to v1.9.0
- Hacker News: **posted** as "Show HN: ContentForge – Content scoring API
  (42 endpoints, 12 platforms)" — https://news.ycombinator.com/item?id=47614618
- Reddit: **not yet posted** — copy-paste drafts at `docs/reddit_drafts.md`
  and `~/Desktop/ContentForge_Reddit_Posts.txt`
- Product Hunt: **draft, not yet launched** — listing exists but is not
  scheduled; description needs updating before launch
- GitHub PR #2: **open** — branch `claude/funny-yonath`
  https://github.com/CaptainFredric/ContentForge/pull/2

### Owner
- GitHub: CaptainFredric
- HN username: DanDeBugger
- The owner is a student (FES Institute, Logic coursework visible in browser)
  who is building this as a commercial side project

---

## 5. Known Weaknesses (Be Honest About These)

1. **Cold start latency:** Render free tier spins down after 15min inactivity.
   First request takes ~30s. This is a real UX problem for anyone demoing it.

2. **Rate limit resets on cold start:** In-memory rate limiting means a cold
   start effectively resets all per-IP counts. Not a security problem but
   inconsistent behavior.

3. **No persistent database:** All state is flat JSON. This works fine at low
   volume but will break under concurrent write load and has no query capability.

4. **Heuristics are educated guesses:** The scoring weights are hand-tuned, not
   empirically validated against real engagement data. The `suggestions` are
   honest but not proven. Some platforms (Pinterest, Threads) have less
   well-understood algorithms.

5. **RapidAPI is a middleman:** All revenue depends on RapidAPI's pricing
   and discovery. The API has no independent billing.

6. **Single-file Flask app:** `api_prototype.py` is ~7000 lines. This works
   but is not maintainable at scale. There is no test suite.

7. **Product Hunt draft:** The PH listing exists but is not scheduled and has
   an outdated description. The `/products/contentforge` settings hash route
   returns a 512 from PH servers, blocking edits via automation.

---

## 6. Coding Conventions (Follow These When Writing Code)

- All Flask routes follow the pattern: `@app.route("/v1/endpoint_name", ...)`
  with legacy aliases `@app.route("/endpoint-name", ...)` and
  `@app.route("/endpoint_name", ...)`
- Scorer functions are named `score_<platform>(text, ...)` and return a dict
  with at minimum: `score`, `grade`, `suggestions`, `breakdown`
- Every endpoint calls `_verify_rapidapi_request()`, `_check_rate_limit()`,
  then `_log_usage(name, ms)` before returning
- `_quality_gate(score)` is called inline before returning any scored result
- New platforms must be added to `_PLATFORM_SCORERS` dict
- Endpoint counts in docstring, `/health`, landing page badge, and both OpenAPI
  specs must all stay in sync
- Version string must be updated in: docstring, `/v1/status`, `/health`,
  landing page badge, both OpenAPI `info.version` fields, PRODUCT_OVERVIEW.md

---

## 7. Files You Need to Know

```
scripts/api_prototype.py     Main Flask app — all 45 endpoints live here
deploy/openapi.json          Full OpenAPI 3.0 spec (45 paths)
rapidapi-upload/openapi.json RapidAPI-specific OpenAPI spec (subset, 32 paths)
docs/PRODUCT_OVERVIEW.md     Complete product documentation
docs/reddit_drafts.md        Copy-paste Reddit posts (r/SideProject, r/webdev,
                             r/selfhosted)
docs/ContentForge_API_Documentation.md  User-facing API docs
.claude/launch.json          Dev server configs (ports 8080 and 8081)
```

---

## 8. What Has Been Done in This Work Session (April 2, 2026)

In chronological order:
1. Updated RapidAPI Hub Listing short description:
   "Score content before you post. 45 endpoints across 12 platforms —
   deterministic heuristics in <50ms + AI generation. Free tier, no credit card."
2. Updated RapidAPI Hub Listing long description with full v1.9.0 copy
   (endpoint table, platform list, quick start snippet)
3. Implemented `generate_ad_copy` endpoint (was documented but missing from code)
4. Added `score_content` — unified single-platform scorer (the primary entry point)
5. Added `generate_subject_line` — AI email subject line generator with scoring
6. Added `score_reddit` — Reddit-specific upvote potential scorer
7. Added Reddit to `_PLATFORM_SCORERS` (was being advertised as supported but missing)
8. Bumped version 1.7.0 → 1.8.0 → 1.9.0 across all files
9. Bumped endpoint count 42 → 44 → 45 across all files
10. Updated both OpenAPI specs (deploy/ and rapidapi-upload/)
11. Posted Show HN: https://news.ycombinator.com/item?id=47614618 (as DanDeBugger)
12. Added maker comment to HN thread explaining architecture and proof dashboard
13. Created docs/reddit_drafts.md and ~/Desktop/ContentForge_Reddit_Posts.txt
14. Cleaned up all stale version/count references in PRODUCT_OVERVIEW.md
15. All changes on branch `claude/funny-yonath`, PR #2 open

---

## 9. Immediate Next Actions (Prioritized)

1. **Merge PR #2** — all code reviewed, clean, pushed
2. **Post to Reddit** — use `~/Desktop/ContentForge_Reddit_Posts.txt`
   Post r/SideProject first, wait 45 min, post r/webdev
3. **Product Hunt** — log in, update the description (currently says
   "AI-powered multimodal content creation platform" which is wrong),
   schedule a launch date
4. **Upgrade Render tier** — free tier cold start is the #1 UX problem.
   $7/month starter tier eliminates it.
5. **Add empirical validation** — collect real engagement data to validate
   the scoring heuristics. Even 50 before/after data points would improve
   credibility significantly.
6. **Set up `gh auth login`** — `gh` is at `/opt/homebrew/bin/gh` but not
   authenticated. Run: `/opt/homebrew/bin/gh auth login`
