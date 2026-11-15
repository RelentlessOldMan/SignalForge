"""NumPy .npz archives (conventions: Signal files, NumPy .npz; ADR 0089)."""

from __future__ import annotations

import struct
import zipfile
import zlib
from pathlib import Path

import numpy as np
import pytest

from signalforge import read_npz, write_npz


def arrays() -> dict[str, np.ndarray]:
    return {
        "taps": np.array([0.5, -0.25, np.nan, np.inf]),
        "iq": np.array([1 + 2j, complex(-np.inf, 0.0), -0.5j]),
        "empty": np.zeros(0),
        "big": np.arange(100000.0),
    }


def assert_same(got: dict[str, np.ndarray], want: dict[str, np.ndarray]) -> None:
    assert list(got) == list(want)
    for k in want:
        assert got[k].dtype == np.asarray(want[k]).astype(got[k].dtype).dtype
        np.testing.assert_array_equal(got[k], want[k])


def test_round_trip_keeps_order(tmp_path: Path) -> None:
    path = tmp_path / "a.npz"
    write_npz(path, arrays())
    assert_same(read_npz(path), arrays())


def test_numpy_load_reads_what_we_write(tmp_path: Path) -> None:
    path = tmp_path / "a.npz"
    write_npz(path, arrays())
    with np.load(path) as z:
        assert_same({k: z[k] for k in z.files}, arrays())
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        assert all(i.compress_type == zipfile.ZIP_STORED for i in z.infolist())


@pytest.mark.parametrize("save", [np.savez, np.savez_compressed])
def test_reads_numpy_savez(tmp_path: Path, save: object) -> None:
    path = tmp_path / "a.npz"
    save(path, **arrays())  # type: ignore[operator]
    assert_same(read_npz(path), arrays())


def test_reads_narrow_numpy_members(tmp_path: Path) -> None:
    path = tmp_path / "a.npz"
    f = np.array([0.5, -1.5], ">f4")
    z = np.array([1 - 2j], "<c8")
    h = np.array([65504.0, 2.0**-24], "<f2")
    np.savez_compressed(path, f=f, z=z, h=h)
    got = read_npz(path)
    np.testing.assert_array_equal(got["f"], f.astype(np.float64))
    np.testing.assert_array_equal(got["z"], z.astype(np.complex128))
    np.testing.assert_array_equal(got["h"], h.astype(np.float64))


def test_empty_archive(tmp_path: Path) -> None:
    path = tmp_path / "a.npz"
    write_npz(path, {})
    assert path.stat().st_size == 22
    assert read_npz(path) == {}
    with np.load(path) as z:
        assert z.files == []


@pytest.mark.parametrize("name", ["", "a/b", "a\\b", "é", "n" * 251, "tab\there", "nul\0", "\x7f"])
def test_bad_names_are_rejected(tmp_path: Path, name: str) -> None:
    with pytest.raises(ValueError):
        write_npz(tmp_path / "a.npz", {name: [1.0]})


def test_bad_arrays_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        write_npz(tmp_path / "a.npz", {"x": [[[1.0, 2.0]]]})
    with pytest.raises(ValueError):
        write_npz(tmp_path / "a.npz", [("x", [1.0])])  # type: ignore[arg-type]


def test_extra_bytes_before_the_archive_are_read_at_their_offsets(tmp_path: Path) -> None:
    # Offsets are absolute; a prefix shifts them, so the archive no longer parses.
    path = tmp_path / "a.npz"
    write_npz(path, {"x": [1.0]})
    path.write_bytes(b"junk" + path.read_bytes())
    with pytest.raises(ValueError):
        read_npz(path)


def test_each_flipped_crc_bit_is_caught(tmp_path: Path) -> None:
    path = tmp_path / "a.npz"
    write_npz(path, {"x": [1.0, 2.0]})
    good = path.read_bytes()
    at = good.index(b"PK\x01\x02") + 16
    crc = struct.unpack_from("<I", good, at)[0]
    assert crc == zlib.crc32(good[good.index(b"\x93NUMPY") : good.index(b"PK\x01\x02")])
    for bit in range(32):
        bad = bytearray(good)
        struct.pack_into("<I", bad, at, crc ^ (1 << bit))
        path.write_bytes(bytes(bad))
        with pytest.raises(ValueError, match="CRC"):
            read_npz(path)
