"""The Chao-Wang-Jost entropy (ADR 0562)."""

from __future__ import annotations

import decimal
import math
from fractions import Fraction

import numpy as np
import pytest

import signalforge as sf


def _closed_form(x: np.ndarray) -> float:
    decimal.getcontext().prec = 60
    v = [int(a) for a in x]
    n = sum(v)
    f1 = v.count(1)
    f2 = v.count(2)
    seen = sum(
        (
            Fraction(a, n) * sum((Fraction(1, k) for k in range(a, n)), Fraction(0))
            for a in v
            if 1 <= a <= n - 1
        ),
        Fraction(0),
    )
    if f1 == 0:
        return float(seen)
    a = Fraction(2 * f2, (n - 1) * f1 + 2 * f2) if f2 > 0 else Fraction(2, (n - 1) * (f1 - 1) + 2)
    if a == 1:
        return float(seen)
    q = 1 - a
    series = sum((q**r / r for r in range(1, n)), Fraction(0))

    def dec(f: Fraction) -> decimal.Decimal:
        return decimal.Decimal(f.numerator) / decimal.Decimal(f.denominator)

    rest = dec(Fraction(f1, n) * q ** (1 - n)) * (-dec(a).ln() - dec(series))
    return float(dec(seen) + rest)


def test_matches_the_closed_form_for_small_records() -> None:
    rng = np.random.default_rng(325)
    for n in range(1, 12):
        x = rng.integers(0, 5, n).astype(float)
        x[0] += 1.0
        if np.sum(x) < 2:
            x[0] += 1.0
        h = sf.chao_wang_jost_entropy(x)
        assert h == pytest.approx(_closed_form(x), rel=1e-9, abs=1e-10)
        assert sf.chao_wang_jost_entropy(rng.permutation(x)) == pytest.approx(
            h, rel=1e-12, abs=1e-13
        )
    assert sf.chao_wang_jost_entropy([0.0, 7.0]) == 0.0


def test_only_singletons_stays_finite() -> None:
    h = sf.chao_wang_jost_entropy(np.ones(500))
    assert math.isfinite(h)
    assert h > math.log(500)


@pytest.mark.parametrize(
    "bad", [[], [1.0], [0.0, 0.0], [1.0, -1.0], [1.5, 2.0], [1e4, 1.0], [np.nan]]
)
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.chao_wang_jost_entropy(bad)
