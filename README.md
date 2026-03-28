# MoneyPrinter V2 — ContentForge Edition

A Python 3.12 automation platform that runs Twitter bots, generates AI content, and monetizes through a public API on RapidAPI.

> Fork of [FujiwaraChoki/MoneyPrinterV2](https://github.com/FujiwaraChoki/MoneyPrinterV2) — extended with multi-account state management, ContentForge API, and deployment automation.

---

## Current Status (March 28, 2026)

| Component | Status | Notes |
|---|---|---|
| **ContentForge API** | ✅ Live | `https://contentforge-api-lpp9.onrender.com` |
| **RapidAPI Listing** | ✅ Public | All 5 endpoints, 4-tier pricing configured |
| **Twitter bot: niche_launch_1** | ✅ Active | health=50, 2 verified posts |
| **Twitter bot: EyeCatcher** | ✅ Active | health=100, 1 verified post |
| **Gemini backend** | ✅ Configured | `gemini-2.0-flash` on Render |
| **Ollama local** | ✅ Running | `llama3.2:3b` at `http://127.0.0.1:11434` |
| **Keep-warm cron** | ✅ Active | cron-job.org pings `/health` every 10 min |
| **Legal docs** | ✅ Done | `docs/TERMS_OF_USE.md`, `docs/TERMS_AND_CONDITIONS.md` |

---

## What This Does

1. **Twitter Bots** — AI-generated posts (copywriting tips, attention psychology) published on schedule via Selenium + Firefox profiles
2. **ContentForge API** — Flask API monetized on RapidAPI that scores headlines, generates hooks, rewrites text, and produces tweet ideas
3. **YouTube Shorts** — LLM script → TTS → image generation → MoviePy composite → Selenium upload
4. **Affiliate Marketing** — Amazon product scraping + AI pitch generation + Twitter posting
5. **Local Business Outreach** — Google Maps scraping (Go) → email extraction → cold outreach via SMTP

The bots drive traffic to the API. The API generates revenue. Zero upfront cost (Render free tier + Gemini free tier + RapidAPI free provider account).

---

## Quick Start

```bash
git clone https://github.com/CaptainFredric/MoneyPrinter3.git
cd MoneyPrinter3

# Copy config and fill in your values
cp config.example.json config.json

# macOS automated setup (creates venv, installs deps, configures Ollama + ImageMagick)
bash scripts/setup_local.sh

# Or manual setup
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Validate everything works
python3 scripts/preflight_local.py

# Run
python3 src/main.py
```

> **Requirements**: Python 3.12, Firefox (with pre-authenticated profiles for bot accounts), ImageMagick (for video subtitles), Ollama or Gemini API key (for AI generation).

---

## ContentForge API

A monetized API product hosted on Render and listed on RapidAPI.

| Endpoint | What It Does |
|---|---|
| `POST /v1/analyze_headline` | Score any headline (0–100) with word-level feedback and suggestions. Instant, no AI needed. |
| `POST /v1/generate_hooks` | Generate scroll-stopping openers for a topic. Viral, professional, or casual style. |
| `POST /v1/rewrite` | Rewrite text for Twitter, LinkedIn, email, or blog with tone control. |
| `POST /v1/tweet_ideas` | Generate tweet ideas for any niche with hashtags. Mix of hot takes, tips, and questions. |
| `GET /health` | Service health check with LLM backend detection. |

**Pricing tiers** (via RapidAPI — live):
- **BASIC** — Free, 50 AI objects + 30 requests/month
- **PRO** — $9.99/month, 750 AI objects + 1,000 requests
- **ULTRA** — $29.99/month, 3,000 AI objects + 4,000 requests
- **MEGA** — $99/month, 18,000 AI objects + 20,000 requests

Full deployment guide: [docs/ContentForge_Deploy.md](docs/ContentForge_Deploy.md)

---

## Phase 2: Multi-Account State Machine

The bot system uses an intelligent state machine for multi-account management:

- **5 account states**: active, cooldown, degraded, blocked, paused
- **Health scoring** (0–100): verified posts heal, failures degrade
- **Automatic account rotation**: best-eligible account selected each cycle
- **Exponential backoff**: blocked accounts retry at 1h → 6h → 24h → 72h
- **Auto-pause**: 2+ consecutive low-confidence posts triggers a 30-min pause
- **Transaction logging**: full audit trail in `logs/transaction_log/`
- **Persistent state**: survives process restarts (`.mp/runtime/account_states.json`)

### Phase 3: Publish Verification

- Multi-strategy permalink resolution (URL match, text match, similarity search)
- ~60%+ verification rate (up from ~30%)
- Enhanced text normalization for consistent comparison

---

## Bot Accounts

| Account | Niche | Firefox Profile |
|---|---|---|
| `niche_launch_1` (NicheNewton) | Content creation, copywriting psychology, headlines | Firefox Developer Edition |
| `EyeCatcher` | Psychology of attention, visual storytelling, pattern interrupts | Firefox (regular) |

Both accounts are pre-configured in `.mp/twitter.json` with their own Firefox profiles, voice styles, and content strategies.

---

## Project Structure

```
src/
├── main.py                  # Interactive CLI menu (primary entrypoint)
├── cron.py                  # Headless runner for scheduled posts
├── config.py                # Config getters (reads config.json)
├── cache.py                 # JSON persistence (.mp/ directory)
├── constants.py             # Menu strings, Selenium selectors
├── llm_provider.py          # Ollama SDK integration
├── account_state_machine.py # Phase 2 multi-account state management
├── firefox_runtime.py       # Firefox binary detection + profile management
├── classes/
│   ├── YouTube.py           # Full YouTube Shorts pipeline
│   ├── Twitter.py           # Tweet generation + Selenium posting
│   ├── Tts.py               # KittenTTS wrapper
│   ├── AFM.py               # Amazon affiliate marketing
│   └── Outreach.py          # Google Maps scraper + SMTP outreach
scripts/
├── api_prototype.py         # ContentForge Flask API (4 endpoints + health)
├── smart_post_twitter.py    # Headless smart posting (one-shot)
├── backfill_pending_twitter.py  # Retry failed/pending posts
├── verify_twitter_posts_phase3.py # Post verification with similarity search
├── session_restore.py       # Firefox cookie/session recovery
├── preflight_local.py       # Pre-run validation
├── setup_local.sh           # macOS bootstrap
├── money_idle_phase2.py     # Intelligent idle mode with account rotation
└── ...
deploy/
├── render.yaml              # Render Blueprint config
├── wsgi.py                  # WSGI entry for cloud deploy
├── openapi.json             # OpenAPI 3.0.3 spec for RapidAPI import
├── requirements-api.txt     # API-only dependencies
└── Procfile                 # Gunicorn start command
```

---

## Configuration

All config lives in `config.json` at the project root. See [config.example.json](config.example.json) and [docs/Configuration.md](docs/Configuration.md).

Key external dependencies:
- **Ollama** — local LLM (optional if using Gemini)
- **Gemini API** — cloud LLM fallback + image generation
- **ImageMagick** — MoviePy subtitle rendering
- **Firefox profiles** — pre-logged-in to target platforms
- **Go** — only needed for Outreach (Google Maps scraper)

> **Security**: Never commit `config.json` with real API keys. Use `config.example.json` as the template.

---

## Documentation

| Doc | What |
|---|---|
| [ContentForge_Deploy.md](docs/ContentForge_Deploy.md) | Full API deploy + RapidAPI monetization guide |
| [MonetizationPlan.md](docs/MonetizationPlan.md) | Revenue strategy and roadmap |
| [Configuration.md](docs/Configuration.md) | Config reference |
| [TwitterBot.md](docs/TwitterBot.md) | Twitter bot setup |
| [YouTube.md](docs/YouTube.md) | YouTube Shorts pipeline |
| [OPERATOR_GUIDE.md](docs/OPERATOR_GUIDE.md) | Day-to-day operations |
| [SAFEGUARDS_IMPLEMENTATION.md](docs/SAFEGUARDS_IMPLEMENTATION.md) | Safety and reliability features |
| [ProfileMapping.md](docs/ProfileMapping.md) | Firefox profile setup |
| [LoginRecovery.md](docs/LoginRecovery.md) | Session recovery procedures |
| [TERMS_OF_USE.md](docs/TERMS_OF_USE.md) | API Terms of Use (RapidAPI) |
| [TERMS_AND_CONDITIONS.md](docs/TERMS_AND_CONDITIONS.md) | Full Terms & Conditions |

---

## Scripts (Quick Reference)

```bash
# Smart post (headless, picks best account)
python scripts/smart_post_twitter.py --headless

# Backfill failed posts for an account
python scripts/backfill_pending_twitter.py --headless niche_launch_1

# Verify posted tweets actually published
python scripts/verify_twitter_posts_phase3.py niche_launch_1 --headless

# System health diagnostic
python scripts/health_diagnostic.py

# Readiness report
python scripts/twitter_readiness_report.py

# Idle mode (continuous posting with smart rotation)
python scripts/money_idle_phase2.py
```

---

## Contributing

PRs against `main`. One feature/fix per PR. Open an issue first. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Affero General Public License v3.0. See [LICENSE](LICENSE).

## Attribution

Based on [MoneyPrinterV2](https://github.com/FujiwaraChoki/MoneyPrinterV2) by [@DevBySami](https://x.com/DevBySami). Original project: automated content generation and monetization. This fork adds ContentForge API, multi-account state management, and deployment automation.
