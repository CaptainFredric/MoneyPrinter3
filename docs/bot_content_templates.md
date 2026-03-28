# Bot Content Templates — ContentForge Funnel

Pre-written tweet templates for both accounts. These can be used as seed content
or as inspiration for the LLM prompt system. Each template is under 270 characters.

**Usage**: Copy a template, customize the bracketed `[placeholders]`, and queue it
for posting. Or add these angles to the account's topic categories for AI generation.

---

## niche_launch_1 (NicheNewton) — Copywriting & Headlines

### Value Drops (no CTA, pure engagement)

```
the word "you" outperforms "we" in headlines by 31%

your reader doesn't care about your product. they care about themselves.
```

```
strong headlines share 3 traits:

1. specific number
2. emotional trigger word
3. implied benefit

weak headlines have none. check yours.
```

```
"how to" headlines are not dead. they're just competing with better hooks now.

the fix: add a specific outcome + a timeframe.

"how to write better" → "how to double your click rate in one afternoon"
```

```
your first sentence is your second headline.

if the headline got them to click, sentence one decides if they stay.

most people waste it on backstory. open with the payoff.
```

```
the reason most tweets flop has nothing to do with the algorithm.

it's the first 5 words. people scroll fast. you have 0.3 seconds.

lead with contrast, a number, or a question. never a filler word.
```

### Soft ContentForge Mentions (educational + tool plug)

```
tested 200 headlines through a scoring API today.

patterns that scored highest:
- odd numbers (7 beats 10)
- "without" framing ("grow without ads")
- direct address ("you" in first 4 words)

the free tier scores 50 headlines/month if you want to try it yourself.
```

```
I built a tool that scores any headline on a 0-100 scale.

paste a title → get word-level suggestions + improved versions.

been using it to A/B test my own threads. wild how much a single word swap changes the score.
```

```
hot take: you should never publish a headline without scoring it first.

humans are bad at predicting what works. data isn't.

I've been feeding every title through an analyzer before posting. engagement is up 40%.
```

### Thread Starters

```
5 headline patterns that outperform everything else in 2025:

(thread) ↓
```

```
I analyzed the top 100 viral tweets from last month.

here's what their first 5 words have in common: ↓
```

---

## EyeCatcher — Attention Psychology & Visual Storytelling

### Value Drops (no CTA, pure engagement)

```
your brain processes images 60,000x faster than text.

that's why a single emoji in a wall of text catches your eye before any word does.
```

```
the reason red "sale" signs work isn't urgency.

it's that red triggers a threat response. your brain says "pay attention, something changed."

every scroll-stopping post uses the same principle.
```

```
pattern interrupts are the oldest attention hack.

a comedian pauses before the punchline.
a headline uses "…" before the payoff.
a tweet starts with a number when everyone else starts with "I."

break the rhythm. win the scroll.
```

```
there's a reason people can't look away from before/after photos.

it's called the contrast effect — your brain is wired to detect change.

want more engagement? show the transformation, not just the result.
```

```
the most underrated attention signal on Twitter: white space.

a one-line tweet surrounded by nothing stands out more than a 280-character block.

less text, more stops.
```

### Soft ContentForge Mentions

```
started running my hooks through a scoring tool before posting.

the ones that score 80+ consistently get 3-5x more engagement than the ones I "felt" were good.

turns out intuition is only right about 40% of the time. data wins.
```

```
interesting experiment: I generated 10 hooks for the same topic using an AI tool.

ranked them by score. posted the top one.

it outperformed my hand-written version by 2x.

the tool doesn't write for you — it just shows you which version of YOUR idea hits hardest.
```

### Thread Starters

```
the science of why you stopped scrolling on this tweet:

(a thread about attention, and why most people get it wrong) ↓
```

```
3 visual tricks that make people stop mid-scroll:

every brand uses them. most creators don't. ↓
```

---

## CTA Variants (Rotate These)

Use sparingly — max 1 in every 5-7 posts. Never the same CTA twice in a row.

### For niche_launch_1:
1. `I put the scoring tool in my bio if you want to try it.`
2. `free headline scorer in bio — 50 objects/month, no card.`
3. `link in bio if you want to test your own headlines.`
4. `been using this daily. it's free on RapidAPI if you search ContentForge.`
5. `ContentForge also scores your tweets before you post them. free, bio link.`
6. `you can generate a 7-day content calendar for any niche with ContentForge. free tier, bio.`

