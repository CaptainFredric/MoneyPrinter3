# ContentForge — Operational Plan

**Last updated:** 2026-04-05
**Status:** Surge (Phase 2 of 3) — Saturday launch live

---

## Phase 1: Pre-Flight (Now → Saturday April 5, 10:00 AM PT)

**Objective:** Zero-risk lock. Everything staged, nothing touched.

| Task | Status | Owner |
|---|---|---|
| r/webdev Saturday post drafted (`saturday-post.md`) | Done | Aden |
| Execution checklist (`saturday-plan.md`) | Done | Aden |
| CWS extension submitted | Done — in review | Aden |
| Landing page CTAs wired to CWS URL | Done — auto-activates on approval | Aden |
| `/v1/extension_config` endpoint live (server-side) | Done | Aden |
| `/v1/feedback` endpoint live (calibration signal capture) | Done | Aden |
| Blind Taste Test template ready (`docs/blind-taste-test.md`) | Done | Aden |
| Render API warm via cron-job.org (10min pings) | Active — **update URL to `/v1/status`** | cron-job.org |
| Repo bloat cleaned (fonts, netlify, rapidapi-upload) | Done | Aden |
| Silent Phase — no code changes to scoring or extension | Active | Aden |

**Pre-flight checklist (Saturday morning before 10am PT):**
- [ ] `curl https://contentforge-api-lpp9.onrender.com/health` → confirms `"status":"ok","endpoints":50`
- [ ] Confirm Gemini quota reset (midnight Pacific)
- [ ] Final read-through of `saturday-post.md`
- [ ] Check CWS review status — if approved, add link to Saturday post under Links

---

## Phase 2: The Surge (Saturday April 5 → CWS Approval)

**Objective:** Execute distribution. Convert attention into calibration data.

### Saturday April 5 — Launch Day

| Time (PT) | Action |
|---|---|
| 10:00 AM | r/webdev Showoff Saturday thread: find it, post `saturday-post.md` content |
| 10:05 AM | First reply: pin demo link + "paste any draft, see the quality_gate field" |
| 10:30 AM–12:00 PM | Monitor for comments — respond within 30 min |
| 12:00 PM–6:00 PM | Engagement window: answer questions, convert skeptics to Blind Taste Test |
| 3:00 PM | Post Twitter/X thread (3 tweets: problem → solution → demo link) |
| 8:00 PM | End-of-day check: upvotes, GitHub stars, RapidAPI sign-ups, Render logs |

### Engagement scripts (ready responses):

**"Why not just use textstat/readability libraries?"**
> ContentForge goes beyond readability. It checks platform-specific signals: hook strength, hashtag density for the specific platform, CTA detection, emoji distribution, power word density. Flesch-Kincaid doesn't know that LinkedIn penalizes more than 5 hashtags or that Twitter rewards questions in the first 10 words.

**"Isn't this just a linter?"**
> Exactly right. A linter for content, not code. Same philosophy: deterministic rules, instant feedback, explainable deductions. If your post fails the quality gate, you know exactly which rule flagged it.

**"How do you know your heuristics are right?"**
> Honest answer: the weights are based on each platform's documented best practices, not validated against a performance corpus yet. That's why we're running a Blind Taste Test — submit 10 posts (5 winners, 5 flops) and we'll tell you which is which without seeing the metrics. If we get it wrong, we adjust the weights publicly. Details on the GitHub repo.

**"What about LLM deterministic modes / structured outputs?"**
> Even in deterministic mode, LLMs can't show you the audit trail. You get a score, but not a traceable explanation of which specific rule caused each deduction. Auditability is the moat, not latency.

**On Gemini 429s:**
> Scoring endpoints are 100% deterministic — they never hit the Gemini quota. AI generation (rewrite, compose_assist) shares a Gemini free-tier quota. If you see a 429, it resets at midnight PT. The core demo (scoring) is unaffected.

### Cross-post schedule:

| Day | Platform | Angle |
|---|---|---|
| Saturday PM | Twitter/X | 3-tweet thread: variance problem → deterministic fix → demo |
| Sunday | LinkedIn | Professional tone: "quality gate for content teams" + compliance angle |
| Monday April 7 | r/SideProject | Trimmed ~200-word version + links |
| Tuesday April 8 | r/selfhosted | Self-hosting angle: AGPL-3.0, `pip install`, Ollama local, no vendor lock-in |

---

## Phase 3: The Calibration (CWS Approval → April 30)

**Objective:** Validate heuristics with real data. Convert from "deterministic" claim to "calibrated" claim.

---

### 🔒 Silent Phase 2.0 — FEATURE FREEZE (April 5 → CWS approval + calibration results)

**Direct order: Stop adding endpoints.** ContentForge is feature-complete at 50 endpoints.

Any further feature work before CWS approval and calibration results is Product Procrastination.

| Allowed | Not Allowed |
|---|---|
| Bug fixes and scoring weight recalibration | New endpoints |
| Documentation updates | New platforms |
| Processing Blind Taste Test submissions | Architecture changes |
| Drafting blog/HN post | UI/UX work |
| Monitoring Render/Gemini stability | Anything on the "nice to have" list |

The only technical work permitted during this phase:
1. **CWS approval response** — standalone tweet + PH update (CTAs already wired)
2. **Blind Taste Test data processing** — the moment a submission arrives, run scores, log delta
3. **Stability watch** — Render health, Gemini cache, cron-job.org pings

---

### Immediate (Day of CWS approval):

