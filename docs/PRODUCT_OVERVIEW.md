# ContentForge — Complete Product Overview

**Version: 1.9.0 | 45 Endpoints | AGPL-3.0**

> A deterministic, latency-first content intelligence platform for professional creators, agencies, and automation operators. Scores content before it's published, generates improved versions on demand, tracks proof of improvement over time, and monitors the state of an automated publishing network in real time.

---

## Table of Contents

1. [The Problem ContentForge Solves](#1-the-problem-contentforge-solves)
2. [Core Value Proposition](#2-core-value-proposition)
3. [Architecture Overview](#3-architecture-overview)
4. [Scoring Engine — Deterministic Heuristics](#4-scoring-engine--deterministic-heuristics)
5. [LLM Provider — Fallback Chain](#5-llm-provider--fallback-chain)
6. [QOps Layer — Quality Operations](#6-qops-layer--quality-operations)
7. [Account State Machine](#7-account-state-machine)
8. [Proof Dashboard — Evidence Intelligence](#8-proof-dashboard--evidence-intelligence)
9. [Platform Friction Monitor](#9-platform-friction-monitor)
10. [All 41 Endpoints — Full Reference](#10-all-41-endpoints--full-reference)
11. [Extension — Browser Intelligence Layer](#11-extension--browser-intelligence-layer)
12. [Deployment Architecture](#12-deployment-architecture)
13. [Configuration Reference](#13-configuration-reference)
14. [Security Model](#14-security-model)
15. [Agency & Operator Use Cases](#15-agency--operator-use-cases)
16. [Competitive Positioning](#16-competitive-positioning)
17. [AGPL Open Core Moat](#17-agpl-open-core-moat)
18. [Pricing & Commercial Structure](#18-pricing--commercial-structure)
19. [Data Storage & Persistence](#19-data-storage--persistence)
20. [Roadmap](#20-roadmap)

---

## 1. The Problem ContentForge Solves

Every content workflow has the same failure mode: you write something, publish it, and find out it underperformed two days later. The feedback loop is backwards. Most tools that try to fix this fall into one of two traps:

**Trap 1 — AI opacity**: Tools that run content through an LLM and return "make it more engaging" or a vague 8/10 score with no explanation. The feedback can't be acted on, reproduced, or explained to a client.

**Trap 2 — Platform monoculture**: Blog SEO tools that apply the same rubric regardless of platform. A LinkedIn post, a YouTube title, and a TikTok hook are scored by completely different rules. Applying a blog-scoring lens to a tweet destroys signal fidelity.

**Trap 3 — Latency cost**: Any tool that depends on LLM inference for every score incurs 2–10 second round-trip latency plus per-token cost. This makes the scoring loop expensive to run at scale and impractical for inline editor integration.

ContentForge solves all three with direct, rule-based scoring:

- Every platform's documented algorithmic best practices are mapped to explicit heuristic rules
- Scores are deterministic — same input, same output, always, at <50ms with zero AI token cost
- Improvement is opt-in AI: pay the inference cost only when you need a rewrite, not on every keystroke
- QOps fields make every score actionable for automated pipelines, agency reporting, and compliance review

---

## 2. Core Value Proposition

**Before-publish intelligence, not after-publish analytics.**

ContentForge operates at the decision point: the moment before a piece of content leaves the creator's hands. The system intercepts that moment and returns a structured verdict: a numeric score, a letter grade, a deterministic quality gate, and a concrete list of improvements the creator can act on immediately.

The information architecture is explicit by design:

```
Input text
    ↓
Platform-specific heuristic rules
    ↓
Score (0–100) + Grade (A/B/C/D)
    ↓
Quality gate (PASSED / REVIEW / FAILED)
    ↓
Operational risk band (LOW / MEDIUM / HIGH)
    ↓
Improvement suggestions (actionable, specific)
    ↓ [optional, if improvement requested]
AI-rewritten versions (scored, ranked)
    ↓
Lift percentage (measurable delta)
    ↓
Audit summary (LLM brief for agency sign-off)
```

The pipeline is auditable at every step. An agency reviewer can see exactly why a score is 47 vs 71, not because an AI decided so, but because specific named signals fired or didn't fire.

---

## 3. Architecture Overview

ContentForge is a Python 3.12 Flask application deployed on Render's free tier as a single-worker Gunicorn process. The architecture is deliberately minimal — no database, no async queue, no microservices — because latency and reliability matter more than horizontal scale at this stage.

```
Client (Browser / API / Extension)
    │
    ├── RapidAPI Gateway (auth + rate limiting)
    │       │
    │       └── Render Web Service
    │               │
    │               ├── scripts/api_prototype.py  [Flask app, 44 endpoints]
    │               │       │
    │               │       ├── Heuristic scoring engine  [_PLATFORM_SCORERS dict]
    │               │       ├── _quality_gate(score)       [QOps verdict]
    │               │       ├── _llm_generate(prompt)      [3-tier LLM fallback]
    │               │       ├── _proof_metrics()           [proof data aggregation]
    │               │       └── AccountStateMachine        [state management]
    │               │
    │               ├── src/account_state_machine.py  [state machine class]
    │               └── .mp/                          [JSON file stores]
    │                       ├── proof.json            [proof events, 5000 entry cap]
    │                       └── runtime/
    │                               └── account_states.json
    │
    └── Browser Extension (Manifest V3)
            ├── background.js   [service worker, API calls, retry logic]
            ├── popup.html/js   [inline scoring UI, quality gate badge]
            └── content.js      [inline badge injection on X.com/LinkedIn]
```

**Intentional design choices:**

- **One file for the app**: `scripts/api_prototype.py` is the entire API. No routing files, no model files, no service files. This is a deliberate choice for a solo-operated API — the entire system can be read and understood in one context window.
- **No database**: All persistence is flat JSON files under `.mp/`. This eliminates the single biggest source of external failure modes (DB connection drops, migration failures, schema drift).
- **Heuristic-first**: AI is never called for scoring. The heuristic engine runs in the same Python process, synchronously, in under 50ms. This means the API has no external dependencies for 19 of its 44 endpoints.
- **Import structure**: The app is run from the project root. `deploy/wsgi.py` explicitly adds `ROOT` and `ROOT/src` to `sys.path`, making all module imports work correctly on Render without package installation.

---

## 4. Scoring Engine — Deterministic Heuristics

The scoring engine is the core of ContentForge and the reason it's fast. It lives in `scripts/api_prototype.py` as a dict of scorer functions:

```python
_PLATFORM_SCORERS = {
    "tweet":          _score_tweet,
    "twitter":        _score_tweet,
    "linkedin":       _score_linkedin_post,
    "instagram":      _score_instagram,
    "tiktok":         _score_tiktok,
    "youtube":        _score_youtube_title,
    "email":          _score_email_subject,
    "threads":        _score_threads,
    "facebook":       _score_facebook,
    "pinterest":      _score_pinterest,
    "ad_copy":        _score_ad_copy,
    "readability":    _score_readability,
}
```

Each scorer function takes a text string and returns a dict containing at minimum `score` (0–100), `grade`, and `suggestions`. The functions are pure — no side effects, no external calls, no mutable state.

### Scoring Signal Taxonomy

Each platform scorer evaluates a specific set of signals. These signals are drawn from each platform's documented content performance research:

#### Tweet / Twitter Scorer (`_score_tweet`)
| Signal | Weight Rationale |
|--------|-----------------|
| Character count (71–280 optimal) | Engagement data shows 71–100 chars highest CTR |
| Hook strength (first 5 words) | Scroll-stopping ratio |
| Hashtag count (1–2 optimal) | >3 hashtags correlated with reach penalty |
| Emoji presence | Engagement lift signal |
| Call-to-action phrase | Reply/retweet prompt |
| Power word detection | 60+ words tracked: "proven", "secret", "free", "earn", etc. |
| ALL-CAPS ratio | Spam signal above 20% |
| Question mark | Engagement hook, small positive |

#### LinkedIn Post Scorer (`_score_linkedin_post`)
| Signal | Weight Rationale |
|--------|-----------------|
| Hook strength (first line) | Algorithm weights first-line CTR for "see more" clicks |
| Paragraph structure (short paragraphs) | Readability for professional feed |
| Hashtag count (3–5 optimal) | Over-tagging penalized by LinkedIn algorithm |
| Professional tone (no slang triggers) | Audience expectation alignment |
| Personal story signals | Higher engagement on first-person narrative |
| CTA presence | Connection request or comment prompt |
| Length (1,300–1,900 chars optimal) | LinkedIn carousel sweet spot |

#### YouTube Title Scorer (`_score_youtube_title`)
| Signal | Weight Rationale |
|--------|-----------------|
| Length (40–60 chars optimal) | SEO title truncation threshold |
| Number presence | CTR uplift from specificity |
| Bracket/parenthetical | "[2024]", "(Official)" — CTR tested |
| Power words | "Ultimate", "Complete", "How to" — thumbnail CTR signals |
| ALL-CAPS word | Emphasis pattern in high-CTR titles |
| Question mark | Discovery search signal |
| Clickbait spam flag | "You won't believe", "SHOCKING" — can suppress impressions |

#### Email Subject Line Scorer (`_score_email_subject`)
| Signal | Weight Rationale |
|--------|-----------------|
| Length (30–50 chars optimal) | Mobile preview truncation |
| Personalization token (`{{name}}`, `[FIRST NAME]`) | Open rate uplift |
| Number presence | Specificity signal |
| Urgency word | "Today", "Deadline", "Expires" — urgency premium |
| Spam trigger words | "Free!!!", "MAKE MONEY", "guaranteed" — filter risk |
| Question hook | Curiosity gap signal |
| Emoji in subject | Tested positive in B2C, negative in B2B |

#### Headline Analyzer (`_analyze_headline`)
The headline analyzer is distinct from the scorers — it performs deeper linguistic analysis:

- Detects 60+ categorized power words (urgency, achievement, curiosity, fear, social proof)
- Evaluates emotional trigger density
- Checks capitalization patterns (Title Case vs sentence case vs ALL-CAPS)
- Validates optimal length for news/blog headlines (50–70 chars)
- Counts specificity signals (numbers, names, dollars)
- Returns `power_words_found` as a list so integrations can display them

#### Readability Scorer (`_score_readability`)
Implements the Flesch-Kincaid algorithm specifically:

- **Flesch Reading Ease** (0–100, higher = easier)
- **Flesch-Kincaid Grade Level** (U.S. school grade equivalent)
- Average sentence length (words)
- Average syllable count per word (estimated by syllable approximation function)
- Reading level label: "Elementary", "Middle School", "High School", "College", "Graduate"
- Actionable suggestions: "Shorten sentences — average X words per sentence"

### Scoring Architecture: Why Heuristics Over AI for Scoring

This is a deliberate, defensible technical decision:

1. **Latency**: Heuristic scoring completes in <5ms in CPython. LLM inference via Gemini 2.5 Flash takes 800–4000ms round-trip. For inline editor use (extension sending a request on keystroke debounce), heuristic is the only viable option.

2. **Cost structure**: Zero marginal cost per heuristic score means unlimited-use free tier is sustainable.

3. **Reproducibility**: A score of 74 for a specific tweet should return 74 every time. An AI score might return 71 or 78 on different requests for the same text. Reproducibility is essential for:
   - A/B test validity (scoring both versions under the same conditions)
   - Proof system integrity (a delta of +12 points should be real signal, not noise)
   - Agency sign-off workflows (clients need to trust the number)

4. **Explainability**: Each suggestion is a deterministic string tied to a specific rule that fired. "Add a hashtag — optimal range 1–2" is auditable. "This content could be more engaging" is not.

5. **AGPL moat**: The heuristic rules themselves are the product IP. They're open-source under AGPL, which means anyone who builds a commercial product on top of them must open-source their modifications. This turns the openness into a moat rather than a liability.

---

## 5. LLM Provider — Fallback Chain

When AI generation is requested (rewrite, improve, generate, etc.), ContentForge uses a 3-tier fallback:

```
Tier 1: Ollama (local, if configured)
    ↓ [if unavailable or timeout]
Tier 2: Gemini 2.5 Flash (primary cloud)
    ↓ [if quota exceeded or API error]
Tier 3: Gemini quota rotation (secondary key pool)
    ↓ [if all failed]
Return error: "AI generation temporarily unavailable"
```

The fallback logic lives in `_llm_generate(prompt: str) -> str` in `api_prototype.py`. Each tier is wrapped in a try/except with specific exception types:

- `ollama.ConnectionError` → skip to Gemini
- `google.genai.errors.ResourceExhaustedError` → rotate key or skip tier
- Any unhandled exception → log + skip tier

**Why Gemini 2.5 Flash specifically?**
- Context window: 1M tokens (can pass large briefs as context)
- Price: ~$0.075 per 1M input tokens (enables aggressive free tier)
- Speed: ~1–2s TTFB for typical content generation requests
- Quality on short-form content generation: consistently high

**Ollama integration**: For operators running ContentForge locally or in a self-hosted environment, Ollama is checked first. This enables zero-cost LLM generation using locally-installed models (Llama 3.1, Mistral, etc.) for development and private deployments.

**Model configuration**: `GEMINI_MODEL` environment variable defaults to `gemini-2.5-flash`. Can be overridden in `deploy/render.yaml` or locally via `.env`.

---

## 6. QOps Layer — Quality Operations

QOps is the structured compliance layer added in v1.7.0. It transforms a numeric score into an actionable operational status across every scoring endpoint.

### The `_quality_gate()` Helper

```python
def _quality_gate(score: int) -> dict:
    if score >= 70:
        return {"quality_gate": "PASSED", "operational_risk": "LOW"}
    elif score >= 50:
        return {"quality_gate": "REVIEW", "operational_risk": "MEDIUM"}
    else:
        return {"quality_gate": "FAILED", "operational_risk": "HIGH"}
```

This is the entire QOps implementation — 7 lines, no external calls, <1ms. It's called inline by every scoring endpoint and the result is merged into the response JSON.

### Why Three Tiers?

The PASSED/REVIEW/FAILED model maps to practical agency workflow gates:

- **PASSED (≥70)**: Content can be published without further review. Score is above the platform-safe threshold. Pipeline can auto-proceed.
- **REVIEW (50–69)**: Content needs human review before publishing. Score is marginal — improvement is recommended but may still perform adequately.
- **FAILED (<50)**: Content should not be published as-is. Score indicates structural problems: wrong length, missing key signals, or active spam flags. Pipeline should halt.

### Operational Risk Band

`operational_risk` is the machine-readable equivalent for automated systems that need to route on risk rather than labels:

- `LOW` → green light any downstream automation
- `MEDIUM` → trigger human review queue
- `HIGH` → halt pipeline, alert operator

### QOps Fields in API Responses

Every endpoint that returns a score now includes:

```json
{
  "score": 74,
  "grade": "B",
  "quality_gate": "PASSED",
  "operational_risk": "LOW",
  "suggestions": [...]
}
```

The `improve_headline` endpoint adds three more QOps fields:

```json
{
  "original": "How to make money online",
  "original_score": 49,
  "original_grade": "C",
  "improved_versions": [...],
  "lift_percentage": "+109%",
  "quality_gate": "PASSED",
  "operational_risk": "LOW",
  "time_to_improve_ms": 1847,
  "audit_summary": "Original headline lacked specificity and numeric hooks. All three rewrites passed the 70-point quality threshold and include number-driven curiosity gaps."
}
```

`lift_percentage` is calculated as:

```
lift = ((best_improved_score - original_score) / original_score) * 100
```

This gives agencies a concrete, client-facing ROI number: "Our rewrite delivered a +109% quality lift on your headline."

---

## 7. Account State Machine

The `AccountStateMachine` class in `src/account_state_machine.py` manages the lifecycle of automation accounts (Twitter/X, LinkedIn) that ContentForge operates on behalf of users.

### Why a State Machine?

Platform APIs and Selenium-based automation are inherently stateful and failure-prone. An account that receives a rate limit warning needs to enter cooldown, not keep posting. An account that gets blocked needs to be flagged and excluded from scheduling. Without a state machine, operators either over-post (causing bans) or under-post (missing revenue windows).

The state machine makes these transitions explicit, auditable, and automatic.

### States

```
┌─────────┐     post_success()      ┌─────────┐
│ ACTIVE  │ ─────────────────────── │ ACTIVE  │ (stays active, health_score++)
└─────────┘
     │
     │ post_failure()
     ↓
┌──────────┐    backoff_expired()   ┌─────────┐
│ COOLDOWN │ ─────────────────────→ │ ACTIVE  │
└──────────┘
     │
     │ consecutive_failures >= 3
     ↓
┌──────────┐    recover()           ┌─────────┐
│ DEGRADED │ ─────────────────────→ │ ACTIVE  │
└──────────┘
     │
     │ platform_warns_account()
     ↓
┌─────────┐     operator_unblock()  ┌─────────┐
│ BLOCKED │ ─────────────────────→  │ ACTIVE  │
└─────────┘
     │
     │ operator_pauses()
     ↓
┌────────┐      operator_resumes()  ┌─────────┐
│ PAUSED │ ─────────────────────→   │ ACTIVE  │
└────────┘
```

### Backoff Schedule

When an account enters COOLDOWN, the backoff duration scales exponentially based on `consecutive_failures`:

| Failure Count | Cooldown Duration |
|---------------|------------------|
| 1 | 1 hour |
| 2 | 6 hours |
| 3 | 24 hours |
| 4+ | 72 hours |

This mirrors the cooling-off patterns that platforms use to detect and flag bot behavior. By backing off proportionally, ContentForge mimics human error recovery patterns.

### Health Score

Each account carries a `health_score` (1–100) that tracks reliability history:

- Successful post: `health_score = min(100, health_score + 2)`
- Failed post: `health_score = max(1, health_score - 10)`
- Blocked event: `health_score = max(1, health_score - 30)`

The health score is used by `platform_friction` to assess aggregate network health.

### Persistence

Account states are persisted to `.mp/runtime/account_states.json`. The file is read on every state change and written atomically. This means the state machine survives process restarts without losing account history.

---

## 8. Proof Dashboard — Evidence Intelligence

The proof dashboard is ContentForge's answer to the question agencies always face: "How do I prove our work made a difference?"

It's built on a single append-only log file (`.mp/proof.json`) with a 5,000-event cap and a suite of 8 read/write endpoints that aggregate, slice, and export the data.

### Core Concept

Every time a creator uses ContentForge to improve content:

1. The original score is recorded
2. The user publishes the improved content
3. They optionally record an outcome (engagement metric, revenue number)
4. The proof dashboard aggregates these events into client-ready reports

This creates a provenance chain: "We scored your headline at 49 (FAILED). We improved it to 100 (PASSED, +109% lift). The improved version drove 340 clicks."

### Write Endpoints

| Endpoint | What It Records |
|----------|----------------|
| `POST /v1/record_score_delta` | Before/after score pair for a piece of content |
| `POST /v1/record_publish_outcome` | Engagement result after publishing (clicks, impressions, etc.) |
| `POST /v1/record_revenue` | Revenue attribution (affiliate, ad, product sale) tied to content |

### Read/Analysis Endpoints

| Endpoint | What It Returns |
|----------|----------------|
| `GET /v1/dashboard_stats` | Aggregate KPIs: total events, average lift, best/worst performing content |
| `GET /v1/proof_timeline` | Chronological event log with filtering by platform/timeframe |
| `GET /v1/export_proof_report` | Full export as JSON or CSV for client delivery |
| `GET /v1/proof_recommendations` | AI-generated recommendations based on proof history patterns |
| `GET /v1/cohort_benchmarks` | Current period vs. trailing period — did performance improve? |

### `_proof_metrics()` Shared Helper

All read endpoints call `_proof_metrics()`, a shared aggregation function that:

- Reads `.mp/proof.json`
- Filters by optional `platform` and `period` query params
- Computes: total records, mean score delta, median score delta, total revenue attributed, best performing content, worst performing content, platform breakdown
- Returns a structured dict that endpoint handlers decorate with their specific view

This shared helper ensures consistency — `dashboard_stats` and `cohort_benchmarks` will never disagree on the underlying numbers.

### Cohort Benchmarks

`/v1/cohort_benchmarks` compares two time windows:

```json
{
  "period": "week",
  "current_window": {
    "avg_score_delta": 18.4,
    "total_events": 12,
    "avg_revenue": 34.50
  },
  "previous_window": {
    "avg_score_delta": 11.2,
    "total_events": 9,
    "avg_revenue": 22.00
  },
  "improvement": {
    "score_delta_change": "+64%",
    "revenue_change": "+57%"
  },
  "platform_medians": { ... }
}
```

This is the data that turns a renewal conversation from "we've been working hard" to "here are the numbers."

---

## 9. Platform Friction Monitor

`GET /v1/platform_friction` is a v1.7.0 operator-tier endpoint that provides real-time aggregate visibility into the automation network health.

### What It Does

It reads `.mp/runtime/account_states.json` and computes a network-level friction assessment:

```json
{
  "friction_level": "LOW",
  "active_accounts": 3,
  "total_accounts": 3,
  "states": {
    "active": 3,
    "cooldown": 0,
    "degraded": 0,
    "blocked": 0,
    "paused": 0
  },
  "accounts": [
    {
      "account": "twitter_main",
      "state": "active",
      "health_score": 88,
      "last_post_at": "2024-01-15T14:22:00Z",
      "consecutive_failures": 0,
      "blocked_retry_count": 0
    }
  ],
  "timestamp": "2024-01-15T15:00:00Z"
}
```

### Friction Level Algorithm

```
LOW     → all accounts active (no cooldown, pause, degraded, or blocked)
MEDIUM  → at least one account in cooldown or paused (managed recovery, normal operation)
HIGH    → any account in degraded or blocked state (operator review recommended)
UNKNOWN → account_states.json missing or unreadable
```

### Why This Is Operationally Useful

An operator running ContentForge across multiple accounts has no way to know at a glance whether their automation network is healthy without checking each account individually. The friction monitor collapses that N-account inspection into a single API call with a single signal.

Extension integrations can ping this endpoint on load and surface a warning badge if friction is HIGH. Cron scripts can check friction before launching a scheduled post batch. Monitoring dashboards can alert on a MEDIUM or HIGH reading.

---

## 10. All 41 Endpoints — Full Reference

### Instant Scoring (19 endpoints — zero AI cost, <50ms)

| Endpoint | Method | Tag | Description |
|----------|--------|-----|-------------|
| `/v1/score_tweet` | POST | Content Analysis | Score text for Twitter/X: length, hook, hashtags (1–2), emojis, CTA, power words |
| `/v1/score_linkedin_post` | POST | Content Analysis | Hook strength, paragraph structure, hashtag count (3–5), CTA, professional tone |
| `/v1/score_instagram` | POST | Content Analysis | Hashtag count (5–15), emojis, hook, line breaks, CTA |
| `/v1/score_youtube_title` | POST | Content Analysis | CTR signals, 40–60 char length, numbers, brackets, power words |
| `/v1/score_youtube_description` | POST | Content Analysis | SEO keywords, timestamps, chapter marks, links, CTA placement |
| `/v1/score_email_subject` | POST | Content Analysis | Open-rate signals, spam triggers, urgency, personalization tokens, length |
| `/v1/score_tiktok` | POST | Content Analysis | Hook speed, hashtag strategy, trending language, ≤150 char ideal |
| `/v1/score_threads` | POST | Content Analysis | Conversational tone, question hooks, hashtag penalty, CTA |
| `/v1/score_facebook` | POST | Content Analysis | Engagement triggers, question hooks, emoji density, hashtag count |
| `/v1/score_pinterest` | POST | Content Analysis | Keyword density, instructional language, hashtags, spam signals |
| `/v1/score_ad_copy` | POST | Content Analysis | Headline length, benefit clarity, urgency, CTA strength, compliance signals |
| `/v1/score_readability` | POST | Content Analysis | Flesch-Kincaid reading ease + grade level + avg sentence/word length |
| `/v1/analyze_headline` | POST | Content Analysis | 60+ power words tracked, numbers, questions, emotional triggers, QOps fields |
| `/v1/analyze_hashtags` | POST | Content Analysis | Uniqueness, spam risk, overuse, per-platform recommendations |
| `/v1/score_multi` | POST | Content Analysis | Score one text across all platforms in one call, with per-platform QOps fields |
| `/v1/batch_score` | POST | Content Analysis | Score up to 20 drafts against one platform, returned best-first |
| `/v1/compare` | POST | Content Analysis | Head-to-head comparison of two texts, with winner and per-signal advantages |
| `/v1/ab_test` | POST | Content Analysis | A/B test 2–20 drafts on any platform, returns ranked list with confidence |
| `/v1/status` | GET | System | Service health: `{"ok": true, "service": "contentforge", "version": "1.7.0"}` |

### AI Content Generation (13 endpoints — Gemini 2.5 Flash, opt-in)

| Endpoint | Method | Tag | Description |
|----------|--------|-----|-------------|
| `/v1/improve_headline` | POST | AI Content Generation | N AI-rewritten headline versions, each scored, lift_percentage, audit_summary |
| `/v1/generate_hooks` | POST | AI Content Generation | Scroll-stopping openers: viral / professional / casual / bold styles |
| `/v1/rewrite` | POST | AI Content Generation | Platform-optimized rewrite for Twitter, LinkedIn, Instagram, TikTok, email, blog |
| `/v1/compose_assist` | POST | AI Content Generation | Generate 2–5 rewrites, score each, return best-performing draft with explanation |
| `/v1/tweet_ideas` | POST | AI Content Generation | 5–10 tweet angles for a niche with hashtag suggestions |
| `/v1/content_calendar` | POST | AI Content Generation | 7-day calendar with daily themes and ready-to-post drafts |
| `/v1/thread_outline` | POST | AI Content Generation | Complete Twitter thread: hook + numbered body + CTA |
| `/v1/generate_bio` | POST | AI Content Generation | Social bio for Twitter (160 chars), LinkedIn (300), or Instagram (150) |
| `/v1/generate_caption` | POST | AI Content Generation | Instagram or TikTok caption with hashtags, emojis, and CTA |
| `/v1/generate_linkedin_post` | POST | AI Content Generation | Full LinkedIn post: hook + story + insight + CTA |
| `/v1/generate_email_sequence` | POST | AI Content Generation | 3-email drip: welcome → value → pitch, with subject lines |
| `/v1/generate_content_brief` | POST | AI Content Generation | Research brief: audience, angle, SEO keywords, outline, hooks |
| `/v1/generate_ad_copy` | POST | AI Content Generation | Short-form ad copy variants for Facebook, Google, Twitter |

### Proof Dashboard (8 endpoints)

| Endpoint | Method | Tag | Description |
|----------|--------|-----|-------------|
| `/v1/record_score_delta` | POST | Proof | Record before/after score pair for content provenance |
| `/v1/record_publish_outcome` | POST | Proof | Record engagement outcome after publishing |
| `/v1/record_revenue` | POST | Proof | Record revenue attribution tied to content |
| `/v1/dashboard_stats` | GET | Proof | Aggregate KPIs: total events, average lift, best content |
| `/v1/proof_timeline` | GET | Proof | Chronological event log with platform/timeframe filtering |
| `/v1/export_proof_report` | GET | Proof | Full export as JSON or CSV for client delivery |
| `/v1/proof_recommendations` | GET | Proof | AI-generated recommendations based on proof history patterns |
| `/v1/cohort_benchmarks` | GET | Proof | Current vs. trailing period comparison with platform medians |

### System / Operator (1 endpoint)

| Endpoint | Method | Tag | Description |
|----------|--------|-----|-------------|
| `/v1/platform_friction` | GET | System | Real-time account state machine health — LOW/MEDIUM/HIGH friction level |

### Infrastructure (standard, not counted in 41)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Returns `{"status": "ok", "version": "1.7.0", "endpoints": 41}` |
| `/` | GET | HTML landing page with live API badge and endpoint grid |

---

## 11. Extension — Browser Intelligence Layer

The ContentForge browser extension (Manifest V3, Chrome/Firefox) brings the API into the creator's existing workflow without requiring them to open a separate tool.

### Architecture

```
background.js (service worker)
    │
    ├── scoreText(text, platform) → POST /v1/score_{platform}
    ├── compareTexts(a, b) → POST /v1/compare
    ├── suggestRewrite(text) → POST /v1/improve_headline (or /v1/rewrite)
    └── rapidPost(data) → POST /v1/record_score_delta

popup.html / popup.js
    │
    ├── Score tab: textarea → score button → displays grade + quality_gate badge
    │       └── QGate display: PASSED (green) / REVIEW (yellow) / FAILED (red)
    └── Suggest tab: textarea → suggest button → shows improved versions + audit_summary

content.js (injected on X.com / LinkedIn)
    └── Detects compose box → injects inline score badge → updates on text change
```

### Reliability Architecture (v0.6.0)

The extension was significantly hardened in v0.6.0 to handle Render's free-tier cold start (30-second spinup):

```javascript
const FETCH_TIMEOUT_MS = 35000;  // covers Render 30s cold boot
const MAX_RETRIES = 2;
const RETRY_DELAYS_MS = [3000, 8000];  // exponential backoff
```

On connection failure:
1. Wait 3 seconds
2. Retry (retry 1)
3. Wait 8 seconds  
4. Retry (retry 2)
5. Surface user-readable error: "Request timed out. The API may be starting up — retrying automatically..."

This pattern means the extension handles cold starts transparently. The user sees a brief loading state on first use after the API has been idle, then normal responses for all subsequent requests in the same session.

### Quality Gate Badge UI

The popup renders quality gate as a colored inline badge:

```CSS
.quality-gate.passed  { background: #22c55e; color: #fff; }
.quality-gate.review  { background: #f59e0b; color: #fff; }
.quality-gate.failed  { background: #ef4444; color: #fff; }
```

This makes the verdict immediately scannable without reading a number.

### Audit Summary Panel

When `improve_headline` returns an `audit_summary` field, the extension renders it in an `#auditSummary` div below the suggestions. This is the LLM-generated agency brief — 1–2 sentences explaining the improvement rationale. Designed for operators who need to explain their edits to a client or manager.

### Lift Display

When `improve_headline` returns `lift_percentage`, it prepends to the improvement suggestion:

```
[+109% lift · PASSED] "Can You Really Earn $5,000 a Month Online? Discover the Secrets"
```

---

## 12. Deployment Architecture

### Render Free Tier

ContentForge is deployed on Render's free web service tier. This imposes one known constraint:

- **Cold start**: The worker spins down after ~15 minutes of inactivity and takes ~30 seconds to spin back up on the first request.

This is mitigated at multiple levels:
- The extension's `FETCH_TIMEOUT_MS = 35000` covers the cold start window
- `gunicorn --timeout 120` ensures the worker doesn't kill a request during spin-up
- `MAX_RETRIES = 2` in the extension means a cold-start timeout will be automatically retried

For production operators, upgrading to Render's $7/month paid tier eliminates cold starts entirely.

### Process Model

```
Render → Gunicorn (1 worker) → Flask app
```

Single worker is intentional for the free tier — multiple workers would compete for the same JSON file stores. For horizontal scale, the flat JSON stores would need to be replaced with a database.

### `deploy/wsgi.py`

The WSGI entry point handles path setup:

```python
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.api_prototype import app
```

This is why the app can use bare imports like `from config import *` — `ROOT/src` is on the path.

### `deploy/render.yaml`

```yaml
services:
  - type: web
    name: contentforge-api
    runtime: python
    plan: free
    buildCommand: pip install -r deploy/requirements-api.txt
    startCommand: gunicorn deploy.wsgi:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120
    envVars:
      - key: GEMINI_API_KEY
        sync: false
      - key: RAPIDAPI_PROXY_SECRET
        sync: false
      - key: GEMINI_MODEL
        value: gemini-2.5-flash
      - key: PYTHONPATH
        value: /opt/render/project/src
```

The `RAPIDAPI_PROXY_SECRET` is the shared secret between RapidAPI's proxy and the backend. All requests arriving at Render will have this header; requests without it are rejected. This prevents bypassing the RapidAPI rate limiter and billing layer by hitting the Render URL directly.

### `deploy/requirements-api.txt`

```
flask>=3.0
gunicorn>=21.2
google-genai>=1.0
ollama>=0.4
```

Intentionally minimal. The heuristic scoring engine has zero pip dependencies — it's pure Python. Only the AI generation layer (google-genai) and the LLM fallback (ollama) require packages.

### RapidAPI Proxy Layer

All public traffic goes through RapidAPI:

```
Client → RapidAPI Gateway
    → validates API key
    → enforces plan rate limits (30 req/min)
    → counts AI call quota per plan
    → forwards to Render with X-RapidAPI-Proxy-Secret header
    → Render validates secret → Flask routes request
```

RapidAPI handles:
- API key issuance and revocation
- Billing and subscription management
- Rate limiting (30 req/min across all plans)
- Usage analytics and monetization reporting

ContentForge validates the `X-RapidAPI-Proxy-Secret` header on every request to ensure the request came through the proxy. This is the only authentication layer for public endpoints.

---

## 13. Configuration Reference

ContentForge is configured via `config.json` at the project root. The API reads the following fields:

| Key | Type | Description |
|-----|------|-------------|
| `ollama_model` | string | Ollama model name for LLM generation (e.g., "llama3.1"). If empty, Gemini is used directly. |
| `imagemagick_path` | string | Path to ImageMagick binary (required for subtitle rendering in video pipeline) |
| `firefox_profile` | string | Default Firefox profile path for Selenium automation |
| `stt_provider` | string | Speech-to-text provider: `local_whisper` or `third_party_assemblyai` |

Environment variables (set in Render dashboard, not committed):

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google AI Studio API key for Gemini generation |
| `GEMINI_MODEL` | Model name (default: `gemini-2.5-flash`) |
| `RAPIDAPI_PROXY_SECRET` | Shared secret with RapidAPI proxy |

---

## 14. Security Model

### Authentication

- All public API traffic flows through RapidAPI, which validates API keys
- ContentForge validates `X-RapidAPI-Proxy-Secret` on every request
- No user accounts or sessions in the API — all state is per-API-key at the RapidAPI layer

### Input Validation

- All `text` inputs are limited: `maxLength: 500` (headlines), `maxLength: 5000` (score_multi)
- All `count` and `limit` inputs are validated against documented min/max ranges
- Request bodies that don't parse as JSON return a 400 with a specific error message
- No eval, no exec, no dynamic code paths in scoring functions

### No SQL / No Injection Surface

The flat JSON file store has no query language and no parameterized input. There is no SQL injection surface. File paths are constructed from constants, not user input.

### AGPL Compliance

ContentForge is AGPL-3.0 licensed. Any hosted deployment that is modified and served to users must open-source those modifications. This is enforced at the license level, not the code level.

---

## 15. Agency & Operator Use Cases

### Use Case 1: Pre-Publish Quality Gate

An agency produces 50 social posts per week for a client. Before any post is published:

1. Each draft is sent to `POST /v1/score_{platform}`
2. If `quality_gate == "FAILED"`: draft is re-queued for rewrite
3. If `quality_gate == "REVIEW"`: draft goes to senior editor for approval
4. If `quality_gate == "PASSED"`: draft is cleared for scheduling

Result: Only A/B-grade content reaches the client's audience. The agency has a documented, repeatable quality standard.

### Use Case 2: Monthly Client Report

At month end, the agency runs:

1. `GET /v1/dashboard_stats` — aggregate lift numbers
2. `GET /v1/cohort_benchmarks?period=month` — this month vs. last month
3. `GET /v1/export_proof_report?format=csv` — raw data for client's own analysis

The report shows: "We processed 218 posts. Average score before our work: 52. Average score after: 79. That's a +52% quality improvement. Here are the 10 best-performing posts by engagement."

### Use Case 3: Automated Content Pipeline

A solo operator runs a Twitter growth account with ContentForge in the loop:

```
Cron job → generate tweet idea (tweet_ideas) 
         → score the idea (score_tweet)
         → if quality_gate == FAILED: improve (improve_headline)
         → record delta (record_score_delta)
         → schedule post (external scheduler)
         → record outcome after 48h (record_publish_outcome)
```

ContentForge serves as the quality control layer in the pipeline, ensuring no sub-50 content is ever published.

### Use Case 4: Multi-Account Friction Monitoring

An operator running ContentForge across 5 Twitter accounts checks the friction monitor before every scheduled batch:

```python
resp = requests.get("/v1/platform_friction", headers=auth)
if resp.json()["friction_level"] == "HIGH":
    alert_operator()
    skip_batch()
elif resp.json()["friction_level"] == "MEDIUM":
    log_warning()
    reduce_post_frequency()
```

This prevents posting to accounts in blocked state and escalates anomalies before they become platform bans.

---

## 16. Competitive Positioning

### vs. CoSchedule Headline Analyzer

| Dimension | CoSchedule | ContentForge |
|-----------|-----------|--------------|
| Latency | ~2s (AI) | <5ms (heuristic) |
| Platforms | Headlines only | 12 platforms |
| API | No public API | 41-endpoint REST API |
| QOps fields | None | quality_gate, operational_risk, lift_percentage |
| Proof system | None | 8 proof endpoints |
| Pricing | $49/mo+ | Free tier available |

### vs. Grammarly Business

| Dimension | Grammarly | ContentForge |
|-----------|-----------|--------------|
| Focus | Grammar / tone | Platform performance prediction |
| API | Enterprise only | Public RapidAPI |
| Deterministic | No (ML-based) | Yes (heuristic rules) |
| Platform-specific | No | Per-platform rules |
| Explainability | Vague suggestions | Named rules + signals |

### vs. ChatGPT / Claude for content review

| Dimension | LLM direct | ContentForge |
|-----------|-----------|--------------|
| Latency | 2–10s | <50ms (heuristic) |
| Cost | $0.01–0.10 per call | Free for scoring |
| Reproducibility | Non-deterministic | Deterministic |
| Platform rules | Hallucinated | Documented best practices |
| Proof system | None | 8 proof endpoints |
| API interoperability | Varies | Standard OpenAPI 3.0.3 |

### Differentiation Summary

ContentForge's core differentiators are not features, they're architectural properties:

1. **Latency** — heuristic scoring is categorically faster than any AI-based approach
2. **Reproducibility** — deterministic output is a requirement for A/B testing, proof systems, and compliance
3. **Platform specificity** — each platform's documented rules are the scoring model, not a general language model
4. **Proof provenance** — the only scoring API with a built-in evidence dashboard for ROI demonstration
5. **State machine safety** — operational safeguards for automation at scale that no content tool offers

---

## 17. AGPL Open Core Moat

ContentForge is licensed under AGPL-3.0. This is a deliberate competitive strategy, not just an ethical posture.

### Why AGPL Specifically

The AGPL is the strongest copyleft license in common use. It extends the GPL's copyleft requirement to network use: if you modify ContentForge and serve it to users over a network, you must publish your modifications under AGPL.

This means:
- A company can't fork ContentForge, add a proprietary scoring model, and sell it as a closed product
- Any improvements made by integrators must come back to the commons
- The AGPL license is the enforcement mechanism for the open-core model

### The Open Core Structure

```
Open (AGPL):                    │  Proprietary:
─────────────────────────────── │  ────────────────────────────
Heuristic scoring engine        │  Managed Render deployment
All 44 endpoints                │  RapidAPI listing + billing
State machine                   │  Enterprise SLA
Proof dashboard                 │  White-label licensing
QOps layer                      │  Custom rule sets for specific
Extension source                │    industry verticals
                                │  Agency dashboard (planned)
```

### Network Effect of Open Core

When ContentForge's heuristic rules are AGPL, the entire community that uses them has an incentive to improve them. A LinkedIn growth agency that adds 10 new signals to the LinkedIn scorer and deploys ContentForge must open-source those signals. Those signals improve the base product for everyone.

This inverts the usual dynamic: rather than closing improvements to maintain moat, ContentForge uses openness to aggregate improvement from every user.

---

## 18. Pricing & Commercial Structure

All plans are managed through RapidAPI. Instant scoring endpoints (`score_*`, `analyze_*`, `batch_score`, `compare`, `ab_test`) never count against the AI call quota.

| Plan | Price | AI Calls/mo | Total Requests/mo | Rate Limit |
|------|-------|------------|-------------------|------------|
| BASIC | Free | 50 | 300 | 30 req/min |
| PRO | $9.99/mo | 750 | 1,000 | 30 req/min |
| ULTRA | $29.99/mo | 3,000 | 4,000 | 30 req/min |
| MEGA | $99/mo | 18,000 | 20,000 | 30 req/min |

### Revenue Model

RapidAPI handles billing, subscription management, and quota enforcement. ContentForge receives a monthly payout based on subscriber count.

The free tier is permanent and includes every endpoint. This is a deliberate acquisition strategy: users integrate ContentForge into their workflow on the free tier, then upgrade when they need more AI calls.

### Monetization Vectors

1. **RapidAPI subscriptions** (current, live)
2. **White-label licensing** for agencies (planned — custom subdomain + branded reports)
3. **Enterprise agreements** (planned — SLA, dedicated worker, custom rule sets)
4. **Agency dashboard** (planned — multi-client proof management, team access)

---

## 19. Data Storage & Persistence

ContentForge uses flat JSON files for all persistence. This is a deliberate architectural choice that prioritizes reliability and operational simplicity over scale.

### File Store Layout

```
.mp/
├── youtube.json          — YouTube account cache (main CLI app)
├── twitter.json          — Twitter account cache (main CLI app)
├── afm.json              — Affiliate marketing cache (main CLI app)
├── proof.json            — Proof dashboard events (API, 5000 entry cap)
└── runtime/
    └── account_states.json  — Account state machine state
```

### Proof Event Schema

Each event in `proof.json` follows this structure:

```json
{
  "event_type": "score_delta",
  "platform": "twitter",
  "original_score": 49,
  "improved_score": 100,
  "delta": 51,
  "content_preview": "How to make money onl...",
  "timestamp": "2024-01-15T14:22:00Z"
}
```

### Account State Schema

Each account in `account_states.json`:

```json
{
  "account_id": "twitter_main",
  "state": "active",
  "health_score": 88,
  "consecutive_failures": 0,
  "blocked_retry_count": 0,
  "last_post_at": "2024-01-15T14:22:00Z",
  "cooldown_until": null,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T14:22:00Z"
}
```

### Atomicity

Writes to JSON files use a read-modify-write pattern:

```python
data = json.loads(path.read_text())
data.append(new_event)
if len(data) > MAX_ENTRIES:
    data = data[-MAX_ENTRIES:]
path.write_text(json.dumps(data, indent=2))
```

This is not atomic at the filesystem level (no lock file). For a single-worker deployment, this is safe. Multi-worker deployments would require a database or Redis.

---

## 20. Roadmap

### Near-Term (v1.8.0)

- **Webhook support**: `POST /v1/webhooks/score_alert` — notify a URL when content scores below a threshold
- **Batch proof recording**: `POST /v1/record_batch_delta` — import score data from external tools
- **TikTok trend API integration**: enrich `score_tiktok` with live trending hashtag data
- **Extension v0.7.0**: inline badge on LinkedIn compose box, keyboard shortcut to quick-score selected text

### Medium-Term (v2.0.0)

- **Agency multi-tenant mode**: namespaced proof stores per agency client
- **PostgreSQL integration**: replace flat JSON stores for horizontal scale
- **Webhook-driven proof recording**: automatic outcome recording via platform webhook forwarding
- **White-label API**: custom domain + branded reports for agency resellers

### Long-Term (v3.0.0)

- **Predictive scoring**: train a lightweight model on proof event data to predict post performance before scoring
- **Editorial calendar API**: structured calendar management with draft versioning
- **Competitor content analysis**: score public competitor posts against your content
- **Team access controls**: scoped API keys per team member with usage reporting

---

## Appendix A: Environment Setup (Local Development)

```bash
# Clone and enter repo
git clone https://github.com/CaptainFredric/ContentForge
cd ContentForge

# Quick macOS setup (creates venv, installs deps, seeds config.json)
bash scripts/setup_local.sh

# Or manual setup
cp config.example.json config.json
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Set API keys in config.json or environment
export GEMINI_API_KEY=your_key_here

# Validate environment
python3 scripts/preflight_local.py

# Run API locally
python3 scripts/api_prototype.py
# API available at http://localhost:5000
```

---

## Appendix B: Request/Response Examples

### Score a Tweet
```http
POST /v1/score_tweet
Content-Type: application/json
X-RapidAPI-Key: your_key

{"text": "I shipped in 48 hours. Here is what I learned 🧵 #buildinpublic"}
```

```json
{
  "score": 79,
  "grade": "B",
  "quality_gate": "PASSED",
  "operational_risk": "LOW",
  "char_count": 59,
  "hashtag_count": 1,
  "emoji_count": 1,
  "suggestions": [
    "Add a specific number to the opening hook",
    "Length is in the lower-optimal range — aim for 71–100 chars"
  ]
}
```

### Improve a Headline
```http
POST /v1/improve_headline
Content-Type: application/json
X-RapidAPI-Key: your_key

{"text": "How to make money online", "count": 3}
```

```json
{
  "original": "How to make money online",
  "original_score": 49,
  "original_grade": "C",
  "original_suggestions": ["Make the headline longer and more specific.", "Add a number."],
  "improved_versions": [
    {"text": "Can You Really Earn $5,000 a Month Online? Discover the Secrets", "score": 100, "grade": "A", "power_words_found": ["earn", "secret", "discover"]},
    {"text": "Unlock $6,000/month: 7 Proven Strategies for Online Success", "score": 85, "grade": "A", "power_words_found": ["proven"]},
    {"text": "5 Lucrative Ways to Make $10K/Mo Online", "score": 80, "grade": "A", "power_words_found": []}
  ],
  "lift_percentage": "+104%",
  "quality_gate": "PASSED",
  "operational_risk": "LOW",
  "time_to_improve_ms": 1847,
  "audit_summary": "Original headline lacked specificity and numeric anchors. All three rewrites passed the quality threshold and include number-driven curiosity gaps optimized for high-CTR performance."
}
```

### Platform Friction Check
```http
GET /v1/platform_friction
X-RapidAPI-Key: your_key
```

```json
{
  "friction_level": "MEDIUM",
  "active_accounts": 2,
  "total_accounts": 3,
  "states": {"active": 2, "cooldown": 1, "degraded": 0, "blocked": 0, "paused": 0},
  "accounts": [
    {"account": "twitter_main", "state": "active", "health_score": 88, "consecutive_failures": 0},
    {"account": "twitter_backup", "state": "active", "health_score": 74, "consecutive_failures": 0},
    {"account": "twitter_v3", "state": "cooldown", "health_score": 52, "consecutive_failures": 2}
  ],
  "timestamp": "2024-01-15T15:00:00Z"
}
```

---

*ContentForge is maintained by Aden Cisneros. Support: captainarmoreddude@gmail.com*  
*Live demo: https://captainfredric.github.io/ContentForge/*  
*GitHub: https://github.com/CaptainFredric/ContentForge*
