"""Signal files: raw sample encoding and SigMF-layout recordings (conventions: Signal files)."""

from __future__ import annotations

import json
import math
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import ArrayLike, NDArray

from ._checks import real
from .core import Signal

SIGMF_VERSION = "1.2.0"
_DATATYPE = re.compile(r"([cr])(f64|f32|i32|i16|i8)(?:_(le|be))?")
_CODES = {"f64": "f8", "f32": "f4", "i32": "i4", "i16": "i2", "i8": "i1"}
_RESERVED = frozenset(
    {
        "core:datatype",
        "core:version",
        "core:sample_rate",
        "core:extensions",
        "core:num_channels",
        "core:dataset",
        "core:metadata_only",
    }
)
_EXTENSION = {"name": "signalforge", "version": "1.0.0", "optional": True}
MAX_DEPTH = 64
"""Deepest nesting of objects and arrays in a ``.sigmf-meta`` file; the top object is level 1."""
_INT64 = (-(2**63), 2**63 - 1)


def _parse(datatype: str) -> tuple[bool, np.dtype[Any], int]:
    """``(is_complex, element dtype in its byte order, integer bits or 0)``."""
    m = _DATATYPE.fullmatch(datatype) if isinstance(datatype, str) else None
    if m is None or (m[2] == "i8") != (m[3] is None):
        raise ValueError(f"unknown datatype {datatype!r}")
    order = {"le": "<", "be": ">", None: "|"}[m[3]]
    bits = int(m[2][1:]) if m[2][0] == "i" else 0
    return m[1] == "c", np.dtype(order + _CODES[m[2]]), bits


def encode_samples(x: ArrayLike, datatype: str) -> bytes:
    """The raw bytes of ``x`` as ``datatype`` (interleaved I/Q for complex types)."""
    is_complex, dt, bits = _parse(datatype)
    a = np.asarray(x)
    if a.ndim != 1 or a.dtype.kind not in "fiuc":
        raise ValueError("x must be a 1-D numeric array")
    if bool(np.iscomplexobj(a)) != is_complex:
        raise ValueError(f"{datatype} needs {'complex' if is_complex else 'real'} samples")
    parts = a.astype(np.complex128).view(np.float64) if is_complex else a.astype(np.float64)
    if not bits:
        with np.errstate(over="ignore"):
            return parts.astype(dt).tobytes()
    if not np.all(np.isfinite(parts)):
        raise ValueError(f"{datatype} cannot hold non-finite samples")
    codes = np.rint(parts * 2.0 ** (bits - 1))
    if codes.size and (codes.min() < -(2 ** (bits - 1)) or codes.max() > 2 ** (bits - 1) - 1):
        raise ValueError(f"a sample is outside the range of {datatype} (full scale is 1.0)")
    return codes.astype(dt).tobytes()


