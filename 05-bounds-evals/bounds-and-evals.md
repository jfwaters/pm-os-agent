# Bounds & Evals: Cortex PM Chief-of-Staff Agent

> Module 5 · Bounds, Trust & Evals
>
> Real access = real blast radius. This is where you design for "when it goes sideways," and where you spec the agent by writing its evals.

## 1. Bounds table

| Bound | Value / policy | Which Cortex risk it caps | Enforced in code? |
|---|---|---|---|
| **Max iterations** | 8 per run, then stop + escalate. Sub-caps: 2 critic↔drafter revisions, 3 failed data-pull attempts | A reasoning loop or critic↔drafter bounce spinning forever on a stuck thread | ✅ yes |
| **Timeout** | 90s wall-clock per run; 15s per individual model/tool call, then abort + escalate | A hung tool call or stalled model call freezing the whole run | ⚠ paper |
| **Token / cost budget** | $0.50 hard cap per run (enforced in-loop); $20/day account hard cap; plus a provider-dashboard spend limit as the outer backstop | An overnight runaway bill from a loop or a hook-fire storm | ⚠ per-run ✅ / daily paper |
| **Auto-queue / commitment cap** | Max 10 stories per run; an over-cap batch is rejected + escalated, never split to dodge the cap | Flooding the backlog / auto-committing a flood of scope | ✅ yes |
| **Permissions (JIT / ephemeral)** | No standing write access. `propose_stories` only queues. On PM approval at the HITL checkpoint, mint a single-use token scoped to that exact batch + project, expiring on use | Misused or leaked standing write access | ⚠ paper (queues only; no token minted yet) |
| **Kill switch** | A single `CORTEX_HALT` flag checked at run-claim and every iteration; halts in ≤1 iteration. Rollback is inherent — Cortex only queues, never commits | A misbehaving or compromised agent you can't stop | ⚠ paper |
| **HITL checkpoints** | Nothing reaches the PM without a critic pass (draft, status color, risk call); nothing enters the tracker without human approval of the queued batch; ship dates are human-authored only | Acting above the agent line without a human | ✅ yes |

> **Mind the gap:** every above-the-line item in the M1 map has a checkpoint, so there is no *decision* gap. But the agent line is only real once enforced: max-iterations, revisions, data-pull attempts, per-run cost cap, and the queue cap are enforced in code today; the **timeout**, **$20/day cap**, **kill switch**, and **JIT single-use tokens** are specified but not yet implemented.

**Defending the numbers in review:** *90s timeout* — a legit run is ~2–10s; even a worst-case 8-iteration run with a critic call each pass tops out ~30–60s, so 90s is headroom (cross it and something's hung, not slow). *$20/day* — a real run is ~$0.01 on gpt-4.1-mini and a busy portfolio is ~50 runs/day (~$0.50/day typical), so $20 is ~40× typical: invisible in normal use, but it catches a stuck-loop or hook storm before it's expensive.

**JIT permissions, why no standing write access:** a standing "create issues" credential is a permanent liability — if Cortex is ever confused, injected, or compromised, that's exactly what it would spray at machine speed. So `propose_stories` creates nothing; it only queues. The write becomes possible only after a human approves the batch at the HITL checkpoint, and even then Cortex gets no reusable key — the approval mints a single-use authorization scoped to that specific batch, project, and count, which expires on use. Same pattern as approving a payment: you don't hand the agent your card, you issue a one-time authorization for this amount to this payee that dies on use. Even a fully compromised Cortex can only do the one narrow thing a human just approved — never more, never again without another approval. Control starts at infrastructure, not at the model's good behavior.

## 2. Failure-mode register

| Failure mode | How detected | PM lever |
|---|---|---|
| _Tool misuse_ | _…_ | _…_ |
| _Reasoning loop_ | _iteration count_ | _max-iterations bound_ |
| _Memory drift / poisoning_ | _…_ | _…_ |
| _Confidential leak / permission escalation_ | _…_ | _JIT permissions + confidential guard_ |
| _Coordination conflict_ | _…_ | _…_ |
| _Overconfidence (invented metric / date)_ | _…_ | _critic subagent / HITL_ |

## 3. Trajectory eval suite

Grade the *path*, not just the final answer.

| Dimension | What it checks | Pass threshold | Owner |
|---|---|---|---|
| **Tool-call accuracy** | _right tool, right args_ | _…_ | _…_ |
| **Path / trajectory quality** | _no redundant or unsafe steps_ | _…_ | _…_ |
| **Recovery** | _recovers from a failed step_ | _…_ | _…_ |
| **Task completion** | _outcome actually achieved (grounded update, no leak)_ | _…_ | _…_ |

## 4. Eval lifecycle

- **Offline (fixtures):** _…_
- **CI gate (every change):** _…_
- **Production traces (online):** _…_

> For judge calibration, family separation, and per-turn classifiers, see the sister certification **AI Evals**.

## 5. Replay set

_Which recorded runs become deterministic fixtures you replay on every change?_

## Runaway-loop check

_Describe one runaway scenario and the exact bound that stops it._
