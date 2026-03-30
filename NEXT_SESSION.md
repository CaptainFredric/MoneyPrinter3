# Next Session Handoff — ContentForge / MoneyPrinterV2

**Last updated:** Autonomous work session (batch_score, CI, 44 promo templates)
**Repo:** https://github.com/CaptainFredric/ContentForge (branch: `main`)
**Contact email:** captainarmoreddude@gmail.com

---

## CURRENT STATE SUMMARY

Both Twitter bots are LIVE and posting. API is live on Render. This session added the
`/v1/batch_score` endpoint, GitHub Actions CI, expanded promo templates (31 → 44),
and updated the openapi.json to 28 endpoints.

---

## ACTION REQUIRED BEFORE NEXT SESSION

1. **Re-import openapi.json to RapidAPI Studio** — new batch_score endpoint needs to be visible
   - File is ready at `~/Desktop/rapidapi-upload/openapi.json`
   - Go to https://rapidapi.com/provider/studio → ContentForge → API Definition → Import
   
2. **Update RapidAPI listing short description:**
   ```
   28-endpoint content API: 16 instant heuristic scorers + 12 Gemini AI generators for Twitter,
   LinkedIn, Instagram, TikTok, YouTube, Pinterest, email & ad copy. Includes batch_score.
   ```

3. **Post the Show HN** — file at `~/Desktop/ShowHN_post.md`
   - Best window: Tuesday or Wednesday, 9–11am EST
   - Warm the server first: `curl https://contentforge-api-lpp9.onrender.com/health`

---

## What's Live and Working Right Now

| System | Status | Notes |
|---|---|---|
| **ContentForge API** | ✅ Live | `https://contentforge-api-lpp9.onrender.com` |
| **RapidAPI Listing** | ⚠️ Needs re-import for batch_score | openapi.json updated locally + on Desktop |
| **Gemini backend** | ✅ Configured | gemini-2.0-flash via Render env var |
| **Keep-warm cron** | ✅ Active | cron-job.org every 10min → /health |
| **Landing Page** | ✅ Live | `https://captainfredric.github.io/ContentForge/` |
| **Bot daemon** | ✅ Running | `money_idle_phase2.py --headless --promo-every 4` |
| **niche_launch_1** | ✅ Active, health=100 | ready-cookie-auth, posted confidence=93 |
| **EyeCatcher** | ✅ Active, health=100 | ready-cookie-auth, posted confidence=93 |
| **venv** | ✅ At ContentForge/venv/ | Python 3.14, all core deps installed |
| **config.json** | ✅ Exists | DO NOT COMMIT — .gitignore covers it |
| **.mp/twitter.json** | ✅ Exists | Both accounts, health=100 |
| **GitHub Actions CI** | ✅ Created | .github/workflows/smoke_test.yml |

---

## Complete Endpoint List — All 28

```
GET  /health                         — status, LLM backend, usage stats

# Instant scoring (no AI, <50ms, always free):
POST /v1/analyze_headline
POST /v1/score_tweet
POST /v1/score_linkedin_post
POST /v1/score_instagram
POST /v1/score_youtube_title
POST /v1/score_youtube_description
POST /v1/score_email_subject
POST /v1/score_tiktok
POST /v1/score_threads
POST /v1/score_facebook
POST /v1/score_pinterest
POST /v1/score_ad_copy
POST /v1/score_readability
POST /v1/analyze_hashtags
POST /v1/score_multi               — 12 platforms in one call
POST /v1/batch_score               — score up to 20 drafts, return best + ranked list  ← NEW

# AI generation (Gemini 2.0 Flash, ~1-3s):
POST /v1/improve_headline
POST /v1/generate_hooks
POST /v1/rewrite
POST /v1/tweet_ideas
POST /v1/content_calendar
POST /v1/thread_outline
POST /v1/generate_bio
POST /v1/generate_caption
POST /v1/generate_linkedin_post
POST /v1/generate_email_sequence
POST /v1/generate_content_brief
```

---

## Important URLs

