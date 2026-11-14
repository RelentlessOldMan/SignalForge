"""Writes vectors/cases/files.json and the recordings in vectors/files/, using only the standard library.

It does not import NumPy or SignalForge. Bytes come from the struct module; integer codes from
round() (half to even) of x * 2^(b-1), plus 2^(b-1) for unsigned (offset binary, ADR 0058);
float32 values from a struct round trip. The recordings'
metadata is written here as literal JSON, some of it laid out the way another tool would.

Run from the repo root: python vectors/generators/files.py [--check]
With --check it writes nothing and exits 1 unless every file matches what it would write.
"""

import json
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOL = {"abs": 0, "rel": 0}
FMT = {"f64": "d", "f32": "f", "i32": "i", "i16": "h", "i8": "b", "u32": "I", "u16": "H", "u8": "B"}


def parts(x):
    out = []
    for v in x:
        out += [v.real, v.imag] if isinstance(v, complex) else [v]
    return out


def stored(v, t):
    """The value as the type holds it: the integer code, or the float after rounding."""
    if t[0] in "iu":
        half = 2 ** (int(t[1:]) - 1)
        return round(v * half) + (half if t[0] == "u" else 0)
    return struct.unpack("<f", struct.pack("<f", v))[0] if t == "f32" else v


def pack(x, datatype):
    t, order = datatype[1:].split("_") if "_" in datatype else (datatype[1:], "le")
    end = "<" if order == "le" else ">"
    return b"".join(struct.pack(end + FMT[t], stored(v, t)) for v in parts(x))


def back(x, datatype):
    """What decoding the packed bytes gives."""
    t = datatype[1:].split("_")[0]
    vals = []
    for v in parts(x):
        if t[0] in "iu":
            half = 2 ** (int(t[1:]) - 1)
            vals.append((stored(v, t) - (half if t[0] == "u" else 0)) / half)
        else:
            vals.append(stored(v, t))
    if datatype[0] == "r":
        return vals
    return {"re": vals[0::2], "im": vals[1::2]}


def arg(x):
    if x and isinstance(x[0], complex):
        return {"re": [v.real for v in x], "im": [v.imag for v in x]}
    return x


REAL = [0.5, -0.25, 0.123456789, -1.0, 0.0, 2.0**-7]
CPLX = [0.5 - 0.25j, 0.123456789 + 1e-3j, -1.0 + 0j]
SRC_ENC = ("struct.pack of each part (integers: round(x * 2^(b-1)), half to even; unsigned "
           "adds 2^(b-1))")
SRC_DEC = ("struct round trip of the same values; integer codes (less 2^(b-1) for unsigned) "
           "divided by 2^(b-1)")

cases = []
for kind, x in (("r", REAL), ("c", CPLX)):
    for t in ("f64", "f32", "i32", "i16", "i8", "u32", "u16", "u8"):
        for order in ("le", "be") if t[1:] != "8" else ("",):
            dt = f"{kind}{t}_{order}" if order else f"{kind}{t}"
            h = pack(x, dt).hex()
            cases.append({"id": f"encode_samples.{dt}", "op": "encode_samples",
                          "args": {"x": arg(x), "datatype": dt}, "expected": h, "tol": TOL,
                          "source": SRC_ENC})
            cases.append({"id": f"decode_samples.{dt}", "op": "decode_samples",
                          "args": {"data": h, "datatype": dt}, "expected": back(x, dt),
                          "tol": TOL, "source": SRC_DEC})

