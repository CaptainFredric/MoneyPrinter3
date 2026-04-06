# r/selfhosted post (Tuesday April 8)

**Title:** ContentForge: self-hostable content scoring API, AGPL-3.0, pure Python, no ML deps

---

Built a content scoring API that runs fully offline with zero external dependencies in the scoring path!

**Why it belongs here:**

- AGPL-3.0 — full source, fork it, run it, modify it
- `pip install -r requirements.txt && python scripts/api_prototype.py` — running in under a minute
- Zero ML dependencies in the scoring engine — pure Python, stdlib + regex only
- 50 endpoints, <50ms, deterministic (same input = same output, always)
- AI generation endpoints (rewrites, hooks) use local Ollama first — if Ollama is running, nothing leaves your machine

**What it scores:** Twitter/X, LinkedIn, Instagram, TikTok, YouTube titles/descriptions, Pinterest, Reddit, Threads, Facebook, email subjects, ad copy, readability. Every scoring endpoint returns the score, grade, `quality_gate` (PASSED/REVIEW/FAILED), and itemized deductions.

**Self-host setup:**
```bash
git clone https://github.com/CaptainFredric/ContentForge
cd ContentForge
pip install -r deploy/requirements-api.txt
python scripts/api_prototype.py
# API running at localhost:8081
```

For AI generation locally: install Ollama, pull llama3.2:3b (or any model), and set `OLLAMA_HOST=http://localhost:11434`. No Ollama? Set `GEMINI_API_KEY` for cloud fallback.

**GitHub:** https://github.com/CaptainFredric/ContentForge

Interested in feedback on the self-hosting experience — particularly Docker setup which is on the roadmap!

---

**Da Calibration Challenge (lifetime Ultra access on the line!!!):**

The scoring weights are built from platform documentation, not validated against real engagement data yet. Running a Blind Taste Test to fix that — and I need people who actually create content.

Submit 10 historical posts! 5 top performers, 5 flops, without labeling which is which. The engine ranks them. You verify the ranking. If it gets your top 5 right, you get **lifetime Ultra API access** (3,000 AI calls/month, no expiry). Either way you get a full deterministic score breakdown for all 10 posts — the same audit trail you'd run in a self-hosted pipeline.

Basically win-win!

Submission template: https://github.com/CaptainFredric/ContentForge/discussions/4

Need 10 more participants across platforms before the Product Hunt relaunch.....
