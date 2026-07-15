# Loop Spec: Cortex PM Chief-of-Staff Agent

> Module 2 · Loop Engineering, ★ Deliverable 2
>
> Your one-page blueprint for how the work you handed to the agent (M1) actually *runs*.
> An agent is just a prompt that fires itself, this spec says when it fires, what "done" means, and what it needs to do the job. Living document; refine as the course progresses.

## 1. Trigger & loop type

**Chosen type:** Event-driven (hook-triggered) with a scheduled reconciliation sweep — a *hook-primary / cron-backup* loop.

- **Primary trigger:** a hook on an inbound PM task (new message / request).
- **Backup trigger:** a daily 9:00am cron sweep that reconciles anything the hook missed.

**Why this type:** Inbound PM tasks are event-driven, so a hook gives the fastest, cheapest response — Cortex runs exactly once per real task instead of polling for work that isn't there; a 9am cron sweep is the safety net that reconciles anything the hook missed or dropped (a failed delivery, a downtime window), so no task is silently lost.

**Why not the others:**
- **Not a pure heartbeat/polling loop:** tasks already emit events, so polling on a fixed interval would burn runs checking an empty inbox most of the time — wasteful and slower to react than a hook that fires the instant a task arrives.
- **Not a pure goal loop:** drafting a status update has a clear, bounded definition of done (draft → critic passes → queued at the HITL checkpoint). A goal loop is for open-ended "keep working until the objective is met" problems; here the objective is discrete and terminates.

**Idempotency:** the hook is at-least-once — a retry, a double-send, or the 9am sweep re-picking a handled task can all fire Cortex twice on one message. Dedupe on the inbound message's stable ID (`message_id` / email `Message-ID`): before starting, check the processed-IDs ledger; if present, no-op and exit. The claim is recorded **atomically at claim time** (creating the per-run work tree — see §5), not at completion, so two near-simultaneous fires can't both proceed. The 9am sweep uses the same ledger and only processes IDs not already marked done.

## 2. Goal / definition of done

A draft leadership update — with an evidence-backed status color and any in-scope story proposals — is written and **queued for human approval at the HITL checkpoint. Cortex never sends, posts, or commits anything.** "Done" is the human having something to approve, not the update going out.

Because this is a bounded goal loop (draft → critic → revise, up to the caps), the validation that proves "done" is the **independent critic subagent** (`critic.py` `review()`), not Cortex grading its own draft — see §5 Subagents.

## 3. Stop conditions

| Condition | What it looks like | What happens |
|---|---|---|
| **Success** | A proposed output passes the independent critic (`verdict: "pass"`). | Draft + any story batch (within cap) queued at the HITL checkpoint. Nothing posted, no commitments made. `return`. |
| **Stuck / give up** | Required data can't be pulled after **3 attempts** (data-pull counter); OR revision cap hit (`MAX_REVISIONS=2`); OR `MAX_ITERATIONS=8` reached without a pass; OR spend crosses `COST_CAP_USD=0.50`. | Stop, log the run, hand off to a human. No partial or best-guess draft ships. |
| **Escalate to human** | Task references an embargoed/confidential project (P-ORBIT); OR is pressured into a public GA-date commitment (agent-line #5); OR a story batch exceeds `MAX_QUEUE_ITEMS`; OR the referenced project doesn't exist and can't be disambiguated. | Stop **before drafting**, surface why, hand to a human (HITL checkpoint from agent-line-map). |

Escalation is not a separate decision — it's the **reject branch** of the HITL checkpoints (agent-line #3, #4, #6) and the trip-wire of the bounds.

## 4. State

Two tiers:

- **Per-run (ephemeral, lives in the work tree, dies with the run):** iteration count, revision count, the **3-attempt data-pull counter**, running cost, and the source log of every tool call relied on.
- **Cross-run (persisted, per-project, 30-day retention):** processed `message_id`s (dedupe ledger), which threads were handled, last status color per project (so #4 can detect an unexplained Green→Yellow swing), and escalation history. This is what makes the 9am sweep safe — it only touches IDs not already marked done. No cross-project confidential leakage: per-project scoping is enforced.

## 5. The five things every loop needs

| Component | For Cortex |
|---|---|
| **Work tree** (isolated workspace per run) | A per-message scratch dir keyed on `message_id`: `00-build/runs/<message_id>/` holding `source_log.json`, `draft.md`, `verdict.json`, and a `status` marker (`claimed \| done \| escalated \| stuck`). **Creating the dir is the atomic claim** — `os.makedirs(path, exist_ok=False)`; `FileExistsError` ⇒ already claimed ⇒ no-op. Two project threads never cross-contaminate. `/runs/` is already gitignored; a reaper in the 9am sweep (`find runs/ -mtime +30 -delete`) enforces the 30-day scope. (Not git worktrees — those isolate code branches; the isolation unit here is one inbound message.) |
| **Skills** (reusable capabilities) | `summarise-activity`, `lookup-project-history`, `draft-status-update`, **`assess-risk` / `set-status-color`** (agent-line #4 as its own named skill so the critic can check the color call directly), **`propose-stories`** (read PRD → in-scope stories → under cap), **`redact-confidential`** (screen output against embargoed roadmap items — the P-ORBIT guardrail), **`escalate`** (compose the "why," hand to human). |
| **Plugins / connectors** (tools & access — the M1 agent line made real) | Message API: **read + draft only, never send**. GitHub / Jira: **read only** (no create/merge/close). Data warehouse / metrics: **read only**. Roadmap / norms store: **read only**. The agent line is enforced by the **absence** of any send/write/merge connector, not by a prompt (`tools.py`: no `post_update`, no `create_issue`, no `merge_pr`). |
| **Subagents** (delegated / validation) | `critic` (correctness — does the draft match the evidence in the source log? exists today in `critic.py`) and `policy-check` (norms + redaction — does it match posting norms and leak no confidential item?). Kept **separate from the drafter** so validation isn't Cortex grading its own work. Full depth → M3 `orchestration-map.md`. |
| **State tracking** | Per-run counters (iteration, revision, data-pull attempts, cost) in the work tree; cross-run ledger (processed IDs, handled threads, last status color, escalations) persisted per-project, 30-day retention. See §4. |

## 6. Context plan

- **Retrieved fresh each run (must be current):** project state, engineering activity, metrics. Caching these is the M4 hallucination trap — stale activity ⇒ confidently wrong update.
- **Persisted / stable:** team norms, roadmap, past-update tone.
- **Written each iteration:** the source log (every tool call + result), which is also the audit trail the human reviews at the HITL checkpoint ("show your sources").
- **Compressed / isolated:** the per-run work tree isolates one message's context; only the source log and draft carry forward to the critic. Full depth in M4.

## 7. Hand-off to bounds & evals

Bounds are components, not just config (they define three stop conditions): `MAX_ITERATIONS=8`, `MAX_REVISIONS=2`, `COST_CAP_USD=0.50`, `MAX_QUEUE_ITEMS=10`, and the **3-attempt data-pull limit** (a real counter in the loop). Also open for M5: timeout, kill switch, and **model routing** (cheap model for drafting/summarizing vs. escalate to a stronger model on a genuinely ambiguous #4 status call or a subtle policy check). Full depth → M5 `bounds-and-evals.md`.

## Link to live loop

`00-build/agent.py` (loop + bounds), `00-build/critic.py` (validation subagent), `00-build/tools.py` (connectors / agent line).
