# Why We Replaced LLMs with If-Statements (And Why That Was the Right Call)

*For Hacker News. Submission title: "Show HN: ContentForge – deterministic content scoring instead of LLM black boxes"*
*Target: submit Tuesday–Thursday any week after CWS approval lands (first comment links to demo + GitHub Discussion)*

---

Six months ago I had a perfectly reasonable idea: use an LLM to score a headline before posting it. Give it a draft, get a quality score back, use that score to decide whether to post or keep editing.

It did not work. Not because the model was wrong. It failed because of this:

```bash
$ curl -s -X POST .../score \
  -d '{"text": "I shipped in 48h. Here is what broke first 🧵"}' \
  | jq .score
74

$ curl -s -X POST .../score \
  -d '{"text": "I shipped in 48h. Here is what broke first 🧵"}' \
  | jq .score
61
```

Same text. Same prompt. Same model. Different numbers.

For a creative opinion, variance is fine. For a publish/hold gate — whether that is a solo creator deciding whether a headline is ready, or an automated pipeline deciding whether to ship — it is a dealbreaker. You cannot build a reliable loop on a coin flip.

---

## The Diagnostic Problem

When an LLM scores content, two things are simultaneously true:

1. It captures real signals. It knows that a tweet with a strong hook and a specific number outperforms a vague opener.

2. It cannot tell you which signals fired. You get a number, sometimes a brief explanation. But the explanation is also generated. There is no traceable rule that produced each deduction.

For individual use ("is this headline good?"), that is often fine. For editing loops — where you need to know *what to fix*, not just that something is wrong — it is not.

The feedback "this could be punchier" tells you nothing actionable. "Missing hook in first 10 words (-12 pts), 4 hashtags when 1–2 is optimal (-15 pts)" tells you exactly where to edit.

---

## The If-Statement Hypothesis

Content quality on a given platform is largely determined by a small number of discrete, measurable signals. Twitter/X rewards:

- Hook in the first 10 words
- Specific number or stat
- 1–2 hashtags (not 0, not 5)
- 71–240 characters
- Question or strong CTA

