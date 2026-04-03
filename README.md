# ContentForge — Content Intelligence API

> **45 endpoints · 12 platforms · Deterministic scoring in <50ms · No AI hallucinations**

Score content before you post. ContentForge is a **Content Intelligence API** — a before-publish quality gate that grades every tweet, LinkedIn post, headline, and ad copy with a deterministic A–F score, actionable suggestions, and a `PASSED | REVIEW | FAILED` verdict in under 50ms — no LLM involved in the scoring layer.

Think of it as a **digital ruler for content quality**. A ruler doesn't need a dataset to tell you something is 12 inches long — it just needs to be correctly calibrated. ContentForge's heuristic engine is that ruler: zero variance on the same input, zero hallucinations, fully auditable open-source logic. AI (Ollama or Gemini) kicks in only for generation endpoints like rewrites, hooks, and subject lines.

```python
import requests

HEADERS = {"X-RapidAPI-Key": "YOUR_KEY", "X-RapidAPI-Host": "contentforge1.p.rapidapi.com"}

r = requests.post("https://contentforge1.p.rapidapi.com/v1/score_tweet",
    headers=HEADERS,
    json={"text": "I'm working on a new project."})
# → {"score": 32, "grade": "C", "quality_gate": "FAILED", "suggestions": [...]}

r = requests.post("https://contentforge1.p.rapidapi.com/v1/score_tweet",
    headers=HEADERS,
    json={"text": "Got 100 signups in 24 hours 🚀 Here's the copy that converted: #buildinpublic"})
# → {"score": 91, "grade": "A", "quality_gate": "PASSED", "suggestions": []}
```

