"""M5: local regressions, paired sampling, and v2 coverage; no M6/M7 assumptions."""
import copy
from collections import Counter
import json
from pathlib import Path

import pytest

from lab9 import evalset, gate

pytestmark = pytest.mark.student


def report(rows):
    return {"rows": rows}


def rows():
    return [{"item_id": f"E-{i}", "seed": s, "pass_rate": True,
             "slices": ["money"] if i < 2 else []} for i in range(8) for s in (11, 22)]


def spec(**updates):
    rule = {"name": "money", "metric": "pass_rate", "min": 0.9,
            "no_significant_drop": True, "blocking": True, **updates}
    return {"slices": [rule], "bootstrap": {"n_resamples": 1000, "rng": 2027, "confidence": 0.95}}


def test_lab9_m5_slice_blocks_local_regression_while_overall_above_floor():
    base = rows()
    changed = copy.deepcopy(base)
    for row in changed:
        if row["item_id"] == "E-0":
            row["pass_rate"] = False
    assert sum(r["pass_rate"] for r in changed) / len(changed) == 0.875
    blocked, _ = gate.slice_check(report(changed), report(base), spec())
    assert blocked == ["slice:money/pass_rate"]


def test_lab9_m5_equal_slice_passes_and_nonblocking_only_warns():
    base = rows()
    assert gate.slice_check(report(base), report(base), spec())[0] == []
    changed = copy.deepcopy(base)
    for row in changed:
        if row["slices"]:
            row["pass_rate"] = False
    blocked, lines = gate.slice_check(report(changed), report(base), spec(blocking=False))
    assert blocked == [] and "warn" in lines[0]


def test_lab9_m5_significant_drop_blocks_even_without_absolute_floor():
    base = rows()
    changed = copy.deepcopy(base)
    for row in changed:
        if row["slices"] and row["seed"] == 11:
            row["pass_rate"] = False
    blocked, lines = gate.slice_check(report(changed), report(base), spec(min=0.1))
    assert blocked == ["slice:money/pass_rate"]
    assert "significant drop" in lines[0]


@pytest.mark.parametrize("case", ["absent", "missing_item", "nonfinite"])
def test_lab9_m5_missing_or_unpaired_slice_does_not_pass(case):
    base = rows()
    changed = copy.deepcopy(base)
    if case == "absent":
        for row in changed:
            row["slices"] = []
    elif case == "missing_item":
        changed = [r for r in changed if r["item_id"] != "E-0"]
    else:
        changed[0]["pass_rate"] = float("nan")
    assert gate.slice_check(report(changed), report(base), spec())[0] == ["slice:money/pass_rate"]


def test_lab9_m5_build_v2_preserves_v1_labels_and_tags(tmp_path, monkeypatch):
    items_v1, labels_v1 = evalset.load_jsonl(evalset.ITEMS), json.loads(evalset.LABELS.read_text(encoding="utf-8"))
    monkeypatch.setattr(evalset, "ITEMS_V2", tmp_path / "items.jsonl")
    monkeypatch.setattr(evalset, "LABELS_V2", tmp_path / "labels.json")
    n, labels_n = evalset.build_v2()
    assert n == labels_n == 28
    result = evalset.load_jsonl(evalset.ITEMS_V2)
    labels = json.loads(evalset.LABELS_V2.read_text(encoding="utf-8"))
    assert b"\r\n" not in evalset.ITEMS_V2.read_bytes()
    for before, after in zip(items_v1, result[:len(items_v1)]):
        assert after["failure_modes"] == before["failure_modes"]
        assert after["provenance"] == before["provenance"]
        assert labels[before["claim_id"]] == labels_v1[before["claim_id"]]
    attacked = {fm for item in result if item["split"] == "adversarial" for fm in item["failure_modes"]}
    counts = Counter(fm for item in result for fm in item["failure_modes"])
    assert all(counts[fm] >= 3 for fm in attacked)
    for item in result:
        assert "expected" not in item and "label" not in item
        assert ("adversarial" in item["slices"]) == (item["split"] == "adversarial")
        assert ("money_movement" in item["slices"]) == (labels[item["claim_id"]]["refund_vnd"] > 0)
