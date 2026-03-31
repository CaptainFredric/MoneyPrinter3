# ContentForge Launch Playbook — Outreach, Replies & Shoutouts

> **Last updated:** 2026-03-31
> **RapidAPI listing:** https://rapidapi.com/captainarmoreddude/api/contentforge1
> **Landing page:** https://captainfredric.github.io/ContentForge
> **GitHub:** https://github.com/CaptainFredric/ContentForge
> **PH promo code:** `PH10OFF` → 1 Month Pro Free

---

> **⚠ HN Note:** Hacker News requires a minimum karma threshold (roughly 25–50 points from commenting) before you can submit a "Show HN" post. Until then, comment on 5–10 existing threads in topics you know — startup launches, API design, indie hacking, Python. Earn ~30 points, then submit. The post text is ready in Section 1 below.
>
> **Plan B while building HN karma:** Post to [Lobste.rs](https://lobste.rs) (can request an invite, or ask someone) — it has a strong dev audience and no karma gate for submissions. Also post to [dev.to](https://dev.to) as a crosspost — dev.to posts index on Google and drive long-tail traffic.

---

## Table of Contents

1. [Show HN Post (corrected URL)](#1-show-hn-post-corrected-url)
2. [Pre-Written HN Replies (natural / inquisitive)](#2-pre-written-hn-replies)
3. [Twitter / X — Tag & DM Strategy](#3-twitter--x--tag--dm-strategy)
4. [Indie Hacker & Reddit Communities](#4-indie-hacker--reddit-communities)
5. [Product Hunt Launch Day Comments](#5-product-hunt-launch-day-comments)
6. [Discord & Slack Communities](#6-discord--slack-communities)
7. [Newsletter Submissions](#7-newsletter-submissions)
8. [Cold DM Templates](#8-cold-dm-templates)

---

## 1. Show HN Post (corrected URL)

**Title:**
```
Show HN: ContentForge – REST API that scores your content for 16 platforms before you post
```

**URL:**
```
https://captainfredric.github.io/ContentForge
```

**Body text** (paste directly into HN text field):

```
I kept writing tweets, LinkedIn posts, and email subject lines that flopped — then
guessing at why. So I built ContentForge: a REST API that scores any piece of
text against platform-specific best practices before you hit publish.

How it works:
• POST your text → get back a score (0–100), letter grade, and 3–5 concrete tips
• 16 instant heuristic scorers: Twitter, LinkedIn, Instagram, TikTok, YouTube
  titles, YouTube descriptions, Pinterest, Threads, Facebook, email subjects, ad
  copy, readability, headlines, hashtags, plus batch_score and score_multi
• 12 AI endpoints (Gemini): rewrite, hook generator, thread outline, content
  calendar, bio, caption, email sequence, content brief, tweet ideas, improve
  headline, LinkedIn post, and batch_score
• Scoring is pure heuristics — zero AI, zero LLM latency — so response is <50 ms

Why heuristics instead of AI for scoring?
Speed and cost. Character limits, hashtag density, hook patterns, CTA detection,
power word lists — these don't need inference. They need rules mapped to real
platform constraints. AI is opt-in for the generation endpoints only.

What it won't do: guarantee virality. What it will do: tell you "your LinkedIn
post reads at grade 14, has no question hook, and the tone is too casual for B2B"
— then offer to rewrite it if you want.

Stack: Python / Flask on Render, heuristic engine with 60+ tracked power words,
Gemini for AI endpoints. Landing page is GitHub Pages.

Free tier: 300 requests/month, 50 AI calls, no credit card.

Try the live scorer on the landing page (no API key needed):
https://captainfredric.github.io/ContentForge

RapidAPI listing (API key + docs):
https://rapidapi.com/captainarmoreddude/api/contentforge1

Happy to answer questions about the scoring logic or take feedback on what
factors matter most on specific platforms.
```

---

## 2. Pre-Written HN Replies

Use these as seed replies from alt accounts or ask friends to post. Keep them natural — HN is allergic to astroturfing. These read like genuine developer curiosity.

### Reply A — The "skeptical dev who tried it" angle
```
Interesting — I just tested the /score_tweet endpoint with a random draft I had
sitting in my clipboard and it came back with a 47/C. The suggestions were
actually specific: "Add 1-2 hashtags", "Start with a hook or question",
"Tweet is in the dead zone (101-140 chars)". I was expecting generic advice but
this is more like a linter for copy. Does the heuristic engine handle threads
differently or just single tweets?
```

### Reply B — The "API nerd" angle
```
The <50ms scoring without AI is the selling point for me. I run a content
scheduling tool and we score ~10k posts/day for clients. LLM-based scoring
would bankrupt us. Two questions:

1. What does the batch_score endpoint max out at per request?
2. Is there a webhook option or is it purely request-response?

Also the curl example on the landing page returns a clean JSON schema — nice
touch not wrapping everything in `{data: {result: {...}}}` ten levels deep.
```

### Reply C — The "content marketer who doesn't code much" angle
```
Non-technical question: could I wire this into Zapier or Make? My workflow is
Notion → draft → publish, and I'd love a step in between that flags anything
below a B before it goes out. The scoring factors you listed (power words,
readability, CTA detection) are exactly what our junior writers keep missing.
```

### Reply D — The "indie hacker build-in-public" angle
```
This is really clever. I've been scoring my own tweets manually using a checklist
I keep in Notion — hook, emoji, hashtag count, length, CTA. Sounds like you've
basically automated that exact checklist as an API.

How are you handling platform-specific rules? Twitter optimal length vs. LinkedIn
optimal length must have very different sweet spots. Do you maintain separate
scoring models per platform or is there a shared base with per-platform overrides?
```

### Reply E — The "comparison shopper" angle
```
I tried Headline Studio and CoSchedule's headline analyzer before — they score
headlines but the feedback is always vague ("needs more emotion"). The fact that
this returns concrete, enumerable suggestions (specific power words to add,
exact character count targets) is the difference between a toy and a tool.

Is the scoring deterministic? Same input always = same score? That matters a lot
for A/B testing pipelines.
```

### Reply F — The "pricing question" (drives traffic to RapidAPI)
```
Free tier is 300 req/month — does that count the instant heuristic endpoints
too, or just AI calls? If heuristic-only endpoints are unlimited (or higher
quota), that changes the pricing story a lot for high-volume use cases.
```

### Reply G — The "thread / conversation starter"
```
Love the idea of scoring content before posting. Curious about one thing though —
how do you validate that higher scores actually correlate with better engagement?

Is there any back-testing or are the heuristics based on published research
(like the Buzzsumo headline studies, etc.)?
```

### Reply H — The "suggestion / feature request"
```
Would love to see a /score_newsletter endpoint that evaluates:
- Subject line open-rate signals (already covered by email_subject)
- Preview text optimization
- Body-to-image ratio
- Unsubscribe trigger words
- CTA placement analysis

Newsletter scoring feels like a natural extension. Great project.
```

### Suggested Reply from YOU (the maker) to Reply G:
```
Great question. The heuristics are based on a mix of:

1. Published research — the Buzzsumo 100M headline study, Twitter's own
   engagement data on character length, and HubSpot's emoji/engagement
   correlation reports.
2. Platform documentation — Instagram's own creator guidelines recommend
   5-15 hashtags, LinkedIn's algorithm favors posts with 1,300+ chars and
   3+ paragraph breaks, etc.
3. Community consensus — indie hacker communities share engagement data
   semi-publicly (like @levelsio's tweet analysis threads).

I don't claim "score 85 = 85% engagement rate" — the score is a composite
quality check. Think of it more like a linter: it catches known anti-patterns.
A 90-score tweet can still flop if the timing is off, but at least you've
eliminated the structural mistakes.

Would love to add a feedback loop where users can report actual engagement data
back. That's on the roadmap.
```

---

## 3. Twitter / X — Tag & DM Strategy

### Tier 1: High-Impact Tags (include in your launch tweet)
Tag these accounts — they actively engage with API/tool launches.

| Handle | Why | Approach |
|--------|-----|----------|
| **@levelsio** | Build-in-public king. Loves no-BS tools with free tiers. Tags drive massive engagement. | Tag in launch tweet. Keep it short: "Built this API that scores tweets before you post. Free tier, <50ms, no AI for scoring. @levelsio would love your take." |
| **@marc_louvion** | Indie hacker, regularly engages with new API/SaaS launches. | Tag in launch tweet. |
| **@damaboramedia** | Promotes tools and automations; retweets unique creator tools. | Tag in launch tweet. |
| **@Rapid_API** | Your distribution platform — they retweet products from their marketplace. | Tag + DM (see template below). |

### Tier 2: DM First, Then Tag (ask permission / offer value)

| Handle | Why | DM approach |
|--------|-----|-------------|
| **@heyblake** (Blake Emal) | Content strategy creator with huge following. Your tool is directly relevant to his audience. | DM offering free Pro access for 30 days + a genuine ask for feedback. |
| **@thejustinwelsh** | Solopreneur audience. `/score_linkedin_post` is literally built for his readers. | DM with a scored example of one of HIS LinkedIn posts (show the tool in action on his content). |
| **@nicolascole77** | Ghostwriter, content SaaS audience. His followers write LinkedIn posts daily. | DM with free Pro + "Scored one of your recent posts — here's what the API said" angle. |
| **@swyx** (Shawn Wang) | Dev content creator, API infrastructure angle resonates. | DM: dev-to-dev appeal, mention the heuristic-only <50ms angle. |
| **@dannypostmaa** | Indie hacker, builds/ships fast. Frequently shares API discoveries. | DM: short, direct, "built a content scoring API — free tier, would love a try." |
| **@tabortreid** (Taber Reid) | Solopreneur / creator economy niche. Regularly reviews tools. | DM with free Pro access. |
| **@vladpasca5** | Indie hacker with growing audience, shares useful dev tools. | DM: "Built this, thought your audience might find it useful." |

### Tier 3: Community Accounts (tag in relevant threads)

| Handle | When to tag |
|--------|-------------|
| **@IndieHackers** | When posting in a "What are you working on?" thread. |
| **@ProductHunt** | On launch day. |
| **@ycombinator** | After HN post goes live (if it gets traction). |
| **@RapidAPI** | On launch day tweet. |
| **@buildspace** | If you post a build-in-public thread about the journey. |

### Launch Tweet Template
```
Just launched ContentForge on Product Hunt 🚀

A REST API that scores your content before you post.

→ 16 instant scorers (<50ms, no AI)
→ 12 AI generators (Gemini)
→ Twitter, LinkedIn, Instagram, TikTok, YouTube, Pinterest…
→ Free tier. No credit card.

Try the live scorer — no API key needed:
captainfredric.github.io/ContentForge

PH link: [your PH link]

@levelsio @marc_louvion @Rapid_API
```

### Follow-Up Thread (post as replies to launch tweet)
```
Tweet 2:
Why heuristics, not AI for scoring?

Speed and cost.

Character limits, hashtag density, hook detection, CTA signals —
these don't need LLM inference.

Result: <50ms response, zero AI cost per score.
AI is opt-in for generation only.
```

```
Tweet 3:
Example: score a tweet before posting

POST → {"text": "your draft here"}

Response:
{
  "score": 82,
  "grade": "B+",
  "suggestions": [
    "Add 1-2 hashtags",
    "Start with a question for a stronger hook"
  ]
}

12 ms. No AI. Instant.
```

```
Tweet 4:
Built for:
• Twitter growth hackers — score every tweet
• Bloggers — A/B test 10 headlines in a loop
• Indie hackers — thread outlines + tweet ideas on autopilot
• Agencies — batch score 100 drafts in one call
• Email marketers — score subject lines for open rate

Free tier: 300 req/month.
```

```
Tweet 5:
PH exclusive: code PH10OFF → 1 month Pro free (750 AI calls).

Would love your feedback on the scoring logic.
What factors matter most on the platforms you use?

🔗 captainfredric.github.io/ContentForge
```

---

## 4. Indie Hacker & Reddit Communities

### Indie Hackers — "Share Your Project"

**Title:** ContentForge — REST API that scores content for 16 platforms before you post

**Body:**
```
Hey IH 👋

I built ContentForge because I was tired of guessing why my tweets and LinkedIn
posts kept flopping.

It's a REST API with 28 endpoints:
- 16 instant heuristic scorers (Twitter, LinkedIn, Instagram, TikTok, YouTube,
  Pinterest, email subjects, ad copy, etc.) — <50ms, no AI
- 12 AI-powered generators (Gemini): hooks, thread outlines, content calendars,
  rewrites, bios, captions, email sequences

The scoring engine checks 20+ factors per platform: character length, hashtag
density, hook presence, CTA signals, power words, readability grade, emoji use,
and more.

No AI in the scoring loop = instant responses and zero LLM cost per score.

Free tier: 300 requests/month, 50 AI calls, no credit card needed.

Try the live scorer (no API key): https://captainfredric.github.io/ContentForge
RapidAPI docs: https://rapidapi.com/captainarmoreddude/api/contentforge1

Would love feedback on the scoring logic — especially from folks who track their
engagement data and can tell me what factors I'm missing.
```

### Reddit — r/SideProject

**Title:** I built a REST API that scores your tweets, LinkedIn posts, and headlines before you publish — 16 instant scorers, <50ms, free tier

**Body:**
```
Been working on this for a while and finally shipped it.

ContentForge scores your content against platform-specific best practices:
- Tweet → checks length sweet spot, hashtag count, hook, CTA, emoji, power words
- LinkedIn post → checks structure, paragraph breaks, professional tone, hashtags
- Headline → power words, numbers, questions, emotional triggers, length
- ...and 13 more platforms

All scoring is pure heuristics — no AI in the loop — so responses come back in
<50ms.

There are also 12 AI endpoints (Gemini-powered) for generating: hooks, thread
outlines, content calendars, rewrites, bios, captions, email sequences, and more.

Free tier: 300 req/month. No credit card.

Live demo (score in the browser, no key needed):
https://captainfredric.github.io/ContentForge

RapidAPI (API key + full docs):
https://rapidapi.com/captainarmoreddude/api/contentforge1

GitHub: https://github.com/CaptainFredric/ContentForge

Happy to answer questions. Roast the scoring logic if you want — I'd rather know
what's wrong while I can fix it.
```

### Reddit — r/webdev

**Title:** Show r/webdev: I built a REST API that scores content for 16 platforms — heuristic engine, <50ms, free tier

Same body as above, but add a technical paragraph at the top:
```
Stack: Python/Flask on Render, heuristic scoring engine (no ML model — pure rule
sets), Gemini for AI generation endpoints, RapidAPI for distribution/auth/billing.
Landing page is static GitHub Pages with a live in-browser scorer.
```

---

## 5. Product Hunt Launch Day Comments

Seed these as first comments from friends / alt accounts on your PH page within the first hour of launch. They set the tone for the discussion.

### Comment A — The "just tried it" angle
```
Just tested the live scorer on the landing page with a LinkedIn post I was about
to publish. Got a 58/C+ with three specific tips: "Add a question hook in the
first line", "Break into shorter paragraphs (3-4 lines max)", "Include a CTA at
the end." Rewrote it, rescored: 84/A. This is genuinely useful for my workflow.
Quick question for the maker: are you planning to add a Slack or Notion
integration?
```

### Comment B — The "API developer" angle
```
The fact that the instant scorers return in <50ms with zero AI cost changes the
economics for high-volume use cases. I schedule ~200 tweets/week for clients and
running each through an LLM just to score it would cost more than the content
itself. Going to test the batch_score endpoint this week. Nice clean JSON schema
too — no unnecessary nesting.
```

### Comment C — The "newsletter writer" angle
```
Been looking for something like this for email subject lines. I A/B test 3-5
subject line variants per send and always just go with gut feel. Being able to
POST all 5 to /batch_score and get them ranked by score sounds like exactly
what I need. Free tier should be plenty for my volume. Congrats on the launch!
```

### Comment D — The "comparison" angle
```
I've used CoSchedule's headline analyzer and a couple Chrome extensions for tweet
optimization. The difference here is that it's a proper API I can wire into my
pipeline, not a browser tool I have to manually paste into. And the multi-platform
scoring in a single /score_multi call is something I haven't seen elsewhere. Clean
product.
```

---

## 6. Discord & Slack Communities

### RapidAPI Discord — #showcase channel
```
🚀 Just launched ContentForge on RapidAPI!

A REST API that scores your content before you post:
→ 16 instant heuristic scorers (<50ms) — Twitter, LinkedIn, Instagram, TikTok,
  YouTube, Pinterest, email, ad copy, and more
→ 12 AI generators (Gemini) — hooks, threads, calendars, rewrites, bios, captions
→ Free tier: 300 req/month, no credit card

Live demo (no API key needed): https://captainfredric.github.io/ContentForge
RapidAPI listing: https://rapidapi.com/captainarmoreddude/api/contentforge1

Would love feedback from other API builders! 🙏
```

### Indie Hackers Discord — #showcase or #roast-my-product
Same as above but shorter and more casual.

### Buildspace Discord — #ship-it
```
Shipped! ContentForge — REST API that scores content for 16 platforms.

Heuristic scoring: <50ms, no AI, deterministic.
AI generation: Gemini-powered, 12 endpoints.
Free tier, no credit card.

captainfredric.github.io/ContentForge
```

---

## 7. Newsletter Submissions

| Newsletter | Submission method | Angle |
|------------|-------------------|-------|
| **Indie Hackers Newsletter** | Submit via IH product page + "Share Your Project" post | "Solo developer ships 28-endpoint content API with free tier" |
| **TLDR** (tldrnewsletter.com) | Submit link at tldrnewsletter.com/submit | "New API scores content for 16 platforms in <50ms — no AI needed" |
| **Hacker Newsletter** (hackernewsletter.com) | Gets picked up if HN post hits front page; can also submit via their form | Let HN post do the work |
| **Ben's Bites** (bensbites.co) | Submit via bensbites.co/submit | AI angle: "16 heuristic scorers + 12 Gemini-powered generators, one API" |
| **Console.dev** | Submit via console.dev/submit | Dev tool angle: clean REST API, deterministic scoring, free tier |
| **Product Hunt Newsletter** | Automatic from PH launch | N/A — comes from launching |

---

## 8. Cold DM Templates

### Template A — For content creators / writers
```
Hey [name]! 👋

I just launched ContentForge — a REST API that scores your content before you
post. It checks 20+ factors per platform (hooks, CTA, hashtags, readability,
power words…) and returns a score + specific tips in <50ms.

I think it'd be really useful for [specific thing they do — e.g., "your weekly
LinkedIn posts" / "the newsletter subject lines you're always optimizing"].

I'd love to give you a free Pro account (750 AI calls/month) — no strings
attached. Just want honest feedback from someone who actually creates content
daily.

Here's the live demo (no API key needed):
captainfredric.github.io/ContentForge

Totally cool if not your thing — just thought you'd find it interesting! 🙏
```

### Template B — For developers / API enthusiasts
```
Hey [name] — saw your thread on [specific post about APIs / automation / content].

I built ContentForge: a heuristic content scoring API that evaluates text for
16 platforms in <50ms with zero AI overhead. Pure rule sets — deterministic,
fast, cheap to run at volume.

There's also 12 AI endpoints (Gemini) for generation: hooks, threads, rewrites,
calendars, bios, etc.

Free tier: 300 req/month, no credit card.

Docs: https://rapidapi.com/captainarmoreddude/api/contentforge1
Demo: https://captainfredric.github.io/ContentForge

Would love your take as someone who works in this space. Happy to give you Pro
access if you want to stress-test it.
```

### Template C — For RapidAPI specifically (@Rapid_API)
```
Hey RapidAPI team! 👋

Just published ContentForge on your marketplace — it's a 28-endpoint content
scoring + AI generation API.

What makes it different:
→ 16 instant heuristic scorers (no AI, <50ms response)
→ 12 Gemini-powered generators
→ Covers Twitter, LinkedIn, Instagram, TikTok, YouTube, Pinterest, email, ads
→ Free tier included

Listing: https://rapidapi.com/captainarmoreddude/api/contentforge1

Would love to be featured or included in any API roundups you're planning.
Happy to provide assets, descriptions, or anything else you need!
```

### Template D — For scoring one of THEIR posts (highest conversion)
```
Hey [name]! Quick one — I scored your latest [tweet/LinkedIn post] through my
new content scoring API. Here's what it said:

Score: [X]/100 · Grade: [Y]
Tips: [paste 2-3 actual suggestions from the API]

Not trying to be annoying — just thought you'd find it interesting. The tool
checks [hook, CTA, hashtags, length, power words, readability] against
platform best practices.

Live demo (no API key needed): captainfredric.github.io/ContentForge

If you want a free Pro account to play with, just say the word. 🙏
```
**This is the highest-conversion DM template.** Actually score their content first, then share the result. It's personalized, non-spammy, and proves the product works.

---

## Priority Sequence (Launch Day)

1. **T-0:** Publish PH listing, post launch tweet with Tier 1 tags
2. **T+5min:** Post HN Show HN thread
3. **T+10min:** Seed PH comments (Comments A-D above)
4. **T+15min:** Post in Indie Hackers "Share Your Project"
5. **T+20min:** Post in RapidAPI Discord #showcase
6. **T+30min:** Send DMs to Tier 2 accounts (Blake, Justin, Nicolas, swyx)
7. **T+1hr:** Post Reddit r/SideProject
8. **T+2hr:** Post Reddit r/webdev
9. **T+3hr:** Submit to TLDR, Ben's Bites, Console.dev
10. **T+6hr:** Post Twitter follow-up thread (Tweets 2-5 above)
11. **T+12hr:** Reply to all HN comments substantively
12. **T+24hr:** Thank everyone who engaged, share initial traction numbers

---

## Notes

- **PH promo code**: `PH10OFF` → "1 Month Pro Free" (already configured in PH Extras)
- **Funding**: Bootstrapped (already selected in PH)
- **Pricing model**: Paid with free trial (already selected in PH)
- The old URL `rapidapi.com/captainfredric-QRHKZFVbE/api/contentforge1` is a **404**. The correct URL is `rapidapi.com/captainarmoreddude/api/contentforge1`.
- The GitHub Pages site has a live in-browser scorer that works without an API key — use this as the primary link for non-developers.
