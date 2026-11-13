import math
from collections.abc import Callable

import numpy as np
import pytest
from numpy.typing import ArrayLike

from signalforge import units


def test_round_trips() -> None:
    x = np.array([1e-9, 0.5, 1.0, 3.7, 1e6])
    np.testing.assert_allclose(units.db_to_lin(units.lin_to_db(x)), x, rtol=1e-14)
    np.testing.assert_allclose(units.db_to_amp(units.amp_to_db(x)), x, rtol=1e-14)
    np.testing.assert_allclose(units.dbm_to_w(units.w_to_dbm(x)), x, rtol=1e-14)
    np.testing.assert_allclose(units.dbm_to_vrms(units.vrms_to_dbm(x, 75), 75), x, rtol=1e-14)


def test_scalar_in_scalar_out() -> None:
    assert isinstance(units.lin_to_db(10), float)
    assert isinstance(units.lin_to_db([10, 100]), np.ndarray)


def test_amplitude_db_is_twice_power_db() -> None:
    assert units.amp_to_db(3.0) == pytest.approx(2 * units.lin_to_db(3.0))


@pytest.mark.parametrize("f", [units.lin_to_db, units.amp_to_db, units.w_to_dbm])
def test_negative_and_nan_raise(f: Callable[[ArrayLike], np.ndarray | float]) -> None:
    with pytest.raises(ValueError):
        f([1.0, -1.0])
    with pytest.raises(ValueError):
        f(math.nan)


def test_zero_is_minus_infinity_without_warning() -> None:
    with np.errstate(all="raise"):
        assert units.lin_to_db(0.0) == -math.inf


@pytest.mark.parametrize("r", [0, -50])
def test_bad_impedance(r: float) -> None:
    with pytest.raises(ValueError):
        units.vrms_to_dbm(1.0, r)
    with pytest.raises(ValueError):
        units.dbm_to_vrms(0.0, r)
