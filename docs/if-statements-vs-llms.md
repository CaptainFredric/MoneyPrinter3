# Why We Replaced LLMs with If-Statements (And Why That Was the Right Call)

*For Hacker News. Submission format: "Show HN: ContentForge, content quality gate using deterministic heuristics instead of LLMs"*

---

Six months ago I had a perfectly reasonable idea: use an LLM to score social media content before posting. Give it a tweet, get a quality score back, use that score as a publish/hold gate in my automation pipeline.

It did not work. Not because the LLM was dumb. It was perceptive about what makes content good. It failed because of this:

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

For a subjective creative opinion, variance is fine. For a binary publish/hold gate in an automated pipeline it is a dealbreaker. You cannot build a reliable workflow on a coin flip.

---

## The Diagnostic Problem

When an LLM scores content, it does something like retrieval and synthesis over its training distribution. Two things are simultaneously true:

1. It captures real signals. It has been trained on enough human feedback to know that a tweet with a strong hook and a specific number outperforms a vague statement.

2. It cannot tell you which signals fired. You get a number. Sometimes you get a brief explanation. But the explanation is also generated. There is no traceable rule that produced the deduction.

For individual use ("is this tweet good?"), that is acceptable. For a pipeline that needs to audit why content passed or failed a quality check, for a client report, for a compliance review, for an ML training label, it is not.

---

## The If-Statement Hypothesis

Content quality on a given platform is largely determined by a small number of discrete, measurable signals. Twitter/X rewards:

- Hook in the first 10 words
- Specific number or stat
- 1-2 hashtags (not 0, not 5)
- 71-120 characters (not 40, not 280)
- Question or strong CTA

LinkedIn penalizes:
- More than 5 hashtags
- Wall-of-text paragraphs with no line breaks
- Zero professional CTA

These are not opinions. They are documented in platform engineering posts, in creator economy research, and in what every serious content practitioner already does by instinct.

The hypothesis: **you can encode most of the predictive signal in deterministic rules, and the residual that LLMs capture better is smaller than you would expect.**

---

## What We Built

ContentForge is a Python heuristic engine. For each platform, a scoring function takes text as input and applies a weighted rule set. Same input, same output, every time:

```python
def score_tweet(text: str) -> dict:
    score = 40  # base

    # Length signal
    char_count = len(text)
    if 71 <= char_count <= 120:
        score += 15          # optimal range
    elif 121 <= char_count <= 200:
        score += 8
    elif char_count > 200:
        score -= 5           # too long for engagement

    # Hook signal: question in first 15 words
    first_words = " ".join(text.split()[:15])
    if "?" in first_words:
        score += 12

    # Hashtag density
    hashtags = re.findall(r'#\w+', text)
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

The response includes not just the score but the specific deductions. If a post scores 58, you know it is in REVIEW because it is missing a CTA (-8), has 4 hashtags when 1-2 is optimal (-10), and the opening line has no hook signal. That is an audit trail.

The same endpoint called with the same input ten times returns the same result ten times. There is nothing to sample, nothing to temperature-adjust, nothing to hallucinate.

---

## What LLMs Are Actually For

We did not remove LLMs from the system. We moved them to where they are irreplaceable.

The heuristic engine scores content. It cannot write content. It cannot take "I want to post about my API launch" and generate a high-scoring tweet. It cannot rewrite a failing draft into something that passes.

So ContentForge uses a two-tier architecture:

**Tier 1: Deterministic scoring.** Pure Python, no API calls, under 50ms, zero variance. All 12 platform scorers live here.

**Tier 2: Generative creation.** Ollama locally or Gemini for rewrites, hook generation, content calendars. When you call `/v1/auto_improve`, it:
1. Scores your draft with the heuristic engine
2. If it fails the quality gate, calls the LLM with the scorer's own suggestions as explicit context ("this post lost points for missing CTA and 4 hashtags, fix them")
3. Re-scores the rewrite
4. Iterates until PASSED or max iterations

The LLM writes. The heuristic judges. The LLM never judges, because it cannot do that deterministically.

---

## The Performance Numbers

On the scoring path:
- Median response time: 12ms on warm instance
- Variance on repeated calls: 0% (deterministic)
- Cost per scoring call: $0, no tokens
- Explainability: full itemized deductions

On a typical LLM scoring approach:
- Median response time: 1.2 to 4 seconds
- Variance on same input: 15 to 30% score delta
- Cost per call: $0.001 to $0.01 depending on model
- Explainability: generated text, not traced rules

For a pipeline running 1,000 content pieces per day, the math is obvious. But even at 10 posts per day, the variance problem makes the LLM-only approach unusable as a gate.

---

## Being Honest About Calibration

Here is the part I want to be upfront about: the heuristic weights are based on documented platform best practices, not validated against a real engagement corpus.

I know the signals matter. I do not have precise coefficients verified against 10,000 data points yet. That is what we are building now. A Blind Taste Test where creators submit 10 historical posts (5 winners, 5 flops) without labeling them. We rank by score, they verify the ranking, we track accuracy.

The engine currently hits around 70-80% correct ranking in informal testing. The target before any serious B2B pitch is 80%+ validated across 3 or more platforms.

If you have 10 historical posts with engagement data and want to stress-test the weights: https://github.com/CaptainFredric/ContentForge/discussions/4

---

## When Heuristics Lose

Worth being direct about the failure modes:

**Platform algorithm changes.** If Twitter/X changes what it rewards next month, our weights are wrong until we update them. An LLM trained on recent data adapts implicitly.

**Niche communities.** A tweet that scores 45 in our engine might be perfect for a specialized crypto or academic audience where the normal engagement signals are inverted.

**Novel formats.** The engine does not understand new content formats it has not been explicitly programmed for.

**Nuance.** A tweet can have perfect structural signals (right length, hook, hashtag count) and still be badly written. The heuristic will not catch that. The LLM might.

These are real. Our position is not "heuristics are better than LLMs universally." It is "for a publish/hold quality gate in an automation pipeline, deterministic and auditable beats smart and stochastic."

---

## The Broader Principle

There is a class of problems where the question is "does this input meet a defined standard?" and not "what is the best possible output I can generate?" For that class:

- Code linters do not use GPT-4 to decide if a variable is named correctly.
- Form validators do not use Claude to check if an email address has an `@`.
- Schema validators do not use LLMs to check if a JSON field is the right type.

Content quality gates belong in the same class. The standard is defined by platform best practices. The inputs are text. The output is pass/fail with a traceable reason. That is a solved problem with a 50-year-old tool: if-statements.

The heuristic is the ruler. It does not need to understand why 12 inches is 12 inches. It just needs to be correctly calibrated.

---

**GitHub (AGPL-3.0):** https://github.com/CaptainFredric/ContentForge
**API and demo:** https://nullmark.tech/r/contentforge
**Free tier:** https://rapidapi.com/captainarmoreddude/api/contentforge1

---

*Target: Submit to HN Wednesday or Thursday this week, after r/SideProject and r/selfhosted posts land and produce organic links to the repo.*

*Include a brief first comment linking directly to the demo and the GitHub Discussion.*
