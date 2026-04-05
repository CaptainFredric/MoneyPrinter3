# Saturday Execution Plan — r/webdev Showoff + Launch Blitz

**Date:** Saturday, April 5 2026
**Primary goal:** r/webdev Showoff Saturday post → GitHub stars → RapidAPI sign-ups
**Secondary goal:** first organic traffic to CWS listing (extension still in review — link is live even if store page isn't fully published)

---

## Pre-flight (Friday night or Saturday morning before 9am PT)

- [ ] **Confirm API is alive:** `curl https://contentforge-api-lpp9.onrender.com/health` — should return `{"status":"ok","endpoints":47}`
- [ ] **Wake the Render instance:** hit the health endpoint once to ensure it's warm before traffic arrives
- [ ] **Check Gemini quota reset:** quota resets at midnight Pacific — confirm AI generation endpoints respond (they may 429 if Gemini has issues; scoring endpoints are unaffected and that's the primary demo)
- [ ] **Read saturday-post.md one last time** — light editing pass only, don't over-think it
- [ ] **Add CWS link to the post** if the extension gets approved before Saturday:
  - Under "## Links" add: `- **Chrome Extension:** https://chromewebstore.google.com/detail/contentforge-score-before/jjbhcmnmjhhepiinipaamjnfogalnibb`

---

## Post window: Saturday 10am–12pm PT

r/webdev Showoff Saturday thread goes live at ~9-10am PT. Comment early — new threads get buried fast.

### Step 1 — Find the thread
1. Go to https://www.reddit.com/r/webdev/
2. Sort by **New**
3. Look for "Showoff Saturday" or "Side Project Saturday" in the top posts
4. Copy the thread URL

### Step 2 — Post
- Copy the full content from `saturday-post.md`
- Title: **"I built a deterministic content scoring API because LLMs kept giving me different answers"**
- No edits needed — post as-is
- Verify all three links render correctly after posting

### Step 3 — First reply (pin your demo link)
Post as a reply immediately after:
```
**Quick demo (no sign-up):** https://captainfredric.github.io/ContentForge/

Try pasting any tweet draft into the scorer at the bottom — you'll see the quality_gate field and itemized deductions.
```

---

## Engagement window: Saturday 12pm–6pm PT

- [ ] **Check for comments every 30-60 min** — r/webdev crowd will ask about the heuristic design, LLM trade-offs, or the extension. These are exactly the right conversations.
- [ ] **Key questions to be ready for:**
  - *"Why not just use readability libraries like textstat?"* → ContentForge goes beyond readability: platform-specific hooks, hashtag density, CTA detection, emoji distribution. Not just Flesch-Kincaid.
  - *"Isn't this basically a linter?"* → Correct framing. A linter for content, not code. That's a fair analogy and a good sign.
  - *"What's the 429 risk on AI endpoints?"* → Scoring endpoints are deterministic and never 429. AI generation (rewrite, compose_assist) use Gemini with a 15 req/day free tier. Quota resets at midnight PT.
  - *"Is the extension open source?"* → Yes, same repo. Manifest V3, service worker background, offline local heuristic fallback.
- [ ] **Upvote your own post** is against Reddit rules — don't. Let it ride organically.
- [ ] **Do not cross-post the same content to r/SideProject or r/selfhosted the same day** — wait 48h minimum.

---

## Cross-post schedule (after Reddit clears)

| Platform | When | Content | Status |
|---|---|---|---|
| r/SideProject | Monday April 7 | Same post, trimmed to ~200 words + links | |
| r/selfhosted | Tuesday April 8 | Focus on self-hosting angle — AGPL-3.0, `docker run`, no vendor lock-in | |
| Twitter/X | Saturday afternoon | 3-tweet thread: problem → solution → demo link. Tag #buildinpublic | |
| LinkedIn | Sunday April 6 | Professional tone version: "quality gate for content teams", API + extension angle | Drafted (90/A/PASSED per ContentForge scorer) |
| Product Hunt | Wait for CWS approval | Update PH with real CWS link, post comment with Saturday feedback highlights | |
| Blind Taste Test | Live now | [Discussion #4](https://github.com/CaptainFredric/ContentForge/discussions/4) — pinned. Tracking calibration results in `docs/validation.md` | Live & pinned |

---

## Twitter thread template (Saturday PM)

**Tweet 1 (hook):**
```
I asked GPT to score the same tweet twice.
Got 72. Then 61. Same tweet.

That's why I built a deterministic scorer instead.
```

**Tweet 2 (solution):**
```
ContentForge: 47 endpoints, 12 platforms, <50ms
Pure heuristic engine — no LLM in the scoring path

Same input → same score → every time.

chrome extension scores as you type 👇
```

**Tweet 3 (demo):**
```
Try it: https://captainfredric.github.io/ContentForge/

Paste any draft → get a 0-100 score + quality_gate + itemized deductions in under 50ms.

AGPL-3.0 · self-hostable · free tier on RapidAPI

#buildinpublic #indiedev #webdev
```

---

## If CWS extension gets approved during/before Saturday

- [ ] Update all 4 extension CTAs in `index.html` are already pointing to the CWS URL — nothing to change
- [ ] Add CWS link to saturday-post.md under links section
- [ ] Add CWS link to Twitter thread tweet 2
- [ ] Post a standalone tweet: *"ContentForge extension is live on the Chrome Web Store → [link]. Score your drafts without leaving Twitter/LinkedIn."*
- [ ] Update Product Hunt listing description with real CWS link

---

## If Gemini 429s hit during Saturday traffic

- Scoring endpoints are unaffected — the core demo (`score_tweet`, `score_multi`, `compare`, `ab_test`) all work
- AI generation endpoints (`rewrite`, `compose_assist`, `generate_hooks`) will return 429 until midnight Pacific
- In thread replies: *"AI generation endpoints share a Gemini free-tier quota — if you hit a 429, it resets at midnight PT. All scoring endpoints are deterministic and never rate-limited."*
- This is actually an honest signal that people are using it — lean into it

---

## End of day check (Saturday 8pm PT)

- [ ] Note comment count + upvotes (screenshot for build-in-public tweet)
- [ ] Check RapidAPI dashboard for new sign-ups
- [ ] Check GitHub for new stars / forks / issues
- [ ] Check Render logs for unusual traffic or errors
- [ ] Draft Monday r/SideProject post based on any feedback themes from Saturday

---

## What success looks like on Saturday

| Metric | Acceptable | Good | Exceptional |
|---|---|---|---|
| Reddit upvotes | 5-15 | 15-50 | 50+ |
| Reddit comments | 2-5 | 5-15 | 15+ |
| GitHub stars gained | 1-3 | 3-10 | 10+ |
| RapidAPI sign-ups | 0-1 | 1-3 | 3+ |
| Landing page visits | 20-50 | 50-200 | 200+ |

r/webdev Showoff Saturday is a grind. Most posts get 5-10 upvotes. A single comment from someone who actually tried it is worth more than 50 passive upvotes. The goal is one real conversation, not virality.
