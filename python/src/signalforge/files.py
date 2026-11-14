"""Signal files: raw sample encoding, SigMF-layout recordings, WAV and NumPy .npy files
(conventions: Signal files)."""

from __future__ import annotations

import json
import math
import os
import re
import struct
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import ArrayLike, NDArray

from ._checks import real
from .core import Signal

SIGMF_VERSION = "1.2.0"
_DATATYPE = re.compile(r"([cr])(f64|f32|[iu]32|[iu]16|[iu]8)(?:_(le|be))?")
_CODES = {
    "f64": "f8",
    "f32": "f4",
    "i32": "i4",
    "i16": "i2",
    "i8": "i1",
    "u32": "u4",
    "u16": "u2",
    "u8": "u1",
}
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
    if m is None or (m[2][1:] == "8") != (m[3] is None):
        raise ValueError(f"unknown datatype {datatype!r}")
    order = {"le": "<", "be": ">", None: "|"}[m[3]]
    bits = int(m[2][1:]) if m[2][0] in "iu" else 0
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
    if dt.kind == "u":  # offset binary
        codes += 2.0 ** (bits - 1)
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
    if dt.kind == "u":  # offset binary
        parts -= 2.0 ** (bits - 1)
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


_WAV_BITS = {"u8": 8, "i16": 16, "i24": 24, "i32": 32, "f32": 32, "f64": 64}
_WAV_FORMATS = {1: {8: "u8", 16: "i16", 24: "i24", 32: "i32"}, 3: {32: "f32", 64: "f64"}}
_GUID_TAIL = bytes.fromhex("000000001000800000aa00389b71")
_U32 = 2**32 - 1


def _chunk(cid: bytes, body: bytes) -> bytes:
    return cid + struct.pack("<I", len(body)) + body + b"\0" * (len(body) % 2)


def _wav_encode(x: NDArray[np.float64], fmt: str) -> bytes:
    if fmt == "f32":
        with np.errstate(over="ignore"):
            return x.astype("<f4").tobytes()
    if fmt == "f64":
        return x.astype("<f8").tobytes()
    bits = _WAV_BITS[fmt]
    if not np.all(np.isfinite(x)):
        raise ValueError(f"{fmt} cannot hold non-finite samples")
    codes = np.rint(x * 2.0 ** (bits - 1))
    if codes.size and (codes.min() < -(2 ** (bits - 1)) or codes.max() > 2 ** (bits - 1) - 1):
        raise ValueError(f"a sample is outside the range of {fmt} (full scale is 1.0)")
    if fmt == "u8":
        return (codes + 128).astype(np.uint8).tobytes()
    if fmt == "i24":
        return codes.astype("<i4").view(np.uint8).reshape(-1, 4)[:, :3].tobytes()
    return codes.astype("<i2" if fmt == "i16" else "<i4").tobytes()


def write_wav(
    path: str | os.PathLike[str], channels: Signal | Sequence[Signal], sample_format: str = "f32"
) -> None:
    """Write real signals, one per channel, as a PCM or IEEE float WAV file (conventions: Signal
    files, WAV). Only the samples and the sample rate are stored."""
    if not isinstance(sample_format, str) or sample_format not in _WAV_BITS:
        raise ValueError(f"unknown WAV sample format {sample_format!r}")
    sigs = [channels] if isinstance(channels, Signal) else list(channels)
    if not sigs or not all(isinstance(s, Signal) for s in sigs):
        raise ValueError("channels must be one signal or a non-empty list of them")
    if any(s.is_complex for s in sigs):
        raise ValueError("WAV channels must be real signals")
    rate, n = sigs[0].sample_rate, len(sigs[0])
    if any(s.sample_rate != rate or len(s) != n for s in sigs):
        raise ValueError("every channel must have the same sample rate and length")
    if not (float(rate).is_integer() and rate <= _U32):
        raise ValueError("sample_rate must be a whole number of hertz below 2^32")
    bits, is_float = _WAV_BITS[sample_format], sample_format[0] == "f"
    block = len(sigs) * bits // 8
    if block > 0xFFFF:
        raise ValueError("too many channels: the block align must fit 16 bits")
    if int(rate) * block > _U32:
        raise ValueError("the byte rate (sample rate x block align) must fit 32 bits")
    nbytes = n * block
    if 4 + (26 + 12 if is_float else 24) + 8 + nbytes + nbytes % 2 > _U32:
        raise ValueError("too many samples for a WAV file")
    x = np.stack([s.samples.astype(np.float64) for s in sigs], axis=1).reshape(-1)
    data = _wav_encode(x, sample_format)
    fmt = struct.pack(
        "<HHIIHH", 3 if is_float else 1, len(sigs), int(rate), int(rate) * block, block, bits
    )
    if is_float:
        body = _chunk(b"fmt ", fmt + bytes(2)) + _chunk(b"fact", struct.pack("<I", n))
    else:
        body = _chunk(b"fmt ", fmt)
    body = b"WAVE" + body + _chunk(b"data", data)
    Path(os.fspath(path)).write_bytes(b"RIFF" + struct.pack("<I", len(body)) + body)


