# ContentForge API — Documentation

**ContentForge** is a 47-endpoint REST API for scoring and generating content across 12 platforms. Score any draft before you post — get a 0–100 score, a letter grade, and specific improvement tips in under 50ms. Use the AI endpoints to generate content from scratch when needed.

---

## Quick Start

All endpoints are available via RapidAPI. Subscribe to any plan and include your `X-RapidAPI-Key` header with every request. No credit card required for the free tier.

**Base URL:** `https://contentforge-api-lpp9.onrender.com`

**Authentication:**
```json
{
  "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY",
  "X-RapidAPI-Host": "contentforge1.p.rapidapi.com",
  "Content-Type": "application/json"
}
```

---

## ⚡ Instant Scorers — <50ms, zero AI cost

These endpoints use a pure heuristic engine — no AI, no latency, no AI call quota consumed. Same input always returns the same score.

---

### 1. `POST /v1/score_tweet` — Score a Tweet Draft

Score any tweet 0–100 for engagement potential before you post.

**Request:**
```json
{
  "text": "I built this API in 48 hours. Here's what I learned 🧵 #buildinpublic"
}
```

**Response:**
```json
{
  "score": 79,
  "grade": "B",
  "char_count": 67,
  "hashtag_count": 1,
  "emoji_count": 1,
  "power_words_found": ["built", "learned"],
  "suggestions": [
    "Add a specific number to the opening hook",
    "Length is in the lower-optimal range — aim for 71–100 chars"
  ]
}
```

**Scoring signals:**
- Character count sweet spot (71–100 chars best, 50–140 good)
- Hashtags: 1–2 is optimal (3+ gets penalized)
- Emojis: 1–3 boosts score
- Power words (60+ tracked)
- Questions + numbers as hooks
- Excessive caps penalty

---

### 2. `POST /v1/analyze_headline` — Score a Headline

