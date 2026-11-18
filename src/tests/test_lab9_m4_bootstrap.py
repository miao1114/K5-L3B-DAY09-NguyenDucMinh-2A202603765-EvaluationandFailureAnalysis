"""M4: resampling must preserve pairs, reject invalid data, and obey confidence."""
import pytest

from lab9.stats import paired_bootstrap

pytestmark = pytest.mark.student


def test_lab9_bootstrap_preserves_pairs_with_constant_difference():
    # Independent resampling would give a wide CI despite identical pairwise deltas.
    delta, low, high = paired_bootstrap([100, 200, 300, 400], [99, 199, 299, 399])
    assert (delta, low, high) == (1.0, 1.0, 1.0)


@pytest.mark.parametrize("a,b,kwargs", [
    ([], [], {}), ([1, 2], [1], {}), ([float("nan"), 1], [0, 1], {}),
    ([float("inf"), 1], [0, 1], {}), ([1, 0], [0, 0], {"n_resamples": 0}),
    ([1, 0], [0, 0], {"confidence": 1.0}),
])
def test_lab9_bootstrap_rejects_unusable_samples(a, b, kwargs):
    with pytest.raises(ValueError):
        paired_bootstrap(a, b, **kwargs)


def test_lab9_bootstrap_confidence_changes_interval():
    a, b = [1, 1, 0.8, 1, 0.6], [1, 0.8, 0.8, 0.6, 0.6]
    _, low_wide, high_wide = paired_bootstrap(a, b, confidence=0.99)
    _, low_narrow, high_narrow = paired_bootstrap(a, b, confidence=0.5)
    assert low_wide <= low_narrow <= high_narrow <= high_wide
    assert high_wide - low_wide > high_narrow - low_narrow
