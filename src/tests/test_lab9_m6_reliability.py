"""M6 combinatorial estimates against enumeration, including invalid input boundaries."""
from itertools import combinations

import pytest

from lab9.stats import pass_at_k, pass_hat_k

pytestmark = pytest.mark.student


def test_lab9_m6_estimates_match_exhaustive_sampling():
    for n in range(1, 8):
        for c in range(n + 1):
            population = [True] * c + [False] * (n - c)
            for k in range(1, n + 1):
                samples = list(combinations(population, k))
                assert pass_at_k(n, c, k) == pytest.approx(sum(any(s) for s in samples) / len(samples))
                assert pass_hat_k(n, c, k) == pytest.approx(sum(all(s) for s in samples) / len(samples))
                assert pass_hat_k(n, c, k) <= c / n + 1e-12
                assert c / n <= pass_at_k(n, c, k) + 1e-12


@pytest.mark.parametrize("args", [(0, 0, 1), (-1, 0, 1), (5, -1, 1), (5, 6, 1),
                                  (5, 2, 0), (5, 2, 6), (5.0, 2, 1), (5, 2.0, 1),
                                  (5, 2, 1.0), (True, 0, 1), (5, False, 1)])
def test_lab9_m6_invalid_sampling_arguments(args):
    for fn in (pass_at_k, pass_hat_k):
        with pytest.raises(ValueError):
            fn(*args)