### For EyeCatcher:
1. `the hook scorer I use is in my bio if you're curious.`
2. `if you write hooks, there's a free scoring tool in my bio.`
3. `I test all my hooks through a free API before posting. bio link.`
4. `ContentForge scores your tweet drafts too — not just headlines. free, bio link.`

---

## Tweet Scorer Templates (new endpoint — score_tweet)

### niche_launch_1:

```
hot take: you should never post a tweet without scoring it first.

I've been running every draft through a scorer before hitting post.

grade A+ tweets get 3x the engagement. C-grade ones die in silence.

free tool in bio.
```

```
the difference between a tweet that flops and one that goes viral:

it's almost never the idea. it's the first 10 words, the char count, and the hook.

a tweet scorer catches all three before you waste it.
```

```
I scored 50 of my past tweets after the fact.

the ones that got the most engagement averaged a score of 81.
the ones that flopped averaged 44.

now I only post 75+.
```

### EyeCatcher:

```
your tweet draft is a rough cut.

scoring it before posting is the edit.

most people skip the edit.
```

```
A/B testing your tweets doesn't require two accounts.

it requires scoring both versions before you pick one.

the one that scores higher almost always wins in the wild.
```

---

## Content Calendar Templates (new endpoint — content_calendar)

### niche_launch_1:

```
content strategy tip: don't plan posts one at a time.

plan 7 days at once. assign themes per day. batch-write the drafts.

you'll post more consistently and you'll never have "what do I post today?" again.
```

```
I generated a week of tweet drafts for my niche in under 60 seconds today.

7 themes, 7 ready-to-post drafts, all aligned to my audience.

AI content calendar. free on RapidAPI if you search ContentForge.
```

### EyeCatcher:

```
consistent posting isn't about discipline.

it's about having a system that pre-loads your decisions.

a content calendar removes the daily "what should I post?"

that one friction point kills more creators than anything else.
```

---

## Content Calendar Suggestion

**Weekly rhythm per account (7 posts/week):**

| Day | Type | CTA? |
|---|---|---|
| Mon | Value drop (educational) | No |
| Tue | Hot take / contrarian | No |
| Wed | Soft tool mention | Subtle |
| Thu | Question / engagement bait | No |
| Fri | Specific data point / stat | No |
| Sat | Thread starter | No |
| Sun | Tool mention + direct CTA | Yes |

This gives a 6:1 value-to-promotion ratio, which is optimal for trust building
without appearing salesy.

---

## New Topic Categories to Add

If these aren't already in account configs, consider adding:

**niche_launch_1:**
- `headline_scoring` — data-driven headline optimization
- `tweet_scoring` — score drafts before posting
- `content_calendar_strategy` — batch-planning content
- `api_tools_for_writers` — tools that improve writing workflow
- `before_after_headlines` — transformation examples

**EyeCatcher:**
- `scroll_stopping_science` — neuroscience of attention
- `hook_testing` — empirical approach to content hooks
- `visual_hierarchy` — how layout affects engagement
- `tweet_optimization` — fine-tuning posts for maximum impact

**Weekly rhythm per account (7 posts/week):**

| Day | Type | CTA? |
|---|---|---|
| Mon | Value drop (educational) | No |
| Tue | Hot take / contrarian | No |
| Wed | Soft tool mention | Subtle |
| Thu | Question / engagement bait | No |
| Fri | Specific data point / stat | No |
| Sat | Thread starter | No |
| Sun | Tool mention + direct CTA | Yes |

This gives a 6:1 value-to-promotion ratio, which is optimal for trust building
without appearing salesy.

---

## New Topic Categories to Add

If these aren't already in account configs, consider adding:

**niche_launch_1:**
- `headline_scoring` — data-driven headline optimization
- `api_tools_for_writers` — tools that improve writing workflow
- `before_after_headlines` — transformation examples

**EyeCatcher:**
- `scroll_stopping_science` — neuroscience of attention
- `hook_testing` — empirical approach to content hooks
- `visual_hierarchy` — how layout affects engagement
