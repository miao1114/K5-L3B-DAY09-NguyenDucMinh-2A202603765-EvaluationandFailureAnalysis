"""Reproduce M1 observations without changing Lab8 or the public variants.

Run from src/: python -m scripts.collect_m1_evidence
The output is trace evidence, not a scored eval/baseline report (M3 is unfinished).
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from lab8.shapes import SHAPES
from lab9.trace_case import investigate
from lab9.variant_agent import make_shape


SCENARIOS = [
    ("FM-01", "leaky_trace", "C-001", 1),
    ("FM-02", "ignore_denied", "C-007", 4),
    ("FM-03", "ticket_trust", "C-002", 3),
    ("FM-04", "sum_parts", "C-014", 4),
    ("FM-05", "pre_deducted", "C-014", 5),
    ("FM-06", "stale_clause", "C-006", 3),
    ("FM-07", "sibling_refund", "C-010", 4),
    ("FM-08", "misreport", "C-008", 4),
]


def summarize(shape: str, claim: str, seed: int, *, events: bool = False) -> dict:
    case = investigate(shape, claim, seed)
    trial = case["trial"]
    result = trial["result"]
    summary = {
        "shape": shape, "claim_id": claim, "seed": seed,
        "trace_run_id": result["run_id"],
        "lab8_pass": trial["lab8_pass"], "lab8_reason": trial["lab8_reason"],
        "result": {k: result.get(k) for k in ("status", "proposal_amount", "error_reason")},
        "snapshot": trial["snapshot"], "unexpected_rows": trial["unexpected_rows"],
        "label": {k: case["label"][k] for k in ("status", "proposal_amount", "refund_vnd", "refund_count")},
        "override_steps": [i for i, e in enumerate(trial["events"], 1) if e["kind"] == "model_override"],
    }
    if events:
        summary["events"] = copy.deepcopy(trial["events"])
        for event in summary["events"]:
            if event["kind"] == "debug_claim_row":
                event["payload"] = {
                    "redacted": True,
                    "fields": list(event["payload"]),
                    "forbidden_token_present": any(
                        token and token in trial["blob"] for token in case["label"]["forbid_substrings"]
                    ),
                }
    return summary


def main() -> None:
    claims = [json.loads(line)["claim_id"] for line in Path("data/public_claims.jsonl").read_text(encoding="utf-8").splitlines()]
    observations = []
    for fm, bug, claim, step in SCENARIOS:
        name = f"m1_{bug}"
        # Diagnostic registration is in memory only; no supplied variant is edited.
        SHAPES[name] = make_shape(name, {"no_override", bug})
        observations.append({
            "failure_mode": fm, "bug_switch": bug, "first_wrong_event": step,
            "failing": summarize(name, claim, 11, events=True),
            "control": summarize("fixed", claim, 11, events=True),
        })
    evidence = {
        "command": "python -m scripts.collect_m1_evidence",
        "scope": "M1 trace observations; not an M4 baseline or completed M3 grading",
        "diagnostic_cases": observations,
        "trace_case": summarize("seeded_regression", "C-002", 11, events=True),
        "trace_case_control": summarize("fixed", "C-002", 11, events=True),
        "swarm_public": [summarize("swarm", c, s) for c in claims for s in (11, 22, 33, 44, 55)],
    }
    output = Path("../docs/m1_trace_evidence.json")
    output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    failed = [f"{r['claim_id']}@{r['seed']}" for r in evidence["swarm_public"] if not r["lab8_pass"]]
    print(f"wrote {output}: {len(observations)} diagnostic pairs, 70 swarm trials; swarm failures={failed}")
    for obs in observations:
        bad = obs["failing"]
        print(obs["failure_mode"], bad["claim_id"], f"step={obs['first_wrong_event']}", bad["snapshot"], f"lab8_pass={bad['lab8_pass']}")


if __name__ == "__main__":
    main()