def _wav_decode(data: bytes, fmt: str) -> NDArray[np.float64]:
    if fmt == "u8":
        return (np.frombuffer(data, np.uint8).astype(np.float64) - 128) / 128
    if fmt == "i24":
        b = np.frombuffer(data, np.uint8).reshape(-1, 3).astype(np.int64)
        v = b[:, 0] | b[:, 1] << 8 | b[:, 2] << 16
        return (v - (v >> 23 << 24)).astype(np.float64) / 2.0**23
    codes = {"i16": "<i2", "i32": "<i4", "f32": "<f4", "f64": "<f8"}[fmt]
    x = np.frombuffer(data, codes).astype(np.float64)
    return x / 2.0 ** (_WAV_BITS[fmt] - 1) if fmt[0] == "i" else x


def read_wav(path: str | os.PathLike[str]) -> list[Signal]:
    """Read a PCM or IEEE float WAV file as real signals, one per channel, in units ``"FS"``."""
    raw = Path(os.fspath(path)).read_bytes()
    if len(raw) < 12 or raw[:4] != b"RIFF" or raw[8:12] != b"WAVE":
        raise ValueError("not a RIFF WAVE file")
    pos, fmt = 12, None
    while True:
        if pos + 8 > len(raw):
            raise ValueError("no data chunk" if fmt is not None else "no fmt chunk")
        cid, (size,) = raw[pos : pos + 4], struct.unpack("<I", raw[pos + 4 : pos + 8])
        start, end = pos + 8, pos + 8 + size
        if end > len(raw):
            raise ValueError(f"the {cid.decode('latin-1')!r} chunk runs past the end of the file")
        if cid == b"data":
            if fmt is None:
                raise ValueError("the fmt chunk must come before the data chunk")
            data = raw[start:end]
            break
        if cid == b"fmt " and fmt is None:
            fmt = raw[start:end]
        pos = end + size % 2
    if len(fmt) < 16:
        raise ValueError("the fmt chunk is shorter than 16 bytes")
    tag, nch, rate, _, block, bits = struct.unpack("<HHIIHH", fmt[:16])
    if tag == 0xFFFE:
        if len(fmt) < 40:
            raise ValueError("an extensible fmt chunk needs at least 40 bytes")
        guid = fmt[24:40]
        if guid[2:] != _GUID_TAIL or guid[:2] not in (b"\x01\x00", b"\x03\x00"):
            raise ValueError("the extensible sub-format is not PCM or IEEE float")
        tag = guid[0]
    if tag not in _WAV_FORMATS:
        raise ValueError(f"WAV format {tag} is not PCM or IEEE float")
    if bits not in _WAV_FORMATS[tag]:
        raise ValueError(f"{bits}-bit {'PCM' if tag == 1 else 'float'} is not supported")
    if nch < 1 or rate < 1:
        raise ValueError("a WAV file needs at least one channel and a sample rate of at least 1")
    if block != nch * bits // 8:
        raise ValueError(f"block align {block} does not match {nch} channels of {bits} bits")
    if len(data) % block:
        raise ValueError(f"{len(data)} data bytes is not a whole number of {block}-byte frames")
    x = _wav_decode(data, _WAV_FORMATS[tag][bits])
    return [Signal(x[c::nch], float(rate), units="FS") for c in range(nch)]


_NPY_MAGIC = b"\x93NUMPY"
_NPY_DESCR = {"<f8": np.dtype("<f8"), "<c16": np.dtype("<c16")}
_NPY_KEYS = frozenset({"descr", "fortran_order", "shape"})


def write_npy(path: str | os.PathLike[str], x: ArrayLike) -> None:
    """Write a 1-D array as a NumPy ``.npy`` file: ``'<f8'`` for real values, ``'<c16'`` for
    complex, in the layout ``numpy.save`` writes (conventions: Signal files, NumPy .npy)."""
    a = np.asarray(x)
    if a.ndim != 1 or a.dtype.kind not in "fiuc":
        raise ValueError("x must be a 1-D numeric array")
    descr = "<c16" if a.dtype.kind == "c" else "<f8"
    text = f"{{'descr': '{descr}', 'fortran_order': False, 'shape': ({a.size},), }}"
    head = (text.ljust(117) + "\n").encode("ascii")
    data = a.astype(_NPY_DESCR[descr]).tobytes()
    Path(os.fspath(path)).write_bytes(
        _NPY_MAGIC + b"\x01\x00" + struct.pack("<H", 118) + head + data
    )


