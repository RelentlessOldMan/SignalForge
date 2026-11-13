"""Argument checks shared by the modules."""

from __future__ import annotations

import math
import numbers
import operator

import numpy as np


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
