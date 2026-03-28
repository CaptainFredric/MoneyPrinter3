# ContentForge — AI Content Toolkit for Creators & Developers

**ContentForge** is a fast, reliable REST API that helps creators, marketers, indie hackers, and developers produce high-performing content without the guesswork.

Whether you're trying to get more clicks on a blog post headline, craft tweets that actually drive engagement, or fill a 7-day content calendar in seconds — ContentForge does the heavy lifting.

---

## What You Can Do

| Endpoint | What It Does | AI? |
|---|---|---|
| `POST /v1/analyze_headline` | Score any headline 0–100 + letter grade + tips | Instant |
| `POST /v1/score_tweet` | Score any tweet draft for engagement potential | Instant |
| `POST /v1/improve_headline` | Get N AI-rewritten, scored versions of a weak headline | AI |
| `POST /v1/generate_hooks` | Generate scroll-stopping hook lines for any topic | AI |
| `POST /v1/rewrite` | Rewrite text for Twitter, LinkedIn, email, blog | AI |
| `POST /v1/tweet_ideas` | Get tweet ideas + hashtags for any niche | AI |
| `POST /v1/content_calendar` | Build a 7-day content calendar for any niche | AI |
| `POST /v1/thread_outline` | Generate a full Twitter thread (hook + body + CTA) | AI |
| `POST /v1/generate_bio` | Write an optimized social bio (Twitter/LinkedIn/Instagram) | AI |

---

## Why ContentForge?

**Before posting, not after.** Most creators wing it and wonder why posts flop. ContentForge gives you data-backed scoring before you hit publish — so you only post A-grade content.

**Instant + AI endpoints in one place.** Two endpoints (`analyze_headline` and `score_tweet`) return results in milliseconds with zero AI cost — perfect for high-volume use cases. The remaining AI endpoints are powered by Gemini and return results in 1–8 seconds.

**Precise, actionable feedback.** Every score comes with a letter grade (A–D) and specific suggestions. Not just "this could be better" — it tells you *why* and *how*.

**Built for automation.** Use it in your CMS, your CI pipeline, your Zapier workflow, or your Twitter bot. Clean JSON responses, consistent schemas, CORS enabled.

---

## Quick Example

Score a tweet draft before posting:

```bash
curl -X POST https://contentforge-api-lpp9.onrender.com/v1/score_tweet \
  -H "X-RapidAPI-Key: YOUR_RAPIDAPI_KEY" \
  -H "X-RapidAPI-Host: contentforge1.p.rapidapi.com" \
  -H "Content-Type: application/json" \
  -d '{"text": "I built an API in 48 hours. It made $500 last month 💸 Here'\''s exactly how: #buildinpublic"}'
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
  "suggestions": []
}
```

---

## How Scoring Works

### Headline Scoring (`analyze_headline`)
- **Length** — Optimal range 30–80 chars
- **Power words** — 60+ tracked (urgency, money, social proof, curiosity, ease)
- **Numbers** — Specific numbers boost credibility
- **Emotional triggers** — Questions, exclamations, all-caps emphasis
- **Structure** — Word count, caps ratio

### Tweet Scoring (`score_tweet`)
- **Length** — Optimal 71–100 chars (best), 50–140 (good)
- **Hashtag count** — 1-2 optimal; more dilutes engagement
- **Emoji presence** — Adds visual pop without overdoing it
- **Power words** — Same 60+ word set
- **Readability** — Shorter average word length scores higher

---

## Use Cases

- **Bloggers & Newsletter Writers** — `analyze_headline` every post before publish
- **Twitter Power Users** — Draft → `score_tweet` → only post A/B-grade content
- **Content Agencies** — Generate full monthly calendars with `content_calendar`
- **Indie Hackers / Product Builders** — Get daily `tweet_ideas` for your niche
- **Copywriters** — `rewrite` any text for a different platform in seconds
- **Email Marketers** — Score subject lines with `analyze_headline` for higher open rates
- **Thread Writers** — `thread_outline` a 7-tweet thread in under 10 seconds
- **New Creators** — `generate_bio` a professional social profile bio instantly

---

## Plans

All plans share a server-side rate limit of **30 requests/minute**. Plans are differentiated by AI calls per month. Instant endpoints (`analyze_headline`, `score_tweet`, `health`) do not consume AI calls.

| Plan | Price | AI Calls/Month | Rate Limit |
|---|---|---|---|
| BASIC | Free | 50 | 30 req/min |
| PRO | $9.99/mo | 750 | 30 req/min |
| ULTRA | $29.99/mo | 3,000 | 30 req/min |
| MEGA | $99/mo | 18,000 | 30 req/min |

Need something custom? Email captainarmoreddude@gmail.com.
