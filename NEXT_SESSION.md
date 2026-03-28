# Next Session Handoff — ContentForge / MoneyPrinterV2

**Last updated:** March 28, 2026 (session 3)
**Repo:** https://github.com/CaptainFredric/MoneyPrinter3 (branch: `main`, HEAD: `30be366`)
**Contact email:** captainarmoreddude@gmail.com

---

## What's Live and Working Right Now

| System | Status | URL / Path |
|---|---|---|
| **ContentForge API** | ✅ Live | `https://contentforge-api-lpp9.onrender.com` |
| **RapidAPI Listing** | ✅ Public | All 7 endpoints, 4-tier pricing active |
| **Gemini backend** | ✅ Configured | `gemini-2.0-flash` via env var on Render |
| **Proxy secret** | ✅ Set | `RAPIDAPI_PROXY_SECRET` in Render env |
| **Keep-warm cron** | ✅ Active | cron-job.org, every 10 min → `/health` |
| **Twitter: niche_launch_1** | ✅ Active | health=50, 3 posts today, Firefox Dev profile |
| **Twitter: EyeCatcher** | ✅ Active | health=100, 2 posts today, Firefox regular profile |
| **Ollama local** | ✅ Running | `llama3.2:3b` at `http://127.0.0.1:11434` |
| **Legal docs** | ✅ Done | `docs/TERMS_OF_USE.md`, `docs/TERMS_AND_CONDITIONS.md` |

---

## API Endpoints — All 7 Live

```
GET  /health                   → service status, LLM backend, usage stats
POST /v1/analyze_headline      → instant score 0-100 + grade + suggestions (no AI)
POST /v1/score_tweet           → instant tweet draft scorer 0-100 + grade (no AI) ← NEW
POST /v1/generate_hooks        → AI viral hooks for any topic
POST /v1/rewrite               → AI rewrite for twitter/linkedin/email/blog
POST /v1/tweet_ideas           → AI tweet ideas + hashtags for any niche
POST /v1/content_calendar      → AI 7-day content calendar ← NEW
```

**Key notes:**
- Base URL: `contentforge-api-lpp9.onrender.com` — **letter L** not digit 1
- Free tier Render → 50s cold start after 15 min idle (keep-warm cron prevents this)
- Gemini daily quota: 1,500 req/day. If you see `503 RESOURCE_EXHAUSTED`, wait until midnight Pacific
- CORS headers added — browser clients (RapidAPI playground, web apps) work directly

---

## What Was Done This Session (March 28, 2026)

### New Features Added
1. **`POST /v1/score_tweet`** — Heuristic tweet scorer (instant, no AI). Scores 0-100, grade A-D, checks char count, hashtags, emojis, power words, readability. Live on production.
2. **`POST /v1/content_calendar`** — AI-powered 7-day content calendar. Accepts niche, days(1-7), platform, tone. Returns themes + ready-to-post drafts. Live on production.
3. **CORS headers** — Added `Access-Control-Allow-*` headers + OPTIONS handler so browser clients and the RapidAPI playground work perfectly.
4. **Enhanced power word set** — 60+ power words vs. 23 before. The analyzer now catches "income", "boost", "blueprint", "shortcut", etc.
5. **`/health` improvements** — Now returns `total_requests_served` + per-endpoint usage counts.
6. **`/` root** — Now lists all 7 endpoints + RapidAPI link.

### New Scripts
7. **`scripts/promo_contentforge.py`** — Dogfood promo script. Uses ContentForge API (local Ollama for generation, score_tweet for ranking) to generate and post the highest-scoring tweet from any account. Usage: `python scripts/promo_contentforge.py --headless`
8. **`scripts/system_dashboard.py`** — Single-pane dashboard: API health, Twitter account states, usage stats, and quick action commands.

### Docs Updated
9. **`docs/ContentForge_API_Documentation.md`** — Full API docs with all 7 endpoints, parameters, examples, error codes, pricing table. Ready to paste into RapidAPI's documentation tab.
10. **`docs/promo_posts.md`** — Updated with 2 new promo options for `score_tweet` and `content_calendar`.
11. **`docs/bot_content_templates.md`** — Added tweet templates for the new endpoints.
12. **`scripts/update_topics.py`** — Updated bot topics to mention all 6 API capabilities.

### Bug Fixes
13. **`deploy/openapi.json`** — Fixed contact email (`alt550458@gmail.com` → `captainarmoreddude@gmail.com`).
14. **`deploy/openapi.json`** — New description mentions all 6 endpoints including `score_tweet` and `content_calendar`.