| Resource | URL |
|---|---|
| API Base | `https://contentforge-api-lpp9.onrender.com` |
| RapidAPI Proxy | `https://contentforge1.p.rapidapi.com` |
| RapidAPI Listing | `https://rapidapi.com/captainarmoreddude/api/contentforge1` |
| RapidAPI Studio | `https://rapidapi.com/provider/studio` |
| Landing Page | `https://captainfredric.github.io/ContentForge/` |
| Render Dashboard | `https://dashboard.render.com` |

---

## File State

| File | Status | Notes |
|---|---|---|
| `scripts/api_prototype.py` | ✅ Clean | 28 endpoints, batch_score added, py_compile OK |
| `deploy/openapi.json` | ✅ Updated | 28 paths, batch_score spec, description updated |
| `~/Desktop/rapidapi-upload/openapi.json` | ✅ Ready | Copy of deploy/openapi.json for import |
| `~/Desktop/ShowHN_post.md` | ✅ Ready | Final HN post + 5 pre-written comment replies |
| `scripts/contentforge_autopilot.py` | ✅ 44 templates | +13 new covering batch_score, email, ad copy, etc. |
| `scripts/money_idle_phase2.py` | ✅ Active | --promo-every 4, promo injection wired |
| `.github/workflows/smoke_test.yml` | ✅ Created | Tests /health + score_tweet + analyze_headline + batch_score |
| `.gitignore` | ✅ Fixed | Added __pycache__/, *.pyc, *.pyo, nohup.out |
| `requirements.txt` | ✅ Py3.14 compatible | kittentts moved to requirements-youtube.txt |
| `requirements-youtube.txt` | ✅ Created | kittentts + moviepy<2.0 isolated here |
| `config.json` | ✅ Exists, gitignored | Firefox profile, ollama settings, headless=true |
| `.mp/twitter.json` | ✅ Exists, gitignored | Both accounts, health=100 |

---

## Bot Quick-Start (if daemon died)

```bash
cd /Users/erendiracisneros/Documents/GitHub/PromisesFrontend/MoneyPrinterV2/ContentForge
source venv/bin/activate
nohup python3 scripts/money_idle_phase2.py --headless --promo-every 4 > nohup.out 2>&1 &
```

Check status:
```bash
tail -20 nohup.out
python3 scripts/check_x_session.py
```

---

## Key Technical Notes

- **Base URL typo trap:** `contentforge-api-lpp9` — letter L not digit 1
- **Gemini daily quota:** 1,500 req/day. 503 RESOURCE_EXHAUSTED = wait until midnight Pacific
- **CORS:** enabled on every response — browser clients work directly
- **LLM fallback:** Gemini 2.0-flash → 2.5-flash → 2.5-flash-lite → 2.0-flash-lite → Ollama
- **RapidAPI Studios 400s:** Fixed via `_ContentForgeRequest` forcing `get_json(force=True)`
- **Python 3.14 on macOS:** kittentts/misaki won't install — use requirements-youtube.txt only for YouTube features

---

## Remaining Improvements (Priority Order)

1. Re-import openapi.json to RapidAPI (batch_score needs to be visible in Studio)
2. Post Show HN (Tuesday/Wednesday 9-11am EST)
3. Push all changes to GitHub (`git add -A && git commit -m "Add batch_score, CI, 44 promo templates" && git push`)
4. Verify GitHub Actions CI passes on push
5. Update index.html endpoint count: 27 → 28
6. Render redeploy (if not auto-deploying from push)
7. Zapier template for batch_score use case
8. Train scoring weights on real engagement data (future)

### Step 1 — Pull latest openapi.json to Desktop

```bash
curl -s "https://raw.githubusercontent.com/CaptainFredric/ContentForge/main/deploy/openapi.json" \
  -o ~/Desktop/rapidapi-upload/openapi.json
```

### Step 2 — Re-import in RapidAPI Studio

1. Go to https://rapidapi.com/provider/studio
2. Open the **ContentForge** listing
3. Click **API Definition** -> **Import API** -> upload `~/Desktop/rapidapi-upload/openapi.json`
4. Save / Publish

### Step 3 — Trigger Render deploy

