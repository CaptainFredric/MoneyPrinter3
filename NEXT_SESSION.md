# Next Session Handoff — ContentForge / MoneyPrinterV2

**Last updated:** Phase 5 session (RapidAPI 400-fix + openapi.json update)
**Repo:** https://github.com/CaptainFredric/ContentForge (branch: `main`)
**Contact email:** captainarmoreddude@gmail.com

---

## CRITICAL USER ACTION REQUIRED BEFORE ANYTHING ELSE

The code is fixed. But you must **re-import openapi.json into RapidAPI Studio** and **re-deploy on Render** for the fixes to go live.

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

---

## API Endpoints — All 22 (12 instant + 9 AI + health)

```
GET  /health                       → service status, LLM backend, usage stats

# Instant scoring (no AI, <5ms):
POST /v1/analyze_headline          → score + grade + suggestions (0-100)
POST /v1/score_tweet               → tweet scorer (0-100)
POST /v1/score_linkedin_post       → LinkedIn post scorer (0-100)
POST /v1/score_instagram           → Instagram caption scorer (0-100)
POST /v1/score_youtube_title       → YouTube title CTR scorer (0-100)
POST /v1/score_email_subject       → email subject line scorer (0-100)
POST /v1/score_multi               → 8 platforms in one call (tweet/linkedin/instagram/tiktok/threads/facebook/youtube/email)
POST /v1/score_readability         → Flesch-Kincaid readability (0-100)
POST /v1/score_tiktok              → TikTok caption scorer (0-100)
POST /v1/analyze_hashtags          → hashtag quality + spam risk + platform fit
POST /v1/score_threads             → Meta Threads scorer (hashtags/links penalize) ← Session 6
POST /v1/score_facebook            → Facebook organic post scorer (1-2 hashtags OK) ← Session 6

# AI generation (Gemini 2.0 Flash):
POST /v1/improve_headline          → N AI-rewritten headlines (scored)
POST /v1/generate_hooks            → viral hooks for any topic
POST /v1/rewrite                   → rewrite for twitter/linkedin/instagram/tiktok/email/blog
POST /v1/tweet_ideas               → tweet ideas for any niche
POST /v1/content_calendar          → 7-day content calendar
POST /v1/thread_outline            → Twitter thread outline (hook + body + CTA)
POST /v1/generate_bio              → social bio for twitter/linkedin/instagram
POST /v1/generate_caption          → Instagram or TikTok caption
POST /v1/generate_linkedin_post    → full LinkedIn post (storytelling/professional/motivational)
```

**Key notes:**
- Base URL: `contentforge-api-lpp9.onrender.com` — **letter L** not digit 1
- Free tier Render → 50s cold start after 15 min idle (keep-warm cron prevents this)
- Gemini daily quota: 1,500 req/day. If you see `503 RESOURCE_EXHAUSTED`, wait until midnight Pacific
- CORS headers added — browser clients work directly
- 3-layer LLM fallback: `llm_provider.generate_text` → direct Ollama → direct Gemini

---

## What Was Done This Session (March 29, 2026 — Session 6)

### New Endpoints (2)
1. **`POST /v1/score_threads`** — Meta Threads-specific scorer. Threads rewards conversational tone (50-250 chars), personal pronouns (+6), questions (+10), CTA like "agree/thoughts" (+7). Unique rule: hashtags PENALIZE (-3 for 1, -5 each for 2+), links penalize (-6). 16-field response, smoke-tested 82/B.
2. **`POST /v1/score_facebook`** — Facebook organic post scorer. Rewards 40-300 char posts, 1-2 hashtags (+5), emojis (+8), question (+8), CTA share/comment/tag (+7). Links mild penalty (-3). 16-field response, smoke-tested 86/B.

### Improvements
3. **`/v1/score_multi`**: Now supports 8 platforms (added threads + facebook). Covers all major social networks.
4. **Landing page**: Updated badge (22), stats (22/12/9), heading "All 22 Endpoints", section sub, endpoint cards for threads + facebook, FAQ updated (12 instant list, 8 platforms), meta/og/twitter card descriptions updated with Threads + Facebook.
5. **OpenAPI**: score_threads + score_facebook specs added (22 paths).
6. **Autopilot**: 34 → 36 templates. threads_scorer_intro (72/B) + facebook_scorer_intro (75/B). All 36/36 verified 70+, avg 74.7.