Score any headline 0–100 with a letter grade and actionable tips. **Instant response, no AI needed.**

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
  "power_words_found": ["money", "sleep"],
  "suggestions": []
}
```

**Scoring signals:**
- Optimal length (30–80 chars)
- Power words (60+ tracked: urgency, money, social proof, curiosity, ease)
- Specific numbers boost credibility
- Question marks as engagement hooks
- ALL CAPS overuse penalty

---

### 3. `POST /v1/score_linkedin_post` — Score a LinkedIn Post

**Request:**
```json
{
  "text": "After 3 years of trial and error, here are the 5 things I wish I knew before building in public..."
}
```

**Response:**
```json
{
  "score": 82,
  "grade": "A",
  "suggestions": []
}
```

**Scoring signals:**
- Hook strength (first line quality)
- Paragraph structure and white space
- Professional tone signals
- Hashtag count (3–5 optimal on LinkedIn)
- CTA presence

---

### 4. `POST /v1/score_instagram` — Score an Instagram Caption

**Request:**
```json
{
  "text": "Quit my job. Built an API. Now 200 users in 30 days.\n\nFull story 👇\n\n#indiehacker #buildinpublic #solofounder #saas #api"
}
```

**Scoring signals:**
- Hashtag count (5–15 optimal)
- Emojis and line breaks
- Opening hook quality
- CTA presence

---

### 5. `POST /v1/score_youtube_title` — Score a YouTube Title

**Request:**
```json
{
  "text": "I Built an API in 48 Hours (Here's What Happened)"
}
```

**Scoring signals:**
- Optimal length (40–60 chars for CTR)
- Numbers and brackets or parentheses
- Power words and curiosity gap

---

### 6. `POST /v1/score_youtube_description` — Score a YouTube Description

**Scoring signals:**
- SEO keyword density in first 150 chars
- Timestamps / chapter marks
- External links and subscribe CTA
- CTA placement

---

### 7. `POST /v1/score_email_subject` — Score an Email Subject Line

**Request:**
```json
{
  "text": "You left something behind 👀"
}
```

**Scoring signals:**
- Curiosity gap, urgency, personalization
- Spam trigger words (penalized)
- Optimal length (30–50 chars)
- Question marks and numbers

---

### 8. `POST /v1/score_tiktok` — Score a TikTok Caption

**Scoring signals:**
- Hook speed (first 3 words)
- Hashtag strategy (3–5 niche + trending mix)
- Ideal length ≤150 chars

---

### 9. `POST /v1/score_threads` — Score a Threads Post

**Scoring signals:**
- Conversational tone
- Question hooks
- Hashtag penalty (Threads deprioritizes heavy hashtag use)
- CTA presence

---

### 10. `POST /v1/score_facebook` — Score a Facebook Post

**Scoring signals:**
- Engagement triggers
- Question hooks (drives comments)
- Emoji density
- Optimal hashtag count (1–2 on Facebook)

---

### 11. `POST /v1/score_pinterest` — Score a Pinterest Description

**Scoring signals:**
- Keyword density
- Instructional language ("how to", "step-by-step")
- Spam signal detection

---

### 12. `POST /v1/score_ad_copy` — Score Ad Copy

**Scoring signals:**
- Headline length and clarity
- Benefit-forward language
- Urgency signals
- CTA strength
- Compliance red flags

---

### 13. `POST /v1/score_readability` — Readability Score

Returns Flesch-Kincaid reading ease, grade level, and structural stats.

**Response:**
```json
{
  "flesch_reading_ease": 68.4,
  "flesch_kincaid_grade": 7.2,
  "avg_sentence_length": 14,
  "avg_word_length": 4.3,
  "grade": "B"
}
```

---

### 14. `POST /v1/analyze_hashtags` — Analyze Hashtags

Check hashtags for spam risk, overuse, and per-platform fit.

**Request:**
```json
{
  "hashtags": ["#buildinpublic", "#indiehacker", "#saas", "#followforfollow"],
  "platform": "twitter"
}
```

**Response:**
```json
{
  "results": [
    { "hashtag": "#buildinpublic", "risk": "low", "recommendation": "keep" },
    { "hashtag": "#followforfollow", "risk": "high", "recommendation": "remove — spam signal" }
  ]
}
```

---

### 15. `POST /v1/score_multi` — Score Across All Platforms

One piece of text, scores for every platform in a single call.

**Response:**
```json
{
  "results": {
    "twitter":   { "score": 74, "grade": "B" },
    "linkedin":  { "score": 61, "grade": "C" },
    "instagram": { "score": 55, "grade": "C" },
    "tiktok":    { "score": 70, "grade": "B" }
  }
}
```

---

### 16. `POST /v1/batch_score` — Batch Score Multiple Drafts

Score up to 20 draft texts against one platform, returned best-first.

**Request:**
```json
{
  "texts": [
    "Built an API in 48 hours.",
    "I built an API in 48 hours — here's the full breakdown 🧵",
    "48 hours. 1 API. 200 users. Here's exactly how I did it."
  ],
  "platform": "twitter"
}
```

**Response:**
```json
{
  "results": [
    { "text": "48 hours. 1 API. 200 users...", "score": 91, "grade": "A" },
    { "text": "I built an API in 48 hours...", "score": 79, "grade": "B" },
    { "text": "Built an API in 48 hours.", "score": 42, "grade": "D" }
  ]
}
```

---

## ✦ AI Generators — Gemini 2.5 Flash

These endpoints call Gemini 2.5 Flash and respond in 1–4 seconds. They **consume AI call quota** from your plan.

---

### 17. `POST /v1/improve_headline` — Improve a Headline with AI

Generates N better AI-written versions of a weak headline — each pre-scored and sorted best-first.

**Request:**
```json
{
  "text": "How to make money online",
  "count": 3
}
```

**Parameters:**

| Field | Type | Required | Default |
|---|---|---|---|
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
    { "text": "Can You Really Earn $5,000 a Month Online? Discover the Secrets", "score": 100, "grade": "A" },
    { "text": "7 Proven Ways to Make Money Online in 2024", "score": 87, "grade": "A" },
    { "text": "Make Money Online: 5 Strategies That Actually Work", "score": 82, "grade": "A" }
  ]
}
```

**Recommended workflow:**
1. Call `analyze_headline` → get score + suggestions
2. If score < 80, call `improve_headline` → get N better versions
3. Pick the top-scored version → publish

---

### 18. `POST /v1/generate_hooks` — Generate Viral Hooks

Returns scroll-stopping openers in multiple styles: viral, professional, casual, bold.

**Request:**
```json
{
  "topic": "building a SaaS while working a full-time job",
  "count": 4
}
```

**Response:**
```json
{
  "hooks": [
    "Nobody tells you how hard it is to ship at midnight when your 9–5 drained you dry.",
    "I built a SaaS between 10pm and 1am for 6 months. Here's the honest truth.",
    "Most 'side project' advice is written by people who quit their job first.",
    "72 hours a week. 1 product. Zero regrets."
  ]
}
```

---

### 19. `POST /v1/rewrite` — Rewrite for Any Platform

Platform-optimized rewrite. Respects each platform's character limits automatically.

**Parameters:**

| Field | Type | Required | Options |
|---|---|---|---|
| `text` | string | ✅ | — |
| `platform` | string | ✅ | `twitter`, `linkedin`, `instagram`, `tiktok`, `email`, `blog` |

---

### 20. `POST /v1/tweet_ideas` — Generate Tweet Ideas

5–10 tweet angles for any niche with hashtag suggestions.