LinkedIn penalizes:
- More than 5 hashtags
- Wall-of-text paragraphs with no line breaks
- External URLs (other than LinkedIn's own domain)
- Zero professional CTA

These are not opinions. They are documented in platform engineering posts, creator research, and what every serious content practitioner already does by instinct.

The hypothesis: **you can encode most of the predictive signal in deterministic rules, and the residual that LLMs capture better is smaller than you would expect.**

---

## What We Built

ContentForge is a Python heuristic engine. For each platform, a scoring function takes text as input and applies a weighted rule set. Same input, same output, every time:

```python
def score_tweet(text: str) -> dict:
    score = 40  # base

    # Length signal
    char_count = len(text)
    if 71 <= char_count <= 100:
        score += 20          # sweet spot
    elif 50 <= char_count <= 240:
        score += 10          # valid engagement range
    elif char_count <= 30:
        score -= 15          # too short to carry context
    elif char_count > 240:
        score -= 8

    # Hook signal: question in first 15 words
    first_words = " ".join(text.split()[:15])
    if "?" in first_words:
        score += 12

    # Hashtag density — require letter after # so ordinals (#1, #2) don't flag
    hashtags = re.findall(r'#[a-zA-Z]\w*', text)
    if len(hashtags) == 1:
        score += 8           # sweet spot
    elif len(hashtags) == 2:
        score += 5
    elif len(hashtags) > 3:
        score -= 5 * (len(hashtags) - 3)  # penalise stuffing

    # ... 12 more signals

    score = max(0, min(100, score))
    gate = _quality_gate(score)  # PASSED >= 70 / REVIEW 50-69 / FAILED < 50
    return {"score": score, "grade": ..., "quality_gate": ..., "suggestions": [...]}
```

The response includes the specific deductions, not just the score. If a post scores 58, you know it is in REVIEW because it is missing a CTA (-8), has 4 hashtags when 1–2 is optimal (-10), and the opening line has no hook signal. That is an audit trail.

The same endpoint called with the same input ten times returns the same result ten times. There is nothing to sample, nothing to temperature-adjust, nothing to hallucinate.

---

## What We Use LLMs For

We did not remove LLMs from the system. We moved them to where they are irreplaceable.

The heuristic engine scores content. It cannot write content. It cannot take "I want to post about my API launch" and generate a high-scoring tweet. It cannot rewrite a failing draft into something that passes.

So the system uses a two-tier architecture:

**Tier 1: Deterministic scoring.** Pure Python, no API calls, under 50ms, zero variance. All 12 platform scorers live here.

**Tier 2: Generative creation.** Ollama locally or Gemini for rewrites, hook generation, content calendars. When you call `/v1/auto_improve`, it:
1. Scores your draft with the heuristic engine
2. If it fails the quality gate, calls the LLM with the scorer's own suggestions as explicit context ("this post lost points for missing CTA and 4 hashtags — fix them")
3. Re-scores the rewrite
4. Iterates until PASSED or max iterations

The LLM writes. The heuristic judges. The LLM never judges, because it cannot do that deterministically.

---

## The Numbers

On the scoring path:
- Median response time: ~12ms on warm instance
- Variance on repeated calls: 0% (deterministic)
- Cost per scoring call: $0, no tokens
- Explainability: full itemized deductions in every response

On a typical LLM scoring approach:
- Median response time: 1.2 to 4 seconds
- Variance on same input: 15 to 30% score delta
- Cost per call: $0.001 to $0.01
- Explainability: generated text, not traced rules

For a pipeline running 1,000 content pieces per day the math is obvious. But even at 10 posts per day, the variance problem makes LLM-only scoring unusable as a gate.

---

## The Chrome Extension

We shipped a Chrome extension last week. It injects a floating score badge into the compose window on Twitter/X, LinkedIn, Instagram, Threads, and Facebook. You get a live score as you type — same deterministic scorer, no API calls from the extension, badge updates on every keystroke.

The use case is simpler than I expected: it is not primarily for pipelines. It is for the moment when you have written a headline and are not sure if it is ready to post. The badge is a second opinion that never changes its mind.

---

## Being Honest About Calibration

The heuristic weights are based on documented platform best practices, not validated against a real engagement corpus.

I know the signals matter. I do not have precise coefficients verified against 10,000 data points yet. That is what we are building now with a Blind Taste Test: creators submit 10 historical posts (5 winners, 5 flops) without labeling them. We rank by score, they verify the ranking, we track accuracy.

The engine currently hits around 70–80% correct ranking in informal testing. The target before any serious B2B pitch is 80%+ validated across three or more platforms.

If you have 10 historical posts with engagement data and want to stress-test the weights: https://github.com/CaptainFredric/ContentForge/discussions/4

---

## When Heuristics Lose

Worth being direct about the failure modes:

**Platform algorithm changes.** If Twitter/X changes what it rewards next month, our weights are wrong until we update them. An LLM trained on recent data adapts implicitly.

**Niche communities.** A tweet that scores 45 might be perfect for a specialized academic or crypto audience where normal engagement signals are inverted.

**Novel formats.** The engine does not understand formats it has not been explicitly programmed for.

**Nuance.** A tweet can have perfect structural signals and still be badly written. The heuristic will not catch that. The LLM might.

Our position is not "heuristics are better than LLMs universally." It is "for a publish/hold quality gate, deterministic and auditable beats smart and stochastic."

---

## The Broader Principle

There is a class of problems where the question is "does this input meet a defined standard?" rather than "what is the best possible output I can generate?" For that class:

- Code linters do not use GPT-4 to decide if a variable is named correctly.
- Form validators do not use Claude to check if an email address has an `@`.
- Schema validators do not use LLMs to check if a JSON field is the right type.

Content quality gates belong in the same class. The standard is defined by platform best practices. The inputs are text. The output is pass/fail with a traceable reason. That is a solved problem with a 50-year-old tool: if-statements.

The heuristic is the ruler. It does not need to understand why 12 inches is 12 inches. It just needs to be correctly calibrated.

---

**Demo (score any headline instantly):** https://nullmark.tech/r/contentforge
**Chrome extension:** https://chromewebstore.google.com/detail/contentforge-score-before/jjbhcmnmjhhepiinipaamjnfogalnibb
**GitHub (AGPL-3.0):** https://github.com/CaptainFredric/ContentForge
**Blind Taste Test (weights calibration):** https://github.com/CaptainFredric/ContentForge/discussions/4

---

*First comment to post after submission:*
> Demo link: https://nullmark.tech/r/contentforge — paste any headline or tweet draft, see the score and exactly which rules fired. The `quality_gate` field is the binary gate: PASSED / REVIEW / FAILED.
> 
> Blind Taste Test details in GitHub Discussion if you want to stress-test the weights against your own historical data.
