"""NumPy .npy files (conventions: Signal files, NumPy .npy; ADR 0056)."""

from __future__ import annotations

import struct
from pathlib import Path

import numpy as np
import pytest

from signalforge import read_npy, write_npy

ARRAYS = [
    np.array([0.5, -0.25, 1e-300, np.nan, np.inf, -np.inf]),
    np.zeros(0),
    np.arange(12345.0),
    np.array([1 + 2j, complex(np.nan, -np.inf), -0.5j]),
    np.zeros(0, complex),
]


@pytest.mark.parametrize("x", ARRAYS)
def test_same_bytes_as_numpy_save(tmp_path: Path, x: np.ndarray) -> None:
    ours, theirs = tmp_path / "ours.npy", tmp_path / "theirs.npy"
    write_npy(ours, x)
    np.save(theirs, x)
    assert ours.read_bytes() == theirs.read_bytes()


@pytest.mark.parametrize("x", ARRAYS)
def test_round_trip_and_numpy_load(tmp_path: Path, x: np.ndarray) -> None:
    path = tmp_path / "x.npy"
    write_npy(path, x)
    got = read_npy(path)
    assert got.dtype == x.dtype
    np.testing.assert_array_equal(got, x)
    np.testing.assert_array_equal(np.load(path), x)


@pytest.mark.parametrize(
    ("x", "dtype"),
    [
        ([1, -2, 3], np.float64),
        (np.array([0.5, 2.0], np.float32), np.float64),
        (np.array([7], np.uint8), np.float64),
        (np.array([1 + 1j], np.complex64), np.complex128),
    ],
)
def test_other_numeric_types(tmp_path: Path, x: object, dtype: type) -> None:
    path = tmp_path / "x.npy"
    write_npy(path, x)  # type: ignore[arg-type]
    got = read_npy(path)
    assert got.dtype == dtype
    np.testing.assert_array_equal(got, np.asarray(x).astype(dtype))


@pytest.mark.parametrize("x", [np.zeros((2, 2)), np.float64(1.0), [True, False], ["a"], [None]])
def test_bad_writes_are_rejected(tmp_path: Path, x: object) -> None:
    path = tmp_path / "x.npy"
    with pytest.raises(ValueError):
        write_npy(path, x)  # type: ignore[arg-type]
    assert not path.exists()


def test_reads_numpy_save_of_a_view(tmp_path: Path) -> None:
    path = tmp_path / "x.npy"
    np.save(path, np.arange(10.0)[::3])
    np.testing.assert_array_equal(read_npy(path), [0.0, 3.0, 6.0, 9.0])


def test_numpy_big_endian_save_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "x.npy"
    np.save(path, np.arange(3.0).astype(">f8"))
    with pytest.raises(ValueError):
        read_npy(path)


def _file(tmp_path: Path, header: str) -> Path:
    raw = header.encode("ascii")
    path = tmp_path / "x.npy"
    path.write_bytes(b"\x93NUMPY\x01\x00" + struct.pack("<H", len(raw)) + raw + bytes(8))
    return path


@pytest.mark.parametrize(
    "header",
    [
        "{'descr':'<f8','fortran_order':False,'shape':(1,),}",
        "{ 'descr' : '<f8' , 'fortran_order' : False , 'shape' : ( 1 , ) }\n",
        "{'shape':(1,),'fortran_order':True,'descr':\"<f8\"}",
    ],
)
def test_header_spellings(tmp_path: Path, header: str) -> None:
    np.testing.assert_array_equal(read_npy(_file(tmp_path, header)), [0.0])


@pytest.mark.parametrize(
    "header",
    [
        "",
        "{",
        "{}",
        "{'descr':'<f8','fortran_order':False,'shape':(1,)",
        "{'descr':'<f8','fortran_order':False,'shape':(1 1,)}",
        "{'descr':'<f8','fortran_order':False,'shape':(,)}",
        "{'descr':'<f8','fortran_order':False,'shape':(1,,)}",
        "{'descr':'<f8','fortran_order':False,'shape':[1]}",
        "{'descr':'<f8','fortran_order':Falsey,'shape':(1,)}",
        "{'descr':'<f8','fortran_order':false,'shape':(1,)}",
        "{'descr':'<f8','fortran_order':None,'shape':(1,)}",
        "{'descr':'<f8','fortran_order':False,'shape':(1,)}}",
        "{'descr':'<f8'\"fortran_order\":False,'shape':(1,)}",
        "{'descr':'<f8\",'fortran_order':False,'shape':(1,)}",
        "{descr:'<f8','fortran_order':False,'shape':(1,)}",
        "{'descr':'<f8','fortran_order':False,'shape':(1,),'shape':(1,)}",
        "{'descr':'<f8','fortran_order':False,'shape':'(1,)'}",
        "{'descr':True,'fortran_order':False,'shape':(1,)}",
        "{'descr':'<f8','fortran_order':False,'shape':(1,)}\0",
        "{'descr':'<f8','fortran_order':False,'shape':(" + chr(0x661) + ",)}",  # Arabic-Indic 1
    ],
)
def test_bad_headers(tmp_path: Path, header: str) -> None:
    raw = header.encode("utf-8")
    path = tmp_path / "x.npy"
    path.write_bytes(b"\x93NUMPY\x03\x00" + struct.pack("<I", len(raw)) + raw + bytes(8))
    with pytest.raises(ValueError):
        read_npy(path)


def test_huge_shape_is_rejected(tmp_path: Path) -> None:
    header = "{'descr':'<f8','fortran_order':False,'shape':(99999999999999999999999,)}"
    with pytest.raises(ValueError):
        read_npy(_file(tmp_path, header))


def test_missing_file_is_an_os_error(tmp_path: Path) -> None:
    with pytest.raises(OSError):
        read_npy(tmp_path / "missing.npy")
