"""Writes vectors/cases/npy.json and the .npy files in vectors/files/, using only the standard library.

It does not import NumPy or SignalForge. The written layout is the one in conventions: Signal files,
NumPy .npy (the one numpy.save writes for these arrays; the Python tests compare with numpy.save,
which this script cannot import). Values come from struct; headers of other writers and broken
headers are written here as literal text.

Run from the repo root: python vectors/generators/npy.py [--check]
With --check it writes nothing and exits 1 unless every file matches what it would write.
"""

import json
import math
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOL = {"abs": 0, "rel": 0}
MAGIC = b"\x93NUMPY"


def parts(x):
    out = []
    for v in x:
        out += [v.real, v.imag] if isinstance(v, complex) else [v]
    return out


def data(x):
    return b"".join(struct.pack("<d", v) for v in parts(x))


def header(text, version=(1, 0)):
    raw = text.encode("ascii") if isinstance(text, str) else text
    size = struct.pack("<H", len(raw)) if version[0] == 1 else struct.pack("<I", len(raw))
    return MAGIC + bytes(version) + size + raw


def npy(x, is_complex):
    """The bytes write_npy writes."""
    descr = "<c16" if is_complex else "<f8"
    text = f"{{'descr': '{descr}', 'fortran_order': False, 'shape': ({len(x)},), }}"
    return header(text.ljust(117) + "\n") + data(x)


def arg(x, is_complex):
    def one(v):
        return "nan" if math.isnan(v) else "inf" if v == math.inf else "-inf" if v == -math.inf else v
    if is_complex:
        return {"re": [one(v.real) for v in x], "im": [one(v.imag) for v in x]}
    return [one(v) for v in x]


cases = []
INF = math.inf  # no NaN in writes: each language's NaN has its own sign bit
for name, x, is_complex, why in (
    ("real", [0.5, -0.25, 0.1, -1e-300, 1e300, 0.0], False, "the NumPy layout, values packed with struct"),
    ("real_infinite", [INF, -INF, 0.0], False, "infinities are stored as they are"),
    ("real_ten", [float(k) for k in range(10)], False, "a two-digit shape: the header is still 118 bytes"),
    ("real_empty", [], False, "shape (0,), no data"),
    ("complex", [1 + 2j, -0.5 - 0.25j, 0.1j, complex(3, -1e-300)], True, "real then imaginary part"),
    ("complex_infinite", [complex(INF, 1), complex(0.5, -INF)], True, "infinities in either part"),
    ("complex_empty", [], True, "an empty complex array is still '<c16'"),
):
    cases.append({"id": f"write_npy.{name}", "op": "write_npy", "args": {"x": arg(x, is_complex)},
                  "expected": npy(x, is_complex).hex(), "tol": TOL, "source": why})
cases.append({"id": "write_npy.integers", "op": "write_npy", "args": {"x": [1, -2, 3]},
              "expected": npy([1.0, -2.0, 3.0], False).hex(), "tol": TOL,
              "source": "real samples of any numeric type are written as '<f8'"})

recs = []  # (name, bytes, expected or None, why)
x3 = [0.5, -1.5, 1e-300]
z2 = [1 - 2j, complex(0.25, INF)]


def good(name, raw, x, why):
    recs.append((name, raw, arg(x, any(isinstance(v, complex) for v in x)), why))


def bad(name, raw, why):
    recs.append((name, raw, None, why))


H = "{'descr': '<f8', 'fortran_order': False, 'shape': (3,), }"
good("numpy_real", npy(x3, False), x3, "the layout numpy.save writes for a float64 array")
good("numpy_complex", npy(z2, True), z2, "the layout numpy.save writes for a complex128 array")
good("empty", npy([], False), [], "shape (0,)")
good("version_2", header(H.ljust(115) + "\n", (2, 0)) + data(x3), x3, "version 2.0: a 32-bit header length")
good("version_3", header("{'descr': '<c16', 'fortran_order': False, 'shape': (2,), }\n", (3, 0)) + data(z2),
     z2, "version 3.0, no alignment padding")
good("fortran_order", header("{'descr': '<f8', 'fortran_order': True, 'shape': (3,), }\n") + data(x3), x3,
     "fortran_order does not change a 1-D array")
good("other_writer", header('{"shape":(3,) ,"descr":"<f8",\t"fortran_order" : False}  \r\n') + data(x3), x3,
     "double quotes, another key order, no trailing comma, tabs and CR LF")
good("old_numpy_16", header("{'descr': '<f8', 'fortran_order': False, 'shape': (3,), }".ljust(69) + "\n")
     + data(x3), x3, "padded to 16 bytes as older NumPy wrote")
good("no_newline", header("{'descr':'<f8','fortran_order':False,'shape':(3,)}") + data(x3), x3,
     "no padding and no newline")


def h(text):
    return header(text + "\n") + data(x3)


