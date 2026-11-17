"""Writes vectors/cases/savgol_coefficients.json and savgol_filter.json, stdlib only.

Savitzky–Golay (conventions: Savitzky–Golay; ADR 0233). The weights come from the normal
equations (A^T A) a = A^T x with A[k, i] = k^i on the unscaled offsets k = -h ... h, solved in
exact rational arithmetic: c = row-combination v^T (A^T A)^-1 A^T, v[i] = i!/(i-d)! p^(i-d).
Checked against the classic tables: (-3, 12, 17, 12, -3)/35 for length 5, order 2, and
(-2, -1, 0, 1, 2)/10 for its first derivative. The filter applies those weights per its
definition, with the edge weights at their own offsets.

Run from the repo root: python vectors/generators/savgol.py [--check]
With --check it writes nothing and exits 1 unless the files match what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-12, "rel": 1e-10}


def solve(a, b):
    n = len(a)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        piv = next(r for r in range(col, n) if m[r][col] != 0)
        m[col], m[piv] = m[piv], m[col]
        for r in range(n):
            if r != col and m[r][col] != 0:
                f = m[r][col] / m[col][col]
                m[r] = [x - f * y for x, y in zip(m[r], m[col])]
    return [m[i][n] / m[i][i] for i in range(n)]


def weights(length, order, d=0, pos=0):
    h = (length - 1) // 2
    ks = range(-h, h + 1)
    ata = [[sum(Fr(k) ** (i + j) for k in ks) for j in range(order + 1)] for i in range(order + 1)]
    v = [Fr(math.perm(i, d)) * Fr(pos) ** (i - d) if i >= d else Fr(0) for i in range(order + 1)]
    w = solve(ata, v)
    return [sum(w[i] * Fr(k) ** i for i in range(order + 1)) for k in ks]


assert weights(5, 2) == [Fr(v, 35) for v in (-3, 12, 17, 12, -3)]
assert weights(5, 2, 1) == [Fr(v, 10) for v in (-2, -1, 0, 1, 2)]
assert weights(7, 2) == [Fr(v, 21) for v in (-2, 3, 6, 7, 6, 3, -2)]

coef = []


def add_c(cid, length, order, why, d=0, pos=0):
    args = {"length": length, "order": order}
    if d:
        args["derivative"] = d
    if pos:
        args["position"] = pos
    coef.append({"id": f"savgol_coefficients.{cid}", "op": "savgol_coefficients", "args": args,
                 "expected": [float(v) for v in weights(length, order, d, pos)], "tol": TOL,
                 "source": why})


add_c("table_5_2", 5, 2, "Savitzky-Golay table: (-3, 12, 17, 12, -3)/35")
add_c("table_7_2", 7, 2, "Savitzky-Golay table: (-2, 3, 6, 7, 6, 3, -2)/21")
add_c("deriv_5_2", 5, 2, "first derivative table: (-2, -1, 0, 1, 2)/10", d=1)
add_c("quartic_11", 11, 4, "length 11, order 4, exact normal equations")
add_c("second_deriv", 9, 3, "length 9, order 3, second derivative", d=2)
add_c("edge_position", 7, 3, "length 7, order 3, evaluated at offset -3", pos=-3)
add_c("edge_deriv", 5, 2, "length 5, order 2, first derivative at offset 2", d=1, pos=2)
add_c("length_one", 1, 0, "length 1: the single weight 1")
add_c("moving_average", 5, 0, "order 0: the moving average 1/5")


def err(store, op, cid, why, **args):
    store.append({"id": f"{op}.{cid}", "op": op, "args": args, "error": "invalid_argument",
                  "source": why})


err(coef, "savgol_coefficients", "even_length", "length must be odd", length=4, order=2)
err(coef, "savgol_coefficients", "order_too_big", "order must be below length", length=5, order=5)
err(coef, "savgol_coefficients", "derivative_too_big", "derivative over order", length=5,
    order=2, derivative=3)
err(coef, "savgol_coefficients", "position_out", "position beyond h", length=5, order=2,
    position=3)

filt = []


def apply(x, length, order, d):
    n = len(x)
    h = (length - 1) // 2
    out = []
    for i in range(n):
        if i < h:
            c, start = weights(length, order, d, i - h), 0
        elif i >= n - h:
            c, start = weights(length, order, d, i - (n - 1 - h)), n - length
        else:
            c, start = weights(length, order, d), i - h
        out.append(sum(c[j] * x[start + j] for j in range(length)))
    return out


def add_f(cid, x, length, order, why, d=0):
    x = [Fr(v) for v in x]
    y = apply(x, length, order, d)
    args = {"samples": [float(v) for v in x], "length": length, "order": order}
    if d:
        args["derivative"] = d
    filt.append({"id": f"savgol_filter.{cid}", "op": "savgol_filter", "args": args,
                 "expected": [float(v) for v in y], "tol": TOL, "source": why})
    return y


quad = [Fr(3) - Fr(k) + Fr(k * k, 4) for k in range(10)]
y = add_f("quadratic_exact", quad, 5, 2, "a quadratic is reproduced exactly, edges included")
assert y == quad
y = add_f("quadratic_slope", quad, 5, 2, "its derivative -1 + k/2, edges included", d=1)
assert y == [Fr(-1) + Fr(k, 2) for k in range(10)]
add_f("noisy", [0.5, 1.25, -0.75, 2.0, 1.5, 0.25, -1.0, 0.75, 1.75, -0.5, 0.0, 1.0], 7, 3,
      "length 7, order 3 on mixed data")
add_f("short", [1.0, 4.0, 2.0], 3, 1, "samples exactly one window long: all from the one fit")
err(filt, "savgol_filter", "too_short", "samples shorter than length", samples=[1.0, 2.0],
    length=3, order=1)
err(filt, "savgol_filter", "nan_sample", "samples must be finite", samples=[1.0, "nan", 2.0],
    length=3, order=1)

check = "--check" in sys.argv[1:]
for name, cases in (("savgol_coefficients", coef), ("savgol_filter", filt)):
    doc = {"schema": 1, "suite": name,
           "description": "Savitzky-Golay (conventions: Savitzky-Golay; ADR 0233).",
           "cases": cases}
    out = pathlib.Path(__file__).resolve().parents[1] / "cases" / f"{name}.json"
    lines = ",\n".join("    " + json.dumps(c) for c in cases)
    head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
    text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
    if check:
        if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
            sys.exit(f"{out} is out of date: run python vectors/generators/savgol.py")
        print(f"{out} is up to date")
        continue
    out.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {out} ({len(cases)} cases)")
