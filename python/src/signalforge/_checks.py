"""Argument checks shared by the modules."""

from __future__ import annotations

import math
import numbers
import operator

import numpy as np


def count(value: int, what: str) -> int:
    """A non-negative integer argument; floats, even whole ones, are rejected."""
    try:
        n = operator.index(value)
    except TypeError:
        raise ValueError(f"{what} must be an integer") from None
    if n < 0:
        raise ValueError(f"{what} must be non-negative")
    return n


def real(value: float, what: str) -> float:
    """A finite real number (any ``numbers.Real`` but a bool) as a ``float``."""
    if (
        isinstance(value, bool | np.bool_)
        or not isinstance(value, numbers.Real)
        or not math.isfinite(value)
    ):
        raise ValueError(f"{what} must be a finite number")
    return float(value)