class _NpyHeader:
    """The header grammar of conventions: Signal files, NumPy .npy. The text is never evaluated."""

    def __init__(self, text: str) -> None:
        self.s, self.i = text, 0

    def fail(self) -> ValueError:
        return ValueError(f"the .npy header is not a dict this reader accepts (at {self.i})")

    def peek(self) -> str:
        while self.i < len(self.s) and self.s[self.i] in " \t\r\n":
            self.i += 1
        return self.s[self.i] if self.i < len(self.s) else ""

    def take(self, c: str) -> None:
        if self.peek() != c:
            raise self.fail()
        self.i += 1

    def string(self) -> str:
        q = self.peek()
        j = self.s.find(q, self.i + 1) if q in ("'", '"') else -1
        if j < 0 or "\\" in self.s[self.i + 1 : j]:
            raise self.fail()
        v, self.i = self.s[self.i + 1 : j], j + 1
        return v

    def integer(self) -> int:
        self.peek()
        j = self.i
        while j < len(self.s) and self.s[j] in "0123456789":
            j += 1
        t = self.s[self.i : j]
        if not t or (len(t) > 1 and t[0] == "0"):
            raise self.fail()
        self.i = j
        return int(t)

    def value(self) -> str | bool | tuple[int, ...]:
        c = self.peek()
        if c in ("'", '"'):
            return self.string()
        if c == "(":
            self.i += 1
            items, trailing = [], False
            while self.peek() != ")":
                items.append(self.integer())
                trailing = self.peek() == ","
                if trailing:
                    self.i += 1
                elif self.peek() != ")":
                    raise self.fail()
            self.i += 1
            if len(items) == 1 and not trailing:
                raise self.fail()
            return tuple(items)
        for word in ("True", "False"):
            if self.s.startswith(word, self.i):
                self.i += len(word)
                return word == "True"
        raise self.fail()

    def parse(self) -> dict[str, str | bool | tuple[int, ...]]:
        d: dict[str, str | bool | tuple[int, ...]] = {}
        self.take("{")
        while self.peek() != "}":
            key = self.string()
            self.take(":")
            if key in d:
                raise ValueError(f"the .npy header has {key!r} twice")
            d[key] = self.value()
            if self.peek() == ",":
                self.i += 1
            elif self.peek() != "}":
                raise self.fail()
        self.i += 1
        if self.peek():
            raise self.fail()
        return d


def read_npy(path: str | os.PathLike[str]) -> NDArray[np.float64] | NDArray[np.complex128]:
    """Read a 1-D ``'<f8'`` or ``'<c16'`` NumPy ``.npy`` file (versions 1.0 to 3.0) as ``float64``
    or ``complex128``."""
    raw = Path(os.fspath(path)).read_bytes()
    if len(raw) < 8 or raw[:6] != _NPY_MAGIC:
        raise ValueError("not a .npy file")
    version = (raw[6], raw[7])
    if version not in ((1, 0), (2, 0), (3, 0)):
        raise ValueError(f".npy version {version[0]}.{version[1]} is not supported")
    width = 2 if version == (1, 0) else 4
    if len(raw) < 8 + width:
        raise ValueError("the .npy file ends inside its header length")
    (size,) = struct.unpack("<H" if width == 2 else "<I", raw[8 : 8 + width])
    start = 8 + width + size
    if start > len(raw):
        raise ValueError("the .npy header runs past the end of the file")
    head = raw[8 + width : start]
    if any(b > 127 for b in head):
        raise ValueError("the .npy header must be ASCII")
    d = _NpyHeader(head.decode("ascii")).parse()
    if d.keys() != _NPY_KEYS:
        raise ValueError("the .npy header needs exactly descr, fortran_order and shape")
    descr, order, shape = d["descr"], d["fortran_order"], d["shape"]
    if not isinstance(descr, str) or descr not in _NPY_DESCR:
        raise ValueError(f"only '<f8' and '<c16' arrays are read, not {descr!r}")
    if not isinstance(order, bool):
        raise ValueError("fortran_order must be True or False")
    if not isinstance(shape, tuple) or len(shape) != 1:
        raise ValueError(f"only 1-D arrays are read, not shape {shape!r}")
    dt = _NPY_DESCR[descr]
    if len(raw) - start != shape[0] * dt.itemsize:
        raise ValueError(f"{len(raw) - start} data bytes do not match shape ({shape[0]},)")
    values = np.frombuffer(raw, dt, offset=start)
    if descr == "<c16":
        return values.astype(np.complex128)
    return values.astype(np.float64)
