"""2-D members of NumPy .npz archives (conventions: Signal files, NumPy .npz; ADR 0093)."""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pytest

from signalforge import read_npz, write_npz

RNG = np.random.default_rng(93)


def _mixed() -> dict[str, np.ndarray]:
    return {
        "taps": RNG.standard_normal(5),
        "bank": RNG.standard_normal((3, 4)),
        "iq": RNG.standard_normal((2, 6)) + 1j * RNG.standard_normal((2, 6)),
        "none": np.zeros((0, 3)),
        "thin": np.zeros((4, 0)),
    }


def test_round_trip_keeps_each_members_dimensions(tmp_path: Path) -> None:
    arrays = _mixed()
    path = tmp_path / "m.npz"
    write_npz(path, arrays)
    got = read_npz(path)
    assert list(got) == list(arrays)
    for k, a in arrays.items():
        assert got[k].shape == a.shape and got[k].dtype == a.dtype and np.array_equal(got[k], a)


def test_numpy_load_reads_what_we_write(tmp_path: Path) -> None:
    arrays = _mixed()
    path = tmp_path / "m.npz"
    write_npz(path, arrays)
    with np.load(path) as z:
        assert z.files == list(arrays)
        for k, a in arrays.items():
            assert z[k].shape == a.shape and np.array_equal(z[k], a)


def test_members_are_what_write_npy_writes(tmp_path: Path) -> None:
    a = RNG.standard_normal((3, 2)).T  # a transposed view: written in C order all the same
    path = tmp_path / "v.npz"
    write_npz(path, {"a": a})
    buf = io.BytesIO()
    np.save(buf, np.ascontiguousarray(a))
    assert buf.getvalue() in path.read_bytes()


@pytest.mark.parametrize("save", [np.savez, np.savez_compressed])
@pytest.mark.parametrize("fortran", [False, True])
def test_reads_numpy_savez(tmp_path: Path, save: object, fortran: bool) -> None:
    arrays = _mixed()
    if fortran:
        arrays = {k: np.asfortranarray(a) for k, a in arrays.items()}
    path = tmp_path / "s.npz"
    save(path, **arrays)  # type: ignore[operator]
    got = read_npz(path)
    for k, a in arrays.items():
        assert got[k].shape == a.shape and np.array_equal(got[k], a)
        assert got[k].flags.c_contiguous


@pytest.mark.parametrize("bad", [np.zeros(()), np.zeros((1, 2, 2)), np.zeros((1, 1, 1, 1))])
def test_other_dimensions_are_rejected(tmp_path: Path, bad: np.ndarray) -> None:
    with pytest.raises(ValueError, match="1-D or 2-D"):
        write_npz(tmp_path / "w.npz", {"x": bad})
    path = tmp_path / "r.npz"
    np.savez(path, ok=np.zeros(2), x=bad)
    with pytest.raises(ValueError, match="only 1-D and 2-D"):
        read_npz(path)


def test_a_dimension_beyond_the_limit_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "w.npz"
    np.savez(path, w=np.zeros((0, 2147483592)))
    with pytest.raises(ValueError, match="beyond 2147483591"):
        read_npz(path)
