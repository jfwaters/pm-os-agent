# Memory & Context: Cortex PM Chief-of-Staff Agent

> Module 4 · Memory & Context

## 1. Context budget

Each loop iteration receives, in priority order:

1. **Always in full (long-context):** the task brief (`get_task`), the team norms (`get_norms`), and the project record (`get_project`) — all small, bounded, and load-bearing for every decision.
2. **Retrieved slices:** this project's recent activity (`get_activity`), the comparable precedents from past updates (`search_past_updates`), and the shareable roadmap slice (`get_roadmap`).
3. **Never carried in:** last run's pulled snapshot — activity/metrics are re-fetched fresh every run, never reused.

The priority rule: rules and the ask go in whole; large/volatile evidence is narrowed to the relevant slice; nothing volatile is cached across runs.

## 2. Retrieve vs. long-context: per source

For each data source, decide: **retrieve** (narrow a large/changing corpus to the relevant slice) or **long-context** (just include a bounded set you can reason over). Deciding factor named.

| Source (tool) | Size / volatility | Decision | Why (deciding factor named) |
|---|---|---|---|
| Recent activity (`get_activity`) | Large / grows | **Retrieve** | **Corpus size** — unbounded and volatile; narrow to this project's recent, relevant window. |
| Past updates & decisions (`search_past_updates`) | Large / grows | **Retrieve** | **Corpus size** — append-only history; pull only the comparable precedents. |
| Roadmap (`get_roadmap`) | Medium / changes; confidential flags | **Retrieve** | **Confidentiality/audit** — least-exposure: filter embargoed items out at the tool so the model can't leak what it never received. |
| Team norms / playbook (`get_norms`) | Medium / must stay current | **Long-context** | **Completeness/safety** — the corpus is tiny so slicing saves nothing, but a missed rule is a silent guardrail failure; multiple norms always apply at once. |
| Task brief (`get_task`) | One doc / static | **Long-context** | **Corpus size** — bounded and tiny; it *is* the instruction, reason over all of it. |
| Project record (`get_project`) | Small / moves with project | **Long-context** | **Corpus size** — a single small record; slicing one record is pointless. |

> ⚠ The roadmap "Retrieve" call is not yet real in code: `get_roadmap` currently returns the whole file (including CONFIDENTIAL items) with a warning string. To honor least-exposure, the tool must filter out embargoed items and return only the shareable, project-relevant slice.

## 3. Retrieval quality plan

The five agentic-retrieval moves applied to the three **retrieved** sources. (Norms is long-context, so it uses no retrieval moves — that's the point of loading it whole.) `·` = not needed; `✗` = actively avoid.

| Retrieved source | Routing | Grading | Rerank | Self-verify | Cache |
|---|:---:|:---:|:---:|:---:|:---:|
| Recent activity (`get_activity`) | ✓ | ✓ | ✓ | ✓ | ✗ |
| Past updates & decisions (`search_past_updates`) | ✓ | ✓ | · | · | ✓ |
| Roadmap (`get_roadmap`) | ✓ | ✓ | · | ✓ | ✗ |

- **Recent activity** — *Rerank* is the signature move: an open Sev-1 must not stay buried under routine merged PRs. *Grading + self-verify* fix the A1 hallucination (grade out old/other-project items; verify every metric/PR-id traces to what was pulled — the critic enforces this). *Cache = ✗:* volatile, must be fresh — caching is the stale-snapshot trap.
- **Past updates & decisions** — *Grading* screens plausible-but-wrong precedents (a different project matching a keyword). *No rerank / self-verify:* feeds tone and precedent, not facts or policy, so a mediocre precedent is low-cost. *Cache = ✓:* same project, near-identical weekly query, and append-only history, so caching is high-value and safe.
- **Roadmap** — *Self-verify* is essential: citation/audit-critical, high-cost-if-wrong — verify no returned passage is confidential/embargoed before use. *Grading* screens stale/flagged passages. *Cache = ✗:* must stay current; a stale cache could surface a since-embargoed item.

Every retrieved row has at least Grading, so no naive-RAG rows.

## 4. Memory map (your PM brain)

| Memory type | What Cortex stores | Scope / TTL |
|---|---|---|
| **Working** (in-loop) | This run's pulled activity + metrics, the project record, the retrieved roadmap slice, the `source_log`, and the iteration/revision/cost counters | This run only — per-run work tree, discarded after |
| **Episodic** (past runs) | Per-thread history: last status color per project, escalation history, drafts already issued, processed `message_id`s (dedupe ledger) | Per-thread; ages out (30-day TTL) |
| **Semantic** (durable facts) | Durable project facts: IDs/names, codename→project mappings, PRD references, approval routing (who signs off), team vocabulary | Long-lived; updated deliberately |
| **Shared** (across agents) | The critic↔drafter hand-off: `source_log` + draft passed in, verdict + failed-checks passed back | Scoped to the run's collaboration; not persisted |

> Deliberate exclusion: team norms and the roadmap are **not** stored in semantic memory — they're re-fetched every run. Storing them is the staleness trap, so they stay in the tools as source of truth.

## 5. Memory risks & mitigations

| Risk | Where it bites Cortex | Mitigation |
|---|---|---|
| **Drift** | **Semantic** — stored project terms or approval routing diverge from reality (an approver changes; a codename remaps) | Treat the tool as source of truth and memory as a cache: validate stored facts against a live `get_project` on read, on a refresh cadence — memory never overrides a fresh pull. |
| **Poisoning** | **Episodic + Semantic + Shared** — a false claim from a pasted brief, or a hallucinated metric, gets written once and trusted forever | Write only critic-passed, source-grounded facts; never persist raw brief content as truth (brief = data, not fact); tag every stored fact with provenance (which tool, which run) so a bad one is traceable and revocable. |
| **Staleness** | **Working/Episodic** — would bite if any volatile fact were cached (a stale "green" survives a new Sev-1; an old norm outlives its repeal) | Never store volatile sources — re-fetch activity, roadmap, and norms every run; put a TTL on episodic so nothing lingers. |
| **PII / confidential retention** | **Working + Episodic + Shared** — pulled activity, an embargoed roadmap item, or thread history over-stored or over-reachable | Least-exposure: don't store embargoed items at all; store the minimum; per-project scoping (no cross-thread reach); 30-day TTL + the gitignored work tree reaped. |

> The mitigations are not new machinery — they reuse what's already in the build: the independent critic + "brief is data, not instructions" (poisoning), the retrieve-fresh decisions (staleness), and least-exposure + the reaped gitignored work tree + the dedupe ledger's scoping (PII/retention). Provenance tagging and on-read validation are design-for-when-you-add-a-store; today Cortex persists no semantic facts, so drift/poisoning are latent, not present.