ties = [2.5 / 128, 3.5 / 128, -2.5 / 128, -0.5 / 128]
cases += [
    {"id": "encode_samples.ri8_ties_to_even", "op": "encode_samples",
     "args": {"x": ties, "datatype": "ri8"}, "expected": "0204fe00", "tol": TOL,
     "source": "by hand: codes 2.5, 3.5, -2.5, -0.5 round half to even to 2, 4, -2, 0"},
    {"id": "encode_samples.ri8_negative_tie", "op": "encode_samples",
     "args": {"x": [-2.5 / 128], "datatype": "ri8"}, "expected": "fe", "tol": TOL,
     "source": "by hand: -2.5 rounds to -2, two's complement 0xfe"},
    {"id": "encode_samples.rf32_overflow_is_inf", "op": "encode_samples",
     "args": {"x": [1e39, -1e39], "datatype": "rf32_le"}, "expected": "0000807f000080ff",
     "tol": TOL, "source": "by hand: beyond binary32's range rounds to +inf 0x7f800000, -inf 0xff800000"},
    {"id": "encode_samples.rf64_inf", "op": "encode_samples",
     "args": {"x": ["inf"], "datatype": "rf64_be"}, "expected": "7ff0000000000000", "tol": TOL,
     "source": "by hand: binary64 +inf, big-endian"},
    {"id": "encode_samples.empty", "op": "encode_samples",
     "args": {"x": [], "datatype": "rf32_le"}, "expected": "", "tol": TOL,
     "source": "no samples, no bytes"},
    {"id": "decode_samples.i16_extremes", "op": "decode_samples",
     "args": {"data": "0080ff7f", "datatype": "ri16_le"}, "expected": [-1.0, 32767 / 32768],
     "tol": TOL, "source": "by hand: codes -32768 and 32767 over 2^15"},
    {"id": "decode_samples.i32_extremes", "op": "decode_samples",
     "args": {"data": "80000000" + "7fffffff", "datatype": "ri32_be"},
     "expected": [-1.0, (2**31 - 1) / 2**31], "tol": TOL,
     "source": "by hand: codes -2^31 and 2^31-1 over 2^31"},
    {"id": "encode_samples.ru8_ends", "op": "encode_samples",
     "args": {"x": [-1.0, 0.0, 127 / 128, 2.5 / 128], "datatype": "ru8"}, "expected": "0080ff82",
     "tol": TOL, "source": "by hand: offset binary, codes -128, 0, 127, 2 (2.5 to even) plus 128"},
    {"id": "encode_samples.cu16_be_ends", "op": "encode_samples",
     "args": {"x": {"re": [-1.0], "im": [32767 / 32768]}, "datatype": "cu16_be"},
     "expected": "0000ffff", "tol": TOL,
     "source": "by hand: codes -32768 and 32767 plus 32768 are 0 and 65535, big-endian"},
    {"id": "decode_samples.u16_le_mid", "op": "decode_samples",
     "args": {"data": "0080" + "ff7f" + "0100", "datatype": "ru16_le"},
     "expected": [0.0, -1 / 32768, -32767 / 32768], "tol": TOL,
     "source": "by hand: codes 32768, 32767 and 1, less 32768, over 2^15"},
    {"id": "decode_samples.u32_be_ends", "op": "decode_samples",
     "args": {"data": "00000000" + "ffffffff", "datatype": "ru32_be"},
     "expected": [-1.0, (2**31 - 1) / 2**31], "tol": TOL,
     "source": "by hand: codes 0 and 2^32-1, less 2^31, over 2^31"},
    {"id": "decode_samples.cu8_receiver", "op": "decode_samples",
     "args": {"data": "807f00ff", "datatype": "cu8"},
     "expected": {"re": [0.0, -1.0], "im": [-1 / 128, 127 / 128]}, "tol": TOL,
     "source": "by hand: unsigned 8-bit I/Q as receivers record it: (u - 128)/128"},
    {"id": "decode_samples.f32_special", "op": "decode_samples",
     "args": {"data": "0000807f" + "00000080", "datatype": "rf32_le"}, "expected": ["inf", -0.0],
     "tol": TOL, "source": "by hand: +inf and -0.0 in binary32"},
    {"id": "decode_samples.complex_inf_part", "op": "decode_samples",
     "args": {"data": "0000807f" + "0000003f", "datatype": "cf32_le"},
     "expected": {"re": ["inf"], "im": [0.5]}, "tol": TOL,
     "source": "by hand: I = +inf (0x7f800000), Q = 0.5 (0x3f000000); the parts stay apart"},
    {"id": "decode_samples.empty_complex", "op": "decode_samples",
     "args": {"data": "", "datatype": "cf64_le"}, "expected": {"re": [], "im": []}, "tol": TOL,
     "source": "no bytes, no samples"},
]


