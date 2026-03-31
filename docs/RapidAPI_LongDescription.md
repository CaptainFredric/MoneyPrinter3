# ContentForge — AI Content Toolkit for Creators & Developers

**ContentForge** is a fast, reliable REST API that helps creators, marketers, indie hackers, and developers produce high-performing content without the guesswork.

Whether you want to score a tweet before you post it, rewrite a headline for LinkedIn, fill a 7-day content calendar, or rank 20 draft variations to find the best one — ContentForge handles it from a single API.

---

## What You Can Do (28 Endpoints)

### Instant Scorers — no AI, zero latency

| Endpoint | What It Does |
|---|---|
| `POST /v1/analyze_headline` | Score any headline 0–100 + letter grade + specific improvement tips |
| `POST /v1/score_tweet` | Score a tweet draft for engagement potential (length, hashtags, emojis, power words) |
| `POST /v1/score_instagram` | Score an Instagram caption for engagement and reach |
| `POST /v1/score_linkedin_post` | Score a LinkedIn post for reach and professional engagement |
| `POST /v1/score_tiktok` | Score a TikTok caption for virality and discovery |
| `POST /v1/score_threads` | Score a Meta Threads post for reach and engagement |
| `POST /v1/score_facebook` | Score a Facebook organic post for reach and shares |
| `POST /v1/score_pinterest` | Score a Pinterest pin description for saves and traffic |
| `POST /v1/score_youtube_title` | Score a YouTube title for CTR potential |
| `POST /v1/score_youtube_description` | Score a YouTube description for SEO and viewer value |
| `POST /v1/score_email_subject` | Score an email subject line for open rate |
| `POST /v1/score_ad_copy` | Score Google or Meta ad copy for CTR potential |
| `POST /v1/score_readability` | Flesch-Kincaid readability score for any text |
| `POST /v1/score_multi` | Score one text across multiple platforms in a single call, ranked by best fit |
| `POST /v1/batch_score` | Score up to 20 draft variations against one platform and get them ranked — pick your best before posting |
| `POST /v1/analyze_hashtags` | Analyze a set of hashtags for quality, diversity, and platform fit |
| `GET /health` | Service health check, version info, and usage stats |

### AI Generators — powered by Gemini

| Endpoint | What It Does |
|---|---|
| `POST /v1/improve_headline` | Takes a weak headline, identifies its problems, returns N rewritten versions each scored and ranked |
| `POST /v1/generate_hooks` | Generates scroll-stopping hooks for any topic in viral, professional, or casual tone |
| `POST /v1/rewrite` | Rewrites any text for a target platform (Twitter, LinkedIn, email, blog) with tone control |
| `POST /v1/tweet_ideas` | Generates tweet ideas tailored to your niche — hot takes, tips, questions, story hooks, and lists |
| `POST /v1/content_calendar` | Builds a full 7-day content calendar with daily themes and ready-to-post drafts |
| `POST /v1/thread_outline` | Generates a complete Twitter thread: scroll-stopping hook + numbered body tweets + CTA |
| `POST /v1/generate_bio` | Writes an optimized social media bio for Twitter (160 chars), LinkedIn (300), or Instagram (150) |
| `POST /v1/generate_caption` | Generates an Instagram or TikTok caption with hashtags and a CTA |
| `POST /v1/generate_linkedin_post` | Generates a full LinkedIn post in storytelling, professional, or motivational format |
| `POST /v1/generate_email_sequence` | Generates a 3-email drip sequence: hook email, value email, CTA email |
| `POST /v1/generate_content_brief` | Generates a content brief with outline, target keywords, angle, and hook suggestions |

---

## Why ContentForge?

**Before posting, not after.** Most creators wing it and wonder why posts flop. ContentForge gives you data-backed scoring before you hit publish so you only post A-grade content.

**Instant and AI in one place.** The scoring endpoints return results in milliseconds with zero AI cost — perfect for high-volume use or building into a workflow. AI endpoints are powered by Gemini and typically respond in 1–8 seconds.

**Precise, actionable feedback.** Every score comes with a letter grade (A–D) and specific suggestions. Not "this could be better" — it tells you exactly what to fix and why.

**Built for automation.** Use it in your CMS, a Zapier workflow, a CI content check, or your own Twitter bot. Clean JSON, consistent schemas, CORS enabled, no session state.

---

## Quick Example

Score a tweet draft before posting:

