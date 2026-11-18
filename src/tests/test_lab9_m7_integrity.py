"""M7 adversarial evidence checks beyond the four supplied traps."""
import copy

import pytest

from lab9.gate import integrity_check

pytestmark = pytest.mark.student
SPEC = {"eval_set_version": "v2", "metrics": [{"id": "pass_rate", "kind": "capability",
        "blocking": True, "threshold": {"min": 0.8, "no_significant_drop": True}}],
        "slices": [{"name": "money", "metric": "pass_rate", "min": 0.9,
                    "blocking": True, "no_significant_drop": True}]}


def clean():
    return {"manifest": {"eval_set_sha": "same", "items": 4, "seeds": [11, 22]},
            "metrics": {"pass_rate": 1.0}, "evaluator_failures": [],
            "rows": [{"item_id": f"E-{i}", "seed": s, "pass_rate": True,
                      "slices": ["money"] if i < 2 else []} for i in range(4) for s in (11, 22)]}


@pytest.mark.parametrize("attack", ["duplicate", "green_evaluator_failure", "missing_score",
                                   "forged_aggregate", "relabel_slice", "changed_seed", "infinite_cost"])
def test_lab9_m7_corrupt_evidence_is_rejected(attack):
    base, pr = clean(), clean()
    if attack == "duplicate":
        pr["rows"][-1] = copy.deepcopy(pr["rows"][0])
    elif attack == "green_evaluator_failure":
        pr["evaluator_failures"] = ["grader crashed despite green metrics"]
    elif attack == "missing_score":
        del pr["rows"][0]["pass_rate"]
    elif attack == "forged_aggregate":
        pr["rows"][0]["pass_rate"] = False
    elif attack == "relabel_slice":
        for row in pr["rows"]:
            if row["item_id"] == "E-0":
                row["slices"] = []
    elif attack == "changed_seed":
        pr["rows"][0]["seed"] = 99
    elif attack == "infinite_cost":
        pr["rows"][0]["cost"] = float("inf")
    assert integrity_check(base, base, SPEC) == []
    assert integrity_check(pr, base, SPEC)


@pytest.mark.parametrize("attack", ["drop_metric", "drop_slice", "drop_ci", "nonblocking", "loosen_slice"])
def test_lab9_m7_spec_ratchet_preserves_guards(attack):
    changed = copy.deepcopy(SPEC)
    if attack == "drop_metric":
        changed["metrics"] = []
    elif attack == "drop_slice":
        changed["slices"] = []
    elif attack == "drop_ci":
        del changed["metrics"][0]["threshold"]["no_significant_drop"]
    elif attack == "nonblocking":
        changed["metrics"][0]["blocking"] = False
    elif attack == "loosen_slice":
        changed["slices"][0]["min"] = 0.8
    base = clean()
    assert integrity_check(base, base, changed, SPEC)


def test_lab9_m7_stricter_spec_and_report_order_are_allowed():
    spec = copy.deepcopy(SPEC)
    spec["metrics"][0]["threshold"]["min"] = 0.9
    base, pr = clean(), clean()
    pr["rows"].reverse()
    assert integrity_check(pr, base, spec, SPEC) == []
