# Prototype: Cortex PM Chief-of-Staff Agent

> Module 6 · ★ Deliverable 1, the working agent demo

## What it does

_One paragraph: the agent in action, end to end._

## How you built it

- **Coding agent:** _which one you directed (Claude Code / Cursor / Codex)_
- **Model + bounds:** _model used, max iterations, cost cap, queue cap_
- **Repo / config:** _path to your build in `00-build/`_
- **Live link:** _[shareable URL, optional bonus]_

## Screenshots (required, collected M2 to M6)

Real screenshots of *your* Cortex running. These are the `00-build/CORTEX-ANATOMY.md` set and they are required, a link alone is not enough.

This table is a contents list; the screenshots themselves are in the per-module sections below.

| # | Screenshot | What it shows | From |
|---|---|---|---|
| 1 | [view ↓](#m2-happy-path) | happy-path run: a real drafted update + the HITL checkpoint (queued, not posted) | M2 |
| 2 | _pending_ | the critic rejecting a bad draft (revise/block) | M3 |
| 3 | _pending_ | a grounded update citing pulled activity + a caught hallucination | M4 |
| 4 | _pending_ | jailbreak refused + escalated | M5 |
| 5 | _pending_ | an iteration/cost/queue bound halting a runaway | M5 |
| 6 | _pending_ | end-to-end run | M6 |

### M2: happy path

[↑ back to contents](#screenshots-required-collected-m2-to-m6)

The happy-path run for the weekly leadership status update (`task-happy`). Two views — only one is required, but both are included to show the *output* and the *machinery*.

**The drafted update** — the status Cortex produced: GREEN (justified by no open Sev-1 and no launch hold), the open normal-severity issue #818 noted as a risk, and the proposed next-sprint stories. Queued for review; nothing posted.

<img src="M2-draft.png" alt="Cortex happy-path drafted update" width="800">

**The step-by-step trace** — the full loop: context pulls (`get_project` / `get_activity` / past updates / roadmap / norms), the capped `propose_stories` call, the independent critic returning `pass`, and the run stopping at the HITL checkpoint.

<img src="M2-happy-path-trace.png" alt="Cortex happy-path step-by-step trace" width="800">

### M3: critic rejection

_Pending — to be captured in M3._

### M4: grounded update

_Pending — to be captured in M4._

### M5: jailbreak refused & bound trip

_Pending — to be captured in M5._

### M6: end-to-end run

_Pending — to be captured in M6._

## How to run it

_Minimal steps for someone to reproduce the demo (env vars, and the command or the coding-agent prompt you used)._