---

## RapidAPI Listing State

- Pricing tiers: BASIC (free), PRO ($9.99), ULTRA ($29.99), MEGA ($99)
- The listing currently shows 5 endpoints (the 2 new ones need to be re-imported via openapi.json)
- **NEXT ACTION**: Go to RapidAPI → My APIs → ContentForge → Endpoints → Import → upload updated `deploy/openapi.json` to add `score_tweet` and `content_calendar` endpoints
- Terms of Use: done ✅
- Health check URL: `https://contentforge-api-lpp9.onrender.com/health`

---

## Twitter Bot State

| Account | Posts Today | Total | Health | State |
|---|---|---|---|---|
| niche_launch_1 (NicheNewton) | 2 | 3 | 50 | active |
| EyeCatcher | 2 | 2 | 100 | active |

**Cooldown:** Both accounts have ~30 min cooldown between posts. Run bots again after 16:34 UTC today.

Run commands:
```bash
source .runtime-venv/bin/activate

# Single smart post (picks best account)
python3 scripts/smart_post_twitter.py --headless

# ContentForge promo post (scores tweets, picks the best one)
python3 scripts/promo_contentforge.py --headless

# System dashboard (see all system health at once)
python3 scripts/system_dashboard.py

# Performance report
python3 scripts/performance_report.py
```

---

## What Still Needs Doing (Priority Order)

### 1. Re-import openapi.json to RapidAPI (manual, 5 min)
- Go to RapidAPI → My APIs → ContentForge → Endpoints
- Click "Import OpenAPI" → upload `deploy/openapi.json`
- This will add the 2 new endpoints (`score_tweet`, `content_calendar`) to the listing

### 2. Add API Documentation on RapidAPI (manual, 5 min)
- Go to RapidAPI → My APIs → ContentForge → Documentation
- Paste the content from `docs/ContentForge_API_Documentation.md`
- This fills the "Documentation is not set" warning on the listing

### 3. Tweet actively to grow both accounts
- Both bots are active and healthy
- Run `python3 scripts/smart_post_twitter.py --headless` periodically
- Or use the VS Code task: **Twitter: Smart Post (Headless)**
- Run `python3 scripts/promo_contentforge.py --headless` for ContentForge-specific promo posts
- Goal: 10+ posts per account over next few days

### 4. Post to your personal account about ContentForge
- Use options from `docs/promo_posts.md`
- Thread format (Option A) or single tweet (Options B-F)
- Target: Indie Hackers, Hacker News, developer Twitter

### 5. Submit to Indie Hackers + Hacker News
- Hacker News: "Show HN: ContentForge — free API to score headlines and tweet drafts instantly"
- Indie Hackers: post in "What did you launch this week?" thread
- This is the #1 driver of first subscribers

### 6. Upgrade Render when you get first paying subscriber
- Render Starter = $7/mo → always-on (no cold starts)
- One PRO subscriber ($9.99) covers it

### 7. Add a `POST /v1/improve_headline` endpoint (future)
- Takes a headline, returns 3 rewritten versions (AI-powered)
- Complements `analyze_headline` perfectly (analyze → improve cycle)

---

## Key Files Reference

| File | Purpose |
|---|---|
| `scripts/api_prototype.py` | ContentForge Flask API (7 endpoints, CORS, rate limiting, proxy validation) |
| `scripts/system_dashboard.py` | Single-pane health dashboard ← NEW |
| `scripts/promo_contentforge.py` | Dogfood promo tweet generator using ContentForge API ← NEW |
| `deploy/wsgi.py` | WSGI entry point for Render |
| `deploy/openapi.json` | OpenAPI 3.0.3 spec — import into RapidAPI (updated with 2 new endpoints) |
| `deploy/render.yaml` | Render Blueprint — 1 worker, all env vars defined |
| `docs/ContentForge_API_Documentation.md` | Full API docs — paste into RapidAPI ← NEW |
| `docs/promo_posts.md` | Promotional tweet templates (updated) |
| `docs/bot_content_templates.md` | Content templates for the bots (updated) |
| `scripts/update_topics.py` | Sync bot topics with ContentForge funnel (updated) |
| `.mp/twitter.json` | Account cache + post history |
| `.mp/runtime/account_states.json` | Live state machine state |
| `docs/TERMS_OF_USE.md` | Terms for RapidAPI |

---

## VS Code Tasks Available

Open Command Palette → "Tasks: Run Task":

