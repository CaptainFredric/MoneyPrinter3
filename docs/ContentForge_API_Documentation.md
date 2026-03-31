# ContentForge API — Documentation

**ContentForge** is a 28-endpoint REST API for scoring and generating content across every major platform. Score any draft before you post — get a 0–100 score, a letter grade, and specific improvement tips in under 50ms. Use the AI endpoints to generate content from scratch when needed.

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

Score any tweet 0–100 fScore any tweet 0–100 before you post.

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
  "power_words_found": ["money", "sleep  "powesuggesti  "power_words


 "power_words_fou** "power_words_fou** 0–80 chars)
- Power words (60+ tracked: urgency, money, social proof, curiosity, ease)
- Specific numbers boost credibility
- Question marks as engagement hooks
- Emotional triggers and exclamations
- ALL CAPS overuse penalty

---

### 3. `POST /v1/score_linkedin_post` — Score a LinkedIn Post

Checks hook strength, paragraph structure, professional tone, hashtag count, and CTA presence.

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
------------------------------------------------------ence

---

### 4. `POST /v1/score_instagram` — Score an Instagram Caption

**Request:**
```json
{
  "text": "Life update 🌿\n\nQuit my job. Built an API. Now 200 users in 30 days.\n\nFu  "text": "Life update 🌿\n\nQuit my job. Built aou  "text": "Life update 🌿\n\nQuit my job. Built an API. Now 200 users ima  "text": "Life update 🌿\n\nne bre  "text": "Life update 🌿\n\nQui- O  "text": "Life update 🌿\n\nQuit --  "text": "Life update �_youtube_title` — Score a YouTube Title

**Request:**
```json
{
  "text": "I Built an API in 48 Hours (Here's What Happened)"
}
```

**Scoring signals:**
- Optimal length (40–60 chars for CTR)
- Numbers in title
- Brackets or parentheses (adds context, boosts CTR)
- Power words
- Curiosity gap signals

---

### 6. `POST /v1/score_youtube_description` — Score a YouTube Description

**Scoring signals:**
- SEO keyword density in first 150 chars
- Timestamps / chapter marks present
- External links
- CTA placement
- Subscribe prompt

---

### 7. `POST /v1/score_email_subject` — Score an Email Subject Line

**Request:**
```json
{
  "tex  "tex  "teft  "texhing  "tex  "tex  "teft  "texhing  "tex  "tex  "teft  "texhing  "tex  "tex  "teft  "texhing  "tex  "tex  "teft  "texhing  "tex  "tex  "teft  "texhing  "tex  "tex  "teft  "texhing  "tex  "tex  "teft  "texhing  "tex  "tex  "teft  "texhing  "tex  "tex  "teft  "texhing  "tex  "tex  "teft  "texhing  "tex  "tex  "teft  "texhing  "tex  "tex  "teft  "texhing  "tex  "tex  "teft  "texhing  "tex  "tex  "teate  "tex  "teiche + trend  "tex  "tex  "teft  "texhing  "tex  "tex  "teft  "texhing  chars

---

### 9. `POST /v1/s### 9. `POST /v1/s### 9. `POST /v1/ost

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
- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor-rat-  gr- Keywor- Keywor- Keywor- Keywor- Keywor- Keywor- Keyw**
`````````````````ch_re`````````````````c
  "  "  "  "  "id_gr  "  "  "  "  "id_gr  "  "  "  "  "id_gr  "  "  "  "  "id_":  "  "  "  "de":  B"
}
```

---

### 14. `POST /v1/analyze_hashtags` — Analyze Hashtags

Check a list of hashtags for spam risk, overuse, uniqueness, and per-Check a list o
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

### 15. `POST /v1/score_multi` — Score Across All Platforms at Once

Send one piece of text, get scores for every platform in a single call.

**Request:**
```json
{
  "text": "Built a tool that scores your content before you post. 28 endpoints, free tier. 🔗"
}
```

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

### 16. `POST /v1/batch_score` — Batch Score Multiple Dra### 16. `POST /v1/batch_score` — Batch Score Multiple Dra### 16. `POST /v1/batches### 1st — g###  for A### 16. `POST /v1/batch_score` — Batch Score Multiple Dra### 16. `POST /v1Bui### 16. `POST /v1/batc",
    "I    "I  n API    48 hour    "I    "s th    "I    "I  n API    48 hour    "I    "s th    "I    "I  n API    48 houw I did it."
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

These endpoints calThesmini 2.5 Flash and respond in 1–4 seconds. They **consume AI call quota** from yoThese endpoints calThesmini 2.5 Flash and rest AI quota.

---

### 17. `POST /v1/improve_headline` — Improve a Headline with AI

