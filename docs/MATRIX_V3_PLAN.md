# ContentForge Matrix V3 Plan

## Goal
Turn ContentForge from a useful scoring API into a sellable "content performance system" with measurable outcomes.

## Revenue Thesis
1. Better drafts before publishing increase click-through rate (CTR).
2. Higher CTR increases traffic and downstream conversions.
3. Teams pay for predictable uplift, not for "AI magic".

## Concrete 30-Day Execution Plan

### Week 1: Quality Gate Everywhere
- Require score checks before posting for all supported platforms.
- Operational rule: publish only B+ drafts.
- Store score history per post and platform.
- KPI: % of drafts filtered out before publishing.

### Week 2: Rewrite Optimization
- Use `/v1/compose_assist` to generate and rank variants.
- Recommend top variant or keep original when rewrites underperform.
- Add extension flow: Suggest Rewrite -> Auto Insert in composer.
- KPI: average score delta from original to selected final draft.

### Week 3: Distribution Discipline
- Use `/v1/ab_test` for 2-5 variants before each major post.
- Cross-score with `/v1/score_multi` to avoid single-platform bias.
- KPI: winner margin (score spread) and tie rate.

### Week 4: Sales Packaging
- Convert outcomes into sellable proof:
  - before/after score examples
  - CTR lift estimate from matrix calculator
  - operational process documented
- Build one-page case study with real numbers from your own channels.
- KPI: number of qualified demos and conversion to paid plans.

### Week 5: Proof Intelligence
- Use `/v1/proof_timeline` to show trend movement by day, not just static totals.
- Use `/v1/export_proof_report` to produce JSON/CSV exports for client recaps and investor updates.
- Build a repeatable monthly review ritual: top wins, weak channels, next-week experiments.
- KPI: proof-report delivery consistency and measurable week-over-week signal growth.

## Product Packaging for Sell-Out Ability

### Offer A: Creator Starter (low friction)
- Promise: "Never post weak drafts again."
- Includes: extension + score/compare + matrix calculator.
- Primary buyer: solo creator and indie founder.

### Offer B: Team Workflow (agency/internal team)
- Promise: "Standardized quality before publish."
- Includes: compose_assist + ab_test + score audit process.
- Primary buyer: agency, social team, growth marketer.

### Offer C: API Automation (developers)
- Promise: "Scored content pipeline in your stack."
- Includes: API integration playbook and production checklist.
- Primary buyer: developer teams with existing tooling.

## Risk Controls (Non-Idealized)
- Cold starts: extension uses status ping + retries + offline fallback.
- API downtime: local fallback scoring and rewrite estimate in extension.
- Rewrite regressions: compose_assist compares winner vs original and can keep original.
- Quota/rate limits: surface clear 429 behavior and retry-after semantics.

## Sales Narrative Template
- Problem: "Most teams post unscored copy and only learn after performance drops."
- Mechanism: "ContentForge scores before publish, rewrites weak drafts, and ranks options."
- Evidence: "Show score delta and estimated monthly revenue lift from your own data."
- Offer: "Start on free tier, then upgrade for team volume and automation."

## Next Engineering Iteration
1. Add weekly summary email with top gains, dropped opportunities, and auto-generated action list.
2. Add per-platform win-rate and confidence interval metrics for A/B outcomes.
3. Add anomaly alerts when score quality rises but revenue signal drops.
4. Add one-click PDF case study export for outreach decks.

## Implemented In Current Sprint
- Proof tracking endpoints: `/v1/record_score_delta`, `/v1/record_publish_outcome`, `/v1/record_revenue`, `/v1/dashboard_stats`.
- Proof intelligence endpoints: `/v1/proof_timeline`, `/v1/export_proof_report`.
- Proof optimization endpoints: `/v1/proof_recommendations`, `/v1/cohort_benchmarks`.
- Extension reliability and workflow: improved insertion stability, persistent rewrite history, and one-click proof outcome logging in popup.