Go to https://dashboard.render.com -> ContentForge -> **Manual Deploy -> Deploy latest commit**

### Step 4 — Update RapidAPI Listing Description (manual in portal)

**Short Description:**
```
27-endpoint content API: 15 instant heuristic scorers + 11 Gemini AI generators for Twitter, LinkedIn, Instagram, TikTok, YouTube, Pinterest, email & ad copy.
```

**Website URL:** `https://captainfredric.github.io/ContentForge/`

---

## What's Live and Working Right Now

The code is fixed. But you must **re-import openapi.json into RapidAPI Studio** and **re-deploy on Render** for the fixes to go live.
| System | Status | URL |
|---|---|---|
| **ContentForge API** | Live on Render | `https://contentforge-api-lpp9.onrender.com` |
| **RapidAPI Listing** | Needs re-import | openapi.json updated in repo |
| **Gemini backend** | Configured | gemini-2.0-flash via env var on Render |
| **Proxy secret** | Set | RAPIDAPI_PROXY_SECRET in Render env |
| **Keep-warm cron** | Active | cron-job.org / health every 10 min |
| **Landing Page** | Live | `https://captainfredric.github.io/ContentForge/` |

---

## What Was Fixed This Session (Phase 5)

### 1. Root cause of ALL 400 errors -- FIXED

Every endpoint used `request.get_json(silent=True) or {}`. Flask returns `None` when
`Content-Type: application/json` is missing -- which RapidAPI Studio sometimes omits.
Result: empty payload -> required fields missing -> 400.

**Fix** (`scripts/api_prototype.py` -- right after `app = Flask(__name__)`):

```python
from flask import Request as _FlaskRequest

class _ContentForgeRequest(_FlaskRequest):
    def get_json(self, force=False, silent=False, cache=True):
        return super().get_json(force=True, silent=silent, cache=cache)

app.request_class = _ContentForgeRequest
```

One class, fixes all 27 endpoints at once.

### 2. Missing OpenAPI body examples -- FIXED

`generate_bio` and `thread_outline` lacked a top-level `example` in their `requestBody`.
RapidAPI Studio reads this to pre-populate the test body form. Both now have proper examples
in `deploy/openapi.json`.

### 3. openapi.json info section -- UPDATED

- `info.description` -- now lists all 27 endpoints by name and category
- `info.contact.url` -- landing page URL added
- `externalDocs` -- landing page link added
- `termsOfService` -- set to landing page

### 4. score_multi now includes readability

Added `"readability"` to `_PLATFORM_SCORERS` dict. Supports 12 platforms:
tweet, twitter, linkedin, instagram, tiktok, threads, facebook,
pinterest, youtube, youtube_description, email, readability

---

## Complete Endpoint List -- All 27

```
GET  /health                       -- status, LLM backend, usage stats

# Instant scoring (no AI, <50ms):
POST /v1/analyze_headline
POST /v1/score_tweet
POST /v1/score_linkedin_post
POST /v1/score_instagram
POST /v1/score_youtube_title
POST /v1/score_youtube_description
POST /v1/score_email_subject
POST /v1/score_tiktok
POST /v1/score_threads
POST /v1/score_facebook
POST /v1/score_pinterest
POST /v1/score_ad_copy
POST /v1/score_readability
POST /v1/analyze_hashtags
POST /v1/score_multi               -- 12 platforms in one call

# AI generation (Gemini 2.0 Flash):
POST /v1/improve_headline
POST /v1/generate_hooks
POST /v1/rewrite
POST /v1/tweet_ideas
POST /v1/content_calendar
POST /v1/thread_outline
POST /v1/generate_bio
POST /v1/generate_caption
POST /v1/generate_linkedin_post
POST /v1/generate_email_sequence
POST /v1/generate_content_brief
```

**Key notes:**
- Base URL: `contentforge-api-lpp9.onrender.com` -- letter L not digit 1
- Gemini daily quota: 1,500 req/day. 503 RESOURCE_EXHAUSTED = wait until midnight Pacific
- CORS on every response -- browser clients work directly
- LLM fallback: Gemini 2.0-flash -> 2.5-flash -> 2.5-flash-lite -> 2.0-flash-lite -> Ollama

