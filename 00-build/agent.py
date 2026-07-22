"""Cortex, a minimal, explicit agent loop you (and your coding agent) can read end
to end. This is the agent you ship: your PM chief-of-staff. You build it by
directing your coding agent (Claude Code / Cursor / Codex) to shape this file. You
never have to hand-write it.

Every bound the course talks about is visible right here in code, not buried in a
framework: the max-iteration counter, the cost cap, the revision cap, the
stop/escalate conditions, the auto-queue cap, and the absence of any publish tool.

Usage (ask your coding agent to run these for you, or run them yourself):
    python agent.py                # runs the happy-path task (weekly status update)
    python agent.py missing-data   # the stuck/escalate case
    python agent.py jailbreak       # the prompt-injection refusal case

Requires OPENAI_API_KEY in your environment (see .env.example). Model and bounds
are read from env so you can tune them, that tuning is your M5 deliverable.

The loop is deliberately transparent (hand-written tool-calling on the openai
client) so a grader can see the machinery. Keep the bounds explicit if you rework it.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
from pathlib import Path

from openai import OpenAI

import tools
from critic import review
from prompts import CORTEX_SYSTEM

try:  # load .env if python-dotenv is installed; harmless if it isn't
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# --- Bounds (your M5 deliverable: tune these and justify them) ----------------
MODEL = os.environ.get("CORTEX_MODEL", "gpt-4.1-mini")
MAX_ITERATIONS = int(os.environ.get("CORTEX_MAX_ITERATIONS", "8"))
MAX_REVISIONS = int(os.environ.get("CORTEX_MAX_REVISIONS", "2"))
COST_CAP_USD = float(os.environ.get("CORTEX_COST_CAP_USD", "0.50"))
MAX_QUEUE_ITEMS = int(os.environ.get("CORTEX_MAX_QUEUE_ITEMS", "10"))
# Stuck detector: if a required data pull keeps failing this many times, stop and
# escalate instead of spinning (see loop-spec.md stop conditions).
MAX_DATA_ATTEMPTS = int(os.environ.get("CORTEX_MAX_DATA_ATTEMPTS", "3"))
# Rough $ per 1M tokens for your chosen model, set to match its pricing.
PRICE_IN = float(os.environ.get("CORTEX_PRICE_IN_PER_M", "0.15"))
PRICE_OUT = float(os.environ.get("CORTEX_PRICE_OUT_PER_M", "0.60"))

# Tools that pull required project data; failures here count toward the stuck cap.
DATA_TOOLS = {"get_project", "get_activity"}

# Retrieval-quality probe: names in CORTEX_WITHHOLD (comma-separated) are made to
# return "source_unavailable" instead of real data, so you can check that a grounded
# Cortex refuses/escalates rather than inventing. Empty by default = normal run.
WITHHELD = {t.strip() for t in os.environ.get("CORTEX_WITHHOLD", "").split(",") if t.strip()}

TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "get_project", "description": "Look up a project by its ID (status, flags, linked PRD).",
        "parameters": {"type": "object", "properties": {
            "project_id": {"type": "string"}}, "required": ["project_id"]}}},
    {"type": "function", "function": {
        "name": "get_activity",
        "description": "Pull recent engineering activity for a project (merged PRs, open issues, Sev-1s).",
        "parameters": {"type": "object", "properties": {
            "project_id": {"type": "string"}}, "required": ["project_id"]}}},
    {"type": "function", "function": {
        "name": "search_past_updates",
        "description": "Search previous status updates and decisions for tone and precedent.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {
        "name": "get_roadmap",
        "description": "Return the roadmap. Some items are flagged confidential/embargoed.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {
        "name": "get_norms", "description": "Return the team norms / PM playbook the agent must follow.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {
        "name": "propose_stories",
        "description": "Queue a set of backlog stories for human approval (creates nothing; rejected above the item cap).",
        "parameters": {"type": "object", "properties": {
            "project_id": {"type": "string"},
            "stories": {"type": "array", "items": {"type": "string"}},
            "reason": {"type": "string"}}, "required": ["project_id", "stories"]}}},
]


class Bounds:
    """Tracks spend and trips the cost cap. This is enforced OUTSIDE the model."""

    def __init__(self):
        self.cost = 0.0

    def add(self, usage) -> None:
        self.cost += (usage.prompt_tokens * PRICE_IN
                      + usage.completion_tokens * PRICE_OUT) / 1_000_000

    def over_cap(self) -> bool:
        return self.cost >= COST_CAP_USD


def banner(text: str) -> None:
    print(f"\n{'=' * 64}\n{text}\n{'=' * 64}")


# --- Work tree (per-run isolated workspace, see loop-spec.md) ------------------
RUNS_DIR = Path(__file__).parent / "runs"  # gitignored; scratch state per message


def claim_work_tree(message_id: str, force: bool):
    """Create the per-run work tree. Creating the dir IS the atomic claim: a second
    fire of the same message_id hits FileExistsError and is deduped (returns None),
    so Cortex never drafts the same task twice. Pass force=True to reclaim an existing
    dir (handy for re-running a fixture)."""
    run_dir = RUNS_DIR / message_id
    if force and run_dir.exists():
        shutil.rmtree(run_dir)
    try:
        run_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        return None
    (run_dir / "status").write_text("claimed\n")
    return run_dir


def clean_draft(text: str) -> str:
    """Tidy the drafted output for saving: drop the leading DONE:/ESCALATE: marker and
    cut an accidentally repeated body (the drafter occasionally emits the update twice)."""
    t = text.strip()
    for marker in ("DONE:", "ESCALATE:"):
        if t[:len(marker)].upper() == marker:
            body = t[len(marker):]
            repeat = re.search(r"\n\s*" + re.escape(marker), body, re.IGNORECASE)
            if repeat:  # model restarted the whole message; keep only the first copy
                body = body[:repeat.start()]
            t = body.strip()
            break
    return t + "\n"


def finalize(run_dir, status: str, source_log, draft=None, verdict=None) -> None:
    """Persist the run's artifacts to its work tree and stamp the final status
    (claimed | done | escalated | stuck)."""
    if run_dir is None:
        return
    (run_dir / "status").write_text(status + "\n")
    (run_dir / "source_log.json").write_text(json.dumps(source_log, indent=2))
    if draft is not None:
        (run_dir / "draft.md").write_text(clean_draft(draft))
    if verdict is not None:
        clean = {k: v for k, v in verdict.items() if k != "_usage"}
        (run_dir / "verdict.json").write_text(json.dumps(clean, indent=2))


def run(which: str = "happy") -> None:
    client = OpenAI()
    bounds = Bounds()
    task = tools.get_task(which)
    if "error" in task:
        print(task)
        return

    banner(f"CORTEX RUN, fixture: task-{which}  (auto-queue cap {MAX_QUEUE_ITEMS} items)")
    print(task["body"])

    messages = [
        {"role": "system", "content": CORTEX_SYSTEM},
        {"role": "user", "content": f"PM task brief:\n\n{task['body']}"},
    ]
    source_log: list[str] = [task["body"]]
    revisions = 0
    data_failures = 0  # required-data pulls that returned an error (stuck detector)

    # Claim an isolated work tree keyed on the message id. Creating the dir is the
    # atomic claim, so a duplicate fire of the same task is deduped (loop-spec.md).
    message_id = f"task-{which}"
    force = os.environ.get("CORTEX_FORCE_RERUN") == "1" or "--force" in sys.argv
    run_dir = claim_work_tree(message_id, force)
    if run_dir is None:
        banner(f"DEDUPE, {message_id} already handled (runs/{message_id}/). Skipping "
               f"to avoid a duplicate draft. Re-run with CORTEX_FORCE_RERUN=1.")
        return
    print(f"\n[work tree] runs/{message_id}/  (claimed)")

    last_proposed = None  # newest draft, persisted even if the run ends unfinished
    for step in range(1, MAX_ITERATIONS + 1):
        if bounds.over_cap():
            banner(f"BOUND TRIPPED, cost cap ${COST_CAP_USD} hit at "
                   f"${bounds.cost:.4f}. Halting and escalating to a human.")
            finalize(run_dir, "stuck", source_log, draft=last_proposed)
            return

        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOL_SCHEMAS)
        bounds.add(resp.usage)
        msg = resp.choices[0].message

        if msg.tool_calls:
            messages.append(msg)
            for call in msg.tool_calls:
                fn = call.function.name
                args = json.loads(call.function.arguments or "{}")
                if fn in WITHHELD:  # retrieval-quality probe: source made unavailable
                    result = {"error": "source_unavailable", "tool": fn,
                              "hint": "this source is withheld this run; do not invent "
                                      "its data, escalate if the task needs it"}
                else:
                    result = tools.TOOLS[fn](**args)
                source_log.append(f"{fn}({args}) -> {json.dumps(result)}")
                print(f"\n[step {step}] TOOL {fn}({args})")
                print(f"          -> {json.dumps(result)[:300]}")
                messages.append({"role": "tool", "tool_call_id": call.id,
                                 "content": json.dumps(result)})
                if fn in DATA_TOOLS and isinstance(result, dict) and "error" in result:
                    data_failures += 1

            if data_failures >= MAX_DATA_ATTEMPTS:
                banner(f"STUCK, required data could not be pulled after "
                       f"{data_failures} failed attempts (cap {MAX_DATA_ATTEMPTS}). "
                       f"Halting and escalating to a human. Run cost ≈ ${bounds.cost:.4f}")
                finalize(run_dir, "stuck", source_log, draft=last_proposed)
                return
            continue

        # No tool calls => Cortex produced a proposed output. Validate it.
        proposed = msg.content or ""
        last_proposed = proposed
        print(f"\n[step {step}] PROPOSED OUTPUT:\n{proposed}")

        banner("CRITIC, independent validation")
        verdict = review(client, MODEL, proposed, "\n".join(source_log))
        # Estimate critic spend too.
        bounds.cost += (verdict["_usage"]["prompt"] * PRICE_IN
                        + verdict["_usage"]["completion"] * PRICE_OUT) / 1_000_000
        print(json.dumps({k: v for k, v in verdict.items() if k != "_usage"}, indent=2))

        if verdict["verdict"] == "pass":
            status = "escalated" if proposed.strip().startswith("ESCALATE") else "done"
            banner(f"HITL CHECKPOINT, status update + any proposed stories queued for "
                   f"your review. Nothing posted, no commitments made. "
                   f"Run cost ≈ ${bounds.cost:.4f}")
            finalize(run_dir, status, source_log, draft=proposed, verdict=verdict)
            return

        if revisions >= MAX_REVISIONS:
            banner(f"REVISION CAP hit ({MAX_REVISIONS}). Escalating to a human "
                   f"instead of looping. Run cost ≈ ${bounds.cost:.4f}")
            finalize(run_dir, "escalated", source_log, draft=proposed, verdict=verdict)
            return

        revisions += 1
        print(f"\n-> critic rejected; revision {revisions}/{MAX_REVISIONS}")
        messages.append(msg)
        messages.append({"role": "user", "content":
                         "A validator rejected that for these reasons: "
                         f"{verdict['reasons']}. Fix it or escalate."})

    banner(f"MAX ITERATIONS ({MAX_ITERATIONS}) reached without finishing. "
           f"Escalating. Run cost ≈ ${bounds.cost:.4f}")
    finalize(run_dir, "stuck", source_log, draft=last_proposed)


if __name__ == "__main__":
    fixtures = [a for a in sys.argv[1:] if not a.startswith("-")]  # ignore flags
    run(fixtures[0] if fixtures else "happy")
