"""The generalized entropy index (ADR 0516)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_holds_the_mld_theil_and_cv_and_is_continuous() -> None:
    rng = np.random.default_rng(279)
    for n in range(1, 30):
        x = rng.random(n) * 10 + 0.1
        ge = sf.generalized_entropy_index
        assert ge(x, 0.0) == pytest.approx(sf.mean_log_deviation(x), rel=1e-12, abs=1e-14)
        assert ge(x, 1.0) == pytest.approx(sf.theil_index(x), rel=1e-12, abs=1e-14)
        cv = sf.coefficient_of_variation(x)
        assert ge(x, 2.0) == pytest.approx(cv * cv / 2, rel=1e-12, abs=1e-14)
        assert ge(x, 1e-6) == pytest.approx(ge(x, 0.0), rel=1e-4, abs=1e-8)
        assert ge(x, 1 + 1e-6) == pytest.approx(ge(x, 1.0), rel=1e-4, abs=1e-8)
        for a in (-2.0, -0.5, 0.5, 1.5, 3.0):
            v = ge(x, a)
            assert v >= -1e-15
            assert ge(3.5 * x, a) == pytest.approx(v, rel=1e-11, abs=1e-14)


@pytest.mark.parametrize("bad", [[], [1.0, 0.0], [-2.0, 1.0], [1.0, np.inf], [[1.0, 2.0]]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.generalized_entropy_index(bad, 2.0)
