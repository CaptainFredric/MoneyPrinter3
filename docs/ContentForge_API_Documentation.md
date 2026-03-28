# ContentForge API — Documentation

**ContentForge** is an AI-powered content toolkit for creators, marketers, and developers.
Use it to score headlines, score tweet drafts, improve weak headlines with AI, generate viral hooks, rewrite for any platform, brainstorm tweet ideas, build full content calendars, generate viral Twitter thread outlines, and create optimized social media bios — all from a single API.

---

## Quick Start

All endpoints are available via RapidAPI. Subscribe to a plan and include your `X-RapidAPI-Key` header with every request.

**Base URL:** `https://contentforge-api-lpp9.onrender.com`

---

## Endpoints

### 1. `POST /v1/analyze_headline` — Score a Headline (instant, no AI)

Score any headline 0-100 with a letter grade and actionable tips. **Instant response, no AI needed.**

**Request:**
```json
{
  "text": "5 AI Tools That Print Money While You Sleep"
}
```

**Response:**
```json
{
  "text": "5 AI Tools That Print Money While You Sleep",
  "score": 85,
  "grade": "A",
  "length": 44,
  "word_count": 9,
  "has_number": true,
  "question_mark": false,
  "power_words_found": [],
  "caps_ratio": 0.11,
  "suggestions": ["Add a power word (e.g. 'proven', 'secret', 'simple')."]
}
```

**Scoring factors:**
- Length (sweet spot: 30–80 chars)
- Power words (proven, secret, hack, free, etc.)
- Numbers increase specificity
- Questions add curiosity
- ALL CAPS penalty
- Excessive exclamation marks penalty

---

### 2. `POST /v1/score_tweet` — Score a Tweet Draft

Score a tweet draft 0-100 for engagement potential before posting. **Instant, no AI needed.**

**Request:**
```json
{
  "text": "Built an API in 48 hours. It made $500 last month 💸 Here's how: #indiehacker #buildinpublic"
}
```

**Response:**
```json
{
  "text": "Built an API in 48 hours. It made $500 last month 💸 Here's how: #indiehacker #buildinpublic",
  "score": 83,
  "grade": "A",
  "char_count": 91,
  "word_count": 16,
  "hashtag_count": 2,
  "hashtags": ["#indiehacker", "#buildinpublic"],
  "mention_count": 0,
  "emoji_count": 1,
  "has_url": false,
  "power_words_found": ["hack"],
  "suggestions": ["Try starting with a number or a question for a stronger hook."]
}
```

**Scoring factors:**
- Character count sweet spot (71–140 chars)
- Hashtags: 1–2 is optimal (4+ gets penalized)
- Emojis: 1–3 boosts score
- Power words
- Questions + numbers as hooks
- Excessive caps penalty

---

### 3. `POST /v1/improve_headline` — Improve a Headline with AI

Takes a weak headline, identifies its problems, and generates N better AI-written versions — each scored and graded. Returns results sorted by score, best first.

**Request:**
```json
{
  "text": "How to make money online",
  "count": 3
}
```

**Parameters:**
| Field | Type | Required | Default |
|-------|------|----------|---------|
| `text` | string | ✅ | — |
| `count` | integer | ❌ | 3 (max 5) |

**Response:**
```json
{
  "original": "How to make money online",
  "original_score": 49,
  "original_grade": "C",
  "original_suggestions": [
    "Make the headline longer and more specific.",
    "Add a number for specificity (e.g. '5 ways', '$6K/mo')."
  ],
  "improved_versions": [
    {
      "text": "Can You Really Earn $5,000 a Month Online? Discover the Secrets",
      "score": 100,
      "grade": "A",
      "power_words_found": ["earn", "secret", "discover"]
    },
    {
      "text": "Unlock $6,000/month: 7 Proven Strategies for Online Success",
      "score": 85,
      "grade": "A",
      "power_words_found": ["proven"]
    },
    {
      "text": "5 Lucrative Ways to Make $10K/Mo Online",
      "score": 80,
      "grade": "A",
      "power_words_found": []
    }
  ]
}
```

**Typical workflow:**
1. Call `analyze_headline` → get score + suggestions
2. If score < 80, call `improve_headline` → get 3 better versions
3. Pick the top-scored version → publish

---

### 4. `POST /v1/generate_hooks` — AI-Generated Hooks

Generate scroll-stopping hooks and headlines for any topic. Choose from viral, professional, or casual styles.

**Request:**
```json
{
  "topic": "passive income with APIs",
  "count": 5,
  "style": "viral"
}
```