def err(case_id, op, args, why):
    cases.append({"id": case_id, "op": op, "args": args, "error": "invalid_argument",
                  "source": why})


for bad in ("cu8_le", "ru64_le", "ru16", "cf32", "ci8_le", "rf16_le", "CF32_LE", "cf32_le ", "cf32_LE", "f32_le", ""):
    err(f"encode_samples.datatype_{bad.strip() or 'empty'}" + ("_space" if bad.endswith(" ") else ""),
        "encode_samples", {"x": [0.5], "datatype": bad}, f"{bad!r} is not a supported datatype")
err("encode_samples.full_scale_i16", "encode_samples", {"x": [1.0], "datatype": "ri16_le"},
    "1.0 needs code 32768, one past the largest i16")
err("encode_samples.below_i8", "encode_samples", {"x": [-129 / 128], "datatype": "ri8"},
    "code -129 is below the smallest i8")
err("encode_samples.full_scale_u8", "encode_samples", {"x": [1.0], "datatype": "ru8"},
    "1.0 needs code 128 + 128 = 256, one past the largest u8")
err("encode_samples.below_u16", "encode_samples", {"x": [-32769 / 32768], "datatype": "ru16_le"},
    "code -32769 + 32768 = -1 is below the smallest u16")
err("encode_samples.nan_unsigned", "encode_samples",
    {"x": {"re": ["nan"], "im": [0]}, "datatype": "cu8"}, "integers cannot hold NaN")
err("encode_samples.nan_int", "encode_samples", {"x": ["nan"], "datatype": "ri32_le"},
    "integers cannot hold NaN")
err("encode_samples.inf_int", "encode_samples",
    {"x": {"re": [0], "im": ["inf"]}, "datatype": "ci16_be"}, "integers cannot hold inf")
err("encode_samples.real_as_complex", "encode_samples", {"x": [0.5], "datatype": "cf32_le"},
    "a complex datatype needs complex samples")
err("encode_samples.complex_as_real", "encode_samples",
    {"x": {"re": [0.5], "im": [0]}, "datatype": "rf32_le"}, "a real datatype needs real samples")
err("decode_samples.partial_sample", "decode_samples", {"data": "000000", "datatype": "ri16_le"},
    "3 bytes is not a whole number of 2-byte samples")
err("decode_samples.half_complex", "decode_samples", {"data": "00000000", "datatype": "cf32_le"},
    "4 bytes is half of one 8-byte complex sample")
err("decode_samples.bad_datatype", "decode_samples", {"data": "00", "datatype": "ri64_le"},
    "64-bit integers are not supported")

# --- recordings: (name, meta text, data bytes, expected record or None for an error, why)
recs = []


def meta(glob, captures=None, annotations=None):
    doc = {"global": glob, "captures": captures if captures is not None else
           [{"core:sample_start": 0}], "annotations": annotations or []}
    return json.dumps(doc, indent=2) + "\n"


def base(datatype, rate=1000, **extra):
    return {"core:datatype": datatype, "core:version": "1.0.0", "core:sample_rate": rate, **extra}


