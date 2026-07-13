# Agent-Line Map: Cortex

## Decisions, scored

| # | Decision | Reversibility | Blast radius | Measurability | Verdict |
|---|---|---|---|---|---|
| 1 | Pull project state + activity | High | Low | High | Below |
| 2 | Decide relevant context / norms | High | Low | Low | Above |
| 3 | Draft the update text | High | Low | Med | HITL |
| 4 | Decide status color / tone framing | High | Med | Med | HITL |
| 5 | Commit a ship date | Low | High | Med | Above |
| 6 | Assess at-risk / escalation-likely | High | Med | Low | HITL |
| 7 | Propose story batch within cap | High | Low | High | Below |

## One-line justifications

1. **Pull project state + activity** (Below): Pulling state and activity sits below the line because it's easy to reverse, has a low blast radius, and is easy to verify, so the deciding factor is that all three axes are safe.
2. **Decide relevant context / norms** (Above): Deciding relevant context sits above the line because it's easy to reverse and has a low blast radius, but is hard to verify, so the deciding factor is measurability.
3. **Draft the update text** (HITL): Drafting the update sits at a checkpoint because it's easy to reverse and has a low blast radius, but is only moderately verifiable, so the deciding factor is measurability.
4. **Decide status color / tone framing** (HITL): Setting the status color sits at a checkpoint because it's easy to reverse but has a moderate blast radius and is only moderately verifiable, so the deciding factor is blast radius.
5. **Commit a ship date** (Above): Committing a date sits above the line because it's hard to reverse and has a high blast radius, and is only moderately verifiable, so the deciding factor is blast radius.
6. **Assess at-risk / escalation-likely** (HITL): Assessing risk sits at a checkpoint because it's easy to reverse and has a moderate blast radius, but is hard to verify, so the deciding factor is measurability.
7. **Propose story batch within cap** (Below): Proposing a capped story batch sits below the line because it's easy to reverse, has a low blast radius, and is easy to verify, so the deciding factor is structural caps keeping all three axes safe.

## Hardest above-vs-below call

#4 — status color / tone framing. It's the only row with no decisive trigger (High/Med/Med), so it sits right on the HITL/Above line — and the call rests on whether your reviewers actually scrutinize it or rubber-stamp it.
