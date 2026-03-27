# ContentForge API — Deploy & Monetize Guide

## What You're Selling

**ContentForge** — an AI-powered content toolkit API. Creators and marketers pay per request to:
- Score headlines instantly (no AI, millisecond response)
- Generate scroll-stopping hooks for any topic
- Rewrite text for Twitter/LinkedIn/email in any tone
- Get tweet ideas for any niche

---

## Step 1: Get a Gemini API Key (Free)

The AI endpoints need an LLM. Gemini 2.0 Flash is free:

1. Go to https://aistudio.google.com/apikey
2. Click **Create API Key**
3. Copy the key — you'll paste it into Render and your local `.env`

Free tier limits: 15 RPM, 1,500 requests/day, 1M tokens/day.
That's more than enough for an MVP.

---

## Step 2: Deploy to Render (Free Tier)

1. Go to https://render.com and sign in with GitHub
2. Click **New → Web Service**
3. Connect the `CaptainFredric/MoneyPrinter3` repo
4. Settings:
   - **Name**: `contentforge-api`
   - **Root Directory**: (leave blank — repo root)
   - **Runtime**: Python
   - **Build Command**: `pip install -r deploy/requirements-api.txt`
   - **Start Command**: `gunicorn deploy.wsgi:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
   - **Plan**: Free
5. Add **Environment Variable**:
   - `GEMINI_API_KEY` = (paste your key from Step 1)
6. Click **Create Web Service**

Your API will be live at: `https://contentforge-api.onrender.com`

Test it:
```bash
curl https://contentforge-api.onrender.com/health
curl -X POST https://contentforge-api.onrender.com/v1/analyze_headline \
  -H "Content-Type: application/json" \
  -d '{"text": "5 AI Tools That Print Money While You Sleep"}'
```

> Note: Render free tier spins down after 15 min of inactivity. First request
> after idle takes ~30s. Upgrade to $7/mo Starter to keep it always-on.

---

## Step 3: List on RapidAPI

1. Go to https://rapidapi.com/provider and sign up as a **provider**
2. Click **My APIs → Add New API**
3. Fill in:
   - **API Name**: ContentForge
   - **Short Description**: AI-powered content toolkit — score headlines, generate hooks, rewrite for any platform, get tweet ideas.
   - **Category**: Text Analysis / Content / AI
4. Under **Endpoints**, add each one:

### Endpoint 1: Analyze Headline
- Method: `POST`
- Path: `/v1/analyze_headline`
- Body params: `text` (string, required)
- Description: Score any headline 0-100 with actionable improvement suggestions. Instant response (no AI).

### Endpoint 2: Generate Hooks
- Method: `POST`
- Path: `/v1/generate_hooks`
- Body params: `topic` (string, required), `count` (int, optional, default 5), `style` (string, optional: viral/professional/casual)
- Description: AI-generated scroll-stopping hooks for any topic.

### Endpoint 3: Rewrite
- Method: `POST`
- Path: `/v1/rewrite`
- Body params: `text` (string, required), `platform` (string, optional: twitter/linkedin/email/blog), `tone` (string, optional: engaging/professional/casual/humorous)
- Description: AI rewrite optimized for any platform and tone.

### Endpoint 4: Tweet Ideas
- Method: `POST`
- Path: `/v1/tweet_ideas`
- Body params: `niche` (string, required), `count` (int, optional, default 5), `hashtags` (bool, optional, default true)
- Description: AI-generated tweet ideas for any niche with hashtag suggestions.

### Endpoint 5: Health
- Method: `GET`
- Path: `/health`

5. Under **Base URL**, set: `https://contentforge-api.onrender.com`

6. Set **Pricing Plans**:

| Plan | Price | Requests/mo | Rate Limit |
|------|-------|-------------|------------|
| Free | $0 | 50 | 5/min |
| Basic | $9.99/mo | 1,000 | 15/min |
| Pro | $29.99/mo | 10,000 | 30/min |

7. Click **Publish**

---

## Step 4: Promote

Now you have a live API on RapidAPI. Promote it:

- **Twitter** (use your own bot!): Post about it daily
  - "I built an API that scores your headlines in milliseconds 🔥"
  - "Struggling with tweet ideas? I automated it."
- **Dev.to / Hashnode**: Write "How I Built a Content API and Listed It on RapidAPI"
- **Reddit**: r/SideProject, r/Entrepreneur, r/webdev
- **Product Hunt**: Quick launch for visibility

---

## Revenue Math

| Monthly subscribers | Plan | Revenue |
|--------------------|------|---------|
| 10 | Basic ($9.99) | $99.90 |
| 5 | Pro ($29.99) | $149.95 |
| **Total** | | **$249.85/mo** |

Even 5 Basic subscribers = $50/mo passive. The headline analyzer alone (instant, no AI cost) is the hook for the free tier.

---

## Local Development

Test locally with Ollama (no API key needed):
```bash
.runtime-venv/bin/python scripts/api_prototype.py --test
.runtime-venv/bin/python scripts/api_prototype.py  # runs on :8081
```

Test with Gemini:
```bash
GEMINI_API_KEY=your_key_here .runtime-venv/bin/python scripts/api_prototype.py --test
```
