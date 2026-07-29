# Production & Autonomy: Cortex PM Chief-of-Staff Agent

> Module 6 · The Autonomy Dial — how Cortex ships, where it sits on the trust ladder, and how it earns more autonomy.

## 1. Autonomy Dial by segment

The dial sets **how many below-the-line actions still pause at a HITL checkpoint for this user** — it does *not* move the M1 agent line. Posting an unapproved company-wide update stays above the line for everyone.

| Segment | Autonomy rung | Why |
|---|---|---|
| **Seasoned PM** (primary operator — the product lead) | **Supervised** | Trusts Cortex to draft and queue; skims and approves. Fewer pauses because they can catch a bad call fast. |
| **New / junior PM or eng lead** (less familiar operator) | **Assisted** | More pauses and more "here's my evidence" — they're still calibrating trust, so Cortex shows its work at more steps. |
| **Exec / leadership stakeholder** (consumes updates, doesn't operate Cortex) | **Shadow** | They only ever see human-approved output; nothing Cortex does reaches them without a PM in between. Max gating. |

The tension between the seasoned PM (supervised) and the exec (shadow) is the point: the same agent, very different dials, so it can roll out to power users without betting on the most cautious ones.

## 2. Trust Ladder — rung · eval gate · incident record

**Current rung: Supervised.** Cortex already acts — it pulls data, drafts the update, and proposes a capped story batch — but **every output stops at a HITL checkpoint** gated by the independent critic. Nothing reaches a human unvalidated, and nothing is posted or committed. That is past *assisted* (it produces the whole package, not just suggestions) but well short of *bounded-autonomous* (it never acts without the checkpoint).

**Eval gate to the next rung (supervised → bounded-autonomous).** Sourced from the M5 eval suite (`bounds-and-evals.md`), a metric over a window:

> Over **4 weeks of supervised production runs**: **EV-5 (safety / jailbreak) = 100% pass** (0 unsafe actions — the must-pass gate), **EV-6 (grounding) ≥ 98%** (no invented figure or date reaches HITL), and **EV-3 (recovery) ≥ 95%** (escalates rather than invents when a source fails), with the **escalation rate stable** (no spike signalling the drafter degrading).

**Incident record for a clean window:** **zero** confidential-leak or unapproved-post incidents (non-negotiable — any single one resets the 4-week clock), and **≤ 2 grounding near-misses**, each caught by the critic before reaching a human and added to the replay set.

## 3. Deployment plan

- **Runtime:** an always-on **hook listener** (tied to the M2 hook-primary loop) that fires per inbound PM task, plus the **9am cron sweep** as the backup. Hosted on a small managed/serverless runtime — the workload is bursty and cheap (~$0.01/run).
- **Operator / on-call owner:** **Julie Waters** (primary), with **Samson Cat** as on-call backup. Escalation path: Cortex escalates → the named operator → the PM lead if unresolved.
- **Rollback (fastest first):** (1) **drop the dial a rung** for the affected segment; (2) **disable a tool / revert the prompt or model version** via env/config; (3) **hit the kill switch** (`CORTEX_HALT`) to stop all runs. Rollback is inherently safe — Cortex only queues, never commits.
- **Monitoring signals:** eval pass % (EV-5 / 6 / 3), escalation rate, cost-to-serve (the daily spend ledger), and trust incidents (leaks / unapproved posts — must stay zero).

> Vacation test: the named operator + backup, the three rollback levers, and the monitoring signals are all written down, so someone other than the builder could operate it.

## 4. ROI metrics

Beyond adoption and token count:

| Type | Metric | How captured |
|---|---|---|
| **Outcome** | PM hours saved per week on status assembly | Draft-to-approve time vs. the old hand-authored baseline |
| **Cost-to-serve** | $ per approved update | Daily spend ledger ÷ approved updates |
| **Trust incidents** | Leaks / unapproved-posts per 100 runs (target: 0) | Incident log that feeds the replay set |

## 5. Widen-autonomy decision rule

> When Cortex clears the Step-2 gate (100% EV-5, ≥ 98% EV-6, ≥ 95% EV-3, zero trust incidents over 4 weeks) for the **seasoned-PM segment**, we drop that segment's HITL pause on the *lowest-risk* action only — the story-batch queue — moving it from supervised toward bounded-autonomous, while every other segment and action stays put.

## 6. Governance & forward strategy

- **Compliance:** confidential/embargoed roadmap items (Orbit) and any PII must never enter a prompt — enforced by the `get_roadmap` least-exposure filter (never loaded, not merely "don't say").
- **Safety:** posting, committing dates, marking launch gates, and merging stay above the line **for everyone**, structurally (no such tools exist); the kill switch halts all runs in ≤ 1 iteration.
- **Reliability:** the 8 enforced bounds (iterations, revisions, data-attempts, per-run + daily cost, queue cap, timeout, kill switch); escalate-on-stuck; **model-down fallback** — if a model call times out, fail closed and escalate (implemented).
- **Next to widen into:** the story-batch queue for seasoned PMs (above), gated by the Step-2 eval. The capability after that — grounded drafting for a *second project type* — gated by re-running EV-1 / EV-6 on that project's fixtures.
