"""Writes vectors/cases/lsf_to_lpc.json, stdlib only.

LSF to prediction filter (conventions: LSF to prediction filter; ADR 0209). Each filter is
expanded from chosen roots inside the unit circle, and its LSFs come from the closed forms of
ADR 0208 (quadratics in cos w for orders 1 to 3); the expected output is the original filter.
One order-4 case multiplies the factors out here with plain lists.

Run from the repo root: python vectors/generators/lsf_to_lpc.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import cmath
import json
import math
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def expand(roots):
    a = [1 + 0j]
    for r in roots:
        a = [x - r * y for x, y in zip(a + [0j], [0j] + a)]
    assert all(abs(v.imag) < 1e-15 for v in a)
    return [v.real for v in a]


def closed(a):
    p = len(a) - 1
    if p == 1:
        xs = [-a[1]]
    elif p == 2:
        xs = [(1 - a[1] - a[2]) / 2, -(1 + a[1] - a[2]) / 2]
    else:
        b, c = a[1] + a[3], a[2] - 1
        d = math.sqrt(b * b - 8 * c)
        xs = [(-b + d) / 4, (-b - d) / 4, (a[3] - a[1]) / 2]
    return sorted(math.acos(x) for x in xs)


def add(cid, a, why, w=None):
    w = closed(a) if w is None else w
    cases.append({"id": f"lsf_to_lpc.{cid}", "op": "lsf_to_lpc", "args": {"frequencies": w},
                  "expected": a, "tol": TOL, "source": why})


add("order_one", [1.0, 0.5], "w = acos(-0.5) = 2 pi/3 inverts to A = 1 + 0.5 z^-1")
add("order_two_real", expand([0.5, -0.25]), "roots 0.5, -0.25: LSFs by the order-2 closed form")
add("order_two_resonant", expand([0.9 * cmath.exp(0.7j), 0.9 * cmath.exp(-0.7j)]),
    "roots 0.9 e^(+-0.7i): LSFs by the order-2 closed form")
add("order_three", expand([0.5, 0.8 * cmath.exp(2j), 0.8 * cmath.exp(-2j)]),
    "roots 0.5, 0.8 e^(+-2i): LSFs by the order-3 closed form")
add("order_three_flat", [1.0, 0.0, 0.0, 0.0], "w = pi/4, pi/2, 3 pi/4 are the LSFs of A = 1",
    [math.pi / 4, math.pi / 2, 3 * math.pi / 4])


def mul(x, y):
    z = [0.0] * (len(x) + len(y) - 1)
    for i, u in enumerate(x):
        for j, v in enumerate(y):
            z[i + j] += u * v
    return z


w4 = [0.3, 0.9, 1.5, 2.2]
pp = mul(mul([1.0, 1.0], [1.0, -2 * math.cos(w4[0]), 1.0]), [1.0, -2 * math.cos(w4[2]), 1.0])
qq = mul(mul([1.0, -1.0], [1.0, -2 * math.cos(w4[1]), 1.0]), [1.0, -2 * math.cos(w4[3]), 1.0])
assert abs(pp[5] + qq[5]) < 1e-15
add("order_four", [(u + v) / 2 for u, v in zip(pp[:5], qq[:5])],
    "w = 0.3, 0.9, 1.5, 2.2: P = (1 + z^-1)(w0)(w2), Q = (1 - z^-1)(w1)(w3), a = (P + Q)/2",
    w4)


def err(cid, why, **args):
    cases.append({"id": f"lsf_to_lpc.{cid}", "op": "lsf_to_lpc", "args": args,
                  "error": "invalid_argument", "source": why})


err("empty", "frequencies must not be empty", frequencies=[])
err("not_ascending", "frequencies must be strictly ascending", frequencies=[1.0, 0.5])
err("repeated", "frequencies must be strictly ascending", frequencies=[1.0, 1.0])
err("zero", "frequencies must lie in (0, pi)", frequencies=[0.0, 1.0])
err("above_pi", "frequencies must lie in (0, pi)", frequencies=[1.0, 3.2])
err("nan", "frequencies must be finite", frequencies=[0.5, "nan"])

doc = {
    "schema": 1,
    "suite": "lsf_to_lpc",
    "description": "LSF to prediction filter (conventions: LSF to prediction filter; ADR 0209).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "lsf_to_lpc.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/lsf_to_lpc.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
