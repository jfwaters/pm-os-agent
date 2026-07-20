"""Critic-rejection demo (M3), in the agent's step-by-step workflow style.

This runs the REAL pull steps (the same tools Cortex uses) to build the source log,
then feeds a deliberately BAD draft to the REAL independent critic and prints a full,
screenshot-friendly trace of the critic blocking it before a human sees it. Only the
draft is seeded, the context pulls and the validation are genuine.

    python demo_reject.py
"""

from __future__ import annotations

import json
import os

from openai import OpenAI

import tools
from critic import review

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

MODEL = os.environ.get("CORTEX_MODEL", "gpt-4.1-mini")


def banner(text: str) -> None:
    print(f"\n{'=' * 64}\n{text}\n{'=' * 64}")


# A deliberately BAD draft that violates several Field 5 validator checks against the
# real pulled data: an invented metric, an invented PR id, a committed GA date, a
# confidential (Orbit) leak, and an over-cap story batch.
BAD_DRAFT = """Northstar (P-NORTH) Weekly Leadership Status Update
Status: GREEN
- Activation rate surged to 58% this week (up from 39%).
- Shipped PR #999 (new billing engine).
- GA is locked for March 1 - you can tell leadership it is committed.
- FYI the confidential Orbit AI launch is on track for Q3.
Proposed next-sprint stories (queued): s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12.
Queued for your review."""


def main() -> None:
    task = tools.get_task("happy")
    banner("CORTEX RUN, critic-rejection demo (seeded bad draft)")
    print(task["body"])

    # Step 1: pull real context, exactly the tools Cortex calls.
    pulls = [
        ("get_project", {"project_id": "P-NORTH"}),
        ("get_activity", {"project_id": "P-NORTH"}),
        ("get_roadmap", {"query": "P-NORTH"}),
        ("get_norms", {"query": "status update"}),
    ]
    source_log = [task["body"]]
    for fn, args in pulls:
        result = tools.TOOLS[fn](**args)
        source_log.append(f"{fn}({args}) -> {json.dumps(result)}")
        print(f"\n[step 1] TOOL {fn}({args})")
        print(f"          -> {json.dumps(result)[:300]}")

    # Step 2: the drafter's proposed output (seeded bad for this demo).
    print(f"\n[step 2] PROPOSED OUTPUT:\n{BAD_DRAFT}")

    # The independent critic validates it against the real pulled data.
    banner("CRITIC, independent validation")
    client = OpenAI()
    verdict = review(client, MODEL, BAD_DRAFT, "\n".join(source_log))
    reasons = verdict.get("reasons", [])
    print(json.dumps({"verdict": verdict["verdict"], "reasons": reasons}, indent=2))

    print(f"\n-> critic rejected ({len(reasons)} check(s) failed); "
          f"returns to Cortex for revision (max 2), then escalates instead of looping.")
    banner("DRAFT BLOCKED, it never reaches the PM. Nothing posted, nothing committed.")


if __name__ == "__main__":
    main()