**Parameters:**
| Field | Type | Required | Default | Options |
|-------|------|----------|---------|---------|
| `topic` | string | ✅ | — | Max 300 chars |
| `count` | integer | ❌ | 5 | 1–10 |
| `style` | string | ❌ | `viral` | `viral`, `professional`, `casual` |

**Response:**
```json
{
  "topic": "passive income with APIs",
  "style": "viral",
  "hooks": [
    "I made $6K last month from an API I built in a weekend",
    "The API economy is minting millionaires — here's how to join",
    "3 APIs that earn more than my 9-to-5 salary"
  ]
}
```

---

### 5. `POST /v1/rewrite` — Rewrite for Any Platform

AI-rewrites any text for a specific platform and tone. Automatically respects character limits for each platform.

**Request:**
```json
{
  "text": "I built an API and now it makes me money every month.",
  "platform": "twitter",
  "tone": "engaging"
}
```

**Parameters:**
| Field | Type | Required | Default | Options |
|-------|------|----------|---------|---------|
| `text` | string | ✅ | — | Max 2000 chars |
| `platform` | string | ❌ | `twitter` | `twitter`, `linkedin`, `email`, `blog` |
| `tone` | string | ❌ | `engaging` | `engaging`, `professional`, `casual`, `humorous` |

**Platform character limits enforced:**
- Twitter: 280 chars
- LinkedIn: 700 chars
- Email: 500 chars
- Blog: 1000 chars

**Response:**
```json
{
  "original": "I built an API and now it makes me money every month.",
  "rewritten": "Built an API on a weekend. Now it pays my rent every month while I sleep. Here's the playbook:",
  "platform": "twitter",
  "tone": "engaging",
  "char_count": 89
}
```

---

### 6. `POST /v1/tweet_ideas` — Tweet Ideas for Any Niche

AI-generates tweet ideas tailored to your niche. Returns a mix of formats: hot takes, tips, questions, story hooks, and lists.

**Request:**
```json
{
  "niche": "indie hacking",
  "count": 5,
  "hashtags": true
}
```

**Parameters:**
| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `niche` | string | ✅ | — | Max 200 chars |
| `count` | integer | ❌ | 5 | 1–10 |
| `hashtags` | boolean | ❌ | `true` | Include hashtag suggestions |

**Response:**
```json
{
  "niche": "indie hacking",
  "count": 3,
  "tweets": [
    "The best marketing for your indie product? Ship faster than you're comfortable with. #indiehackers #buildinpublic",
    "Unpopular opinion: A $500/mo SaaS is harder to build than a $5K/mo one. Here's why:",
    "3 tools I use daily that cost $0 and saved my startup: Thread"
  ]
}
```

---

### 7. `POST /v1/content_calendar` — 7-Day Content Calendar

AI-generates a full content calendar with daily themes and ready-to-post drafts for any niche and platform.

**Request:**
```json
{
  "niche": "indie hacking",
  "days": 7,
  "platform": "twitter",
  "tone": "engaging"
}
```

**Parameters:**
| Field | Type | Required | Default | Options |
|-------|------|----------|---------|---------|
| `niche` | string | ✅ | — | Max 200 chars |
| `days` | integer | ❌ | 7 | 1–7 |
| `platform` | string | ❌ | `twitter` | `twitter`, `linkedin`, `instagram`, `blog` |
| `tone` | string | ❌ | `engaging` | `engaging`, `professional`, `casual`, `humorous` |

**Response:**
```json
{
  "niche": "indie hacking",
  "platform": "twitter",
  "tone": "engaging",
  "days": 3,
  "calendar": [
    {
      "day": "Monday",
      "theme": "Motivation Monday",
      "draft": "Your first $1 online proves the model works. The next $1,000 is just systems. What's your system? #indiehackers"
    },
    {
      "day": "Tuesday",
      "theme": "Tip Tuesday",
      "draft": "3 tools every solo founder needs: 1/ Stripe 2/ Notion 3/ Plausible. All under $50/mo. #buildinpublic"
    },
    {
      "day": "Wednesday",
      "theme": "Story Hook",
      "draft": "6 months ago I had 0 users. Today I have 847. The only thing I changed: I started shipping every week. Thread 🧵"
    }
  ]
}
```

---

### 8. `POST /v1/thread_outline` — Generate Twitter Thread Outline ← NEW

Generate a complete, ready-to-post Twitter thread outline for any topic. Returns a scroll-stopping hook tweet, numbered body tweets with real insights, and a CTA closing tweet.

