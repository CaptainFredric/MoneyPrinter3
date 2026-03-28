# ContentForge API — Complete Deploy & Monetize Guide

## How This Works (Big Picture)

ContentForge is a **monetized API product** built on top of the automation work in this repo. Here is the full money flow:

```
Your Twitter bots (niche_launch_1, EyeCatcher)
    │  post daily content about copywriting, headlines, viral hooks
    │  occasionally mention "ContentForge — free headline scorer"
    ▼
Curious followers hit the RapidAPI listing page
    │  try the free tier (50 requests/mo, no credit card)
    │  get hooked on the headline scoring tool
    ▼
They upgrade to PRO ($9.99), ULTRA ($29.99), or MEGA ($99/mo)
    │  RapidAPI handles billing, fraud protection, and quota enforcement
    │  you receive payouts monthly
    ▼
Render hosts the Flask backend
    │  free tier for MVP, $7/mo Starter when revenue covers it
    │  Gemini API (free tier) handles all AI generation
    ▼
You earn passive monthly income while the bots keep funneling traffic
```

The beauty of this architecture: **your cost is $0 until you generate revenue**. Render free tier + Gemini free tier + RapidAPI free provider account = zero upfront spend. The only cost is your time setting it up.

---

## Architecture Details

```
deploy/
  wsgi.py               ← WSGI entry point (adds ROOT + ROOT/src to sys.path)
  render.yaml           ← Render auto-deploy config (IaC — no dashboard clicking)
  Procfile              ← Heroku-compatible fallback
  requirements-api.txt  ← Minimal deps: flask, gunicorn, google-genai
  openapi.json          ← Full OpenAPI 3.0.3 spec (import directly to RapidAPI)

scripts/
  api_prototype.py      ← The Flask app (4 endpoints + health + rate limiting)
  update_topics.py      ← Aligns bot posting topics with ContentForge funnel

src/
  llm_provider.py       ← LLM abstraction (Ollama → Gemini fallback chain)
```

The Flask app has an **LLM fallback chain**: it tries the project's built-in `llm_provider` first (Ollama locally), then falls back to direct Gemini API calls. This means the same code runs on your Mac with Ollama and on Render with just a `GEMINI_API_KEY`.

---

## Prerequisites Checklist

Before starting, confirm you have:

