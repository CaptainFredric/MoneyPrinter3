# r/SideProject post (Monday April 7)

**Title:** Built a deterministic content scoring API because LLMs kept giving me different scores for the same post

---

I kept running into a frustrating problem with LLM-based content scoring: ask the same model to score the same tweet twice and you get different numbers. For a publish/hold quality gate, that variance kills the whole idea.

So I built ContentForge, a pure heuristic engine that scores social content 0-100 with zero variance. Same input, same score, always.

**What it does:**
- 50 endpoints covering 12 platforms (Twitter, LinkedIn, Instagram, TikTok, YouTube, Pinterest, Reddit, Threads, Facebook, email, ad copy, readability)
- Every score in under 50ms, no inference, no model loading
- Returns `quality_gate: PASSED/REVIEW/FAILED` plus itemized deductions showing exactly what dragged the score down
- `/v1/auto_improve`: scores your draft, rewrites it with AI if it fails, re-scores, loops until it passes. Generator and scorer working as a closed feedback loop.
- Chrome extension that scores as you type on any of those platforms

**The honest trade-off:** LLMs are smarter. They understand nuance a rule engine never will. But for a quality gate running in an automation pipeline, I'd rather have something consistent and auditable than something smart and unpredictable.

AI is still in the system (Gemini handles rewrites and content generation), just not in the scoring path. `/v1/auto_improve` is where the two sides meet.

**Links:**
- GitHub (AGPL-3.0): https://github.com/CaptainFredric/ContentForge
- Live demo: https://captainfredric.github.io/ContentForge/
- API (free tier): https://rapidapi.com/captainarmoreddude/api/contentforge1

Open to feedback on the heuristic weights. There's a `/v1/feedback` endpoint specifically for "this score feels wrong" reports.

---

**Calibration challenge (lifetime Ultra access on the line):**

The heuristic weights are based on platform best-practices documentation, not yet validated against a real performance corpus. I'm running a Blind Taste Test to fix that.

Submit 10 historical posts (5 that performed well, 5 that flopped) without telling me which is which. I run them through the scoring engine and return a ranked order. You tell me if I got it right.

If the engine correctly identifies your top performers: you get **lifetime Ultra API access** (3,000 AI calls/month, every endpoint, no expiry) plus your anonymized results appear in the public validation report.

If it gets it wrong: the mismatch tells me exactly which signal weights are off. That is a direct R&D contribution and you still get a full score breakdown for all 10 posts.

Details and submission template: https://github.com/CaptainFredric/ContentForge/discussions/4

Need 10 more participants to hit statistical confidence before the Product Hunt relaunch.