bad("bad_magic", b"\x93NUMPZ" + npy(x3, False)[6:], "the magic is \\x93NUMPY")
bad("version_4", header(H + "\n", (4, 0)) + data(x3), "only versions 1.0, 2.0 and 3.0")
bad("version_1_1", header(H + "\n", (1, 1)) + data(x3), "only versions 1.0, 2.0 and 3.0")
bad("too_short", MAGIC + b"\x01\x00\x76", "the file ends inside the header length")
bad("header_past_end", MAGIC + b"\x01\x00\xff\x00" + H.encode(), "the header length runs past the file")
bad("big_endian", h("{'descr': '>f8', 'fortran_order': False, 'shape': (3,), }"), "'>f8' is big-endian")
bad("float32", h("{'descr': '<f4', 'fortran_order': False, 'shape': (6,), }"), "only '<f8' and '<c16'")
bad("int64", h("{'descr': '<i8', 'fortran_order': False, 'shape': (3,), }"), "only '<f8' and '<c16'")
bad("object", h("{'descr': '|O', 'fortran_order': False, 'shape': (3,), }"), "object arrays hold pickles")
bad("structured", h("{'descr': [('a', '<f8')], 'fortran_order': False, 'shape': (3,), }"),
    "a structured descr is a list, which the grammar has no place for")
bad("two_dims", h("{'descr': '<f8', 'fortran_order': False, 'shape': (1, 3), }"), "a 2-D shape")
bad("zero_dims", header("{'descr': '<f8', 'fortran_order': False, 'shape': (), }\n") + data([0.5]),
    "a 0-D shape")
bad("shape_not_tuple", h("{'descr': '<f8', 'fortran_order': False, 'shape': (3), }"),
    "(3) is an integer, not a tuple")
bad("shape_leading_zero", h("{'descr': '<f8', 'fortran_order': False, 'shape': (03,), }"),
    "integers have no leading zero")
bad("shape_negative", h("{'descr': '<f8', 'fortran_order': False, 'shape': (-3,), }"), "no sign")
bad("shape_long", h("{'descr': '<f8', 'fortran_order': False, 'shape': (3L,), }"), "no L suffix")
bad("shape_expression", h("{'descr': '<f8', 'fortran_order': False, 'shape': (1+2,), }"),
    "the header is not evaluated")
bad("extra_key", h("{'descr': '<f8', 'fortran_order': False, 'shape': (3,), 'x': True, }"), "an extra key")
bad("missing_key", h("{'descr': '<f8', 'shape': (3,), }"), "fortran_order is missing")
bad("duplicate_key", h("{'descr': '<f8', 'descr': '<f8', 'fortran_order': False, 'shape': (3,), }"),
    "descr twice")
bad("fortran_int", h("{'descr': '<f8', 'fortran_order': 0, 'shape': (3,), }"), "fortran_order must be a bool")
bad("escape", h("{'descr': '<f8\\x', 'fortran_order': False, 'shape': (3,), }"), "no backslash in a string")
bad("non_ascii", header("{'descr': '<f8', 'fortran_order': False, 'shape': (3,), 'é': True}\n".encode("utf-8"),
                        (3, 0)) + data(x3), "the header must be ASCII")
bad("trailing_text", h("{'descr': '<f8', 'fortran_order': False, 'shape': (3,), } x"),
    "only whitespace after the dict")
bad("double_comma", h("{'descr': '<f8', 'fortran_order': False, 'shape': (3,),, }"), "two commas")
bad("data_short", header(H.ljust(117) + "\n") + data(x3[:2]), "16 bytes for shape (3,)")
bad("data_long", header(H.ljust(117) + "\n") + data(x3 + [0.0]), "32 bytes for shape (3,)")
bad("complex_odd", header("{'descr': '<c16', 'fortran_order': False, 'shape': (1,), }\n") + data([0.5]),
    "8 bytes for one complex128")

for name, _, expected, why in recs:
    c = {"id": f"read_npy.{name}", "op": "read_npy", "args": {"file": f"{name}.npy"}}
    c.update({"error": "invalid_argument", "source": why} if expected is None
             else {"expected": expected, "tol": TOL, "source": why})
    cases.append(c)

doc = {
    "schema": 1,
    "suite": "npy",
    "description": "Writing NumPy .npy files, and reading them as NumPy and other writers lay them "
    "out, from vectors/files (conventions: Signal files, NumPy .npy).",
    "cases": cases,
}
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
outputs = {ROOT / "cases" / "npy.json": (head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n").encode()}
for name, raw, _, _ in recs:
    outputs[ROOT / "files" / f"{name}.npy"] = raw

if "--check" in sys.argv[1:]:
    stale = [p for p, b in outputs.items() if not p.is_file() or p.read_bytes() != b]
    stale += [p for p in (ROOT / "files").glob("*.npy") if p not in outputs]
    if stale:
        sys.exit("out of date (run python vectors/generators/npy.py): "
                 + ", ".join(str(p.relative_to(ROOT)) for p in stale))
    print(f"{len(outputs)} files are up to date")
    sys.exit(0)
for p, b in outputs.items():
    p.write_bytes(b)
print(f"wrote {len(outputs)} files ({len(cases)} cases)")