---

## Important URLs

| Resource | URL |
|---|---|
| API Base | `https://contentforge-api-lpp9.onrender.com` |
| RapidAPI Proxy | `https://contentforge1.p.rapidapi.com` |
| RapidAPI Listing | `https://rapidapi.com/captainarmoreddude/api/contentforge1` |
| RapidAPI Studio | `https://rapidapi.com/provider/studio` |
| Landing Page | `https://captainfredric.github.io/ContentForge/` |
| Render Dashboard | `https://dashboard.render.com` |

---

## File State

| File | Notes |
|---|---|
| `scripts/api_prototype.py` | ForceJSON fix + readability in score_multi |
| `deploy/openapi.json` | Full description + 2 missing requestBody examples |
| `index.html` | All 27 endpoint cards present, correct stats |

---

## Next Improvements

1. Verify 400 fix -- test generate_bio, thread_outline, score_tweet in RapidAPI Studio after re-import
2. Set up RapidAPI pricing tiers -- FREE/PRO/ULTRA/MEGA plans in portal
3. Post on Indie Hackers / r/SideProject
4. Add /v1/batch_score endpoint
5. GitHub Actions CI -- smoke test on push

---

## Twitter Bot State

| Account | State |
|---|---|
| niche_launch_1 (NicheNewton) | active |
| EyeCatcher | active |

```bash
source .runtime-venv/bin/activate
python3 scripts/smart_post_twitter.py --headless
python3 scripts/contentforge_autopilot.py --verify
```

---

## What's Live and Working Right Now

| System | Status | URL / Path |
|---|---|---|
| **ContentForge API** | ✅ Live (deploying b697c19) | `https://contentforge-api-lpp9.onrender.com` |
| **RapidAPI Listing** | ⚠️ Needs re-import | 22 endpoints in spec — re-import `deploy/openapi.json` |
| **Gemini backend** | ✅ Configured | `gemini-2.0-flash` via env var on Render |
| **Proxy secret** | ✅ Set | `RAPIDAPI_PROXY_SECRET` in Render env |
| **Keep-warm cron** | ✅ Active | cron-job.org, every 10 min → `/health` |
| **Twitter: niche_launch_1** | ✅ Active | Firefox Dev profile |
| **Twitter: EyeCatcher** | ✅ Active | Firefox regular profile |
| **Ollama local** | ✅ Running | `llama3.2:3b` at `http://127.0.0.1:11434` |

### Step 1 — Pull latest openapi.json to Desktop

```bash
curl -s "https://raw.githubusercontent.com/CaptainFredric/ContentForge/main/deploy/openapi.json" \
  -o ~/Desktop/rapidapi-upload/openapi.json
```

### Step 2 — Re-import in RapidAPI Studio

