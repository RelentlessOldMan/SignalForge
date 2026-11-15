"""Writes vectors/cases/npy.json and the .npy files in vectors/files/, using only the standard library.

It does not import NumPy or SignalForge. The written layout is the one in conventions: Signal files,
NumPy .npy (the one numpy.save writes for these arrays; the Python tests compare with numpy.save,
which this script cannot import). Values come from struct (d, f and e in both byte orders; ADR 0088); headers of other writers and broken
headers are written here as literal text. 2-D files (ADR 0092) pack their items row by row (C order)
or column by column (Fortran order); expected values are listed flat in C order with the shape.

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


def data(x, fmt="<d"):
    return b"".join(struct.pack(fmt, v) for v in parts(x))


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



def npy2(rows, is_complex):
    """The bytes write_npy writes for a 2-D array given as rows: C order."""
    descr = "<c16" if is_complex else "<f8"
    shape = f"({len(rows)}, {len(rows[0]) if rows else 0})"
    text = f"{{'descr': '{descr}', 'fortran_order': False, 'shape': {shape}, }}"
    return header(text.ljust(117) + "\n") + data([v for r in rows for v in r])


def write2(name, rows, ncols, is_complex, why):
    flat = [v for r in rows for v in r]
    expected = npy2(rows, is_complex) if rows else header(
        f"{{'descr': '<f8', 'fortran_order': False, 'shape': (0, {ncols}), }}".ljust(117) + "\n")
    cases.append({"id": f"write_npy.{name}", "op": "write_npy",
                  "args": {"x": arg(flat, is_complex), "shape": [len(rows), ncols]},
                  "expected": expected.hex(), "tol": TOL, "source": why})


M = [[1.5, -2.0, 3.0], [0.25, 1e-300, -INF]]
MZ = [[1 + 2j, -0.5j], [complex(INF, 0.125), 3.0 + 0j], [0j, -1 - 1j]]
write2("matrix_2x3", M, 3, False, "C order: row 0 then row 1, shape (2, 3); numpy.save writes the same")
write2("matrix_complex_3x2", MZ, 2, True, "C order, real then imaginary part of each, shape (3, 2)")
write2("matrix_1x1", [[0.5]], 1, False, "shape (1, 1)")
write2("matrix_zero_rows", [], 3, False, "shape (0, 3), no data")
write2("matrix_zero_columns", [[], []], 0, False, "shape (2, 0), no data")
write2("matrix_10x10", [[float(10 * i + j) for j in range(10)] for i in range(10)], 10, False,
       "two-digit dimensions: the header is still 118 bytes")

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


# ADR 0088: narrower floats and big-endian data, widened exactly. Each value is one the narrow
# type holds exactly, so the expected double is the value itself.
x16 = [0.5, -1.5, 2.0**-24, 65504.0, -INF, -0.0]
x32 = [0.5, -1.5, 2.0**-149, 3.4028234663852886e38, INF, 0.1875]
z32 = [complex(0.25, -2.0**-149), complex(-INF, 2.0**-126)]
z16 = [complex(1.0, -2.0**-14), complex(65504.0, 2.0**-24)]


def typed(descr, x, fmt):
    return header(f"{{'descr': '{descr}', 'fortran_order': False, 'shape': ({len(x)},), }}\n") + data(x, fmt)


good("big_endian_f8", typed(">f8", x3, ">d"), x3, "'>f8': big-endian binary64, as NumPy saves a '>f8' array")
good("float32", typed("<f4", x32, "<f"), x32,
     "'<f4' packed with struct 'f': the smallest subnormal 2^-149, the largest finite, inf")
good("float32_be", typed(">f4", x32, ">f"), x32, "'>f4' packed with struct '>f'")
good("float16", typed("<f2", x16, "<e"), x16,
     "'<f2' packed with struct 'e': the smallest subnormal 2^-24, the largest finite 65504, -inf, -0")
good("float16_be", typed(">f2", x16, ">e"), x16, "'>f2' packed with struct '>e'")
good("complex64", typed("<c8", z32, "<f"), z32, "'<c8': two binary32 parts per item, real first")
good("complex64_be", typed(">c8", z32, ">f"), z32, "'>c8' packed with struct '>f'")
good("complex128_be", typed(">c16", z2, ">d"), z2, "'>c16' packed with struct '>d'")
good("float16_even", typed("<f2", [1.0, -2.0**-14], "<e"), [1.0, -2.0**-14],
     "a real '<f2' file read as reals, even with an even count")

# Integers (ADR 0090): each value as the double of the same value, no scaling.
for descr, fmt, x in (
    ("|i1", "b", [0, 1, -1, 127, -128]),
    ("|u1", "B", [0, 1, 128, 255]),
    ("<i2", "<h", [0, -1, 32767, -32768, 258]),
    (">i2", ">h", [0, -1, 32767, -32768, 258]),
    ("<u2", "<H", [0, 1, 65535, 258]),
    (">u2", ">H", [0, 1, 65535, 258]),
    ("<i4", "<i", [0, -1, 2**31 - 1, -(2**31), 16909060]),
    (">i4", ">i", [0, -1, 2**31 - 1, -(2**31), 16909060]),
    ("<u4", "<I", [0, 2**32 - 1, 16909060]),
    (">u4", ">I", [0, 2**32 - 1, 16909060]),
    ("<i8", "<q", [0, -1, 2**53, -(2**53), -(2**63), 72623859790382856]),
    (">i8", ">q", [0, -1, 2**53, -(2**53), -(2**63), 72623859790382856]),
    ("<u8", "<Q", [0, 2**53, 2**63, 2**64 - 2**11]),
    (">u8", ">Q", [0, 2**53, 2**63, 2**64 - 2**11]),
):
    # Every value here is exact in binary64: at most 2^53 in magnitude, or a multiple of the spacing
    # at its size (72623859790382856 = 0x0102030405060708 is a multiple of 8, the spacing in
    # [2^56, 2^57)), so the expected double is the integer itself.
    name = ("int" if descr[1] == "i" else "uint") + str(8 * int(descr[2:])) + ("_be" if descr[0] == ">" else "")
    good(name, typed(descr, x, fmt), [float(v) for v in x], f"'{descr}' packed with struct '{fmt}'")
# Beyond 2^53, worked by hand. Near 2^53 doubles are 2 apart, near 2^60 256 apart, near 2^63 and
# 2^64 2048 and 4096 apart; a value halfway between two goes to the one whose significand is even.
rounded = [
    (2**53 + 1, 2**53),  # halfway between 2^53 (even) and 2^53 + 2 (odd)
    (2**53 + 3, 2**53 + 4),  # halfway between 2^53 + 2 (odd) and 2^53 + 4 (even)
    (2**60 + 2**7, 2**60),  # halfway, 2^60 is even
    (2**60 + 3 * 2**7, 2**60 + 2**9),  # halfway between 2^60 + 2^8 (odd) and 2^60 + 2^9 (even)
    (2**60 + 2**7 + 1, 2**60 + 2**8),  # just past halfway: up
    (2**63 - 1, 2**63),  # below 2^63 doubles are 1024 apart; 2^63 - 1 is nearest 2^63
]
good("int64_rounded", typed("<i8", [v for v, _ in rounded], "<q"), [float(r) for _, r in rounded],
     "64-bit values beyond 2^53 round to the nearest double, ties to even, worked by hand")
good("uint64_rounded", typed(">u8", [2**64 - 1, 2**64 - 3 * 2**10, 2**63 + 2**10], ">Q"),
     [float(2**64), float(2**64 - 2**12), float(2**63)],
     "near 2^64 doubles are 2^11 apart: 2^64 - 1 rounds up to 2^64; 2^64 - 3 * 2^10 is halfway "
     "between 2^64 - 2^12 (even) and 2^64 - 2^11 (odd); 2^63 + 2^10 is halfway, 2^63 is even")


def h(text):
    return header(text + "\n") + data(x3)


bad("bad_magic", b"\x93NUMPZ" + npy(x3, False)[6:], "the magic is \\x93NUMPY")
bad("version_4", header(H + "\n", (4, 0)) + data(x3), "only versions 1.0, 2.0 and 3.0")
bad("version_1_1", header(H + "\n", (1, 1)) + data(x3), "only versions 1.0, 2.0 and 3.0")
bad("too_short", MAGIC + b"\x01\x00\x76", "the file ends inside the header length")
bad("header_past_end", MAGIC + b"\x01\x00\xff\x00" + H.encode(), "the header length runs past the file")
bad("native_order", h("{'descr': '=f8', 'fortran_order': False, 'shape': (3,), }"),
    "'=' would depend on the reader's byte order")
bad("no_order", h("{'descr': '|f8', 'fortran_order': False, 'shape': (3,), }"), "'|' is for single bytes")
bad("long_double", header("{'descr': '<f16', 'fortran_order': False, 'shape': (1,), }\n") + bytes(16),
    "'<f16' is a 16-byte long double, not binary16 ('<f2')")
bad("float32_short", header("{'descr': '<f4', 'fortran_order': False, 'shape': (3,), }\n") + data(x32[:2], "<f"),
    "8 bytes for shape (3,) of '<f4'")
bad("complex64_odd", header("{'descr': '<c8', 'fortran_order': False, 'shape': (1,), }\n") + data([0.5], "<f"),
    "4 bytes for one complex64")
bad("float32_uppercase", h("{'descr': '<F4', 'fortran_order': False, 'shape': (6,), }"), "descrs are lowercase")
bad("int8_order", typed("<i1", [1], "<b"), "a one-byte integer's descr uses '|', not '<'")
bad("uint8_order", typed(">u1", [1], ">B"), "a one-byte integer's descr uses '|', not '>'")
bad("int16_native", typed("=i2", [1], "<h"), "'=' is rejected for integers too")
bad("int16_none", typed("|i2", [1], "<h"), "'|' on a two-byte integer")
bad("bool", typed("|b1", [1], "<B"), "booleans are not read")
bad("int32_short", typed("<i4", [1, 2], "<i")[:-1], "7 data bytes for shape (2,)")
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

recs2 = []  # (name, bytes, expected or None, why) for read_npy_2d


def file2(descr, shape, fortran, items, fmt="<d", version=(1, 0)):
    """A 2-D .npy file whose items are already in the file's order."""
    text = f"{{'descr': '{descr}', 'fortran_order': {fortran}, 'shape': {shape}, }}\n"
    return header(text, version) + data(items, fmt)


