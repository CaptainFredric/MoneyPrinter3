# r/SideProject post (Monday April 7)

**Title:** Built a deterministic content scoring API — same tweet, same score, every time

---

I kept running into a fundamental problem with LLM-based content scoring: ask the same model to score the same tweet twice and you get different numbers. For a "publish/hold" quality gate, that variance is a dealbreaker.

So I built ContentForge — a pure heuristic engine that scores social content 0-100 with zero variance. Same input, same score, always.

**What it does:**
- 48 endpoints, 12 platforms (Twitter, LinkedIn, Instagram, TikTok, YouTube, Pinterest, Reddit, Threads, Facebook, email, ad copy, readability)
- Every score under 50ms — no inference, no model loading
- Returns `quality_gate: PASSED/REVIEW/FAILED` + itemized deductions showing exactly why
- `/v1/auto_improve`: score → if not PASSED → AI rewrites it → re-scores → loops until PASSED (up to 5 iterations). Generator and scorer in a closed feedback loop.
- Chrome extension scores as you type on any of those platforms

**The honest trade-off:** LLMs are smarter. They understand nuance a rule engine never will. But for a quality gate that runs in automation pipelines, I'll take consistent and auditable over smart and unpredictable.

AI is still in the system (Gemini for rewrites and content generation) — just not in the scoring path. `/v1/auto_improve` is where the two sides meet.

**Links:**
- GitHub (AGPL-3.0): https://github.com/CaptainFredric/ContentForge
- Live demo: https://captainfredric.github.io/ContentForge/
- API (free tier): https://rapidapi.com/captainarmoreddude/api/contentforge1

Open to feedback on the heuristic weights — there's a `/v1/feedback` endpoint specifically for "this score feels wrong" reports.
