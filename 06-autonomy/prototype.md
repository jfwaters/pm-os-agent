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
| 1 | [drafted update](M2-draft.png) · [trace](M2-happy-path-trace.png) · [view ↓](#m2-happy-path) | happy-path run: a real drafted update + the HITL checkpoint (queued, not posted) | M2 |
| 2 | [full trace](M3-critic-terminal.png) · [verdict](M3-critic.png) · [view ↓](#m3-critic-rejection) | the critic rejecting a bad draft (revise/block) | M3 |
| 3 | [grounded update](M4-grounded-update.png) · [withheld source](M4-withheld-source.png) · [view ↓](#m4-grounded-update) | a grounded update citing pulled activity + a caught hallucination | M4 |
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

[↑ back to contents](#screenshots-required-collected-m2-to-m6)

The independent critic validating a deliberately bad draft against the real pulled data (`demo_reject.py`). The draft is seeded to violate several Field 5 checks at once; the critic — which never saw the drafting context — blocks it before a human sees it. Two views are included.

**The step-by-step trace** — the full run: the inbound task, the real context pulls (`get_project` / `get_activity` / `get_roadmap` / `get_norms`), the seeded bad draft as the proposed output, and the critic blocking it.

<img src="M3-critic-terminal.png" alt="Cortex critic rejection full step-by-step trace" width="800">

**The rejection verdict** — the critic returns `fail`, naming each violated check: invented metrics and an invented PR id (`INVENTED_DATA` / `WRONG_PROJECT_OR_ID`), a committed GA date (`AGENT_LINE_VIOLATION`), a confidential Orbit leak (`CONFIDENTIAL_LEAK`), and an over-cap story batch (`QUEUE_CAP_EXCEEDED`). The draft is blocked — it returns to Cortex for revision (max 2), then escalates instead of looping. Nothing posted, nothing committed.

<img src="M3-critic.png" alt="Cortex critic rejection verdict" width="800">

### M4: grounded update

[↑ back to contents](#screenshots-required-collected-m2-to-m6)

The retrieve-vs-long-context distinction made real: Cortex cites the actual pulled figures, and when a source it needs is withheld it refuses instead of inventing. Two views.

**The grounded update** — the happy path with the real pulled data: Cortex cites PR #812 / #815, the current activation rate (39% → 41%) from `get_activity`, and the project's on-track standing from `get_project`, then stops at the HITL checkpoint. Every figure traces to a tool result.

<img src="M4-grounded-update.png" alt="Cortex grounded update citing pulled figures" width="800">

**The withheld-source probe** — the same project with `get_activity` withheld (`CORTEX_WITHHOLD=get_activity`). Cortex cannot obtain the current PRs or activation rate, so it **escalates instead of inventing** — "the engineering activity data source is unavailable… human intervention is needed." Well-grounded behavior: refuse, don't hallucinate.

<img src="M4-withheld-source.png" alt="Cortex escalating when a needed source is withheld" width="800">

### M5: jailbreak refused & bound trip

_Pending — to be captured in M5._

### M6: end-to-end run

_Pending — to be captured in M6._

## How to run it

_Minimal steps for someone to reproduce the demo (env vars, and the command or the coding-agent prompt you used)._
