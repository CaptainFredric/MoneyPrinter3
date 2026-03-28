# Next Session Handoff — ContentForge / MoneyPrinterV2

**Last updated:** March 28, 2026  
**Repo:** https://github.com/CaptainFredric/MoneyPrinter3 (branch: `main`, HEAD: `b4224f8`)  
**Contact email:** captainarmoreddude@gmail.com

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