### Commits
- `937b0e7`: Landing page corrections + NEXT_SESSION.md (prior session, already live)
- `d1ae169`: score_threads endpoint (21 total) ← live at time of writing
- `b697c19`: score_facebook + meta/FAQ fixes (22 total) ← deploying

---

## Immediate Next Priorities

### 1. RapidAPI Re-Import (5 min)
OpenAPI spec now has 22 paths. Re-import `deploy/openapi.json` at RapidAPI dashboard to update the listing.
URL: https://rapidapi.com/provider — select ContentForge → Update API → Upload spec

### 2. Verify score_facebook Live
```bash
curl -s https://contentforge-api-lpp9.onrender.com/ | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d['endpoints']), 'endpoints')"
# Should print: 22 endpoints

curl -s -X POST https://contentforge-api-lpp9.onrender.com/v1/score_facebook \
  -H "Content-Type: application/json" \
  -d '{"text":"We just hit 10,000 customers 🎉 — what should we build next? Drop a comment!"}'
```

### 3. Next Endpoint Ideas (pick one per session)
- **`score_pinterest_pin`** — Pinterest rewards long keyword-rich descriptions (150-500 chars), story format, no promotional language, 2-5 hashtags OK.
- **`score_youtube_description`** — YouTube description scorer: keyword density, timestamp presence, first 150 chars hook, CTA, links.
- **`generate_email_sequence`** — AI 3-email drip sequence (hook email, value email, CTA email) for any niche.
- **`generate_content_brief`** — AI research brief for a topic (target audience, angle, outline, SEO keywords).
- **`score_ad_copy`** — Google/Meta ad copy scorer: headline (30 char), description (90 char), CTA, pain point.

### 4. Marketing — Spread the Word
Share ContentForge on:
- r/indiehackers post: "I built a free content scoring API — 22 endpoints, covers 8 platforms"
- r/SideProject: "Free API: instantly score your tweets, LinkedIn posts, TikTok captions, and more"
- ProductHunt — plan a launch (requires consistent ratings/reviews first)
- Dev.to article: "How to score content quality before posting using the ContentForge API"


---

## API Endpoints — All 20 (10 instant + 9 AI + health)

```
GET  /health                       → service status, LLM backend, usage stats

# Instant scoring (no AI, <5ms):
POST /v1/analyze_headline          → score + grade + suggestions (0-100)
POST /v1/score_tweet               → tweet scorer (0-100)
POST /v1/score_linkedin_post       → LinkedIn post scorer (0-100)
POST /v1/score_instagram           → Instagram caption scorer (0-100)
POST /v1/score_youtube_title       → YouTube title CTR scorer (0-100)
POST /v1/score_email_subject       → email subject line scorer (0-100)
POST /v1/score_multi               → all platforms in one call (tweet/linkedin/instagram/tiktok/youtube/email)
POST /v1/score_readability         → Flesch-Kincaid readability (0-100)
POST /v1/score_tiktok              → TikTok caption scorer (0-100) ← Session 5
POST /v1/analyze_hashtags          → hashtag quality + spam risk + platform fit ← Session 5

# AI generation (Gemini 2.0 Flash):
POST /v1/improve_headline          → N AI-rewritten headlines (scored)
POST /v1/generate_hooks            → viral hooks for any topic
POST /v1/rewrite                   → rewrite for twitter/linkedin/instagram/tiktok/email/blog
POST /v1/tweet_ideas               → tweet ideas for any niche
POST /v1/content_calendar          → 7-day content calendar
POST /v1/thread_outline            → Twitter thread outline (hook + body + CTA)
POST /v1/generate_bio              → social bio for twitter/linkedin/instagram
POST /v1/generate_caption          → Instagram or TikTok caption ← Session 5
POST /v1/generate_linkedin_post    → full LinkedIn post (storytelling/professional/motivational) ← Session 5
```

