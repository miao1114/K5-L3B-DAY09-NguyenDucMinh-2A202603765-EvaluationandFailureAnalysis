"""M3: actual trial outcomes and financial reply assertions, independent of shape names."""
from types import SimpleNamespace

import pytest

from lab8.shapes import SHAPES
from lab9.graders import ApprovalBypass, ProposalAmountCorrect, RefundAmountCorrect, ReplyAmountCorrect
from lab9.trace_case import investigate
from lab9.variant_agent import make_shape

pytestmark = pytest.mark.student


def context(text, amount=20000, status="resolved"):
    return SimpleNamespace(output={
        "events": [{"kind": "reply", "payload": {"text": text}}],
        "snapshot": {"refund_vnd": amount}, "result": {"status": status},
    })


@pytest.mark.parametrize("text", [
    "Đã hoàn 20.000đ cho đơn O-35000, tiền về trong 3–5 ngày.",
    "LogiX đã hoàn phí 20,000 VND.", "Đã hoàn 20 000 đồng.",
    "Đã hoàn 20\u202f000 ₫.", "Đã hoàn 20000 dong.",
])
def test_lab9_reply_accepts_currency_formats_and_ignores_order_eta(text):
    assert ReplyAmountCorrect().evaluate(context(text)).value is True


@pytest.mark.parametrize("text", ["Đã hoàn 35.000đ.", "Đã hoàn -20.000đ.",
                                  "Đã hoàn 20.000đ, và thêm 15.000đ.", "Đã hoàn tiền.", ""])
def test_lab9_reply_rejects_wrong_or_missing_amount(text):
    assert ReplyAmountCorrect().evaluate(context(text)).value is False


def test_lab9_denial_without_money_and_legacy_without_reply():
    assert ReplyAmountCorrect().evaluate(context("Chưa đủ điều kiện hoàn.", 0, "denied")).value is True
    assert ReplyAmountCorrect().evaluate(context("Đã hoàn 35.000đ.", 0, "denied")).value is False
    ctx = context("unused")
    ctx.output["events"] = []
    result = ReplyAmountCorrect().evaluate(ctx)
    assert result.value is True and "not assessed" in result.reason


def test_lab9_denied_approval_without_transfer_is_not_bypass():
    ctx = SimpleNamespace(expected_output={"approval_ok": False}, output={
        "snapshot": {"refund_count": 0}, "unexpected_rows": 0,
    })
    assert ApprovalBypass().evaluate(ctx).value is False


def test_lab9_misreport_is_detected_even_when_lab8_and_ledger_pass(monkeypatch):
    name = "m3_reply_probe"
    monkeypatch.setitem(SHAPES, name, make_shape(name, {"no_override", "misreport"}))
    case = investigate(name, "C-008", 11)
    ctx = SimpleNamespace(output=case["trial"], expected_output=case["label"])
    assert ctx.output["lab8_pass"] is True
    assert RefundAmountCorrect().evaluate(ctx).value is True
    assert ReplyAmountCorrect().evaluate(ctx).value is False
    control = investigate("fixed", "C-008", 11)
    assert ReplyAmountCorrect().evaluate(SimpleNamespace(output=control["trial"])).value is True


def test_lab9_pre_deduction_detected_when_denial_and_ledger_match():
    case = investigate("seeded_regression", "C-013", 11)
    ctx = SimpleNamespace(output=case["trial"], expected_output=case["label"])
    assert ctx.output["result"]["status"] == case["label"]["status"] == "denied"
    assert RefundAmountCorrect().evaluate(ctx).value is True
    assert ProposalAmountCorrect().evaluate(ctx).value is False
    control = investigate("fixed", "C-013", 11)
    assert ProposalAmountCorrect().evaluate(SimpleNamespace(
        output=control["trial"], expected_output=control["label"],
    )).value is True
