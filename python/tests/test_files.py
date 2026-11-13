"""Signal files: round trips, metadata mapping, write errors (conventions: Signal files)."""

import json
from pathlib import Path

import numpy as np
import pytest

import signalforge as sf

TYPES = [f"{k}{t}_{o}" for k in "cr" for t in ("f64", "f32", "i32", "i16") for o in ("le", "be")]
TYPES += ["ci8", "ri8"]


@pytest.mark.parametrize("datatype", TYPES)
def test_round_trip_every_datatype(tmp_path: Path, datatype: str) -> None:
    rng = np.random.default_rng(1)
    x = rng.uniform(-0.99, 0.99, 64)
    if datatype[0] == "c":
        x = x + 1j * rng.uniform(-0.99, 0.99, 64)
    sf.write_sigmf(tmp_path / "r", sf.Signal(x, 1e3), datatype)
    y = sf.read_sigmf(tmp_path / "r").samples
    step = {"f64": 0.0, "f32": 2.0**-24, "i32": 2.0**-31, "i16": 2.0**-15, "i8": 2.0**-7}
    assert np.iscomplexobj(y) == np.iscomplexobj(x)
    assert np.max(np.abs(y - x)) <= step[datatype[1:4].rstrip("_")]
    assert (tmp_path / "r.sigmf-data").stat().st_size == len(sf.encode_samples(x, datatype))


def test_fields_and_metadata_round_trip(tmp_path: Path) -> None:
    s = sf.Signal(
        np.array([1 + 1j, -0.5j]),
        2.5e6,
        center_frequency=915e6,
        time_origin=-1.25,
        units="V",
        impedance=50.0,
        metadata={"core:author": "me", "run": 3, "gains": [1, 2.5], "nested": {"a": None}},
    )
    sf.write_sigmf(tmp_path / "x.sigmf-meta", s)
    r = sf.read_sigmf(tmp_path / "x.sigmf-data")
    assert np.array_equal(r.samples, s.samples)
    assert (r.sample_rate, r.center_frequency, r.time_origin) == (2.5e6, 915e6, -1.25)
    assert (r.units, r.impedance) == ("V", 50.0)
    assert dict(r.metadata) == dict(s.metadata)
    glob = json.loads((tmp_path / "x.sigmf-meta").read_text(encoding="utf-8"))["global"]
    assert glob["core:datatype"] == "cf64_le" and glob["core:author"] == "me"
    assert glob["signalforge:metadata"] == {"run": 3, "gains": [1, 2.5], "nested": {"a": None}}


def test_default_datatype_is_lossless_real(tmp_path: Path) -> None:
    sf.write_sigmf(tmp_path / "x", sf.Signal(np.array([0.1, 0.2]), 1.0))
    meta = json.loads((tmp_path / "x.sigmf-meta").read_text(encoding="utf-8"))
    assert meta["global"]["core:datatype"] == "rf64_le"
    assert "signalforge:units" not in meta["global"]


def test_empty_signal(tmp_path: Path) -> None:
    sf.write_sigmf(tmp_path / "e", sf.Signal(np.array([], dtype=complex), 1.0), "ci16_le")
    r = sf.read_sigmf(tmp_path / "e")
    assert len(r) == 0 and r.is_complex


def test_numpy_metadata_values_are_plain_json(tmp_path: Path) -> None:
    s = sf.Signal(np.zeros(2), 1.0, metadata={"n": np.int64(4), "g": np.float32(0.5)})
    sf.write_sigmf(tmp_path / "n", s)
    assert dict(sf.read_sigmf(tmp_path / "n").metadata) == {"n": 4, "g": 0.5}


@pytest.mark.parametrize(
    ("kwargs", "datatype"),
    [
        ({"metadata": {"core:sample_rate": 2}}, None),
        ({"metadata": {"signalforge:x": 1}}, None),
        ({"metadata": {"bad": object()}}, None),
        ({"metadata": {"bad": float("nan")}}, None),
        ({"metadata": {"bad": {1: 2}}}, None),
        ({"center_frequency": float("inf")}, None),
        ({"time_origin": float("nan")}, None),
        ({}, "cf32_le"),
        ({}, "nope"),
    ],
)
def test_write_errors(tmp_path: Path, kwargs: dict[str, object], datatype: str | None) -> None:
    s = sf.Signal(np.array([0.5]), 1.0, **kwargs)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        sf.write_sigmf(tmp_path / "w", s, datatype)


def test_decode_rejects_non_bytes() -> None:
    with pytest.raises(ValueError):
        sf.decode_samples("0000", "ri16_le")  # type: ignore[arg-type]


def test_encode_rejects_bad_shapes_and_kinds() -> None:
    for x in ([[0.5]], [True], ["a"]):
        with pytest.raises(ValueError):
            sf.encode_samples(x, "rf64_le")


def test_missing_file_is_an_os_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        sf.read_sigmf(tmp_path / "absent")
