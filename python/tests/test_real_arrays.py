"""Arrays of real numbers refuse other dtypes with ValueError, as `real_values` does (ADR 0621)."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pytest

import signalforge as sf
from signalforge._checks import real_values

CALLS: dict[str, Callable[[object], object]] = {
    "lloyd_mean_crowding": lambda v: sf.lloyd_mean_crowding(v),  # type: ignore[arg-type]
    "cassie_index": lambda v: sf.cassie_index(v),  # type: ignore[arg-type]
    "fisher_dispersion": lambda v: sf.fisher_dispersion(v),  # type: ignore[arg-type]
    "eberhardt_index": lambda v: sf.eberhardt_index(v),  # type: ignore[arg-type]
    "clark_evans_ratio": lambda v: sf.clark_evans_ratio(v, 1.0),  # type: ignore[arg-type]
    "hopkins_statistic": lambda v: sf.hopkins_statistic(v, [1.0, 2.0]),  # type: ignore[arg-type]
    "strauss_selection": lambda v: sf.strauss_selection(v, [1.0, 2.0]),  # type: ignore[arg-type]
    "real_cepstrum": lambda v: sf.real_cepstrum(v),  # type: ignore[arg-type]
}

BAD = {
    "huge_int": [10**400, 1],
    "object_complex": np.array([1, 1j], dtype=object),
    "object_string": np.array([1, "2"], dtype=object),
    "object_bool": np.array([1, True], dtype=object),
    "strings": ["1", "2"],
    "bytes": [b"1", b"2"],
    "bools": [True, False],
    "datetime": np.array(["2020-01-01", "2020-01-02"], dtype="datetime64[D]"),
    "timedelta": np.array([1, 2], dtype="timedelta64[s]"),
}


@pytest.mark.parametrize("name", sorted(CALLS))
@pytest.mark.parametrize("bad", sorted(BAD))
def test_rejects_non_numbers(name: str, bad: str) -> None:
    with pytest.raises(ValueError):
        CALLS[name](BAD[bad])


@pytest.mark.parametrize("name", sorted(CALLS))
def test_accepts_numbers(name: str) -> None:
    for good in (
        [1, 2],
        [1.0, 2.0],
        np.array([1, 2], dtype=np.uint8),
        np.array([1, 2], dtype=np.float32),
        np.array([1, 2.0], dtype=object),
        [2**64, 1],
    ):
        CALLS[name](good)


def test_object_values_are_converted() -> None:
    a = real_values(np.array([[1, 2.5], [np.int64(3), 2**70]], dtype=object), "x")
    assert a.dtype == np.float64 and a.shape == (2, 2)
    assert a.tolist() == [[1.0, 2.5], [3.0, float(2**70)]]


def test_numbers_pass_through() -> None:
    x = np.array([1.0, 2.0])
    assert real_values(x, "x") is x