Takes a weakTaeadlTne, identifies its problems, and generates N better AI-written versions — each scored and sorted best-first.

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
    { "text": "Can You Really Earn $5,000 a Month Online? Discover the Secrets", "score":  00, "grad    { "text": "Can You Really Earn $5,s to     { "text": "Can You Really Earn $5,000 a Month Online? Discover the Secrets", "score":  00, "grad    { "text": "Can You Really Earn $5,s to     { "text": "Can`

**Recommended workflow:**
1. Call `analyze_headline` → get score + suggestions
2. If score < 80, call `improve_headline` → get 3 better versions
3. Pick the top-scored version → publish

---

### 18### 18### 1/generate_ho### 18### 18### 1/generate_ho### 18#at### 18###stopping op### 18### 1ny top### 18### 18### 1/generate_ho### 1s.


## 18### 18###`js## 18### 18###`js## 18#ng a SaaS while working a full-time job",
  "count": 4
}
```

**Response:***Response:***Response:***Res"Nobody tells you how hard it is to ship at midnight when your 9–5 drained you dry.",
    "I built a SaaS between 10pm and 1am for 6 months. Here's the honest truth.",
    "Most 'side project' advice is wri    "Most 'side project their job first.",
    "72 hours a week. 1 product. Zero regrets."
  ]
}
```

---

### 19. `POST /v1/rewrite` — Rewrite for Any Platform

Platform-optimized rewrite. Respects each platform's character limits automatically.

**Request:**
```json
{
  "text": "I launched a content scoring API and got 200 use  "text": "I launched a 
                                                    ield | Type | Required | Options |
|---|---|---|---|
| `text` | string | ✅ | — |
| `platform` | string | ✅ | `twitt| `platform` | string | ✅ | `twitt| `platform` | string | ✅ | `twitt| `platform` | string | ✅ | `twitt| `platform` | string | ✅ | `s fo| `platform` | string | ✅ | `twitt| `platform` | string | ✅ | `twitt| `platfns| `play hooks, | d l| `platform` | string | ✅ | `twitt| `platform` | string | ✅ | `twitt| `platform` | string | ✅ | `twitt| `platform` | str Ge| `platform` | string | ✅ | `twitt| `platform` | string | ✅ | `twitt| `platfst drafts.

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
  "ca  ndar": [
    { "day": "Monday", "theme": "Mindset", "draft":    { "day": "Monday", "theme": "Mindset", "draft":    { "day": "Monday", "theme": ��"    { "da "da    { uesday", "theme": "Quick Win", "draft": "One thing you can do today to save $200/month..    { "day": "Monday", "theme": "Mindset", "draft":    { "day": "Monday", "theme": "M
CCCCCCCCCCCCCCCCCthCCCCCCCCCCCCCCCCCthCCCCCCCCCCnumbered body + CTA.

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
  "cta": "Follow for weekly API build breakdowns. Bookmark this if you're planning to   "cta": "Follow for weekly API build breakdonerate_bio` — Generate a Social  "cta Bio

Optimized biOptimized brrectOptimized biOptimized brrectOptimized biOptimized brrectOptimized biOptimized brrectOptimized biOptimized brrectOptimized biOptimized brrectOptimized biOptimized brrectOptimized biOptimized brrectOptimized biOptimized brrectOptimized biOptimized brrectOptimized biOptimized brrectOptimized biOptimized brrectOptimized biOptimize |Optimized biOptimized brrectOptimized biOptimized brrectOptimized b150 chars) |

**Response:***Response:***Response:***Response:***Responso-**Response:***Res, si** in**Response:*ng**Respblic | Follow for weekly breakdowns",
  "char_count": 104,
  "char_limit": 160
}
```

---

### 24. `POST /v1/generate_caption` — Generate a Social Caption

IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIest:**
IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIatform"IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIatform"IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIatform"IIIIIIIIIIIIIIIIIIIIIIIIIIIIA. Formatted for the platform's algorithm.

**Request:**
```json
{
  "topic": "lessons from building in public for 6 months"
}
```

---

### 26. `POST /v1/generate_email_sequence` — Generate a 3-Email Drip Sequence

Returns a 3-part email drip: welcome → value → pitch. Subject lines included for each.

**Request:**
```json
{
  "product": "ContentForge API",
  "audience": "indie hackers and content creators"
}
```

**Response:**
```json
{
  "emails": [  "emails": [  "emails": [  "emails": [  "emails": [  "emails": [  "emails": [  "emails": [  "emails": [  "emails": [  "emails": [  "emails":ni  "emails": [  "em     "emails": [ence": 2,
      "subject": "The one thing most creators skip before posting",
      "body": "Most people post and hope. Here's a better way..."
    },
    {
      "seque      "seque      "seque      "seque      "seque      "seque      "seque      "seque      "seque      "seque      "seque      "seque      "seque      "seque      "seque      "seque      "seque      "seque      "seque      "seque      "seque      "seque      rge   udience, c       angle, SEO keyword suggestions, outline, and 5 hook options.

***equ*st:****equ*st:****equ*st:****equ*st:****equ*st:****equ*st:****equ*st:****equ*st:*ndie***equ*st:****equ*st:****equ*st:****equ*st:****equ*st:****equ*st:****equ*st:****equ*st:*rm a***equ*st:iants for Facebook, Google, and Twitter/X.

*****************************duct": "ContentForge",
  "benef  "be"score yo  "content  "benef  "be"score yo  "content  "benef  "be"score yo  "content  "benef  "be"score yo  "content  "benef  "be"score yo  "content  "benef  "be"score yo  "content  "benef  "be"score yo  "content  "bent   "benef  "be"score yo  "content  "benef  "be"score yo  "content  Li  "benef  "be"score yo  "content  "benef  "be"score yo  "contenteq  "be|
| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **on | **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR|//c| **PR| **PR| **PR| **PR| **PR| **PR| **PR| **PR:** https://github.com/CaptainFredric/ContentForge
