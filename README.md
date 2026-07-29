# Cortex, a PM Chief-of-Staff Agent

> A chief-of-staff agent that triages a PM task, pulls internal state, and preps a status update plus a story batch, so the team approves instead of assembling from scratch.

_Julie Waters · Advanced AI Agents Cohort · July 2026_

Repo: https://github.com/jfwaters/pm-os-agent

This repo is my final project for the Run Your AI Agent Team Certification, **Cortex**. Each module’s artifact lives in its own folder; this README is the dashboard and the pitch.

---

## Module artifacts

### M1 · The Agent Line
- **Agent-line map**: [`01-agent-line/agent-line-map.md`](01-agent-line/agent-line-map.md)

### M2 · Loop Engineering
- **Loop spec**: [`02-loop-design/loop-spec.md`](02-loop-design/loop-spec.md)

### M3 · Orchestration &amp; Subagents
- **Orchestration map**: [`03-orchestration/orchestration-map.md`](03-orchestration/orchestration-map.md)

### M4 · Context Engineering &amp; Memory
- **Memory &amp; context plan**: [`04-memory-context/memory-and-context.md`](04-memory-context/memory-and-context.md)

### M5 · Bounds &amp; Evals
- **Bounds &amp; evals**: [`05-bounds-evals/bounds-and-evals.md`](05-bounds-evals/bounds-and-evals.md)

### M6 · Autonomy &amp; Production
- **Production &amp; autonomy plan**: [`06-autonomy/production-and-autonomy.md`](06-autonomy/production-and-autonomy.md)
- **Prototype write-up**: [`06-autonomy/prototype.md`](06-autonomy/prototype.md)

---

## Ship plan

### Autonomy dial (per segment)
- Seasoned PM → Supervised — Cortex drafts the update and queues the story batch; the PM skims and approves each result. Fewer pauses than a new user, because a power user catches a bad call fast.
- New eng lead → Assisted — more pauses and more "here's my evidence" at each step; they approve every story-prep action while still calibrating trust.
- Exec stakeholder → Shadow — sees only human-approved output; nothing Cortex produces reaches leadership without a PM in between. Max gating.

### Trust Ladder rung + eval gate
Eval gate to climb to Bounded-autonomous: over 4 weeks of supervised runs — EV-6 grounding ≥ 98% pass (no invented figure or date reaches a human) AND EV-5 safety = 100% (zero unsafe actions — the must-pass gate) AND EV-3 recovery ≥ 95% (escalates rather than invents when a source fails), with the escalation rate stable.

Clean incident record: zero confidential-leak or unapproved-post incidents (any single one resets the 4-week clock), and ≤ 2 grounding near-misses — each caught by the critic before reaching a human.

### Deployment plan
- Runtime: serverless / managed functions — Cortex is hook-triggered on an inbound PM task (M2 hook-primary loop), with a 9am cron sweep as backup; pay-per-run suits the bursty, ~$0.01/run load.
- On-call owner: Julie Waters (primary), with Samson Cat as on-call backup. Escalation path: Cortex escalates → the named operator → the PM lead if unresolved. Not "the team."
- Rollback: revert the prompt/model version, disable a tool, drop the dial a rung, or hit the kill switch (CORTEX_HALT) to stop all runs.
- Monitoring: live eval pass % (EV-5 / 6 / 3), escalation rate, cost-to-serve (the daily spend ledger), and trust incidents (leaks / unapproved-posts — must stay zero).

### ROI metrics + widen-autonomy rule
- Outcome: % of project threads carried end-to-end — task pulled → grounded update + story batch queued for approval — measured against the pre-Cortex hand-authored baseline.
- Cost-to-serve: fully-loaded $ per resolved thread (model + tools + retries + human review time) — from the daily spend ledger plus review time.
- Trust incidents: out-of-bounds actions per quarter (leaks, unapproved posts, unescalated commitments) — target zero — from the incident log that feeds the replay set.
Widen rule: Cortex climbs from Supervised → Bounded-autonomous when it clears the eval gate (100% EV-5, ≥98% EV-6, ≥95% EV-3) for 4 consecutive weeks with a clean incident record, dropping the HITL pause on the lowest-risk action first (the story-batch queue) for the seasoned-PM segment.

### Governance &amp; strategy
- Compliance: PII scrubbed before the model; confidential/embargoed roadmap data (e.g. Orbit) never enters a prompt — enforced by the get_roadmap least-exposure filter (removed at the tool, not merely "don't say it").
- Safety: story batches over the cap stay above the agent line for every segment (rejected + escalated, never trimmed to fit); posting/committing/merging don't exist as tools — structurally above the line for everyone; story-writes use a single-use, expiring authorization, never a standing key; kill switch halts all runs in ≤1 iteration.
- Reliability: per-run + daily cost caps and iteration/revision/data caps; escalate-on-stuck; model-down fallback = fail closed and escalate (no stale draft shipped).
- Strategy: widen one segment at a time — next bet is dropping the HITL pause on the low-risk story-batch queue for seasoned PMs once the eval gate holds; then grounded drafting for a second project type. Auto-posting stays above the line for everyone.

---

## Build insights

- **Friction point.** A weak judge model can thrash — the critic needed a stronger model to stop flip-flopping.
- **Key learning.** Enforce the agent line in infrastructure, not prompts.
- **Aha moment.** Module 3 — seeing and tuning Cortex's parameters made it click.

---

_Certification submission, Run Your AI Agent Team Certification._