ci16 = [(16384, -8192), (32767, 0), (-32768, 1), (0, 0)]
recs.append((
    "foreign_ci16",
    meta(base("ci16_le", 48000, **{"core:author": "a test", "core:description": "four samples"}),
         [{"core:sample_start": 0, "core:frequency": 915000000,
           "core:datetime": "2026-11-13T00:00:00Z"}],
         [{"core:sample_start": 0, "core:sample_count": 2, "core:label": "burst"}]),
    b"".join(struct.pack("<hh", i, q) for i, q in ci16),
    {"samples": {"re": [i / 32768 for i, _ in ci16], "im": [q / 32768 for _, q in ci16]},
     "sample_rate": 48000, "center_frequency": 915000000, "time_origin": 0, "units": None,
     "impedance": None,
     "metadata": {"core:author": "a test", "core:description": "four samples",
                  "core:annotations": [{"core:sample_start": 0, "core:sample_count": 2,
                                        "core:label": "burst"}]}},
    "a file laid out as another tool writes one: codes over 2^15, frequency from the capture, "
    "core:author and core:description kept as metadata, the annotation under core:annotations",
))
labelled = [
    {"core:sample_start": 0, "core:label": "start", "x:score": 0.75},
    {"core:sample_start": 1, "core:sample_count": 0, "core:comment": "empty span"},
    {"core:sample_start": 1, "core:sample_count": 9, "core:freq_lower_edge": -1.5e3,
     "core:freq_upper_edge": 1.5e3, "x:tags": ["a", {"b": None}]},
]
recs.append((
    "annotations_ri16",
    meta(base("ri16_le"), None, labelled),
    struct.pack("<2h", 8192, -8192),
    {"samples": [0.25, -0.25], "sample_rate": 1000, "center_frequency": 0, "time_origin": 0,
     "units": None, "impedance": None, "metadata": {"core:annotations": labelled}},
    "annotations kept in file order with every field: a tie at sample 1, a zero count, a span "
    "past the two samples (not checked), nested values",
))
recs.append((
    "annotations_missing",
    '{"global": {"core:datatype": "ri16_le", "core:version": "1.0.0", '
    '"core:sample_rate": 1000}, "captures": []}\n',
    struct.pack("<h", 16384),
    {"samples": [0.5], "sample_rate": 1000, "center_frequency": 0, "time_origin": 0,
     "units": None, "impedance": None, "metadata": {}},
    "no annotations array: no core:annotations key, as for an empty one",
))
recs.append((
    "signalforge_rf32_be",
    meta({**base("rf32_be", 2.5e6),
          "core:extensions": [{"name": "signalforge", "version": "1.0.0", "optional": True}],
          "signalforge:time_origin": 1.5, "signalforge:units": "V", "signalforge:impedance": 50.0,
          "signalforge:metadata": {"run": 7, "note": "hi"}},
         [{"core:sample_start": 0, "core:frequency": 0.0},
          {"core:sample_start": 2, "core:frequency": 0.0}]),
    struct.pack(">3f", 0.5, -2.0, 3.25),
    {"samples": [0.5, -2.0, 3.25], "sample_rate": 2.5e6, "center_frequency": 0, "time_origin": 1.5,
     "units": "V", "impedance": 50, "metadata": {"run": 7, "note": "hi"}},
    "the signalforge extension fields map back to the Signal; two captures at one frequency",
))
recs.append((
    "int64_extremes",
    meta(base("ri16_le", **{"x:min": -(2**63), "x:max": 2**63 - 1})),
    struct.pack("<h", -16384),
    {"samples": [-0.5], "sample_rate": 1000, "center_frequency": 0, "time_origin": 0,
     "units": None, "impedance": None,
     "metadata": {"x:min": -(2**63), "x:max": 2**63 - 1}},
    "the int64 extremes are kept as integers",
))
recs.append((
    "no_captures_ri8",
    meta(base("ri8"), []),
    bytes([0x80, 0x7F, 0x00]),
    {"samples": [-1.0, 127 / 128, 0.0], "sample_rate": 1000, "center_frequency": 0,
     "time_origin": 0, "units": None, "impedance": None, "metadata": {}},
    "no captures: center frequency 0; i8 codes over 2^7",
))
recs.append((
    "receiver_cu8",
    meta(base("cu8", 2.048e6), [{"core:sample_start": 0, "core:frequency": 100e6}]),
    bytes([0x80, 0x80, 0xC0, 0x40, 0x00, 0xFF]),
    {"samples": {"re": [0.0, 0.5, -1.0], "im": [0.0, -0.5, 127 / 128]}, "sample_rate": 2.048e6,
     "center_frequency": 100e6, "time_origin": 0, "units": None, "impedance": None,
     "metadata": {}},
    "unsigned 8-bit I/Q as a receiver records it: offset binary, (u - 128)/128",
))
one = struct.pack("<h", 1)
for name, text, why in (
    ("two_frequencies", meta(base("ri16_le"), [{"core:sample_start": 0, "core:frequency": 1e6},
                                              {"core:sample_start": 1, "core:frequency": 2e6}]),
     "captures at different frequencies are not one Signal"),
    ("two_channels", meta(base("ri16_le", **{"core:num_channels": 2})), "one channel only"),
    ("one_channel_as_float", meta(base("ri16_le", **{"core:num_channels": 1.0})),
     "core:num_channels must be the integer 1, and 1.0 is a float"),
    ("header_bytes", meta(base("ri16_le"), [{"core:sample_start": 0, "core:header_bytes": 2}]),
     "header bytes inside the data are not supported"),
    ("no_sample_rate", meta({"core:datatype": "ri16_le", "core:version": "1.0.0"}),
     "a Signal needs a sample rate"),
    ("zero_sample_rate", meta(base("ri16_le", 0)), "the sample rate must be positive"),
    ("no_datatype", meta({"core:version": "1.0.0", "core:sample_rate": 1000}),
     "core:datatype is required"),
    ("version_2", meta({**base("ri16_le"), "core:version": "2.0.0"}), "major version 1 only"),
    ("half_float", meta(base("rf16_le")), "16-bit floats are not supported"),
    ("dataset", meta(base("ri16_le", **{"core:dataset": "other.bin"})),
     "a non-conforming dataset is not read"),
    ("duplicate_key", '{"global": {"core:datatype": "ri16_le", "core:version": "1.0.0", '
     '"core:sample_rate": 1000, "core:sample_rate": 2000}, "captures": [], "annotations": []}\n',
     "duplicate JSON keys are ambiguous"),
    ("nan_token", '{"global": {"core:datatype": "ri16_le", "core:version": "1.0.0", '
     '"core:sample_rate": NaN}, "captures": [], "annotations": []}\n', "NaN is not JSON"),
    ("not_an_object", '[1, 2]\n', "the metadata must be a JSON object"),
    ("captures_null", '{"global": {"core:datatype": "ri16_le", "core:version": "1.0.0", '
     '"core:sample_rate": 1000}, "captures": null, "annotations": []}\n',
     "captures, when present, must be an array; null is not one"),
    ("captures_object", meta(base("ri16_le"), {"core:sample_start": 0}),
     "captures must be an array"),
    ("metadata_null", meta(base("ri16_le", **{"signalforge:metadata": None})),
     "signalforge:metadata, when present, must be an object; null is not one"),
    ("integer_beyond_int64", meta(base("ri16_le", **{"x:big": 2**63})),
     "JSON integers must fit in signed 64 bits; 2^63 does not"),
    ("float_overflow", '{"global": {"core:datatype": "ri16_le", "core:version": "1.0.0", '
     '"core:sample_rate": 1000, "x:huge": 1e400}, "captures": [], "annotations": []}\n',
     "1e400 overflows a double; numbers must be finite"),
    ("huge_integer_rate", meta(base("ri16_le", 10**400)),
     "a 401-digit sample rate is outside the signed 64-bit range"),
    ("lone_surrogate", '{"global": {"core:datatype": "ri16_le", "core:version": "1.0.0", '
     '"core:sample_rate": 1000, "x:note": "a\\ud800b"}, "captures": [], '
     '"annotations": []}\n', "an unpaired surrogate escape is not valid Unicode"),
    ("too_deep", '{"global": {"core:datatype": "ri16_le", "core:version": "1.0.0", '
     '"core:sample_rate": 1000, "x:deep": ' + "[" * 63 + "]" * 63 + '}, '
     '"captures": [], "annotations": []}\n',
     "63 arrays inside global inside the document are 65 levels; at most 64"),
    ("infinity_token", '{"global": {"core:datatype": "ri16_le", "core:version": "1.0.0", '
     '"core:sample_rate": Infinity}, "captures": [], "annotations": []}\n',
     "Infinity is not JSON"),
    ("metadata_only", meta(base("ri16_le", **{"core:metadata_only": True})),
     "a metadata-only recording has no samples"),
    ("units_number", meta(base("ri16_le", **{"signalforge:units": 5})),
     "signalforge:units must be a string"),
    ("time_origin_string", meta(base("ri16_le", **{"signalforge:time_origin": "0"})),
     "signalforge:time_origin must be a number"),
    ("impedance_bool", meta(base("ri16_le", **{"signalforge:impedance": True})),
     "signalforge:impedance must be a number, and a bool is not one"),
    ("header_bytes_float",
     meta(base("ri16_le"), [{"core:sample_start": 0, "core:header_bytes": 0.0}]),
     "core:header_bytes must be the integer 0, and 0.0 is a float"),
    ("annotations_null", '{"global": {"core:datatype": "ri16_le", "core:version": "1.0.0", '
     '"core:sample_rate": 1000}, "captures": [], "annotations": null}\n',
     "annotations, when present, must be an array; null is not one"),
    ("annotations_object", meta(base("ri16_le"), None, {"core:sample_start": 0}),
     "annotations must be an array"),
    ("annotation_not_object", meta(base("ri16_le"), None, [5]), "each annotation is an object"),
    ("annotation_no_start", meta(base("ri16_le"), None, [{"core:label": "x"}]),
     "core:sample_start is required"),
    ("annotation_start_float", meta(base("ri16_le"), None, [{"core:sample_start": 2.0}]),
     "core:sample_start must be an integer, and 2.0 is a float"),
    ("annotation_start_negative", meta(base("ri16_le"), None, [{"core:sample_start": -1}]),
     "core:sample_start must be at least 0"),
    ("annotation_count_bool",
     meta(base("ri16_le"), None, [{"core:sample_start": 0, "core:sample_count": True}]),
     "core:sample_count must be an integer, and a bool is not one"),
    ("annotation_count_negative",
     meta(base("ri16_le"), None, [{"core:sample_start": 0, "core:sample_count": -2}]),
     "core:sample_count must be at least 0"),
    ("annotations_unsorted",
     meta(base("ri16_le"), None, [{"core:sample_start": 5}, {"core:sample_start": 4}]),
     "annotations must be sorted by core:sample_start; they are not sorted for the caller"),
    ("annotations_in_global",
     meta(base("ri16_le", **{"core:annotations": [{"core:sample_start": 0}]})),
     "core:annotations is the top-level array, not a global field"),
):
    recs.append((name, text, one, None, why))