def good2(name, raw, rows, ncols, why):
    flat = [v for r in rows for v in r]
    recs2.append((f"m2_{name}", raw, {"shape": [len(rows), ncols],
                                      "x": arg(flat, any(isinstance(v, complex) for v in flat))}, why))


def bad2(name, raw, why):
    recs2.append((f"m2_{name}", raw, None, why))


def columns(rows):
    return [rows[i][j] for j in range(len(rows[0])) for i in range(len(rows))]


good2("c_order", npy2(M, False), M, 3, "the layout numpy.save writes for a C-ordered (2, 3) float64 array")
good2("fortran", file2("<f8", "(2, 3)", True, columns(M)), M, 3,
      "Fortran order: the file holds column 0, then 1, then 2; read back as rows")
good2("complex", npy2(MZ, True), MZ, 2, "a C-ordered (3, 2) complex128 array")
Z2 = [[1 + 2j, 0.5 - 0.25j], [-3j, 4 + 0j]]
good2("complex64_big_fortran", file2(">c8", "(2, 2)", True, columns(Z2), ">f"), Z2, 2,
      "big-endian complex64 in Fortran order, values exact in binary32")
I16 = [[1, -2, 32767], [-32768, 0, 5]]
good2("int16_fortran", file2("<i2", "(2, 3)", True, columns(I16), "<h"),
      [[float(v) for v in r] for r in I16], 3, "integers in Fortran order, no scaling (ADR 0090)")
