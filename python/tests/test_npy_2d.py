"""2-D NumPy .npy files (conventions: Signal files, NumPy .npy; ADR 0092)."""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pytest

from signalforge import read_npy, read_npy_2d, write_npy

RNG = np.random.default_rng(92)
SHAPES = [(1, 1), (2, 3), (3, 2), (0, 4), (5, 0), (17, 33), (1, 100), (100, 1)]


def _numpy_save(a: np.ndarray) -> bytes:
    buf = io.BytesIO()
    np.save(buf, a)
    return buf.getvalue()


@pytest.mark.parametrize("shape", SHAPES)
@pytest.mark.parametrize("kind", ["real", "complex"])
def test_same_bytes_as_numpy_save(tmp_path: Path, shape: tuple[int, int], kind: str) -> None:
    a = RNG.standard_normal(shape)
    if kind == "complex":
        a = a + 1j * RNG.standard_normal(shape)
    path = tmp_path / "x.npy"
    write_npy(path, a)
    assert path.read_bytes() == _numpy_save(a)
    got = read_npy_2d(path)
    assert got.dtype == a.dtype and got.shape == shape and np.array_equal(got, a)


@pytest.mark.parametrize("shape", SHAPES)
def test_reads_fortran_order_from_numpy(tmp_path: Path, shape: tuple[int, int]) -> None:
    a = np.asfortranarray(RNG.standard_normal(shape))
    path = tmp_path / "f.npy"
    np.save(path, a)
    got = read_npy_2d(path)
    assert np.array_equal(got, a)
    assert got.flags.c_contiguous


def test_fortran_layout_by_hand(tmp_path: Path) -> None:
    head = "{'descr': '<i2', 'fortran_order': True, 'shape': (2, 3), }"
    raw = b"\x93NUMPY\x01\x00" + bytes([len(head) + 1, 0]) + head.encode() + b"\n"
    path = tmp_path / "h.npy"
    path.write_bytes(raw + np.array([1, 4, 2, 5, 3, 6], "<i2").tobytes())  # column by column
    assert read_npy_2d(path).tolist() == [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]


@pytest.mark.parametrize("descr", ["<f4", ">f8", "<f2", ">c8", "<i4", ">u2", "|i1", "<u8"])
@pytest.mark.parametrize("fortran", [False, True])
def test_every_dtype_in_both_orders(tmp_path: Path, descr: str, fortran: bool) -> None:
    a = RNG.integers(-100, 100, (4, 3)) if descr[1] == "i" else RNG.integers(0, 200, (4, 3))
    a = a.astype(descr)
    path = tmp_path / "d.npy"
    np.save(path, np.asfortranarray(a) if fortran else a)
    got = read_npy_2d(path)
    want = a.astype(np.complex128 if a.dtype.kind == "c" else np.float64)
    assert got.dtype == want.dtype and np.array_equal(got, want)


def test_a_transposed_view_is_written_in_c_order(tmp_path: Path) -> None:
    a = np.arange(6.0).reshape(2, 3).T
    path = tmp_path / "t.npy"
    write_npy(path, a)
    assert np.load(path).flags.c_contiguous
    assert np.array_equal(read_npy_2d(path), a)


def test_each_reader_takes_only_its_own_dimensions(tmp_path: Path) -> None:
    one, two = tmp_path / "one.npy", tmp_path / "two.npy"
    write_npy(one, [1.0, 2.0])
    write_npy(two, [[1.0, 2.0]])
    with pytest.raises(ValueError, match="only 2-D"):
        read_npy_2d(one)
    with pytest.raises(ValueError, match="only 1-D"):
        read_npy(two)


@pytest.mark.parametrize(
    "shape", ["(2147483592, 0)", "(0, 2147483592)", "(2147483648, 0)", "(4294967296, 1)"]
)
def test_dimensions_beyond_the_limit_are_rejected(tmp_path: Path, shape: str) -> None:
    head = f"{{'descr': '<f8', 'fortran_order': False, 'shape': {shape}, }}"
    path = tmp_path / "big.npy"
    path.write_bytes(b"\x93NUMPY\x01\x00" + bytes([len(head) + 1, 0]) + head.encode() + b"\n")
    with pytest.raises(ValueError, match="beyond 2147483591"):
        read_npy_2d(path)


def test_largest_dimension_with_no_data(tmp_path: Path) -> None:
    path = tmp_path / "wide.npy"
    np.save(path, np.zeros((0, 2147483591)))
    assert read_npy_2d(path).shape == (0, 2147483591)