**→ [Start free on RapidAPI](https://rapidapi.com/captainarmoreddude/api/contentforge1)** — no credit card required, 300 requests/month on BASIC.

---

## Current Status (v1.9.0)

| Component | Status | Notes |
|---|---|---|
| **ContentForge API** | ✅ Live | `https://contentforge-api-lpp9.onrender.com` |
| **RapidAPI Listing** | ✅ Public | 45 endpoints, 4-tier pricing |
| **Keep-warm cron** | ✅ Active | cron-job.org pings `/health` every 10 min, 60s timeout |
| **Gemini backend** | ✅ Configured | `gemini-2.5-flash` on Render (AI generation fallback) |
| **Ollama local** | ✅ Running | Scoring uses zero AI calls — pure heuristics |
| **Twitter bots** | ✅ Active | Multi-account state machine, health scoring |
| **Legal docs** | ✅ Done | `docs/TERMS_OF_USE.md`, `docs/TERMS_AND_CONDITIONS.md` |

---

## Why Deterministic Scoring?

Every LLM-based scorer has the same flaw: ask it to score the same tweet twice and you'll get two different answers. For a professional content workflow, that's not a tool — that's a vibe check.

ContentForge's scoring layer is pure Python heuristics. Same input → same output, every time. The logic is open source; you can read exactly why a post scored 74 and not 83. This is the **Deterministic Advantage**:

| | ContentForge | LLM-based scoring |
|---|---|---|
| Response time | <50ms | 1–5 seconds |
| Variance on same input | 0% | ~15–30% |
| Explainability | Full — every deduction itemised | Black box |
| Cost per call | Free (heuristics) | $0.001–0.01 per call |
| Self-hostable | ✅ (`python scripts/api_prototype.py`) | Depends on provider |

---

## All 45 Endpoints

### Instant Scorers (no AI, <50ms)
| Endpoint | What It Does |
|---|---|
| `POST /v1/score_tweet` | Score a tweet 0–100 with grade + quality gate |
| `POST /v1/score_linkedin_post` | Score a LinkedIn post for professional engagement |
| `POST /v1/score_instagram` | Score an Instagram caption for saves and reach |
| `POST /v1/score_youtube_title` | Score a YouTube title for CTR and SEO |
| `POST /v1/score_youtube_description` | Score a YouTube description for watch time |
| `POST /v1/score_email_subject` | Score an email subject line for open rate |
| `POST /v1/score_readability` | Flesch–Kincaid + grade level + suggestions |
| `POST /v1/score_threads` | Score a Threads post |
| `POST /v1/score_facebook` | Score a Facebook post |
| `POST /v1/score_tiktok` | Score a TikTok caption |
| `POST /v1/score_pinterest` | Score a Pinterest pin description |
| `POST /v1/score_reddit` | Score a Reddit post/title |
| `POST /v1/analyze_headline` | Headline power word detection + CTR scoring |
| `POST /v1/analyze_hashtags` | Hashtag strategy audit across platforms |
| `POST /v1/score_content` | Single unified endpoint — pass `platform` param |
| `GET  /v1/analyze_headline` | GET variant for quick headline scoring |

### Multi-Content & Comparison
| Endpoint | What It Does |
|---|---|
| `POST /v1/score_multi` | Score one post across all platforms simultaneously |
| `POST /v1/ab_test` | Head-to-head score comparison of two drafts |

### AI Generation (Ollama → Gemini fallback)
| Endpoint | What It Does |
|---|---|
| `POST /v1/improve_headline` | Rewrite a weak headline N times, sorted by score |
| `POST /v1/generate_hooks` | Scroll-stopping openers for any topic/style |
| `POST /v1/rewrite` | Rewrite for Twitter, LinkedIn, email, or blog |
| `POST /v1/compose_assist` | Full draft generation with platform constraints |
| `POST /v1/tweet_ideas` | Tweet ideas for a niche with hashtags |
| `POST /v1/content_calendar` | 7-day content calendar with ready-to-post drafts |
| `POST /v1/thread_outline` | Full Twitter thread: hook + body + CTA close |
| `POST /v1/generate_bio` | Optimised social bio, auto-trimmed to platform limits |
| `POST /v1/generate_ad_copy` | Google/Meta ad copy with CTA and compliance signals |
| `POST /v1/generate_subject_line` | AI email subject line with open-rate optimisation |

### Quality Operations (QOps)
| Endpoint | What It Does |
|---|---|
| `POST /v1/quality_gate` | Batch PASSED/REVIEW/FAILED verdict for up to 10 posts |
| `GET  /v1/platform_friction` | Real-time platform state (rate limits, algo signals) |
| `POST /v1/proof_export` | Export scored posts + engagement delta as proof report |

### Utility
| Endpoint | What It Does |
|---|---|
| `GET  /health` | Service health: LLM backend, usage stats |
| `GET  /v1/status` | Lightweight ping — version, endpoint count |

*(Full 45-endpoint list with request/response schemas: [RapidAPI docs](https://rapidapi.com/captainarmoreddude/api/contentforge1))*

---

## Self-Hosting

ContentForge runs fully locally with Ollama. No external AI calls needed for scoring.

```bash
git clone https://github.com/CaptainFredric/ContentForge.git
cd ContentForge
pip install -r requirements.txt
python scripts/api_prototype.py
# → Listening on http://localhost:5000
```

What runs locally with zero external calls:
- All 12 platform scorers (deterministic, <50ms)
- Quality gate evaluation (`PASSED / REVIEW / FAILED`)
- Rate limiting and proof dashboard

What uses Ollama locally or falls back to Gemini:
- Hook generation, rewrites, bio generation, subject lines, ad copy

LLM chain: Ollama first → Gemini 2.5 Flash if Ollama unavailable → model rotation. If Ollama is running locally, nothing leaves your machine for AI calls.

**License**: AGPL-3.0

---

## Pricing (via RapidAPI)

| Plan | Price | AI calls/mo | Requests/mo |
|---|---|---|---|
| **BASIC** | Free | 50 | 300 |
| **PRO** | $9.99/mo | 750 | 1,000 |
| **ULTRA** | $29.99/mo | 3,000 | 4,000 |
| **MEGA** | $99/mo | 18,000 | 20,000 |

All plans include every endpoint. Heuristic scoring calls don't count against your AI quota.

**→ [Get your free API key](https://rapidapi.com/captainarmoreddude/api/contentforge1)**

---

## Architecture

```
scripts/
└── api_prototype.py         # ContentForge Flask API — all 45 endpoints
extension/
├── manifest.json            # Chrome extension (Manifest V3)
├── popup.html / popup.js    # Score, compare, rewrite from the toolbar
├── content.js / content.css # Real-time scoring badge on X, LinkedIn, etc.
└── background.js            # Service worker — API calls + offline fallback
deploy/
├── render.yaml              # Render Blueprint
├── openapi.json             # OpenAPI 3.0.3 spec (45 paths)
└── Procfile                 # Gunicorn start command
docs/
├── ContentForge_API_Documentation.md
└── RapidAPI_GettingStarted.md
```

---

## Contributing

PRs against `main`. One feature/fix per PR. Open an issue first. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Affero General Public License v3.0. See [LICENSE](LICENSE).

## Acknowledgements

Early development scaffolding adapted from [MoneyPrinterV2](https://github.com/FujiwaraChoki/MoneyPrinterV2) by [@DevBySami](https://x.com/DevBySami).
