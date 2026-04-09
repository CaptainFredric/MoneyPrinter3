# ContentForge Blind Test — We'll Score Your Content History Without Looking at Your Metrics

**Post this as a GitHub Discussion on Sunday/Monday after the r/webdev thread.**

---

## GitHub Discussion Post

**Title:** ContentForge Calibration Challenge — submit your content history and we'll tell you which posts performed

**Body:**

We built ContentForge on the premise that deterministic heuristics can predict content performance better than gut feel — and we want to prove it publicly before our Product Hunt launch.

Here's the challenge:

**Submit 10 historical posts** (5 that performed well, 5 that flopped) with their actual engagement numbers. Don't label which is which — just give us the text. We'll run them through the scoring engine and return the ranked order. Then you tell us if we got it right.

---

### How to participate

Copy this template into a comment below:

```
Platform: [Twitter/LinkedIn/Instagram/etc.]

Post 1: [paste text]
Post 2: [paste text]
Post 3: [paste text]
Post 4: [paste text]
Post 5: [paste text]
Post 6: [paste text]
Post 7: [paste text]
Post 8: [paste text]
Post 9: [paste text]
Post 10: [paste text]

Actual metrics: [e.g. "posts 1,3,7 were top performers — 10x avg impressions"]
```

You can also DM the texts if you'd rather keep your content private — results will be reported without attribution.

---

### What you get

- **If we correctly identify your top performers:** You get early API credits (500 AI calls, no expiry) and your results appear anonymized in our public validation report.
- **If we get it wrong:** The mismatch tells us exactly which heuristic signals are weighted incorrectly — that's an R&D win and you've directly improved the tool for everyone.
- Either way, you get a complete score breakdown for all 10 posts: score, grade, quality_gate, and itemized deductions.

---

### Why we're doing this in public

The scoring engine uses deterministic heuristics — same input, same score, always. But heuristics are only as good as their calibration. We want to validate the weights against real-world performance data before we claim the engine is production-ready.

Public calibration > private testing. If you find a flaw, we'd rather know now.

---

*Running until April 30, 2026. Results will be posted in `/docs/validation.md` in this repo.*

---

## Internal Notes (don't post)

### What to do with submissions

1. Run each post through the appropriate `score_{platform}` endpoint
2. Rank by score descending
3. Compare to participant's "actual metrics" label
4. Record: `correct_rank / total_posts` for each submission
5. Or run the calibration harness locally:

```bash
python scripts/calibrate_content.py \
  --input docs/calibration_dataset_template.csv \
  --report-json docs/calibration_report.json \
  --report-md docs/calibration_report.md \
  --examples-json docs/calibration_examples.json
```

6. Track summary rows in `/docs/validation.md`:

```
| Participant | Platform | Posts | Correct Rankings | Accuracy |
|---|---|---|---|---|
| anon_01 | Twitter | 10 | 8/10 | 80% |
```

### Aggregate target before Product Hunt

- Minimum 20 submissions across ≥3 platforms
- Target accuracy: ≥70% correct ranking (top 5 identified correctly)
- If accuracy < 60% on any platform → recalibrate that platform's weights before PH

### Early credits redemption

Reply to participant with:
> "Your results: [paste scores]. You get 500 API credits — send your email to [captainarmoreddude@gmail.com] and I'll apply them manually. Thanks for helping calibrate."

Credits tracked manually in a private spreadsheet until a formal credits system is built.

### /v1/feedback endpoint

Any participant who feels a score is off can also hit:
```bash
curl -X POST https://contentforge-api-lpp9.onrender.com/v1/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "text": "their post text",
    "platform": "tweet",
    "score": 42,
    "expected": "higher",
    "notes": "this post got 2k impressions"
  }'
```
Submissions are logged and reviewed weekly.
