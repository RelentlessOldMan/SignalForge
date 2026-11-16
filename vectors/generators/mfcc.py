"""Writes vectors/cases/mfcc.json, stdlib only.

MFCC of one frame (conventions: MFCC; ADR 0157): band energies W @ P, natural log of
max(E, floor), then the orthonormal DCT-II, all in 50-digit decimal from the float arguments.
The DCT uses exact cosines for N = 2, 3, 4 (cos(pi/6) = sqrt(3)/2, cos(pi/4) = sqrt(2)/2,
cos(pi/8) = sqrt(2 + sqrt(2))/2, cos(3 pi/8) = sqrt(2 - sqrt(2))/2).

Run from the repo root: python vectors/generators/mfcc.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from decimal import Decimal as D
from decimal import getcontext

getcontext().prec = 50
TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []
R2, R3 = D(2).sqrt(), D(3).sqrt()
QUARTER = {
    2: [D(1), R2 / 2],
    3: [D(1), R3 / 2, D(1) / 2],
    4: [D(1), (2 + R2).sqrt() / 2, R2 / 2, (2 - R2).sqrt() / 2],
}


def cos_table(n):
    q = QUARTER[n]
    first = q + [D(0)] + [-v for v in reversed(q[1:])]
    return first + [-v for v in first]


def dct(x):
    n = len(x)
    t = cos_table(n)
    s = [(D(1) / n).sqrt()] + [(D(2) / n).sqrt()] * (n - 1)
    return [s[k] * sum(t[k * (2 * i + 1) % (4 * n)] * x[i] for i in range(n)) for k in range(n)]


def mfcc(p, w, k, floor):
    p = [D(v) for v in p]
    bands = [sum(D(wk) * pk for wk, pk in zip(row, p)) for row in w]
    return dct([max(e, D(floor)).ln() for e in bands])[:k]


def case(cid, p, w, k, why, floor=None, hand=None):
    out = mfcc(p, w, k, 1e-10 if floor is None else floor)
    if hand is not None:
        assert all(abs(a - b) < D(10) ** -40 for a, b in zip(out, hand)), cid
    args = {"power_spectrum": p, "filterbank": w, "n_coefficients": k}
    if floor is not None:
        args["floor"] = floor
    cases.append({"id": f"mfcc.{cid}", "op": "mfcc", "args": args,
                  "expected": [float(v) for v in out], "tol": TOL, "source": why})


EYE3 = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
L2 = D(2).ln()
case("identity", [1.0, 2.0, 4.0], EYE3, 3,
     "identity bank: logs 0, ln 2, 2 ln 2; N = 3 DCT gives sqrt(3) ln 2, -sqrt(2) ln 2, 0",
     hand=[R3 * L2, -R2 * L2, D(0)])
case("equal_bands", [1.0, 1.0, 1.0], [[1.0, 1.0, 0.0], [0.0, 1.0, 1.0]], 2,
     "both bands are 2: ln 2 twice, so c_0 = sqrt(2) ln 2 and c_1 = 0", hand=[R2 * L2, D(0)])
case("truncated", [1.0, 2.0, 4.0], EYE3, 1, "the identity case keeping c_0 only: sqrt(3) ln 2",
     hand=[R3 * L2])
case("floor_default", [0.0, 0.0, 0.0, 0.0], [[1.0, 0, 0, 0], [0, 1.0, 0, 0], [0, 0, 1.0, 0],
     [0, 0, 0, 1.0]], 4, "all bands 0 hit the floor 1e-10: c_0 = 2 ln(1e-10), the rest 0")
case("floor_custom", [0.25, 0.0, 3.0], EYE3, 3,
     "floor 0.5 lifts 0.25 and 0 to 0.5: logs ln 0.5, ln 0.5, ln 3, N = 3 DCT", floor=0.5)
TRI = [[0.5, 1.0, 0.5, 0.0, 0.0, 0.0], [0.0, 0.5, 1.0, 0.5, 0.0, 0.0],
       [0.0, 0.0, 0.5, 1.0, 0.5, 0.0], [0.0, 0.0, 0.0, 0.5, 1.0, 0.5]]
case("triangles", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0], TRI, 2,
     "overlapping triangles: bands 4, 6, 8, 10, logs and N = 4 DCT in decimal")


def err(cid, change, why):
    args = {"power_spectrum": [1.0, 2.0, 4.0], "filterbank": EYE3, "n_coefficients": 2}
    args.update(change)
    cases.append({"id": f"mfcc.{cid}", "op": "mfcc", "args": args, "error": "invalid_argument",
                  "source": why})


err("no_coefficients", {"n_coefficients": 0}, "n_coefficients must be at least 1")
err("too_many_coefficients", {"n_coefficients": 4}, "n_coefficients must not exceed n_filters = 3")
err("negative_power", {"power_spectrum": [1.0, -1.0, 4.0]}, "power must be non-negative")
err("nan_power", {"power_spectrum": [1.0, "nan", 4.0]}, "power must be finite")
err("empty_power", {"power_spectrum": [], "filterbank": [[]]}, "needs at least one bin")
err("row_length", {"filterbank": [[1.0, 0.0], [0.0, 1.0]]}, "each row needs len(power) weights")
err("no_filters", {"filterbank": []}, "needs at least one filter")
err("negative_weight", {"filterbank": [[1.0, -0.5, 0.0], [0.0, 1.0, 0.0]]},
    "weights must be non-negative")
err("zero_floor", {"floor": 0.0}, "floor must be positive")
err("inf_floor", {"floor": "inf"}, "floor must be finite")

doc = {
    "schema": 1,
    "suite": "mfcc",
    "description": "MFCC of one frame (conventions: MFCC; ADR 0157).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "mfcc.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/mfcc.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