1. Go to [https://rapidapi.com/provider/studio](https://rapidapi.com/provider/studio)
2. Open the **ContentForge** listing
3. Click **API Definition** → **Import API** → upload `~/Desktop/rapidapi-upload/openapi.json`
4. Save / Publish

### Step 3 — Trigger Render deploy

Go to [https://dashboard.render.com](https://dashboard.render.com) → ContentForge → **Manual Deploy → Deploy latest commit**

(Or wait — if Render is auto-deploy on push, it should pick up the last commit automatically.)

### Step 4 — Update RapidAPI Listing Description (manual in portal)

**Short Description:**
```
27-endpoint content API: 15 instant heuristic scorers + 11 Gemini AI generators for Twitter, LinkedIn, Instagram, TikTok, YouTube, Pinterest, email & ad copy.
```

**Website URL:** `https://captainfredric.github.io/ContentForge/`

**Long Description** — copy from `docs/RapidAPI_LongDescription.md` or use this:
```markdown
# ContentForge — AI Content Scoring & Generation API

Score and generate content for every major platform in seconds.

## ⚡ Instant Scorers (15 endpoints — zero latency, no AI cost)
- analyze_headline, score_tweet, score_linkedin_post, score_instagram
- score_youtube_title, score_youtube_description, score_email_subject
- score_tiktok, score_threads, score_facebook, score_pinterest, score_ad_copy
- score_readability, analyze_hashtags, score_multi

## ✦ AI Generators (11 endpoints — Gemini 2.0 Flash)
- improve_headline, generate_hooks, rewrite, tweet_ideas, content_calendar
- thread_outline, generate_bio, generate_caption, generate_linkedin_post
- generate_email_sequence, generate_content_brief

**CORS enabled · Rate limit headers on every response · <50ms for instant endpoints**
```

---

## What's Live and Working Right Now

| System | Status | URL / Path |
|---|---|---|
| **ContentForge API** | ✅ Live on Render | `https://contentforge-api-lpp9.onrender.com` |
| **RapidAPI Listing** | ⚠️ Needs re-import | openapi.json updated in repo — re-import required |
| **Gemini backend** | ✅ Configured | `gemini-2.0-flash` via env var on Render |
| **Proxy secret** | ✅ Set | `RAPIDAPI_PROXY_SECRET` in Render env |
| **Keep-warm cron** | ✅ Active | cron-job.org → `/health` every 10 min |
| **Landing Page** | ✅ Live | `https://captainfredric.github.io/ContentForge/` |

---

## What Was Fixed This Session (Phase 5)

### 1. Root cause of ALL 400 errors — FIXED

Every endpoint used `request.get_json(silent=True) or {}`. Flask returns `None` when `Content-Type: application/json` is missing from the request — which RapidAPI Studio sometimes omits during testing. Result: empty payload → required fields missing → 400.

**Fix** (`scripts/api_prototype.py` — right after `app = Flask(__name__)`):
```python
from flask import Request as _FlaskRequest

class _ContentForgeRequest(_FlaskRequest):
    """Override get_json so it always uses force=True."""
    def get_json(self, force: bool = False, silent: bool = False, cache: bool = True):
        return super().get_json(force=True, silent=silent, cache=cache)

app.request_class = _ContentForgeRequest
```

One class, fixes all 27 endpoints at once.

### 2. Missing OpenAPI body examples — FIXED

`generate_bio` and `thread_outline` lacked a top-level `example` in their `requestBody`. RapidAPI Studio reads this to pre-populate the test body form. Without it, users submitted empty bodies → 400.

Now both have proper examples in `deploy/openapi.json`.

### 3. openapi.json info section — UPDATED

- `info.description` — now lists all 27 endpoints by name and category
- `info.contact.url` — landing page URL added
- `externalDocs` — landing page link added
- `termsOfService` — set to landing page

### 4. `score_multi` now includes readability

Added `"readability"` to `_PLATFORM_SCORERS` dict. `score_multi` now supports 12 platforms:
```
tweet, twitter, linkedin, instagram, tiktok, threads, facebook,
pinterest, youtube, youtube_description, email, readability
```

---

## Complete Endpoint List — All 27

```
GET  /health                       → status, LLM backend, usage stats

# ⚡ Instant scoring (no AI, <50ms):
POST /v1/analyze_headline          → score 0-100 + grade + power words
POST /v1/score_tweet               → Twitter/X engagement score
POST /v1/score_linkedin_post       → LinkedIn reach score
POST /v1/score_instagram           → Instagram caption score
POST /v1/score_youtube_title       → YouTube CTR score + thumbnail check
POST /v1/score_youtube_description → YouTube description SEO score      ← added phase 4
POST /v1/score_email_subject       → email subject open-rate score
POST /v1/score_tiktok              → TikTok viral-potential score
POST /v1/score_threads             → Meta Threads reach score
POST /v1/score_facebook            → Facebook organic reach score
POST /v1/score_pinterest           → Pinterest pin discoverability score  ← added phase 4
POST /v1/score_ad_copy             → Google/Meta ad copy CTR score        ← added phase 4
POST /v1/score_readability         → Flesch-Kincaid grade level and ease
POST /v1/analyze_hashtags          → hashtag quality + spam risk + fit
POST /v1/score_multi               → 12 platforms in one call

# ✦ AI generation (Gemini 2.0 Flash):
POST /v1/improve_headline          → N AI-rewritten headlines (scored)
POST /v1/generate_hooks            → scroll-stopping hooks for any topic
POST /v1/rewrite                   → rewrite for any platform + tone
POST /v1/tweet_ideas               → tweet batch for any niche
POST /v1/content_calendar          → 7-day content calendar
POST /v1/thread_outline            → full Twitter thread (hook + body + CTA)
POST /v1/generate_bio              → social bio (twitter/linkedin/instagram)
POST /v1/generate_caption          → Instagram or TikTok caption
POST /v1/generate_linkedin_post    → full LinkedIn post
POST /v1/generate_email_sequence   → 3-email drip sequence                ← added phase 4
POST /v1/generate_content_brief    → research brief (outline/keywords/CTAs) ← added phase 4
```

**Key notes:**
- Base URL: `contentforge-api-lpp9.onrender.com` — **letter L** not digit 1
- Free tier Render → 50s cold start after 15 min idle (keep-warm cron active)
- Gemini daily quota: 1,500 req/day. If you see `503 RESOURCE_EXHAUSTED`, wait until midnight Pacific
- CORS headers on every response — browser clients work directly
- LLM fallback chain: Gemini 2.0 Flash → 2.5 Flash → 2.5 Flash Lite → 2.0 Flash Lite → Ollama

---

## Important URLs

| Resource | URL |
|---|---|
| API Base | `https://contentforge-api-lpp9.onrender.com` |
| RapidAPI Proxy | `https://contentforge1.p.rapidapi.com` |
| RapidAPI Listing | `https://rapidapi.com/captainarmoreddude/api/contentforge1` |
| RapidAPI Studio | `https://rapidapi.com/provider/studio` |
| Landing Page | `https://captainfredric.github.io/ContentForge/` |
| Render Dashboard | `https://dashboard.render.com` |
| GitHub Repo | `https://github.com/CaptainFredric/ContentForge` |

---

## File State

| File | State | Notes |
|---|---|---|
| `scripts/api_prototype.py` | ✅ Updated | ForceJSON fix + readability in score_multi |
| `deploy/openapi.json` | ✅ Updated | Full description + 2 missing examples fixed |
| `index.html` | ✅ Up to date | All 27 endpoint cards present, correct stats |
| `scripts/contentforge_autopilot.py` | ✅ Unchanged | 36 templates, avg 74.7 score |

---

## Next Improvements (Priority Order)

### High Priority — after re-import confirms 400s are resolved
1. **Verify 400 fix** — test `generate_bio`, `thread_outline`, `score_tweet` in RapidAPI Studio after re-import
2. **Set up RapidAPI pricing tiers** — FREE/PRO/ULTRA/MEGA plans in portal (gateway-level rate limits)
3. **Monitor cold starts** — Render free tier sleeps after 15 min; confirm cron-job.org pinger is still active

### Medium Priority
4. **Add `score_ad_copy` to `score_multi`** — currently excluded; could treat `text` as headline + empty description
5. **Post on Indie Hackers / r/SideProject** — "Show HN: ContentForge — free API 27 endpoints, 8 platforms"
6. **Update score_multi openapi.json docs** — add `readability` to available_platforms list in spec description

### Low Priority
7. **`/v1/batch_score`** — Score an array of texts against one platform (useful for A/B testing variations)
8. **Async mode for AI endpoints** — Webhook callback for endpoints that take >2s
9. **GitHub Actions CI** — Smoke test on push, alert on regression

---

## How to Run the API Locally

```bash
# From project root
source venv/bin/activate
cd scripts && python api_prototype.py

# Server starts at http://localhost:5050

# Run built-in smoke tests
python api_prototype.py --test
```

---

## Twitter Bot State

| Account | State |
|---|---|
| niche_launch_1 (NicheNewton) | active, posting ContentForge promo |
| EyeCatcher | active, posting ContentForge promo |

```bash
source .runtime-venv/bin/activate

# Single smart post (picks best account)
python3 scripts/smart_post_twitter.py --headless

# Verify autopilot templates all score 70+
python3 scripts/contentforge_autopilot.py --verify
```