good2("uint8_column", file2("|u1", "(3, 1)", False, [0, 128, 255], "B"), [[0.0], [128.0], [255.0]], 1,
      "one column of unsigned bytes")
good2("zero_rows", file2("<f8", "(0, 3)", False, []), [], 3, "shape (0, 3): no data")
good2("zero_columns", file2("<f8", "(4, 0)", True, []), [[], [], [], []], 0, "shape (4, 0): no data")
good2("one_by_one", file2("<f8", "(1, 1)", False, [0.5]), [[0.5]], 1, "shape (1, 1)")
good2("version_2", file2("<f8", "(2, 3)", False, [v for r in M for v in r], version=(2, 0)), M, 3,
      "version 2.0, a 32-bit header length")
good2("other_writer", header("{\"shape\":( 2 ,3 ),\"fortran_order\":False,\"descr\":\"<f8\"}\n")
      + data([v for r in M for v in r]), M, 3, "another writer's spacing and key order")
bad2("one_dim", npy(x3, False), "shape (3,) is 1-D")
bad2("three_dims", file2("<f8", "(1, 2, 3)", False, [0.0] * 6), "shape (1, 2, 3) is 3-D")
bad2("zero_dims", file2("<f8", "()", False, [0.5]), "shape () is 0-D")
bad2("data_short", file2("<f8", "(2, 3)", False, [0.0] * 5), "40 bytes for shape (2, 3)")
bad2("data_long", file2("<f8", "(2, 3)", True, [0.0] * 7), "56 bytes for shape (2, 3)")
bad2("dimension_too_big", file2("<f8", "(2147483592, 0)", False, []),
     "2147483592 rows is one beyond the 2147483591 limit, even with no data")
bad2("product_too_big", file2("<f8", "(2147483591, 2147483591)", False, [0.0]),
     "each dimension fits, but 8 bytes are not 2147483591^2 items")
bad2("bool", file2("|b1", "(1, 1)", False, [1], "B"), "booleans are not read")

for name, _, expected, why in recs2:
    c = {"id": f"read_npy_2d.{name}", "op": "read_npy_2d", "args": {"file": f"{name}.npy"}}
    c.update({"error": "invalid_argument", "source": why} if expected is None
             else {"expected": expected, "tol": TOL, "source": why})
    cases.append(c)

doc = {
    "schema": 1,
    "suite": "npy",
    "description": "Writing NumPy .npy files, and reading them as NumPy and other writers lay them "
    "out, from vectors/files, 1-D and 2-D (conventions: Signal files, NumPy .npy).",
    "cases": cases,
}
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
outputs = {ROOT / "cases" / "npy.json": (head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n").encode()}
for name, raw, _, _ in recs + recs2:
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