- **ContentForge: System Dashboard** ← NEW — see everything at once
- **ContentForge: Promo Post (Best Account)** ← NEW — dogfood promo tweet
- **ContentForge: Promo Post Dry Run** ← NEW — test without posting
- **ContentForge: API Health Check** ← NEW — quick curl health
- **Twitter: Smart Post (Headless)** — post once
- **Twitter: Performance Report** ← NEW — growth scoreboard
- **Twitter: Readiness Report** — check account health
- **Twitter: Backfill niche_launch_1** — retry failed posts
- **Twitter: Backfill EyeCatcher** — retry failed posts
- **Twitter: Verify Phase3 niche_launch_1** — verify recent posts published
- **Twitter: Verify Phase3 EyeCatcher** — verify recent posts published
- **Twitter: Session Restore (All)** — refresh Firefox cookies

---

## Gemini Quota Status

- Daily free limit: 1,500 requests/day
- Resets: midnight Pacific time
- If `503 RESOURCE_EXHAUSTED` appears: AI endpoints return 503 (heuristic endpoints still work!)
- `analyze_headline` and `score_tweet` are **100% instant, no Gemini quota** — they work always

---

_Updated by GitHub Copilot at end of session. Date: 2026-03-28_


---

## What's Live and Working Right Now

| System | Status | URL / Path |
|---|---|---|
| **ContentForge API** | ✅ Live | `https://contentforge-api-lpp9.onrender.com` |
| **RapidAPI Listing** | ✅ Public | All 5 endpoints, 4-tier pricing active |
| **Gemini backend** | ✅ Configured | `gemini-2.0-flash` via env var on Render |
| **Proxy secret** | ✅ Set | `RAPIDAPI_PROXY_SECRET` in Render env |
| **Keep-warm cron** | ✅ Active | cron-job.org, every 10 min → `/health` |
| **Twitter: niche_launch_1** | ✅ Active | health=50, 2 verified posts, Firefox Dev profile |
| **Twitter: EyeCatcher** | ✅ Active | health=100, 1 verified post, Firefox regular profile |
| **Ollama local** | ✅ Running | `llama3.2:3b` at `http://127.0.0.1:11434` |
| **Legal docs** | ✅ Done | `docs/TERMS_OF_USE.md`, `docs/TERMS_AND_CONDITIONS.md` |

---

## API Endpoints (All Verified Working)

```
GET  /health                → {"status":"ok","llm_backend":"gemini","ai_endpoints_ready":true}
POST /v1/analyze_headline   → instant, no AI, score 0-100 + grade A-D + suggestions
POST /v1/generate_hooks     → Gemini, hooks for a topic, viral/professional/casual styles
POST /v1/rewrite            → Gemini, rewrite for twitter/linkedin/email/blog
POST /v1/tweet_ideas        → Gemini, tweet ideas with hashtags for any niche
```

Critical notes:
- Base URL is `contentforge-api-lpp9.onrender.com` — **letter L** not digit 1
- Render is on free tier → 50s cold start after 15 min idle (keep-warm cron prevents this)
- Gemini daily quota: 1,500 free req/day. If you see `503 RESOURCE_EXHAUSTED`, wait until midnight Pacific or enable billing at https://aistudio.google.com

---

## RapidAPI Listing State

- Pricing tiers: BASIC (free), PRO ($9.99), ULTRA ($29.99), MEGA ($99)
- AI Objects quotas: 50 / 750 / 3,000 / 18,000 per month
- Terms of Use: paste content from `docs/TERMS_OF_USE.md` into RapidAPI → General → Terms of Use (if not done yet)
- Health check URL on RapidAPI: `https://contentforge-api-lpp9.onrender.com/health` (not `/ping`)

---

## Twitter Bot State

Accounts (`.mp/twitter.json`):

| Account | Internal UUID | Firefox Profile | Posts | Health |
|---|---|---|---|---|
| niche_launch_1 (NicheNewton) | `9b3eb949-...` | `3867tdvq.dev-edition-default-1` | 2 verified | 50 |
| EyeCatcher | `d8dbc044-...` | `jtgCLZXw.Profile 2` | 1 verified | 100 |

State machine: `.mp/runtime/account_states.json`
- Both accounts: `state=active`
- EyeCatcher last confirmed: `posted:confidence=93:level=high`

Run bots:
```bash
# One-shot smart post (picks best account)
source .runtime-venv/bin/activate
python3 scripts/smart_post_twitter.py --headless

# Continuous idle mode
python3 scripts/money_idle_phase2.py

# Backfill failed posts
python3 scripts/backfill_pending_twitter.py --headless niche_launch_1
```