```bash
curl -X POST https://contentforge-api-lpp9.onrender.com/v1/score_tweet \
  -H "X-RapidAPI-Key: YOUR_RAPIDAPI_KEY" \
  -H "X-RapidAPI-Host: contentforge1.p.rapidapi.com" \
  -H "Content-Type: application/json" \
  -d '{"text": "I built an API in 48 hours. It made $500 last month 💸 Here'\''s how: #buildinpublic"}'
```

Response:
```json
{
  "text": "I built an API in 48 hours...",
  "score": 83,
  "grade": "A",
  "char_count": 87,
  "hashtag_count": 1,
  "emoji_count": 1,
  "power_words_found": ["built"],
  "suggestions": ["Try starting with a number or a question for a stronger hook."]
}
```

Rank 20 drafts and get the best one back:

```bash
curl -X POST https://contentforge-api-lpp9.onrender.com/v1/batch_score \
  -H "X-RapidAPI-Key: YOUR_RAPIDAPI_KEY" \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Draft A...", "Draft B...", "Draft C..."], "platform": "tweet"}'
```

Response includes results ranked by score with the best draft highlighted.

---

## How Scoring Works

### Headline Scoring (`analyze_headline`)
- **Length** — Optimal range 30–80 chars
- **Power words** — 60+ tracked across urgency, money, social proof, curiosity, and ease categories
- **Numbers** — Specific numbers boost credibility and CTR
- **Emotional triggers** — Questions, exclamations, all-caps emphasis
- **Structure** — Word count and caps ratio

### Tweet Scoring (`score_tweet`)
- **Length** — Optimal 71–100 chars (best), 50–140 (good)
- **Hashtags** — 1–2 is optimal; 4+ dilutes engagement and gets penalized
- **Emojis** — 1–3 boosts score; 0 or heavy emoji use gets downgraded
- **Power words** — Same 60+ word library
- **Readability** — Shorter average word length scores higher
- **Hook strength** — Posts starting with a number or question get a bonus

### Platform-Specific Scoring
Each platform scorer is tuned independently. LinkedIn rewards length and personal storytelling. Instagram rewards hashtag density and CTR. TikTok rewards hooks, trending format, and engagement bait. YouTube titles are scored for CTR patterns and length. Every scorer returns a letter grade and 2–4 specific suggestions.

---

---

## Use Cases

- **Bloggers and Newsletter Writers** — Score every headline with `analyze_headline` before hitting publish. Never post a C-grade headline again.
- **Twitter Power Users** — Draft several versions, run them through `batch_score`, and only post the highest-ranked one.
- **Twitter Bot Builders** — Pipe generated tweets through `score_tweet` before auto-posting. Only publish A/B-grade content automatically.
- **Content Agencies** — Generate a full month of content per client with `content_calendar` and `tweet_ideas`. Cut production time dramatically.
- **Indie Hackers and Founders** — Use `generate_hooks` and `thread_outline` to turn a product update into a viral thread in under a minute.
- **Copywriters** — `rewrite` any copy for a different platform or tone instantly. One piece of content repurposed for Twitter, LinkedIn, email, and blog in four API calls.
- **Email Marketers** — Score subject lines with `score_email_subject` for higher open rates before every send.
- **New Creators** — Generate your first professional social bio with `generate_bio`. Works for Twitter, LinkedIn, and Instagram.
- **CMS and Workflow Builders** — Drop `analyze_headline` or `score_tweet` into any Zapier, Make, or n8n workflow as a quality gate before publish.
- **Developers Building Content Tools** — Use the full 28-endpoint suite to power your own content scoring, generation, or optimization product.

---

## Plans

All plans share a server-side rate limit of **30 requests/minute**. Plans are differentiated by AI calls and total requests per month. Instant endpoints (`analyze_headline`, `score_tweet`, `score_*`, `batch_score`, `analyze_hashtags`, `health`) do not consume AI calls and do not count toward your AI call quota.

| Plan | Price | AI Calls/Month | Requests/Month | Rate Limit |
|---|---|---|---|---|
| BASIC | Free | 50 | 300 | 30 req/min |
| PRO | $9.99/mo | 750 | 1,000 | 30 req/min |
| ULTRA | $29.99/mo | 3,000 | 4,000 | 30 req/min |
| MEGA | $99/mo | 18,000 | 20,000 | 30 req/min |

Need a custom plan for higher volume or white-label use? Email captainarmoreddude@gmail.com.

---

## Support

- **Email**: captainarmoreddude@gmail.com
- **RapidAPI Discussions**: Use the Discussions tab on this API's RapidAPI page
- **GitHub**: https://github.com/CaptainFredric/ContentForge