- [ ] A GitHub account with this repo pushed (Render deploys from GitHub)
- [ ] A Render account (free at https://render.com)
- [ ] A Google AI Studio account (free at https://aistudio.google.com)
- [ ] A RapidAPI provider account (free at https://rapidapi.com/provider)
- [ ] The repo either public, or Render connected to your GitHub with access granted

---

## Step 0: Test Locally First

Never deploy something you have not tested locally. The API has a built-in smoke test that exercises all 4 endpoints.

**With Ollama (no API key needed):**
```bash
# Make sure Ollama is running with a model pulled
ollama pull llama3.2:3b   # ~2GB, fast

# Run smoke test
.runtime-venv/bin/python scripts/api_prototype.py --test

# Start the server (runs on http://127.0.0.1:8081)
.runtime-venv/bin/python scripts/api_prototype.py
```

**With Gemini (cloud, no Ollama needed):**
```bash
GEMINI_API_KEY=your_key_here .runtime-venv/bin/python scripts/api_prototype.py --test
```

**Test the WSGI entry point exactly as Render will use it:**
```bash
cd /path/to/repo
GEMINI_API_KEY=your_key_here \
  .runtime-venv/bin/python -m gunicorn deploy.wsgi:app --bind 127.0.0.1:8081 --workers 1
```
Then open http://127.0.0.1:8081/health — you should see `{"status":"ok","llm_backend":"gemini","ai_endpoints_ready":true}`.

If you see `ai_endpoints_ready: false`, your Gemini key is either wrong or not set. Fix it before deploying.

---

## Step 1: Get a Gemini API Key (Free)

Gemini 2.0 Flash is Google's fast, free LLM. Every AI endpoint in ContentForge calls it.

1. Go to https://aistudio.google.com/apikey
2. Click **Create API Key** → select a project (or create one)
3. Copy the key — it starts with `AIza...`
4. Keep it in a safe place — you'll paste it into Render

**Free tier limits:**
- 15 requests/minute
- 1,500 requests/day
- 1,000,000 tokens/day

That comfortably serves your API until you have ~50 paying subscribers generating real usage. Well past the point where revenue covers a paid Gemini tier.

---

## Step 2: Deploy to Render

Render is the best free hosting option for this. The `deploy/render.yaml` file already contains the full config — Render will read it automatically when you connect the repo.

### 2a. Connect the Repo

There are two ways to deploy. Both work — use whichever you see first.

**Option A — Blueprint (recommended, uses render.yaml directly):**

1. Go to https://render.com and sign in with GitHub
2. Click **New → Blueprint**
3. Under "Connect a repository", find **CaptainFredric/MoneyPrinter3** (or wherever your fork lives)
4. Render reads `deploy/render.yaml` and shows a **"Create Blueprint Instance"** page
5. You'll see the service name `contentforge-api` pre-filled
6. Under **Environment Variables**, Render shows `GEMINI_API_KEY` and `RAPIDAPI_PROXY_SECRET` as empty fields (because `sync: false`). Enter your Gemini key now; leave proxy secret blank for now (Step 4b)
7. Click **Apply** at the bottom

Render will create the web service, install dependencies, and start it automatically. Skip to **2d** below.

**Option B — Manual Web Service:**

1. Go to https://render.com and sign in (use GitHub OAuth for easiest connection)
2. Click **New → Web Service**
3. Under "Connect a repository", find and select this repo
4. Render will detect `deploy/render.yaml` and pre-fill all settings — do not change them

### 2b. Verify the Auto-Filled Settings

Confirm these match exactly:

| Field | Value |
|---|---|
| Name | `contentforge-api` |
| Runtime | Python |
| Build Command | `pip install -r deploy/requirements-api.txt` |
| Start Command | `gunicorn deploy.wsgi:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120` |
| Plan | Free |

### 2c. Set Environment Variables

In the **Environment** section, you must set these manually (they are marked `sync: false` in render.yaml for security — Render intentionally does not let secrets live in committed files):

| Variable | Value | When to set |
|---|---|---|
| `GEMINI_API_KEY` | Your `AIza...` key from Step 1 | Before first deploy |
| `RAPIDAPI_PROXY_SECRET` | From RapidAPI dashboard (Step 4b) | After RapidAPI listing is created |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Already in render.yaml — no action needed |

> **Important**: Do NOT set `RAPIDAPI_PROXY_SECRET` until you have actually created the RapidAPI listing and copied the secret. Leave it blank for now — the API will still work, it just will not verify RapidAPI authenticity (fine during initial testing).

### 2d. Deploy

Click **Create Web Service**. Render will:
1. Clone the repo
2. Run `pip install -r deploy/requirements-api.txt` (~30 seconds)
3. Start gunicorn
4. Assign you a URL: `https://contentforge-api-lpp9.onrender.com`

Watch the build logs for errors. A successful deploy log ends with something like:
```
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:10000
[INFO] Worker booting (pid: ...)
```

### 2e. Verify the Deploy

```bash
# Health check
curl https://contentforge-api-lpp9.onrender.com/health

# Headline analyzer (instant, no AI)
curl -X POST https://contentforge-api-lpp9.onrender.com/v1/analyze_headline \
  -H "Content-Type: application/json" \
  -d '{"text": "5 AI Tools That Print Money While You Sleep"}'

# Tweet ideas (calls Gemini)
curl -X POST https://contentforge-api-lpp9.onrender.com/v1/tweet_ideas \
  -H "Content-Type: application/json" \
  -d '{"niche": "indie hacking", "count": 3}'
```

Expected health response:
```json
{
  "status": "ok",
  "service": "contentforge",
  "version": "1.0.0",
  "llm_backend": "gemini",
  "ai_endpoints_ready": true
}
```

If `ai_endpoints_ready` is `false`: go to Render dashboard → your service → Environment → confirm `GEMINI_API_KEY` is set and redeploy.

### 2f. Free Tier Gotcha — Cold Starts

Render free tier **spins down after 15 minutes of inactivity**. The first request after idle takes ~25–40 seconds. This is fine for:
- Your own testing
- RapidAPI's health pings (RapidAPI sends periodic health checks which keep it warm during business hours)
- Low-traffic early days

When you start getting paying subscribers (Basic/Pro tier), upgrade to Render Starter ($7/mo) for always-on uptime. One Basic subscriber ($9.99) covers it.

### Custom Domain (Optional but Recommended)

If you own a domain, point a subdomain at Render:
1. In Render dashboard → your service → Settings → Custom Domains → Add
2. Type `api.yoursite.com`
3. Add the CNAME record Render gives you at your DNS provider
4. Render issues a free TLS cert automatically

Having `api.yoursite.com` instead of `contentforge-api-lpp9.onrender.com` looks more professional on the RapidAPI listing and lets you switch hosting providers later without changing your listing URL.

---

## Step 3: Prepare the OpenAPI Spec Import

RapidAPI lets you import an OpenAPI spec to auto-create all your endpoints. The spec is at `deploy/openapi.json`.

**One thing to update before importing**: the server URL. Open `deploy/openapi.json` and confirm the `servers` block matches your actual Render URL (or custom domain if you set one up in Step 2f):

```json
"servers": [
  {
    "url": "https://contentforge-api-lpp9.onrender.com",
    "description": "Production"
  }
]
```

If your URL is different (e.g. you used a custom domain), update it now with:
```bash
# Replace the URL in openapi.json
sed -i '' 's|contentforge-api-lpp9.onrender.com|api.yoursite.com|g' deploy/openapi.json
```

---

## Step 4: List on RapidAPI

This is how the billing layer gets added in front of your API. RapidAPI sits between subscribers and your Render backend. They charge subscribers, take a 20% cut, and pay you monthly.

### 4a. Create the Listing

1. Go to https://rapidapi.com/provider and sign in (create an account if needed)
2. Click **Add New API** → **Import OpenAPI file**
3. Upload `deploy/openapi.json` — RapidAPI will auto-fill:
   - API name: ContentForge
   - All 5 endpoints with descriptions and request bodies
   - Category suggestions
4. Review the auto-filled info. Set:
   - **Category**: `Text Analysis` (primary), `Artificial Intelligence/Machine Learning` (secondary)
   - **Tags**: `content`, `copywriting`, `headlines`, `twitter`, `marketing`, `AI`
   - **Visibility**: Public
5. Under **About**, write the long description (copy from below)

**Long description to paste into RapidAPI:**
```
ContentForge is an AI-powered content toolkit for creators, marketers, and developers.

🎯 Score Headlines Instantly
The /analyze_headline endpoint scores any headline 0-100 with a letter grade (A-D)
in under 50ms — no AI needed. It checks length, power words, numbers, capitalization,
and curiosity factors, then gives you specific improvement suggestions.

🪝 Generate Scroll-Stopping Hooks
Give it any topic and get AI-written hooks optimized for going viral.
Choose from viral, professional, or casual style. Great for ads, landing pages,
email subject lines, and social posts.

✍️ Rewrite for Any Platform
Paste any text and get a version optimized for Twitter (280 chars), LinkedIn,
email, or blog — in your chosen tone (engaging, professional, casual, humorous).

💬 Tweet Ideas on Demand
Describe your niche and get a mix of hot takes, tips, questions, story hooks,
and lists — complete with relevant hashtags.

Built for: content creators, growth marketers, newsletter writers, Twitter ghostwriters,
Notion templates sellers, and anyone who writes for an audience.
```

### 4b. Get the Proxy Secret

This is the critical security step. After creating the listing:

1. Go to **My APIs → ContentForge → Settings → Security**
2. Copy the **X-RapidAPI-Proxy-Secret** value
3. Go to your Render dashboard → contentforge-api → Environment
4. Set `![alt text](image.png)` = (the value you just copied)
5. Render will redeploy automatically

What this does: RapidAPI injects this secret into every request it forwards to your backend. Your API (`_verify_rapidapi_request()` in `api_prototype.py`) validates it. Anyone who finds your Render URL and tries to call it directly without going through RapidAPI gets a `403 Forbidden`. This means all traffic — and therefore all billing — must flow through RapidAPI.

### 4b-fix. Clean Up Duplicate Endpoint Groups

When you imported the OpenAPI spec, RapidAPI may have created **duplicate groups** from both the `tags` and the `/v1/` path prefix. You might see:
- **Content Analysis** (correct — has `analyzeHeadline`)
- **AI Content Generation** (correct — has `generateHooks`, `rewriteText`, `tweetIdeas`)
- **System** (correct — has `healthCheck`)
- **v1** (duplicate — empty or has stubs ← DELETE this group)
- **health** (duplicate — empty or has stubs ← DELETE this group)

To fix:
1. Go to **Definitions → Endpoints** tab
2. Expand the **v1** group — if it has endpoints inside, use **Move to** to move them into the correct group (Content Analysis or AI Content Generation). If empty, proceed.
3. Click the checkbox next to the **v1** group → click **Delete**
4. Do the same for the **health** group (the real health endpoint should be under **System**)
5. Expand each correct group and verify:

| Group | Endpoints |
|---|---|
| Content Analysis | `analyzeHeadline` (POST) |
| AI Content Generation | `generateHooks` (POST), `rewriteText` (POST), `tweetIdeas` (POST) |
| System | `healthCheck` (GET) |

6. For each endpoint, click **Edit** and make sure:
   - **Description** is filled in (should be auto-populated from OpenAPI import)
   - **Body** tab shows the example JSON (e.g., `{"text": "5 AI Tools That Print Money While You Sleep"}`)
   - The **path** is correct (e.g., `/v1/analyze_headline`)

If any endpoint is missing its body/description, the OpenAPI values to paste are:

**generateHooks** — Body example:
```json
{"topic": "passive income with APIs", "count": 5, "style": "viral"}
```

**rewriteText** — Body example:
```json
{"text": "I built an API and now it makes me money.", "platform": "twitter", "tone": "engaging"}
```

**tweetIdeas** — Body example:
```json
{"niche": "indie hacking", "count": 5, "hashtags": true}
```

**healthCheck** — No body (GET request).

### 4b-pre. Link Your Payout Account First — DO THIS BEFORE ANYTHING ELSE

Before you configure pricing or publish, link a payout account. RapidAPI holds all revenue until you do. You will see this banner at the top:
> *"No payout account linked. Revenue from your API projects will be held by RapidAPI until an account is linked."*

1. Click **Link account** in that orange banner
2. Connect via **Stripe** (recommended — fastest payouts, works internationally) or PayPal
3. Complete Stripe's identity/bank KYC flow (~5 minutes — need ID + bank account or debit card)
4. Come back to the Monetize tab when done

If you skip this and start getting subscribers, your money sits in RapidAPI's holding account. Get it done now while you're already here.

---

### 4c. Configure Pricing Plans

You have 4 plans already created (BASIC free / PRO $9.99 / ULTRA $29.99 / MEGA $99).
Each plan has two quota **Objects**: **Requests** (every API call) and **AI Objects** (calls to AI-powered endpoints only).

#### What "AI Objects" means

- **Requests** counts every call to any endpoint — including `/analyze_headline` (heuristic, instant, zero AI cost).
- **AI Objects** counts only calls to `/generate_hooks`, `/rewrite`, and `/tweet_ideas` — the three endpoints that call Gemini.

Both objects consume simultaneously. A call to `/generate_hooks` = 1 Request + 1 AI Object. A call to `/analyze_headline` = 1 Request + 0 AI Objects.

This separation lets you apply a **Hard Limit on AI Objects for the free tier** — which protects your Gemini daily quota (1,500 calls/day free) from being abused by free users. Paid tiers get Soft Limits so they're never blocked mid-workflow but pay overages.

---

#### BASIC Plan (Free — $0/mo)

**Requests object** — confirm it shows:
- Quota Limit: `50` / month
- Limit Type: **Hard Limit**
- Overages: `$0`

**AI Objects object** — currently open in the modal on your screen. Fill it in exactly:

| Field | Value | Notes |
|---|---|---|
| Quota Type | Monthly ✓ | Already selected |
| Quota Limit | `30` | 30 out of 50 requests can be AI-powered |
| Limit Type | **Hard Limit** | CHANGE from Soft → Hard. Critical for free tier. |
| Overages | `$0` ✓ | Already correct — free users are never charged |

Click **Save Changes**.

---

#### PRO Plan ($9.99/mo)

Click **Edit** on the PRO card → find AI Objects → configure:

| Field | Value |
|---|---|
| Quota Limit | `750` / month |
| Limit Type | Soft Limit |
| Overages | `$0.02` per extra AI Object |

**Requests object** (1,000/month already set — confirm):
- Limit Type: Soft Limit
- Overages: `$0.01` per extra request

---

#### ULTRA Plan ($29.99/mo)

AI Objects:

| Field | Value |
|---|---|
| Quota Limit | `3,000` / month |
| Limit Type | Soft Limit |
| Overages | `$0.015` per extra AI Object |

Requests (4,000/month already set — confirm):
- Limit Type: Soft Limit
- Overages: `$0.008` per extra request

---

#### MEGA Plan ($99/mo)

AI Objects:

| Field | Value |
|---|---|
| Quota Limit | `18,000` / month |
| Limit Type | Soft Limit |
| Overages | `$0.008` per extra AI Object |

Requests (20,000/month already set — confirm):
- Limit Type: Soft Limit
- Overages: `$0.005` per extra request

---

#### Bandwidth Platform Fee

RapidAPI auto-adds this (10,240/month, then $0.001/extra). Leave it as-is — this is RapidAPI infrastructure metering, not your pricing. It does not affect subscribers' experience.

---

#### Final Plan Summary

| Plan | Price | Requests | AI Objects | AI Overage/call |
|---|---|---|---|---|
| **BASIC** | Free | 50, Hard, $0 | 30, Hard, $0 | blocked |
| **PRO** | $9.99 | 1,000, Soft, +$0.01 | 750, Soft, +$0.02 | $0.02 |
| **ULTRA** | $29.99 | 4,000, Soft, +$0.008 | 3,000, Soft, +$0.015 | $0.015 |
| **MEGA** | $99 | 20,000, Soft, +$0.005 | 18,000, Soft, +$0.008 | $0.008 |

Mark PRO as the **Recommended Plan** (it should already have that badge).

**Pricing logic:**
- Hard limits on BASIC protect your Gemini free quota from abuse — 500 free users × 30 calls = 15K Gemini calls/month, comfortably under the 45K free monthly cap.
- Soft limits on paid tiers mean subscribers are **never blocked mid-workflow** — they pay overages instead. Better UX, extra income for you.
- Each tier roughly doubles the AI quota, justifying the price jump. ULTRA → MEGA is a bigger jump (4× requests) for serious business use.
- Overage unit cost decreases at higher tiers — rewards volume, incentivises staying subscribed rather than churning.

### 4d. Endpoint Visibility Check

Make sure all 5 endpoints are set to **Public** (not internal/private):
- `POST /v1/analyze_headline` ✓
- `POST /v1/generate_hooks` ✓
- `POST /v1/rewrite` ✓
- `POST /v1/tweet_ideas` ✓
- `GET /health` ✓

### 4e. Test via RapidAPI Console Before Publishing

Before clicking Publish, use RapidAPI's built-in API console (the "Test Endpoint" tab on each endpoint) to send a real request. This confirms:
1. RapidAPI → Render routing works
2. The proxy secret is being validated correctly
3. Your Gemini key is working

If you get `403`: the proxy secret in Render does not match what RapidAPI is sending. Re-copy it carefully.
If you get `503`: the Gemini key is missing or wrong. Check Render environment variables.
If you get a cold start timeout, just retry — Render was asleep.

### 4f. Publish

Click **Publish API**. Your listing will be live within a few minutes at:
`https://rapidapi.com/contentforge/api/contentforge`

---

## Step 5: Align the Bots to the Funnel

Now that the API is live, update your Twitter bots to drive traffic to it:

```bash
# Preview what will change (no writes)
.runtime-venv/bin/python scripts/update_topics.py --dry-run

# Apply
.runtime-venv/bin/python scripts/update_topics.py
```

This updates `niche_launch_1` to post about headlines, copywriting, and hooks — subtly mentioning ContentForge as a tool. `EyeCatcher` posts about psychology of attention and scroll-stopping content — the ideal audience for the API.

The funnel is now complete: bots post → followers discover ContentForge → they subscribe on RapidAPI → you get paid.

---

## Step 6: Promotion Strategy

### Immediate (Day 1–3)
- **Your own bots**: Update topics and let them run. They should naturally mention ContentForge 1-2 times per week — not every post or it looks like an ad.
- **Reply to threads**: Search Twitter for "how do I write better headlines" or "how to improve copywriting" — reply with genuinely useful advice and mention ContentForge naturally.
- **Dev.to / Hashnode post**: Title: "I built a free API that scores your headlines in 50ms — here's how". Write 600 words. Include code examples using your API. Dev audiences love this.

### Week 1–2
- **Reddit posts**: 
  - r/SideProject: "I shipped a content toolkit API — instant headline scoring + AI hooks"
  - r/Entrepreneur: "Built a passive income API in a weekend — here's the breakdown"
  - r/webdev: "Free API for scoring headline quality — feedback welcome"
  - Rule: be genuinely helpful, not spammy. Post the useful thing first, mention the API second.
- **Product Hunt**: Submit a launch. Write a good tagline: "Score any headline in 50ms — AI hooks, rewrites & tweet ideas". Upvotes from PH can drive hundreds of signups in a day.
- **Twitter threads**: Write a short thread showing before/after headline scores. "I ran 50 blog titles through my headline scorer. Here's what I found:" — shows the tool working, drives curiosity.

### Ongoing
- Keep the bots running — they are your 24/7 sales reps
- Watch RapidAPI analytics for which endpoints get used most — double down on those in promotion
- Respond to RapidAPI reviews (once you have them) — shows you're active
- When you hit 20+ subscribers, write a "from 0 to $X/mo API" post — these go viral in indie hacker communities

---

## Step 7: Monitor Usage and Revenue

### RapidAPI Analytics
Your RapidAPI dashboard shows:
- Daily/monthly request volume per endpoint
- Subscriber counts by plan
- Revenue to date

Check it weekly. Key metrics to watch:
- **Free → Paid conversion rate**: Should be ~5–10% of free users upgrading. If lower, your free tier might be too generous.
- **Most-used endpoint**: If `/v1/analyze_headline` dominates, promote it more (it's free to run, instant). If `/v1/tweet_ideas` is popular, that means AI demand is strong — consider a higher-tier plan.
- **Churn**: If subscribers cancel after month 1, your API is not sticky enough. Think about what would make them need it every single day.

### Render Logs
```bash
# Check recent API logs via Render CLI (install: brew install render)
render logs contentforge-api --tail

# Or just watch from the Render dashboard: Services → contentforge-api → Logs
```

### Local Usage Log
The API writes a local usage log for latency analytics:
```bash
cat .mp/api_usage.json | python3 -m json.tool | tail -20
```

---

## Revenue Math

### Conservative Scenario (2–3 months in)

| Plan | Subscribers | Monthly Revenue |
|---|---|---|
| PRO ($9.99) | 15 | $149.85 |
| ULTRA ($29.99) | 4 | $119.96 |
| MEGA ($99) | 1 | $99.00 |
| Overages (AI Objects) | — | ~$20 |
| **Total (gross)** | | **~$389/mo** |
| RapidAPI cut (20%) | | −$78 |
| **Net to you** | | **~$311/mo** |

### Moderate Scenario (6 months in)

| Plan | Subscribers | Monthly Revenue |
|---|---|---|
| PRO ($9.99) | 50 | $499.50 |
| ULTRA ($29.99) | 15 | $449.85 |
| MEGA ($99) | 5 | $495.00 |
| Overages | — | ~$80 |
| **Total (gross)** | | **~$1,524/mo** |
| RapidAPI cut (20%) | | −$305 |
| **Net to you** | | **~$1,219/mo** |

At this scale, you should:
1. Upgrade Render to Starter ($7/mo) for always-on uptime
2. Upgrade Gemini to a paid tier if you are hitting daily limits (unlikely — 1,500/day free is a lot for a content API)
3. Consider adding a 5th endpoint (something no competitor has — e.g., "viral post format detector" or "engagement score predictor")

### Costs at scale

| Item | Cost |
|---|---|
| Render Starter | $7/mo |
| Gemini API (paid) | ~$0.001 per 1K tokens → ~$5–20/mo at moderate volume |
| Domain (optional) | ~$12/year |
| **Total costs** | < $30/mo |

Margin is excellent — 97%+ at the conservative scenario, approaching 95% even at scale.

---

## Troubleshooting

### "Module 'scripts' not found" on Render

This means `PYTHONPATH` is not set to the repo root. Check `render.yaml`:
```yaml
- key: PYTHONPATH
  value: /opt/render/project/src
```
That path is the repo root on Render's filesystem. The `scripts/` package must be importable from there. Redeploy after confirming.

### "LLM generation failed: Gemini failed"

1. Go to Render dashboard → Environment → confirm `GEMINI_API_KEY` is set (not empty)
2. Try the key locally: `GEMINI_API_KEY=your_key python scripts/api_prototype.py --test`
3. Check https://aistudio.google.com — if your free tier quota is exhausted (1,500 requests today), it will fail until midnight Pacific

### Cold Start Timeouts (RapidAPI console shows timeout)

Render free tier was idle. RapidAPI's default request timeout is 10 seconds, but Render cold starts can take 25–40s. Options:
1. Just retry once — it will be warm for the next 15 minutes
2. Upgrade to Render Starter ($7/mo) for zero cold starts permanently
3. Add a cron job that pings `/health` every 10 minutes to keep it warm (see below)

**Keep-warm cron (free):**
Use https://cron-job.org (free) to ping `https://contentforge-api-lpp9.onrender.com/health` every 10 minutes. This prevents cold starts entirely on the free tier. No code changes needed.

### RapidAPI returns 403 from your backend

The proxy secret does not match. Steps:
1. RapidAPI dashboard → My APIs → ContentForge → Settings → Security → copy `X-RapidAPI-Proxy-Secret`
2. Render dashboard → contentforge-api → Environment → set `RAPIDAPI_PROXY_SECRET` to that value exactly (no trailing spaces)
3. Render redeploys automatically — wait 60 seconds, retry

### RapidAPI returns 429 from your backend

A subscriber is hitting your in-API rate limiter (30/min). This is expected. The rate limiter in `api_prototype.py` uses `X-RapidAPI-User` so each subscriber gets their own 30/min bucket. If a legitimate Pro subscriber is hitting this, consider increasing `RATE_LIMIT` for the Pro tier. For now, it protects your Gemini quota.

### AI endpoints return 503 "Gemini failed: 429 RESOURCE_EXHAUSTED"

You've hit the **Gemini free tier daily quota** (1,500 req/day). This only affects AI endpoints (`generate_hooks`, `rewrite`, `tweet_ideas`). The `analyze_headline` endpoint is always available since it uses no AI.

Options:
1. **Wait for daily reset** — quota resets at midnight Pacific time. Next day, all endpoints work again.
2. **Enable Gemini billing** — go to https://aistudio.google.com → API key → Enable billing. Free tier usage stays free; you only pay beyond the quota. At API MVP scale you likely never pay anything.
3. **Rotate API keys** — create a second Gemini API key in a different Google Cloud project and swap it in Render environment when the first hits its daily limit.

> **Note**: This error should not appear for normal RapidAPI users. Gemini's daily limit is 1,500 requests/day which handles ~30 users' full BASIC-tier monthly allocation (50 req/month × 30 = 1,500). You'd only hit this limit during intensive testing or if you have unexpectedly high traffic — at which point you should enable billing anyway.

---

## Going Further — Next Features to Add

Once you have paying subscribers and real feedback, these are the highest-leverage additions:

### 1. Per-Plan Rate Limits (High impact, medium effort)
Right now all subscribers get the same 30/min limit. RapidAPI injects the subscriber's plan tier via `X-RapidAPI-Subscription` header. You could read that and apply different limits per plan:
```python
PLAN_LIMITS = {"BASIC": 5, "PRO": 15, "ULTRA": 30}
tier = request.headers.get("X-RapidAPI-Subscription", "BASIC")
rate_limit = PLAN_LIMITS.get(tier, 5)
```

### 2. Headline A/B Comparison (High marketing value, low effort)
A new endpoint `POST /v1/compare_headlines` that takes two headlines and returns which scores higher with a side-by-side breakdown. Creators love A/B comparisons. This would be the most-shared feature — great for organic growth.

### 3. Content Calendar Generator (Stickiness play)
`POST /v1/content_calendar` — given a niche and posting frequency, returns a week of post ideas in different formats. This creates daily return visits because users want fresh ideas each week. Nothing creates stickiness like "I use this every Monday morning."

### 4. Webhook / Bulk Endpoint (Enterprise upsell)
`POST /v1/analyze_batch` — send up to 20 headlines at once and score all of them. This is immediately useful for content agencies and newsletter writers reviewing multiple draft titles. Charge 1 request per headline processed. Opens the door to an Enterprise plan at $99/mo.

### 5. Your Own Billing (Long-term)
RapidAPI's 20% cut is fine for MVPs. Once you hit $500+/mo, examine whether building a direct billing flow with Stripe ($109/mo for Stripe fees at that volume) makes financial sense. It usually does not until you are doing $2,000+/mo because building a billing system takes significant engineering time.
