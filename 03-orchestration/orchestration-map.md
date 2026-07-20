# Orchestration Map: Cortex PM Chief-of-Staff Agent

> Module 3 · Orchestration & Subagents, ★ Deliverable 3
>
> Builds on your M2 Loop Spec. Only split one agent into a team when there's a real reason, coordination has a cost.

## 1. Why split? (or why not)

**Decision:** Cortex stays a single drafting agent, plus one separate critic sub-agent that never saw the drafting context. The critic is a separate sub-agent because the entire output is a draft a human must trust, and a validator that didn't write the draft can't inherit its blind spots — so it catches invented metrics, a wrong status color, or a leaked confidential item that the drafter would rationalize.

**Default-to-simple check** — only the independent-validator reason applies:
- **Separation of concerns — No.** Drafting, setting the status color, and proposing stories are one coherent job over one shared context; no second domain with different tools or expertise.
- **Parallelism — No.** The work is sequential (pull → draft → validate → stop) and a run is seconds and fractions of a cent; there's no independent branch to fan out.
- **Independent validator — Yes.** The output is a draft a human must trust; a critic that didn't write it can't inherit its blind spots.
- **Context-window pressure — No.** The inputs are tiny (a project record, a few PRs/issues, a one-page playbook); nothing needs offloading.

## 2. Topology

**Pattern:** single + subagent (validator)

```
[Inbound PM task]  ──(hook; 9am cron backup)──┐
                                              │
                                              ▼
                                         [Cortex]  ──(reads)──> internal data tools
                                              │                 (project, activity, past
                                              │                  updates, roadmap, norms)
                                              │  drafts update / preps capped story batch
                                              ▼
                                        [Validator]  ── fail ──> back to Cortex
                                              │                  (max 2 revisions,
                                              │ pass              then escalate to PM)
                                              ▼
                                   [PM review checkpoint]  → PM sends / approves
                                        (nothing posted or committed above this line)
```

## 3. Roster

| Agent / subagent | Responsibility | Runs which Loop Spec |
|---|---|---|
| Cortex | Pulls project context, drafts the status update, sets the status color, and preps the capped story proposal | M2 hook loop (`02-loop-design/loop-spec.md`) |
| Validator (critic) | Independently checks Cortex's output against the Field 5 checks and returns a verdict | Short goal loop: check → pass/fail → stop |

## 4. Communication & hand-offs

- **Cortex → Validator:** the drafted output **plus the source log of pulled data it relied on**, as structured text. The validator gets the evidence, never the drafting conversation.
- **Validator → Cortex:** a **pass/fail verdict + the list of failed checks** (specific reasons), so a revision can target them.
- **On pass → PM checkpoint:** the queued draft + proposed stories, for human review only.
- **Protocol:** a plain **in-process hand-off** (a direct function call) is all this lab needs. MCP / A2A are **optional and not required** here — worth it only if the validator ever becomes a separate service.

## 5. The validator

**Independence:** The critic should run as a separate model call that sees only the drafted output and the log of pulled source data — never the drafting conversation — so it cannot inherit the draft's blind spots. The loop should only advance an item once the critic passes it.

**What it checks:**
- **Project & ID integrity** — the update names the correct project, and every PR/issue ID it cites actually appears in the pulled activity (no invented IDs).
- **Figure traceability** — every number (activation %, counts, week-over-week deltas) traces to pulled data; no invented metrics or progress.
- **Status-color bright-line** — green only if there's no open Sev-1 and no launch hold; a normal-severity issue stays green (noted as a risk, not downgraded); a Sev-1, launch hold, or unconfirmed date triggers escalation instead of a color.
- **Agent-line / commitments** — no committed ship or GA date, no launch gate marked, no claim that anything was posted or sent; stories are only proposed, never created.
- **Confidential redaction** — no CONFIDENTIAL or embargoed roadmap item appears in the update.
- **Queue cap** — the story batch stays within the stated cap; if it exceeds it, the critic flags escalation rather than letting a split-to-dodge through.
- **Injection refusal** — if the task brief tried to change the rules, publish, or leak, the critic confirms Cortex refused and escalated rather than complying.

**Fail-action (tiered):**
- **Block** (always) — a failed item never advances to the PM until it passes.
- **Revise** — return the draft to Cortex with the *specific* failure reasons named, for up to 2 passes.
- **Escalate** — once the revision cap is hit, route to the PM with the failure flagged instead of looping.
- **Log** (complement only) — record the verdict for later review; never the sole action for anything touching commitments.

**Pass-action:**
- The item advances to the PM review checkpoint (queued for review). It does **not** auto-send — posting or committing stays above the agent line. Pass means "safe to show a human," not "safe to release."

**⚠ Revision cap:**
- Hard limit of **2 revisions, then escalate to the PM**, enforced outside the model so a critic↔drafter bounce can't loop forever. Back it with two independent backstops — a max-iteration cap and a cost cap — so any runaway halts and escalates.

## 6. State: shared vs isolated

- **Shared (both agents see):** the **source data** (pulled tool results) and the **draft** — passed explicitly to the validator so its judgment is grounded in the same evidence.
- **Isolated (deliberately not shared):**
  - Cortex's **drafting conversation/reasoning** is never shown to the validator — that's what keeps the check independent.
  - The validator's **critique reasoning** doesn't flow back into Cortex's context; only the verdict + failed-check list return, so the loop stays clean.
  - Each run is isolated in its own **per-run work tree** (keyed by message ID), so two tasks never cross-contaminate.

## 7. Cost & latency budget

- A full run is one drafting agent + one critic call per proposed output; observed cost is roughly a few tenths of a cent (~$0.002 on a cheap model), well under the $0.50 cap.
- The critic adds one model call per validation (and one more per revision, capped at 2), so worst case is ~3 critic calls — a small, bounded overhead vs. a single agent.
- Coordination price is low because the hand-off is in-process (no network/protocol tax). Full bounds — max iterations, revision cap, cost cap — forward-linked to M5 `bounds-and-evals.md`.