---

## Render Environment Variables (All Set)

```
GEMINI_API_KEY      = AIza...  (configured — do not commit to repo)
GEMINI_MODEL        = gemini-2.0-flash
PYTHONPATH          = /opt/render/project/src
RAPIDAPI_PROXY_SECRET = ade9a690-2a05-11f1-89f7-d78cc526f9aa
```

---

## Local Python Environment

- Virtual env: `.runtime-venv/` (NOT `venv/` — all scripts prefer `.runtime-venv`)
- Activate: `source .runtime-venv/bin/activate`
- Run preflight: `python3 scripts/preflight_local.py`
- Expected result: `Preflight passed. Local setup looks ready.` (2 warnings OK: firefox_profile default, gemini key missing locally)

---

## Recent Commits (Most Recent First)

```
b4224f8  Remove disruptive chat image: contentforge_logo_500x500.png
43cba01  new
0c9aea0  Update contact email in Terms files (use captainarmoreddude@gmail.com)
dedef90  Add Terms & Conditions (docs/TERMS_AND_CONDITIONS.md)
3095e7f  Add Terms of Use (docs/TERMS_OF_USE.md)
73f4c86  Fix openapi.json: remove securitySchemes + root security (caused RapidAPI upload rejection)
755b3d6  Fix openapi.json: add body-level examples with count:5 (fixes count:0 validation error)
284b251  Fix preflight: Gemini key not blocking when Ollama available
49cc2f7  Fix daemon venv path: prefer .runtime-venv over legacy venv
8500fc9  Update docs: correct live URL (lpp9), Gemini quota troubleshooting
```

---

## What Still Needs Doing (Priority Order)

### 1. Paste Terms of Use into RapidAPI (manual, 2 min)
- Go to RapidAPI → My APIs → ContentForge → General
- Scroll to "Terms of Use" field
- Paste text from `docs/TERMS_OF_USE.md` (skip the first "Note:" line at the bottom)

### 2. Test a live RapidAPI subscriber call (manual, 5 min)
- Go to RapidAPI → My APIs → ContentForge → Testing tab
- Test `analyzeHeadline` with any headline text
- Confirm you get a 200 response (proves proxy secret is working end-to-end)

### 3. Set up promotions for the API listing
- Tweet about ContentForge from NicheNewton/EyeCatcher accounts
- Share the RapidAPI listing URL
- Consider posting to: Hacker News "Show HN", Indie Hackers, Product Hunt

### 4. Upgrade Render when you get first paying subscriber
- Render Starter = $7/mo → always-on (no cold starts)
- One PRO subscriber ($9.99) covers it

### 5. YouTube Shorts pipeline (optional)
- Not yet running. Would expand content + add additional revenue stream.
- Config: `config.json` → `youtube_*` fields
- Run: `python3 src/main.py` → YouTube menu

---

## Key Files Reference

| File | Purpose |
|---|---|
| `scripts/api_prototype.py` | ContentForge Flask API (all 5 endpoints, rate limiting, proxy validation) |
| `deploy/wsgi.py` | WSGI entry point for Render |
| `deploy/openapi.json` | OpenAPI 3.0.3 spec — import this to RapidAPI |
| `deploy/render.yaml` | Render Blueprint — 1 worker, all env vars defined |
| `src/classes/Twitter.py` | Tweet generation + Selenium posting |
| `src/account_state_machine.py` | Health scoring, state transitions |
| `scripts/smart_post_twitter.py` | Headless post script used by VS Code tasks |
| `.mp/twitter.json` | Account cache + post history |
| `.mp/runtime/account_states.json` | Live state machine state |
| `docs/TERMS_OF_USE.md` | Terms to paste into RapidAPI |
| `docs/ContentForge_Deploy.md` | Full deploy + publish guide |

---

## VS Code Tasks Available

Open Command Palette → "Tasks: Run Task":

- **Twitter: Smart Post (Headless)** — post once
- **Twitter: Backfill niche_launch_1** — retry failed posts
- **Twitter: Backfill EyeCatcher** — retry failed posts
- **Twitter: Readiness Report** — check account health
- **Twitter: Verify Phase3 niche_launch_1** — verify recent posts published
- **Twitter: Verify Phase3 EyeCatcher** — verify recent posts published
- **Twitter: Session Restore (All)** — refresh Firefox cookies

---

_This file is auto-generated by the handoff process. Update it at the end of each session._
