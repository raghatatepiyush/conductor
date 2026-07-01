#!/usr/bin/env python3
"""
Conductor - A-grade gate teeth (Stop hook).

The quality gate used to live only in prose: the orchestrator was *asked* to run
tests + Security Gate + review and not ship failing work. This hook gives that
one real tooth. A Stop hook fires when the main agent tries to end its turn; by
returning {"decision": "block", "reason": ...} it sends the agent back to finish
the job instead of stopping on unfinished, sub-A-grade work.

It is deliberately CONSERVATIVE - it must never trap a legitimate pause:
  * It respects `stop_hook_active`: if we already blocked once this turn, we let
    the stop through (no loops).
  * It only fires when a `.conductor/state.json` ledger exists and an
    *in_progress* task carries a `gate` record with an EXPLICIT failure
    (a criterion recorded as false). A simply-absent gate is NOT a trap - that
    may be a trivial-lane task or work not yet at its gate.
  * It always allows the stop when `state.waitingOnHuman` is true - that's the
    orchestrator legitimately pausing to ask a genuine question or wait on a
    confirmation, which is the whole point of supervised autonomy.
  * On ANY error it fails open (exit 0) - it can only ever *add* a nudge, never
    brick the session.

So the only thing it catches is the precise bad pattern "a task's gate is on
record as failing and the agent is trying to walk away from it anyway".
"""

import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

CRITERIA = ("correct", "secure", "clean", "complete", "documented", "explained")


def _failing_inprogress(state):
    """Return list of (task_id, [failing criteria]) for in_progress tasks whose
    gate record has at least one explicit false. Absent gate => not failing."""
    out = []
    tasks = state.get("tasks", []) if isinstance(state, dict) else []
    for t in tasks:
        if not isinstance(t, dict) or t.get("status") != "in_progress":
            continue
        gate = t.get("gate")
        if not isinstance(gate, dict):
            continue  # no recorded gate yet -> do not trap
        failing = [c for c in CRITERIA if c in gate and not gate.get(c)]
        if failing:
            out.append((t.get("id", "?"), failing))
    return out


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    # Never loop: if our own block already re-engaged the agent, let it stop.
    if data.get("stop_hook_active"):
        sys.exit(0)

    path = os.path.join(".conductor", "state.json")
    if not os.path.isfile(path):
        sys.exit(0)
    try:
        with open(path, encoding="utf-8") as fh:
            state = json.load(fh)
    except Exception:
        sys.exit(0)

    # Legitimate pause for a question / confirmation -> allow the stop.
    if isinstance(state, dict) and state.get("waitingOnHuman"):
        sys.exit(0)

    failing = _failing_inprogress(state)
    if not failing:
        sys.exit(0)

    bits = "; ".join("%s (missing: %s)" % (tid, ", ".join(cs)) for tid, cs in failing)
    reason = (
        "Conductor A-grade gate: an in-progress task is on record as NOT yet "
        "A-grade, so don't finish here. " + bits + ". Resolve each failing "
        "criterion (run the Test Architect and the Security Gate, fix what they "
        "find, refresh docs, add the plain-language summary), update the task's "
        "gate in .conductor/state.json, then continue. If you're genuinely blocked "
        "and need the human, set that task to 'blocked' (with blockedBy) or set "
        "state.waitingOnHuman=true and ask your question - either lets you stop."
    )
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


if __name__ == "__main__":
    main()
