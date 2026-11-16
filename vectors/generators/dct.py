"""Writes vectors/cases/dct.json, stdlib only.

DCT-II and its exact inverse (conventions: DCT-II; ADR 0156). The cosines are exact:
cos(pi/4) = sqrt(2)/2, cos(pi/8) = sqrt(2 + sqrt(2))/2, cos(3 pi/8) = sqrt(2 - sqrt(2))/2, and
their signs and symmetries, written out in 50-digit decimal. The transform is the plain sum of
the definition over that table; the generator checks the hand-worked cases.

Run from the repo root: python vectors/generators/dct.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from decimal import Decimal as D
from decimal import getcontext

getcontext().prec = 50
TOL = {"abs": 1e-13, "rel": 1e-13}
cases = []
R2 = D(2).sqrt()
C8 = (2 + R2).sqrt() / 2
S8 = (2 - R2).sqrt() / 2
# cos(pi j / (2N)) for j = 0 .. 4N-1, exact for N = 1, 2, 4.
QUARTER = {1: [D(1)], 2: [D(1), R2 / 2], 4: [D(1), C8, R2 / 2, S8]}


def cos_table(n):
    q = QUARTER[n]  # j = 0 .. N-1 gives angles 0 .. pi/2 (exclusive)
    first = q + [D(0)] + [-v for v in reversed(q[1:])]  # 0 .. pi (exclusive)
    return first + [-v for v in first]  # pi .. 2 pi (exclusive)


def scales(n, ortho):
    if not ortho:
        return [D(2)] * n
    return [(D(1) / n).sqrt()] + [(D(2) / n).sqrt()] * (n - 1)


def dct(x, ortho):
    n = len(x)
    t = cos_table(n)
    s = scales(n, ortho)
    return [s[k] * sum(t[k * (2 * i + 1) % (4 * n)] * x[i] for i in range(n)) for k in range(n)]


def idct(c, ortho):
    n = len(c)
    t = cos_table(n)
    if ortho:
        w = [s * v for s, v in zip(scales(n, True), c)]
    else:
        w = [(c[0] / 2) / n] + [v / n for v in c[1:]]
    return [sum(t[k * (2 * i + 1) % (4 * n)] * w[k] for k in range(n)) for i in range(n)]


def both(cid, x, why, hand=None):
    x = [D(v) for v in x]
    for ortho in (True, False):
        tag = "" if ortho else "_unnormalized"
        out = dct(x, ortho)
        if hand and ortho in hand:
            assert all(abs(a - b) < D(10) ** -40 for a, b in zip(out, hand[ortho])), (cid, ortho)
        back = idct(out, ortho)
        assert all(abs(a - b) < D(10) ** -40 for a, b in zip(back, x)), (cid, "inverse")
        args = {"samples": [float(v) for v in x]}
        iargs = {"coefficients": [float(v) for v in out]}
        if not ortho:
            args["orthonormal"] = False
            iargs["orthonormal"] = False
        scaling = "orthonormal" if ortho else "unnormalized (2 times the sum)"
        cases.append({"id": f"dct.{cid}{tag}", "op": "dct", "args": args,
                      "expected": [float(v) for v in out], "tol": TOL,
                      "source": f"{why}; {scaling}, exact cosines in decimal"})
        cases.append({"id": f"idct.{cid}{tag}", "op": "idct", "args": iargs,
                      "expected": [float(v) for v in x], "tol": TOL,
                      "source": f"inverse of dct.{cid}{tag}: gives back the samples ({why})"})


both("single", [3], "N = 1: X[0] = s_0 x[0], s_0 = 1 or 2", {True: [D(3)], False: [D(6)]})
both("constant", [2, 2, 2, 2], "a constant has only k = 0: the cosines for k >= 1 sum to 0",
     {True: [D(4), 0, 0, 0], False: [D(16), 0, 0, 0]})
both("pair", [1, 0], "N = 2, x = [1, 0]: X = [1, cos(pi/4)] scaled",
     {True: [R2 / 2, R2 / 2], False: [D(2), R2]})
both("impulse", [0, 1, 0, 0], "N = 4, impulse at n = 1: X[k] = s_k cos(3 pi k / 8)",
     {True: [D(1) / 2, S8 / R2, -R2 / 2 / R2, -C8 / R2]})  # s_k = 1/2, then 1/sqrt(2)
both("basis", [C8, S8, -S8, -C8], "N = 4, x[n] = cos(pi (2n+1)/8), the k = 1 basis: X = "
     "sqrt(N/2) at k = 1 alone", {True: [0, R2, 0, 0]})


def err(op, cid, args, why):
    cases.append({"id": f"{op}.{cid}", "op": op, "args": args, "error": "invalid_argument",
                  "source": why})


err("dct", "empty", {"samples": []}, "needs at least one value")
err("dct", "nan", {"samples": [1.0, "nan"]}, "values must be finite")
err("dct", "inf", {"samples": ["inf"]}, "values must be finite")
err("idct", "empty", {"coefficients": []}, "needs at least one value")
err("idct", "nan", {"coefficients": ["nan", 0.0]}, "values must be finite")

doc = {
    "schema": 1,
    "suite": "dct",
    "description": "DCT-II and its inverse (conventions: DCT-II; ADR 0156).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "dct.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/dct.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