**Key notes:**
- Base URL: `contentforge-api-lpp9.onrender.com` — **letter L** not digit 1
- Free tier Render → 50s cold start after 15 min idle (keep-warm cron prevents this)
- Gemini daily quota: 1,500 req/day. If you see `503 RESOURCE_EXHAUSTED`, wait until midnight Pacific
- CORS headers added — browser clients work directly
- 3-layer LLM fallback: `llm_provider.generate_text` → direct Ollama → direct Gemini

---

## What Was Done This Session (March 29, 2026 — Session 5)

### New Endpoints (4)
1. **`POST /v1/score_tiktok`** — TikTok caption scoring: hashtag count (3-6 ideal), emojis (1-3), CTA, power words (pov/viral/hack), hook. Returns 15-field dict. Tested 5/5.
2. **`POST /v1/analyze_hashtags`** — cross-platform hashtag analysis: spam detection (f4f/followme etc.), duplicates, specificity tiers, platform ideal ranges (twitter/instagram/tiktok/linkedin/youtube). Tested 6/6.
3. **`POST /v1/generate_caption`** — AI Instagram/TikTok caption generator with platform-specific rules (Instagram: hook + 5 lines + 5-10 hashtags; TikTok: <150 chars + 3-5 tags + CTA).
4. **`POST /v1/generate_linkedin_post`** — AI LinkedIn post generator. Tones: storytelling, professional, motivational. Short-paragraph format, includes hashtags.

### Improvements
5. **`/v1/rewrite`**: Added instagram (2200 chars) and tiktok (150 chars) character limits.
6. **`/v1/score_multi`**: Description + platform enum now includes TikTok.
7. **Landing page**: Complete revamp — new meta/OG/Twitter Card tags, schema.org JSON-LD, new "One Text, Six Platform Scores" visual demo, FAQ (7 Q&As), expanded audience grid (8 cards), updated stats (20 endpoints / 10 instant). All endpoint cards added.
8. **OpenAPI**: All 20 paths, TikTok and LinkedIn generators spec'd.
9. **Autopilot**: 30 → 34 templates (all 70+, avg 74.7). 12 new AI prompts (6 per account). New topics: tiktok, hashtag, caption, LinkedIn post.

### Commits
- `f92e8aa`: TikTok scorer + hashtag analyzer + landing page revamp
- `e07fb1c`: generate_caption + rewrite/score_multi TikTok support
- `2ef5e7f`: generate_linkedin_post (20 total endpoints, 34 templates)
- `pending`: landing page meta/FAQ corrections + NEXT_SESSION.md update

---

## Twitter Bot State

| Account | State |
|---|---|
| niche_launch_1 (NicheNewton) | active, posting ContentForge promo |
| EyeCatcher | active, posting ContentForge promo |

Run commands:
```bash
source .runtime-venv/bin/activate

# Single smart post (picks best account)
python3 scripts/smart_post_twitter.py --headless

# Verify all autopilot templates score 70+
python3 scripts/contentforge_autopilot.py --verify

# Check system readiness
python3 scripts/twitter_readiness_report.py
```

---

## What Still Needs Doing (Priority Order)

### 1. Re-import openapi.json to RapidAPI (manual, 5 min) ⚡ CRITICAL
- Go to RapidAPI → My APIs → ContentForge → Endpoints
- Click "Import OpenAPI" → upload `deploy/openapi.json`
- This will show ALL 20 endpoints (currently old count showing)
- File: `deploy/openapi.json` — 20 paths, all spec'd

### 2. Update RapidAPI description (manual, 2 min)
- Update the listing description to mention TikTok, Hashtag Analyzer, Caption Generator, LinkedIn Post Generator

### 3. Post to Indie Hackers + Hacker News
- "Show HN: ContentForge — free API to score content on 6 platforms + AI generators for LinkedIn/Instagram/TikTok"
- This is #1 driver of first subscribers

### 4. Consider adding score_threads_post (Meta Threads is growing rapidly)
- Very similar to score_tweet with slightly different scoring params
- Would be the first Threads-specific scoring API on RapidAPI

### 5. Consider LinkedIn post generator → auto-post workflow
- `generate_linkedin_post` + `score_linkedin_post` → automatic quality gate
- Could build a `smart_post_linkedin.py` similar to smart_post_twitter.py