def decode_samples(
    data: bytes | bytearray | memoryview, datatype: str
) -> NDArray[np.complex128] | NDArray[np.float64]:
    """Samples from the raw bytes of ``datatype``, as ``float64`` or ``complex128``."""
    is_complex, dt, bits = _parse(datatype)
    if not isinstance(data, bytes | bytearray | memoryview):
        raise ValueError("data must be bytes")
    size = dt.itemsize * (2 if is_complex else 1)
    nbytes = memoryview(data).nbytes
    if nbytes % size:
        raise ValueError(f"{nbytes} bytes is not a whole number of {datatype} samples")
    parts = np.frombuffer(data, dtype=dt).astype(np.float64)
    if bits:
        parts /= 2.0 ** (bits - 1)
    if not is_complex:
        return parts
    z = np.empty(parts.size // 2, dtype=np.complex128)
    z.real, z.imag = parts[0::2], parts[1::2]
    return z


def _base(path: str | os.PathLike[str]) -> Path:
    p = Path(os.fspath(path))
    return p.with_suffix("") if p.suffix in (".sigmf-meta", ".sigmf-data") else p


def _files(path: str | os.PathLike[str]) -> tuple[Path, Path]:
    base = _base(path)
    return base.with_name(base.name + ".sigmf-meta"), base.with_name(base.name + ".sigmf-data")


def _text(s: str, where: str) -> str:
    try:
        s.encode("utf-8")
    except UnicodeEncodeError:
        raise ValueError(f"{where}: not valid Unicode (a lone surrogate)") from None
    return s


def _json(v: Any, where: str, depth: int = 1) -> Any:
    """``v`` as plain JSON data within the limits of conventions: Signal files, or ValueError.

    ``depth`` is the level an object or array ``v`` would sit at.
    """
    if isinstance(v, np.generic):
        v = v.item()
    if v is None or isinstance(v, bool):
        return v
    if isinstance(v, str):
        return _text(v, where)
    if isinstance(v, int):
        if not _INT64[0] <= v <= _INT64[1]:
            raise ValueError(f"{where}: integer outside the signed 64-bit range")
        return v
    if isinstance(v, float):
        if not math.isfinite(v):
            raise ValueError(f"{where}: JSON cannot hold {v}")
        return v
    if isinstance(v, list | tuple | Mapping) and depth > MAX_DEPTH:
        raise ValueError(f"{where}: nested deeper than {MAX_DEPTH} levels")
    if isinstance(v, list | tuple):
        return [_json(x, f"{where}[{i}]", depth + 1) for i, x in enumerate(v)]
    if isinstance(v, Mapping):
        if not all(isinstance(k, str) for k in v):
            raise ValueError(f"{where}: object keys must be strings")
        return {_text(k, where): _json(x, f"{where}.{k}", depth + 1) for k, x in v.items()}
    raise ValueError(f"{where}: {type(v).__name__} is not JSON data")


def _finite(v: float, what: str) -> float:
    return real(v, what)


def write_sigmf(path: str | os.PathLike[str], signal: Signal, datatype: str | None = None) -> None:
    """Write ``signal`` as ``<base>.sigmf-data`` and ``<base>.sigmf-meta``. ``datatype`` defaults
    to ``cf64_le`` or ``rf64_le``, which lose nothing."""
    if datatype is None:
        datatype = "cf64_le" if signal.is_complex else "rf64_le"
    data = encode_samples(signal.samples, datatype)
    glob: dict[str, Any] = {
        "core:datatype": datatype,
        "core:version": SIGMF_VERSION,
        "core:sample_rate": float(signal.sample_rate),
        "core:extensions": [dict(_EXTENSION)],
        "signalforge:time_origin": _finite(signal.time_origin, "time_origin"),
    }
    if signal.units is not None:
        if not isinstance(signal.units, str):
            raise ValueError("units must be a string")
        glob["signalforge:units"] = signal.units
    if signal.impedance is not None:
        glob["signalforge:impedance"] = float(signal.impedance)
    meta = _json(signal.metadata, "metadata", depth=-MAX_DEPTH)  # depth checked on doc below
    plain = {k: v for k, v in meta.items() if ":" not in k}
    if plain:
        glob["signalforge:metadata"] = plain
    for k, v in meta.items():
        if ":" in k:
            if k in _RESERVED or k.startswith("signalforge:"):
                raise ValueError(f"metadata key {k!r} is reserved")
            glob[k] = v
    capture = {
        "core:sample_start": 0,
        "core:frequency": _finite(signal.center_frequency, "center_frequency"),
    }
    doc = _json({"global": glob, "captures": [capture], "annotations": []}, "the metadata")
    text = json.dumps(doc, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    meta_path, data_path = _files(path)
    data_path.write_bytes(data)  # only once nothing above can fail
    meta_path.write_bytes(text.encode("utf-8"))


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(f"duplicate JSON key {k!r}")
        out[k] = v
    return out


def _no_constant(name: str) -> Any:
    raise ValueError(f"{name} is not JSON")


def _integer(v: Any, n: int) -> bool:
    """Whether ``v`` is the JSON integer ``n`` (not ``n.0``, not a bool)."""
    return type(v) is int and v == n


def _object(v: Any, what: str) -> dict[str, Any]:
    if not isinstance(v, dict):
        raise ValueError(f"{what} must be a JSON object")
    return v


def read_sigmf(path: str | os.PathLike[str]) -> Signal:
    """Read a ``.sigmf-meta`` / ``.sigmf-data`` pair as a :class:`Signal`."""
    meta_path, data_path = _files(path)
    try:
        parsed = json.loads(
            meta_path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique,
            parse_constant=_no_constant,
        )
    except RecursionError:
        raise ValueError(f"the metadata is nested deeper than {MAX_DEPTH} levels") from None
    doc = _object(_json(parsed, "the metadata"), "the metadata")
    glob = _object(doc.get("global"), "global")
    datatype = glob.get("core:datatype")
    if not isinstance(datatype, str):
        raise ValueError("core:datatype is required")
    version = glob.get("core:version")
    if not isinstance(version, str) or not version.startswith("1."):
        raise ValueError(f"unsupported core:version {version!r}")
    rate = _finite(glob.get("core:sample_rate"), "core:sample_rate")  # type: ignore[arg-type]
    if not _integer(glob.get("core:num_channels", 1), 1):
        raise ValueError("only single-channel recordings are supported")
    for k in ("core:dataset", "core:metadata_only"):
        if k in glob:
            raise ValueError(f"{k} recordings are not supported")
    captures = doc.get("captures", [])
    if not isinstance(captures, list):
        raise ValueError("captures must be a JSON array")
    freqs = set()
    for i, c in enumerate(captures):
        c = _object(c, f"captures[{i}]")
        if not _integer(c.get("core:header_bytes", 0), 0):
            raise ValueError("captures with header bytes are not supported")
        freqs.add(_finite(c.get("core:frequency", 0), f"captures[{i}] core:frequency"))
    if len(freqs) > 1:
        raise ValueError("captures at different frequencies are not supported")
    units = glob.get("signalforge:units")
    if units is not None and not isinstance(units, str):
        raise ValueError("signalforge:units must be a string")
    impedance = glob.get("signalforge:impedance")
    metadata = dict(_object(glob.get("signalforge:metadata", {}), "signalforge:metadata"))
    metadata.update(
        {k: v for k, v in glob.items() if k not in _RESERVED and not k.startswith("signalforge:")}
    )
    return Signal(
        decode_samples(data_path.read_bytes(), datatype),
        rate,
        center_frequency=freqs.pop() if freqs else 0.0,
        time_origin=_finite(glob.get("signalforge:time_origin", 0.0), "signalforge:time_origin"),
        units=units,
        impedance=None if impedance is None else _finite(impedance, "signalforge:impedance"),
        metadata=metadata,
    )
