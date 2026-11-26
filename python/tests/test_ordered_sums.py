"""The index functions of ADRs 0607-0620 sum in record order without a Python loop per value
(ADR 0623): the Python lines they run do not grow with the input, and each sum is bit for bit
the left-to-right sum the C# library takes."""

from __future__ import annotations

import sys
from collections.abc import Callable
from types import FrameType
from typing import Any

import numpy as np
import pytest

import signalforge as sf
from signalforge import measurements
from signalforge.measurements import _ordered_sum


def _counts(n: int) -> list[float]:
    return [float(v) for v in np.random.default_rng(n).integers(0, 9, n)] + [3.0]


def _dists(n: int, seed: int = 0) -> list[float]:
    return list(np.random.default_rng((n, seed)).uniform(0.1, 5.0, n))


CALLS: dict[str, Callable[[int], object]] = {
    "strauss_selection": lambda n: sf.strauss_selection(_dists(n), _dists(n, 1)),
    "johnson_rank_preference": lambda n: sf.johnson_rank_preference(_dists(n), _dists(n, 1)),
    "lloyd_mean_crowding": lambda n: sf.lloyd_mean_crowding(_counts(n)),
    "lloyd_patchiness": lambda n: sf.lloyd_patchiness(_counts(n)),
    "green_index": lambda n: sf.green_index(_counts(n)),
    "morisita_dispersion": lambda n: sf.morisita_dispersion(_counts(n)),
    "david_moore_clumping": lambda n: sf.david_moore_clumping(_counts(n)),
    "cassie_index": lambda n: sf.cassie_index(_counts(n)),
    "fisher_dispersion": lambda n: sf.fisher_dispersion(_counts(n)),
    "clark_evans_ratio": lambda n: sf.clark_evans_ratio(_dists(n), 0.5),
    "clark_evans_z": lambda n: sf.clark_evans_z(_dists(n), 0.5),
    "hopkins_statistic": lambda n: sf.hopkins_statistic(_dists(n), _dists(n, 1)),
    "pielou_nonrandomness": lambda n: sf.pielou_nonrandomness(_dists(n), 0.5),
    "eberhardt_index": lambda n: sf.eberhardt_index(_dists(n)),
}


def _lines_in_measurements(call: Callable[[], object]) -> int:
    count = 0
    target = measurements.__file__

    def tracer(frame: FrameType, event: str, arg: Any) -> Any:
        nonlocal count
        if frame.f_code.co_filename != target:
            return None
        if event == "line":
            count += 1
        return tracer

    old = sys.gettrace()
    sys.settrace(tracer)
    try:
        call()
    finally:
        sys.settrace(old)
    return count


@pytest.mark.parametrize("name", sorted(CALLS))
def test_python_lines_do_not_grow_with_the_input(name: str) -> None:
    small = _lines_in_measurements(lambda: CALLS[name](8))
    large = _lines_in_measurements(lambda: CALLS[name](800))
    assert small > 0
    assert large == small


def _left_to_right(values: np.ndarray) -> float:
    s = 0.0
    for v in values.tolist():
        s += v
    return s


def test_ordered_sum_is_the_left_to_right_sum() -> None:
    rng = np.random.default_rng(623)
    t = rng.standard_normal(5000) * np.exp(rng.uniform(-20, 20, 5000))
    expected = _left_to_right(t)
    assert expected != float(np.sum(t))  # pairwise summation would round differently here
    assert _ordered_sum(t.copy()) == expected
    assert _ordered_sum(np.empty(0)) == 0.0


def test_eberhardt_matches_a_left_to_right_loop() -> None:
    rng = np.random.default_rng(6230)
    a = rng.uniform(0.0, 1.0, 3001) ** 6
    top = float(np.max(a))
    s1 = s2 = 0.0
    for v in a.tolist():
        u = v / top
        s1 += u
        s2 += u * u
    assert sf.eberhardt_index(a) == min(max(a.size * s2 / (s1 * s1), 1.0), float(a.size))
