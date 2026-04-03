# Saturday Showoff: I built a deterministic content scoring API because LLMs kept giving me different answers

I've been building ContentForge for the past few months and wanted to share the approach, because it goes against the grain of what everyone seems to be doing right now.

## The problem

I wanted a "quality gate" for social media content — something that scores a tweet or LinkedIn post before publishing and blocks anything below a threshold. Simple enough. So I started with an LLM-based scorer.

The issue: ask GPT or Claude to score the same tweet twice and you'll get different numbers. Not wildly different, but enough. A post that scores 72 on one call scores 61 on the next. For a quality gate that decides "publish" vs. "hold," that variance is a deal-breaker. You can't build reliable automation on a system that changes its mind.

## The solution: heuristics, not inference

I scrapped the LLM scorer and built a deterministic heuristic engine instead. Pure Python rules mapped to each platform's documented best practices. Character length, hashtag density, question usage, CTA presence, readability grade, emoji distribution, hook strength — about 30 signals per platform, weighted and summed into a 0-100 score.

Same input, same score, every time. Zero variance.

The API now has 45 endpoints covering 12 platforms (Twitter, LinkedIn, Instagram, TikTok, YouTube, Pinterest, Reddit, Threads, Facebook, email subjects, ad copy, and general readability). Every scoring endpoint returns in under 50ms. No model loading, no token generation, no inference cost.

```bash
curl -X POST https://contentforge-api-lpp9.onrender.com/v1/score_tweet \
  -H "Content-Type: application/json" \
  -d '{"text": "Just shipped a new feature. Check it out."}'
```

```json
{
  "score": 38,
  "grade": "D",
  "quality_gate": "FAILED",
  "suggestions": [
    "Add a hook or question to stop the scroll",
    "Include 1-3 relevant hashtags",
    "Specify what the feature does — vague CTAs underperform",
    "Consider adding a metric or result to build credibility"
  ]
}
```

Every deduction is itemized. You can read the scoring logic in the source and trace exactly why a post scored 38 and not 72.

## The trade-off (and I'm honest about it)

LLMs are smarter. They understand nuance, tone, cultural context, and sarcasm in ways a heuristic engine never will. A rule that says "questions boost engagement" doesn't know the difference between a genuine question and a rhetorical one.

But for a quality gate? I'll take consistent and fast over smart and unpredictable:

| | Heuristic scoring | LLM-based scoring |
|---|---|---|
| Latency | <50ms | 1-5s |
| Variance | 0% | ~15-30% |
| Cost per call | $0 | $0.001-0.01 |
| Explainability | Every deduction shown | Black box |

AI is still in the system — it's just not in the scoring path. Rewrites, hook generation, bio generation, and subject line optimization all use Gemini 2.5 Flash (with local Ollama as first choice). Generation is where LLMs shine. Measurement is where they don't.

## Stack

- **API:** Flask, deployed on Render (free tier with keep-warm cron)
- **Scoring engine:** Pure Python, no ML dependencies
- **AI generation:** Ollama locally, Gemini 2.5 Flash as fallback
- **Chrome extension:** Manifest V3, injects a floating score badge on X/Twitter, LinkedIn, Instagram, Threads, Facebook — scores as you type
- **Extension popup:** Score any text for any of the 12 platforms, A/B compare two drafts, AI rewrite with tone selection

The Chrome extension also has an offline fallback. If the API is cold or unreachable, it runs local heuristics so you still get a score.

## What I'd do differently

I underestimated how much time platform-specific rules take to calibrate. Twitter rewards brevity and hooks. LinkedIn rewards paragraph breaks and professional framing. Pinterest is all about keyword density in descriptions. Each platform is basically its own scoring module, and keeping 12 of them accurate is an ongoing job.

I also wish I'd built the extension first. The API is useful for automation pipelines, but the extension is what people actually want to use day-to-day.

## Links

- **GitHub:** https://github.com/CaptainFredric/ContentForge (AGPL-3.0, self-hostable)
- **Landing page / live demo:** https://captainfredric.github.io/ContentForge/ (try the scorer without signing up)
- **RapidAPI:** https://rapidapi.com/captainarmoreddude/api/contentforge1 (free tier, 300 req/month)

Happy to answer questions about the heuristic design, the extension architecture, or the trade-offs around deterministic vs. LLM scoring.