| Task | Time est. | Priority |
|---|---|---|
| Swap CWS store icon to crystal logo from PH | 15 min | P0 |
| Landing page: CTAs auto-activate (already wired) | 0 min | Done |
| Update PH listing with live CWS link | 10 min | P1 |
| Post standalone tweet: "Extension is live on Chrome Web Store" | 5 min | P1 |

### Week 1 — Distribution + Calibration Acquisition (April 6–12):

| Task | Time est. | Priority | Status |
|---|---|---|---|
| **Blind Taste Test live** — Discussion #4 pinned | Done | P0 | ✅ |
| r/SideProject post (Mon April 7) — includes Blind Test recruit + lifetime Ultra offer | 10 min | P0 | 📋 Draft ready |
| r/selfhosted post (Tue April 8) — self-hosting angle + Blind Test recruit | 10 min | P0 | 📋 Draft ready |
| Process ALL Blind Test submissions within 24h of receipt | 2 hrs each | P0 | ⏳ Waiting |
| Draft "Why We Ditched LLMs for If-Statements" (HN post) | Done | P1 | ✅ `docs/if-statements-vs-llms.md` |
| Extension update: fetch selectors from `/v1/extension_config` | 2 hrs | P1 | ⏳ Post-CWS |
| Extension update: "Automate This Check" cURL generator button | 1 hr | P2 | ⏳ Post-CWS |

**Week 1 single metric that matters:** Blind Taste Test submission count. Target ≥5 by April 12.

**Recruitment frame (use in r/SideProject + r/selfhosted):** "Need 10 more Blind Taste Test participants. Submit 10 historical posts — if the engine correctly ranks your top performers, you get lifetime Ultra access (3,000 AI calls/month). Details: https://github.com/CaptainFredric/ContentForge/discussions/4"

### Week 2 — Data Processing + Calibration (April 13–19):

| Task | Time est. | Priority | Notes |
|---|---|---|---|
| Publish `/docs/validation.md` — Blind Test accuracy results | 1 hr | P0 | Blocked until ≥5 submissions |
| Recalibrate any platform weights with accuracy < 60% | 3 hrs | P0 | Fix in scoring functions directly |
| Submit "If-Statements vs LLMs" to Hacker News | 30 min | P1 | Target: Wed-Thu April 15-16 |
| RapidAPI listing reframe: "Pre-Flight Content Validation for Automation Workflows" | 30 min | P1 | |
| Add "Burst" tier pricing model to RapidAPI if demand signal exists | 1 hr | P2 | Only if ≥3 paying subscribers |

### Week 3–4 — Grand Redistribution (April 20–30):

| Task | Time est. | Priority | Notes |
|---|---|---|---|
| **Product Hunt relaunch** with calibration data + CWS link | 2 hrs | P0 | Blocked on CWS approval + ≥70% accuracy data |
| Reddit reposts (r/webdev comment thread, r/SideProject update) | 1 hr | P1 | With validation results as proof |
| Pitch regulated verticals: compliance/audit angle | 2 hrs | P2 | After PH relaunch |
| Agency outreach if Burst tier demand signals exist | 1 hr | P2 | |

---

## Strategic Positioning (locked)

### Primary narrative
**Interpretable Content Intelligence** — every deduction has a traceable rule, every score has an audit trail. In a world of black-box AI, ContentForge is the white-box alternative.

### Secondary narratives
- **"A Digital Ruler, Not a Black Box"** — the ruler is transparent; you can see the markings
- **"Pre-Flight Content Validation"** — score before you ship, not after you flop
- **"Anti-Stochastic Quality Gate"** — deterministic in a world of LLM variance

### The moat (definitive)
**Auditability > Latency.** When LLMs get faster, "we're faster" dies. "We can show you the exact rule that deducted 12 points for headline sentiment mismatch" gets stronger as black-box alternatives proliferate.

### Target segments (prioritized)
1. **Indie hackers / build-in-public** — extension + free API tier (Saturday r/webdev audience)
2. **Content agencies** — bulk scoring, Burst tier, "defensible content decisions for clients"
3. **Regulated verticals** — finance, healthcare, B2B compliance — can't deploy black-box tools for audit trails

---

## Metrics dashboard (track weekly)

| Metric | Baseline (April 4) | Week 1 target | Month-end target |
|---|---|---|---|
| GitHub stars | current | +10 | +50 |
| RapidAPI subscribers | current | +3 | +20 |
| CWS installs | 0 | 10 (post-approval) | 50 |
| Blind Test submissions | 0 | 5 | 20 |
| Heuristic accuracy (blind test) | unknown | ≥70% | ≥80% |
| `/v1/feedback` submissions | 0 | 3 | 15 |
| Revenue | $0 | $0 | first paid subscriber |

---

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| CWS rejected on first review | Medium | High | Fix issues, resubmit within 24h. Web demo is the fallback. |
| CWS approval takes 14+ days | Medium | Medium | Focus on API/web demo. Extension is additive, not blocking. |
| Gemini 429 during Saturday traffic | High | Low | Scoring is deterministic. AI 429s are expected and scripted. |
| Heuristic accuracy < 60% on a platform | Medium | High | Recalibrate weights within 48h. Be transparent about the process. |
| Twitter DOM change breaks extension badge | Medium | Medium | `/v1/extension_config` ready. Hot-swap + CWS resubmit. |
| r/webdev post gets no traction | Low | Medium | Cross-post schedule continues regardless. One real conversation > 50 upvotes. |
| Someone finds the MonyPrinterV2 git history | Low | Low | Repo is clean. History shows professional evolution, not a cover-up. |

---

*This document is the single source of truth for ContentForge operations through April 30, 2026. Update weekly.*
