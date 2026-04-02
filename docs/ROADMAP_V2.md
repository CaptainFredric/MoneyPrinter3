# ContentForge — Feature Roadmap V2

> **Created:** April 1, 2026
> **Owner:** Aden Cisneros / Dan DeBugger
> **Status:** Active — living document for all planned upgrades

---

## Why This Exists Instead of GPT (The Core Value Proposition)

**What GPT does:** Open-ended conversation. You paste text, ask "is this good?", get a subjective paragraph. Different answer every time. Costs tokens. Takes 2-5 seconds. No structured data. Can't be automated.

**What ContentForge does that GPT cannot:**

1. **Deterministic scoring.** Same input = same score = same suggestions, every time. CI pipelines, A/B test loops, quality gates, automated workflows. GPT: different opinion every ask.
2. **Platform-specific rules.** LinkedIn rewards 1,300+ char posts with 3+ paragraphs. Twitter penalizes >3 hashtags. TikTok captions peak under 150 chars. Email subjects with "FREE" in caps trigger spam filters. GPT knows none of this.
3. **Sub-50ms latency.** Score 1,000 tweets in 50 seconds via batch_score. GPT: 1,000 calls at 2-5s each = 30-80 minutes + $5-15 in tokens.
4. **Structured JSON output.** `{"score": 82, "grade": "B+", "suggestions": [...]}` — machine-readable. GPT returns prose.
5. **Cost.** Free tier: 300 req/month + 50 AI calls. GPT-4: ~$0.03/req minimum. At 300 req = $9/month vs free.

**Elevator pitch:** "ContentForge is a linter for content. GPT is a writing partner. Use both — ContentForge tells you what's wrong, GPT helps fix it. Or ContentForge fixes it via AI endpoints."

---

## Feature 0: Request Leniency (Wasted Request Protection)

Don't count 4xx error responses against quota. Malformed request = 400 error, not a lost credit.

**Tier 1 (ship this week):** Only call `_log_usage()` on 2xx responses. Document in API description.
**Tier 2 (future):** First 10 requests per new API key un-metered (onboarding buffer).
**Tier 3 (future):** Idempotency window — same (key + endpoint + body) within 60s returns cached response.

**Effort:** 1 hour (T1), 1 day (T2), 3 days (T3)
**File:** `scripts/api_prototype.py` — modify where `_log_usage()` is called in each endpoint

---

## Feature A: Chrome Extension — Inline Content Scoring

**What:** Browser extension scores content in real-time as users type on twitter.com, linkedin.com, etc. Floating badge shows "74/B", expands for suggestions. "Improve with AI" one-click.

**Why this is the #1 priority after launch:**
- Meets users where they are — zero workflow change
- Every user is a walking billboard (friends see badge)
- Chrome Web Store = organic distribution channel
- Habit loop: type → see score → improve → post

**Tech:** Manifest V3 + content script + debounced API calls (500ms). Platform auto-detected from hostname. Auth: RapidAPI key in extension settings.

**Effort:** 2-3 weeks MVP (Twitter + LinkedIn), +1 week per platform
**Files:** `extension/manifest.json`, `content.js`, `popup.html`, `popup.js`, `background.js`, `styles.css`

---

## Feature B: Zapier / Make Integration

**What:** Official Zapier actions: Score Tweet, Score LinkedIn, Score Headline, Score Multi, Improve Headline, Generate Hooks. Users wire into Notion → score → Slack, Google Sheets → batch score, etc.

**Why:** Unlocks non-coders (content marketers, agencies, newsletter writers). 7M+ Zapier users. Once embedded in a Zap, nobody removes it.

**Tech:** Register at platform.zapier.com, define actions pointing to existing endpoints. Mostly config.

**Effort:** 1 week
**Dependencies:** Zapier developer account (free)

---

## Feature C: /v1/publish — Auto-Post to Social Media

**What:** Score content → gate quality → publish directly to user's social accounts.

**Stage 1 — Desktop CLI (wk 1-4):** Selenium + user's Firefox profile. Reuses `src/classes/Twitter.py`. Local only.
**Stage 2 — Twitter OAuth (wk 5-12):** Twitter Dev Basic ($100/mo), `tweet.write` scope, works from any device.
**Stage 3 — Multi-Platform (mo 3-6):** LinkedIn OAuth, Instagram Graph API, scheduling.

**Key Decision:** Stay API-first. Let Buffer/Typefully call scoring endpoints AND let solo users use publish endpoint. Don't become a dashboard company unless revenue demands it.

