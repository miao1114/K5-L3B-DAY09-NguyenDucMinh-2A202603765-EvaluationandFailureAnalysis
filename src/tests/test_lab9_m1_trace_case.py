"""FM-03 regression: the same invariant rejects the buggy trial and accepts fixed."""
from types import SimpleNamespace

import pytest

from lab9.graders import DbFactKept
from lab9.trace_case import investigate


@pytest.mark.student
@pytest.mark.parametrize("shape, expected_pass", [("seeded_regression", False), ("fixed", True)])
def test_lab9_m1_ticket_cannot_override_database(shape, expected_pass):
    case = investigate(shape, "C-002", 11)
    trial, label = case["trial"], case["label"]
    fact_check = DbFactKept().evaluate(SimpleNamespace(output=trial))
    assert bool(fact_check.value) is expected_pass
    outcome_correct = (
        trial["result"]["status"] == label["status"]
        and trial["snapshot"]["refund_vnd"] == label["refund_vnd"]
        and trial["snapshot"]["refund_count"] == label["refund_count"]
    )
    assert outcome_correct is expected_pass
    assert trial["lab8_pass"] is expected_pass
    if not expected_pass:
        # Establish the earliest observable divergence, not just the final error.
        assert trial["events"][1]["payload"]["lookup_order"]["order"]["delay_days"] == 2
        assert trial["events"][2]["kind"] == "model_override"
        assert trial["events"][2]["payload"]["delay_days"] == 5
