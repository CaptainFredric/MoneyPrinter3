# ContentForge Reddit Launch Notes

Updated: 2026-04-09

These notes are not calibration proof. They are early market signal from public launch posts and comment threads.

## Why keep this file

The product story changed once real people saw it:

- determinism landed quickly
- broad feature lists landed poorly
- public calibration got the strongest trust response
- the headline workflow was easier to understand than the full API matrix

That should affect how ContentForge is presented everywhere else.

## Snapshot

### 1. r/webdev: Blind Taste Test announcement

Source:
- [post](https://www.reddit.com/r/webdev/comments/1scs839/blind_taste_test_announcement/)
- [JSON snapshot](https://www.reddit.com/r/webdev/comments/1scs839/blind_taste_test_announcement/.json)

Observed metrics:
- score: 5 in Reddit JSON
- comments: 6 in Reddit JSON
- screenshot capture showed roughly 3.8K views at the time of export

What seemed to work:
- explicit admission that weighting is not fully validated yet
- concrete ask: submit 10 historical posts
- win condition was obvious for both sides
- a commenter explicitly said using real engagement outcomes "makes way more sense" than throwing random posts at a model

Product implication:
- lead with calibration and real outcome testing when asking for trust

### 2. r/SideProject: deterministic scoring API feature pitch

Source:
- [post](https://www.reddit.com/r/SideProject/comments/1se5n71/i_built_a_deterministic_content_scoring_api_same/)
- [JSON snapshot](https://www.reddit.com/r/SideProject/comments/1se5n71/i_built_a_deterministic_content_scoring_api_same/.json)

Observed metrics:
- score: 2 in Reddit JSON
- comments: 1 in Reddit JSON
- screenshot capture showed 226 views at the time of export

What seemed weaker:
- too many capabilities in the first impression
- the product read as a wide API surface before it read as one useful tool
- the calibration challenge was present, but buried underneath the platform and endpoint list

Product implication:
- the first impression should be "headline doctor" or "before-publish quality gate"
- the full endpoint list should support the pitch, not be the pitch

### 3. r/webdev: Showoff Saturday technical explainer

Source:
- [post](https://www.reddit.com/r/webdev/comments/1scepuw/showoff_saturday_i_built_a_deterministic_content/)
- [JSON snapshot](https://www.reddit.com/r/webdev/comments/1scepuw/showoff_saturday_i_built_a_deterministic_content/.json)

Observed metrics:
- score: 0 in Reddit JSON
- upvote ratio: 0.14 in Reddit JSON

What seemed to happen:
- technical rationale alone was not enough
- explainability and speed are interesting, but they need an immediate user-facing payoff
- your own hindsight inside the post was probably right: the extension is what people can picture using every day

Product implication:
- show the extension and before or after comparison fast
- keep the technical architecture below the fold

## Current messaging rule

For cold traffic, use this order:

1. headline doctor
2. compare two drafts
3. public calibration log
4. extension for daily use
5. API depth for people who want automation

If the page starts with all 50 endpoints, it is leading with the wrong layer.

## What changed because of this

- the landing page now starts with headline scoring and proof
- the compare flow is treated as a primary workflow
- calibration is framed as a public log, not a hidden caveat
- the README now describes ContentForge as a deterministic headline scorer and quality gate first