recs.append(("partial_sample", meta(base("ri16_le")), b"\x01\x00\x02", None,
             "3 bytes is not a whole number of 2-byte samples"))

for name, _, _, expected, why in recs:
    case = {"id": f"read_sigmf.{name}", "op": "read_sigmf", "args": {"file": name}}
    if expected is None:
        case.update({"error": "invalid_argument", "source": why})
    else:
        case.update({"expected": expected, "tol": TOL, "source": why})
    cases.append(case)

doc = {
    "schema": 1,
    "suite": "files",
    "description": "Raw sample encoding in every supported datatype, and reading SigMF-layout "
    "recordings from vectors/files (conventions: Signal files).",
    "cases": cases,
}
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
outputs = {ROOT / "cases" / "files.json": (head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n").encode()}
for name, text, data, _, _ in recs:
    outputs[ROOT / "files" / f"{name}.sigmf-meta"] = text.encode()
    outputs[ROOT / "files" / f"{name}.sigmf-data"] = data

if "--check" in sys.argv[1:]:
    stale = [p for p, b in outputs.items() if not p.is_file() or p.read_bytes() != b]
    known = set(outputs)
    stale += [p for p in (ROOT / "files").glob("*.sigmf-*") if p not in known]
    if stale:
        sys.exit("out of date (run python vectors/generators/files.py): "
                 + ", ".join(str(p.relative_to(ROOT)) for p in stale))
    print(f"{len(outputs)} files are up to date")
    sys.exit(0)
(ROOT / "files").mkdir(exist_ok=True)
for p, b in outputs.items():
    p.write_bytes(b)
print(f"wrote {len(outputs)} files ({len(cases)} cases)")
