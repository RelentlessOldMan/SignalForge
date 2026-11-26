"""Scalar arguments that must be real numbers refuse strings, bytes and bools, as `real` does."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pytest

import signalforge as sf

_X = np.sin(0.3 * np.arange(256.0))

CALLS: dict[str, Callable[[object], object]] = {
    "clark_evans_ratio.density": lambda v: sf.clark_evans_ratio([0.5, 1.0], v),  # type: ignore[arg-type]
    "clark_evans_z.density": lambda v: sf.clark_evans_z([0.5, 1.0], v),  # type: ignore[arg-type]
    "pielou_nonrandomness.density": lambda v: sf.pielou_nonrandomness([0.5, 1.0], v),  # type: ignore[arg-type]
    "temporal_centroid.sample_rate": lambda v: sf.temporal_centroid(_X, v),  # type: ignore[arg-type]
    "time_weighting.sample_rate": lambda v: sf.time_weighting(_X, v, 0.125),  # type: ignore[arg-type]
    "time_weighting.time_constant": lambda v: sf.time_weighting(_X, 8.0, v),  # type: ignore[arg-type]
    "autocorrelation_pitch.sample_rate": lambda v: sf.autocorrelation_pitch(_X, v, 0.5, 2.0),  # type: ignore[arg-type]
    "autocorrelation_pitch.min_frequency": lambda v: sf.autocorrelation_pitch(_X, 64.0, v, 20.0),  # type: ignore[arg-type]
    "autocorrelation_pitch.max_frequency": lambda v: sf.autocorrelation_pitch(_X, 64.0, 1.0, v),  # type: ignore[arg-type]
    "cepstrum_pitch.sample_rate": lambda v: sf.cepstrum_pitch(_X, v, 0.5, 2.0),  # type: ignore[arg-type]
    "cepstrum_pitch.min_frequency": lambda v: sf.cepstrum_pitch(_X, 64.0, v, 20.0),  # type: ignore[arg-type]
    "cepstrum_pitch.max_frequency": lambda v: sf.cepstrum_pitch(_X, 64.0, 1.0, v),  # type: ignore[arg-type]
}


@pytest.mark.parametrize("name", sorted(CALLS))
@pytest.mark.parametrize("bad", ["4", b"4", True, np.True_, None, [4.0], np.array([4.0])])
def test_rejects_non_numbers(name: str, bad: object) -> None:
    with pytest.raises(ValueError):
        CALLS[name](bad)


@pytest.mark.parametrize("name", sorted(CALLS))
def test_accepts_numbers(name: str) -> None:
    for good in [4, 4.0, np.float32(4.0), np.int64(4)]:
        CALLS[name](good)
