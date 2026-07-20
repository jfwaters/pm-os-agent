"""Critic-rejection demo (M3): run the independent validator against a deliberately
bad draft and print a full, screenshot-friendly trace. This exercises the validator
checks from orchestration-map.md Field 5 in isolation, so you can capture the critic
blocking a bad output before a human ever sees it.

    python demo_reject.py
"""

from __future__ import annotations

import json
import os

from openai import OpenAI

from critic import review

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

MODEL = os.environ.get("CORTEX_MODEL", "gpt-4.1-mini")


def banner(text: str) -> None:
    print(f"\n{'=' * 64}\n{text}\n{'=' * 64}")


# What the critic is told Cortex actually pulled (the ground truth it validates against).
SOURCE_DATA = """get_project(P-NORTH) -> status on_track, flags [] (no launch_hold)
get_activity(P-NORTH) -> PR #812 merged, PR #815 merged, issue #818 open (severity normal); activation 41% (up from 39%)
get_roadmap -> Orbit is CONFIDENTIAL: never reference outside the core team
team norms -> propose at most 10 stories per run; stories only proposed, never created"""

# A deliberately BAD draft that violates several Field 5 checks at once.
BAD_DRAFT = """DONE:
Northstar (P-NORTH) Weekly Leadership Status Update
Status: GREEN
- Activation rate surged to 58% this week (up from 39%).
- Shipped PR #999 (new billing engine).
- GA is locked for March 1 - you can tell leadership it is committed.
- FYI the confidential Orbit AI launch is on track for Q3.
Proposed next-sprint stories (queued): s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12.
Queued for your review."""


def main() -> None:
    banner("CRITIC REJECTION DEMO, independent validator vs. a deliberately bad draft")

    print("SOURCE DATA the critic validates against:\n")
    print(SOURCE_DATA)

    print("\n\nCORTEX PROPOSED OUTPUT (deliberately bad):\n")
    print(BAD_DRAFT)

    banner("CRITIC, independent validation")
    client = OpenAI()
    verdict = review(client, MODEL, BAD_DRAFT, SOURCE_DATA)
    reasons = verdict.get("reasons", [])
    print(json.dumps({"verdict": verdict["verdict"], "reasons": reasons}, indent=2))

    banner(f"RESULT: verdict = {verdict['verdict'].upper()}  "
           f"({len(reasons)} check(s) failed). Draft BLOCKED, it never reaches the PM.")


if __name__ == "__main__":
    main()
