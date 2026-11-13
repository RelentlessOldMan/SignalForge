"""Argument checks shared by the modules."""

from __future__ import annotations

import operator


def count(value: int, what: str) -> int:
    """A non-negative integer argument; floats, even whole ones, are rejected."""
    try:
        n = operator.index(value)
    except TypeError:
        raise ValueError(f"{what} must be an integer") from None
    if n < 0:
        raise ValueError(f"{what} must be non-negative")
    return n