**Request:**
```json
{
  "niche": "indie hacking",
  "count": 5
}
```

---

### 21. `POST /v1/content_calendar` — Generate a 7-Day Content Calendar

Full calendar with daily themes and ready-to-post drafts.

**Request:**
```json
{
  "niche": "personal finance for millennials",
  "platform": "twitter"
}
```

**Response:**
```json
{
  "calendar": [
    { "day": "Monday", "theme": "Mindset", "draft": "The most expensive thing you own isn't your house. It's your bad money habits. 🧠" },
    { "day": "Tuesday", "theme": "Quick Win", "draft": "One thing you can do today to save $200/month..." }
  ]
}
```

---

### 22. `POST /v1/thread_outline` — Generate a Twitter Thread

Complete thread: scroll-stopping hook + numbered body tweets + CTA.

**Request:**
```json
{
  "topic": "how I got my first 100 API users",
  "tweet_count": 7
}
```

**Response:**
```json
{
  "hook": "Want to get your first 100 API users? Here's exactly what worked for me 🧵",
  "tweets": [
    "2/ Start with one pain point. Not ten. One.",
    "3/ Post about building it before it's finished. Document, don't just ship.",
    "4/ Give the free tier real value. Don't cripple it."
  ],
  "cta": "Follow for weekly API build breakdowns. Bookmark this if you're planning to launch 🔖"
}
```

---

### 23. `POST /v1/generate_bio` — Generate a Social Media Bio

**Parameters:**

| Field | Type | Required | Options |
|---|---|---|---|
| `name` | string | ✅ | — |
| `role` | string | ✅ | — |
| `platform` | string | ✅ | `twitter` (160 chars), `linkedin` (300 chars), `instagram` (150 chars) |

**Response:**
```json
{
  "bio": "Indie dev building micro-SaaS tools | APIs, side income, shipping in public | Follow for weekly breakdowns",
  "char_count": 104,
  "char_limit": 160
}
```

---

### 24. `POST /v1/generate_caption` — Generate a Social Caption

Instagram or TikTok caption with hashtags, emojis, and CTA included.

**Request:**
```json
{
  "topic": "launched my first paid API",
  "platform": "instagram"
}
```

---

### 25. `POST /v1/generate_linkedin_post` — Generate a LinkedIn Post

Full post: hook + personal story + insight + CTA. Formatted for LinkedIn's algorithm.

**Request:**
```json
{
  "topic": "lessons from building in public for 6 months"
}
```

---

### 26. `POST /v1/generate_email_sequence` — Generate a 3-Email Drip Sequence

Returns a 3-part drip: welcome → value → pitch. Subject lines included for each.

**Response:**
```json
{
  "emails": [
    { "sequence": 1, "subject": "Welcome — here's how to get the most out of ContentForge", "body": "..." },
    { "sequence": 2, "subject": "The one thing most creators skip before posting", "body": "..." },
    { "sequence": 3, "subject": "Ready to go deeper? Here's what PRO unlocks", "body": "..." }
  ]
}
```

---

### 27. `POST /v1/generate_content_brief` — Generate a Content Brief

Research brief: target audience, content angle, SEO keywords, outline, and 5 hook options.

**Request:**
```json
{
  "topic": "content scoring for Twitter growth",
  "audience": "indie hackers"
}
```

---

### 28. `POST /v1/generate_ad_copy` — Generate Ad Copy

Short-form ad copy variants for Facebook, Google, and Twitter/X.

**Request:**
```json
{
  "product": "ContentForge",
  "benefit": "score your content before posting — stop publishing underperforming posts",
  "platform": "facebook"
}
```

---

## Plans

Instant endpoints (`score_*`, `analyze_*`, `batch_score`, `/health`) **never** count against AI call quota.

| Plan | Price | AI Calls/mo | Requests/mo | Rate Limit |
|---|---|---|---|---|
| **BASIC** | Free | 50 | 300 | 30 req/min |
| **PRO** | $9.99/mo | 750 | 1,000 | 30 req/min |
| **ULTRA** | $29.99/mo | 3,000 | 4,000 | 30 req/min |
| **MEGA** | $99/mo | 18,000 | 20,000 | 30 req/min |

No credit card required for BASIC. Every endpoint is included on the free tier.

---

## Error Reference

| Status | Meaning |
|---|---|
| `400` | Missing or invalid request body |
| `422` | Validation error (e.g. text too long) |
| `429` | Rate limit exceeded |
| `503` | AI provider temporarily unavailable |

---

## Support

- **Email:** captainarmoreddude@gmail.com
- **Live demo (no API key needed):** https://captainfredric.github.io/ContentForge/
- **GitHub:** https://github.com/CaptainFredric/ContentForge