**Request:**
```json
{
  "topic": "how to build a micro-SaaS in a weekend",
  "tweet_count": 7,
  "tone": "motivational"
}
```

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `topic` | string | ✅ | — | Thread topic (max 300 chars) |
| `tweet_count` | integer | ❌ | 7 | Total tweets including hook + CTA (3-10) |
| `tone` | string | ❌ | "informative" | Tone: informative, motivational, casual, bold, etc. |

**Response:**
```json
{
  "topic": "how to build a micro-SaaS in a weekend",
  "tone": "motivational",
  "total_tweets": 7,
  "hook": "Want to build a micro-SaaS in just one weekend? It's possible. Here's exactly how: 🧵",
  "tweets": [
    "2/ Pick a pain you've personally lived. Not an imaginary problem — YOUR problem.",
    "3/ Build the smallest version that solves it. No fancy features. Just the core value.",
    "4/ Launch on Sunday. Post 'I built this in 48hrs'. Indie Hacker audience loves these.",
    "5/ Price it at $9/mo. Underpriced feels safe. Get 10 customers first."
  ],
  "cta": "Follow me for weekly micro-SaaS breakdowns. Bookmark this 🔖 and come back when you're ready to build.",
  "full_thread": ["Want to build a micro-SaaS...", "2/ Pick a pain...", "..."]
}
```

---

### 9. `POST /v1/generate_bio` — Generate Social Media Bio ← NEW

Generate an optimized social media bio for Twitter (160 chars), LinkedIn (300 chars), or Instagram (150 chars). AI crafts a punchy bio with value proposition and CTA, automatically trimmed to fit the platform.

**Request:**
```json
{
  "name": "Alex Rivera",
  "niche": "indie developer building micro-SaaS tools",
  "keywords": ["APIs", "side income", "buildinpublic"],
  "platform": "twitter",
  "tone": "casual"
}
```

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | string | ✅ | — | Your name or brand name (max 100 chars) |
| `niche` | string | ✅ | — | What you do or your niche (max 200 chars) |
| `keywords` | array | ❌ | [] | Keywords to weave in (up to 10) |
| `platform` | string | ❌ | "twitter" | `twitter` (160), `linkedin` (300), `instagram` (150) |
| `tone` | string | ❌ | "professional" | professional, casual, bold, friendly, etc. |

**Response:**
```json
{
  "name": "Alex Rivera",
  "platform": "twitter",
  "tone": "casual",
  "bio": "Indie dev building micro-SaaS tools to help others monetize their APIs & build public products | Side income, simplified.",
  "char_count": 121,
  "char_limit": 160,
  "is_valid_length": true
}
```

---

### 10. `GET /health` — Health Check

Returns service status and usage statistics.

**Response:**
```json
{
  "status": "ok",
  "service": "contentforge",
  "version": "1.0.0",
  "llm_backend": "gemini",
  "ai_endpoints_ready": true,
  "total_requests_served": 42,
  "endpoint_usage": {
    "analyze_headline": 15,
    "generate_hooks": 10,
    "rewrite": 8,
    "tweet_ideas": 7,
    "score_tweet": 2
  }
}
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request — missing or invalid parameter |
| 403 | Forbidden — invalid or missing API key |
| 429 | Rate limit exceeded |
| 503 | AI generation temporarily unavailable (Gemini quota or outage) |

---

## Rate Limits by Plan

| Plan | Requests/Month | Rate Limit | AI Objects/Month |
|------|---------------|------------|-----------------|
| BASIC (Free) | 500,000 | 1,000 req/hr | 50 |
| PRO | 1,000 | 15 req/sec | 750 |
| ULTRA | 4,000 | 30 req/min | 3,000 |
| MEGA | Unlimited | Custom | 18,000 |

---

## Use Cases

- **Bloggers / Newsletter Writers** — Score your headline before publishing with `analyze_headline`
- **Twitter Growth Hackers** — Draft → `score_tweet` → post only A-grade content
- **Content Agencies** — Generate a full month of posts with `content_calendar` for multiple clients
- **Indie Hackers** — Get ready-to-post `tweet_ideas` for your product niche daily
- **Copywriters** — Use `rewrite` to instantly adapt any copy for a different platform or tone
- **Email Marketers** — Score subject lines with `analyze_headline` for higher open rates
- **Thread Writers** — Build viral Twitter threads with `thread_outline` in seconds, not hours
- **New Creators** — Generate your first professional social bio with `generate_bio`

---

## Support

- Email: captainarmoreddude@gmail.com
- RapidAPI Discussions: Use the Discussions tab on this API's RapidAPI page