---

## Feature D: Competitive Score Comparison

**What:** `POST /v1/compare` — submit your text + competitor's text. Side-by-side scores, advantages, gaps.

**Why:** Game dynamic ("beat" successful creators). Viral loop ("I scored 87 vs @garyvee's 72"). Repeat usage.

**Tech:** Score both through existing scorer, diff the results. Optional URL scraping via requests + BeautifulSoup.

**Effort:** 2 weeks

---

## Feature E: Historical Score Tracking & Analytics

**What:** Store scores (opt-in), dashboard showing trends, most common suggestions, weekly reports.

**Why:** #1 SaaS retention feature. Switching costs. Justifies higher pricing.

**Stages:** API (wk 1-3) → Web Dashboard with Chart.js (wk 4-8) → Email Reports (wk 6-10)

**Effort:** 6-10 weeks
**Critical:** Render ephemeral filesystem kills file storage on redeploy. Need Supabase (free 500MB Postgres) or Render Postgres.

---

## Feature F: Custom Scoring Rules & Brand Profiles

**What:** Users define custom parameters: emoji tolerance, CTA requirements, length targets, power word lists, banned words, mandatory hashtags. Agencies create per-client profiles.

**Why:** Deepest moat possible. 30 minutes configuring a profile = never switching. Agency feature charges per-profile.

**Tech:** `POST /v1/profiles`, scoring endpoints accept `?profile_id=xyz`. Profile overrides base heuristics.

**Effort:** 3 weeks

---

## Prioritization Matrix

| # | Feature | Effort | Revenue | Acquisition | Retention | Build Order | Status |
|---|---------|--------|---------|-------------|-----------|-------------|--------|
| 0 | Request Leniency (T1-T3) | 1 hr–3 days | Low | Medium | Medium | **This week** | **SHIPPED** (T1+T3) |
| A | Chrome Extension | 2-3 wk | Medium | **Very High** | High | **Next** | **SHIPPED** (MVP) |
| B | Zapier Integration | 1 wk | Medium | High | Medium | After A | Not started |
| D | Compare Endpoint | 2 wk | Low-Med | Medium | Medium | Flexible | **SHIPPED** |
| D+ | A/B Test Endpoint | 1 day | Low-Med | Medium | High | Flexible | **SHIPPED** |
| C1 | /v1/publish Desktop | 3-4 wk | Med-High | Medium | High | After B | Not started |
| C2 | /v1/publish OAuth | 6-8 wk | High | High | Very High | After C1 | Not started |
| E | Analytics Dashboard | 6-10 wk | High | Medium | **Very High** | After C2 | Not started |
| F | Brand Profiles | 3 wk | High | Medium | **Very High** | After E | Not started |

---

## Build Phases

**Phase 1 — Foundation & Distribution (April 2026):**
- Feature 0: Request leniency
- Feature A: Chrome Extension MVP (Twitter + LinkedIn)
- Feature D: Compare endpoint (quick win, good marketing)

**Phase 2 — Integration Layer (May 2026):**
- Feature B: Zapier integration
- Feature C1: /v1/publish desktop CLI

**Phase 3 — Platform Play (June-August 2026):**
- Feature C2: Twitter OAuth publishing
- Feature E: Analytics API + dashboard
- Feature F: Custom brand profiles

**Phase 4 — Scale (September+ 2026):**
- Multi-platform OAuth, team/agency features
- Email reports, full web dashboard (if revenue justifies)

---

## Infrastructure Notes

**Render free tier:** Ephemeral filesystem. Add Supabase (free 500MB Postgres) when reaching Phase 3.

**Claude API:** Account in progress. Add as `"model": "claude"` option in `src/llm_provider.py`. Price at 2x Gemini quota. Marketing: "Premium AI — sharper rewrites."

**Pretext (bookmarked):** https://github.com/changeio/pretext — Pure JS text measurement. Use when building browser-based shareable score cards.

---

## GPT vs ContentForge (marketing copy)

| | ContentForge | ChatGPT |
|---|---|---|
| Speed | <50ms | 2-5 seconds |
| Cost (300 req/mo) | Free | ~$9 |
| Deterministic | Yes | No |
| Output | Structured JSON | Prose |
| Platform rules | 16 rule sets | Generic |
| Automatable | Loop, batch, CI | Manual |
| Scoring | 0-100 + grade | Subjective paragraph |
