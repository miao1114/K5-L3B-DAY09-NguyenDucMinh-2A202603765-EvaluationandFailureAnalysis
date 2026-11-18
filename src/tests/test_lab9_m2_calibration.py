"""M2: class orientation, invalid inputs, and unusable judges must fail calibration."""
import math
from pathlib import Path

import pytest

from lab9 import stats
from lab9.judge import calibrate

pytestmark = pytest.mark.student


def test_fail_is_positive_and_missing_predictions_have_zero_recall():
    assert stats.confusion(["FAIL", "PASS"], ["PASS", "FAIL"]) == dict(tp=0, fp=1, fn=1, tn=0)
    assert stats.precision_recall(["FAIL", "PASS"], ["PASS", "PASS"]) == (0.0, 0.0)
    assert stats.cohen_kappa(["PASS", "FAIL"], ["FAIL", "PASS"]) == -1.0


@pytest.mark.parametrize("human, judge", [(["PASS"], []), (["MAYBE"], ["PASS"])])
def test_invalid_label_pairs_are_rejected(human, judge):
    with pytest.raises(ValueError):
        stats.confusion(human, judge)


def test_empty_kappa_is_undefined():
    with pytest.raises(ValueError):
        stats.cohen_kappa([], [])


@pytest.mark.parametrize("rates", [(0.2, 0.5, 0.5), (0.2, 0.1, 0.2),
                                   (float("nan"), 0.8, 0.9), (1.1, 0.8, 0.9)])
def test_unidentifiable_or_invalid_correction_is_rejected(rates):
    with pytest.raises(ValueError):
        stats.rogan_gladen(*rates)


def test_rogan_gladen_upper_clip():
    assert stats.rogan_gladen(1.0, 0.8, 0.9) == 1.0


def test_public_tone_is_usable_but_helpful_misses_failures():
    tone = calibrate(Path("data/eval/judge_tone_public.csv"))
    helpful = calibrate(Path("data/eval/judge_helpful_public.csv"))
    assert tone["passed"] is True
    assert helpful["passed"] is False
    assert helpful["recall"] < 0.7
    assert helpful["confusion"]["fn"] > helpful["confusion"]["tp"]


def test_constant_judge_fails_without_crashing(tmp_path):
    source = tmp_path / "constant.csv"
    source.write_text("item_id,reply,human,judge\nx,ok,PASS,PASS\n", encoding="utf-8")
    result = calibrate(source)
    assert result["passed"] is False
    assert math.isnan(result["kappa"])
    assert math.isnan(result["corrected_fail_rate"])
