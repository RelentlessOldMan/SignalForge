"""Argument checks shared by the modules."""

from __future__ import annotations

import math
import numbers
import operator
from typing import Any

import numpy as np
from numpy.typing import NDArray


def count(value: int, what: str) -> int:
    """A non-negative integer argument; floats, even whole ones, and bools are rejected."""
    if isinstance(value, bool | np.bool_):
        raise ValueError(f"{what} must be an integer")
    try:
        n = operator.index(value)
    except TypeError:
        raise ValueError(f"{what} must be an integer") from None
    if n < 0:
        raise ValueError(f"{what} must be non-negative")
    return n


def real(value: float, what: str) -> float:
    """A finite real number (any ``numbers.Real`` but a bool) as a ``float``."""
    if isinstance(value, bool | np.bool_) or not isinstance(value, numbers.Real):
        raise ValueError(f"{what} must be a finite number")
    try:
        f = float(value)
    except OverflowError:  # an int too large for a float
        raise ValueError(f"{what} must be a finite number") from None
    if not math.isfinite(f):
        raise ValueError(f"{what} must be a finite number")
    return f


def real_values(a: NDArray[Any], what: str) -> NDArray[np.float64]:
    """An array of real numbers as float64 (ADR 0621): integer, unsigned and floating dtypes
    pass, as do object arrays of ``numbers.Real`` values (not bools) that fit in a double;
    bools, strings, bytes, dates, times and anything else are rejected."""
    kind = a.dtype.kind
    if kind in "iuf":
        return a.astype(np.float64, copy=False)
    if kind != "O":
        raise ValueError(f"{what} must be real numbers")
    out = np.empty(a.shape, np.float64)
    flat = out.reshape(-1)
    for i, v in enumerate(a.flat):
        if isinstance(v, bool | np.bool_) or not isinstance(v, numbers.Real):
            raise ValueError(f"{what} must be real numbers")
        try:
            flat[i] = float(v)
        except OverflowError:  # an int too large for a float
            raise ValueError(f"{what} must be real numbers that fit in a double") from None
    return out


def sample_values(a: NDArray[Any], what: str) -> NDArray[Any]:
    """An array of samples, real or complex (ADR 0622): floating and complex dtypes pass as
    they are, integer and unsigned dtypes become float64, and object arrays of
    ``numbers.Number`` values (not bools) that fit in a double become float64, or complex128
    when one is complex; bools, strings, bytes, dates, times and anything else are rejected."""
    kind = a.dtype.kind
    if kind in "fc":
        return a
    if kind in "iu":
        return a.astype(np.float64)
    if kind != "O":
        raise ValueError(f"{what} must be numbers")
    values = list(a.flat)
    for v in values:
        if isinstance(v, bool | np.bool_) or not isinstance(v, numbers.Number):
            raise ValueError(f"{what} must be numbers")
    is_complex = any(not isinstance(v, numbers.Real) for v in values)
    try:
        out = np.array(
            [complex(v) if is_complex else float(v) for v in values],
            dtype=np.complex128 if is_complex else np.float64,
        )
    except (OverflowError, TypeError):  # an int too large, or a Number with no conversion
        raise ValueError(f"{what} must be numbers that fit in a double") from None
    return out.reshape(a.shape)
