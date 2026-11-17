"""Writes vectors/cases/line_spectral_frequencies.json, stdlib only.

Line spectral frequencies (conventions: Line spectral frequencies; ADR 0208). On the unit
circle P and Q reduce to quadratics in x = cos(w) once the trivial factors (1 +- z^-1) and
(1 - z^-2) are divided out, so orders 1 to 3 have closed forms:
  order 1: w = acos(-a1)
  order 2: cos w = (1 - a1 - a2)/2 (from P), cos w = -(1 + a1 - a2)/2 (from Q)
  order 3: 2x^2 + (a1 + a3)x + (a2 - 1) = 0 (from P), cos w = (a3 - a1)/2 (from Q)
The filters are expanded from chosen roots inside the unit circle.

Run from the repo root: python vectors/generators/line_spectral_frequencies.py [--check]
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
    assert all(-1 < x < 1 for x in xs), xs
    return sorted(math.acos(x) for x in xs)


def add(cid, a, why):
    w = closed(a)
    assert all(w[i + 1] - w[i] > 1e-6 for i in range(len(w) - 1))
    cases.append({"id": f"line_spectral_frequencies.{cid}", "op": "line_spectral_frequencies",
                  "args": {"coefficients": a}, "expected": w, "tol": TOL, "source": why})


add("order_one", [1.0, 0.5], "A = 1 + 0.5 z^-1: w = acos(-0.5) = 2 pi/3")
add("order_one_negative", [1.0, -0.9], "A = 1 - 0.9 z^-1: w = acos(0.9)")
add("order_two_real", expand([0.5, -0.25]),
    "roots 0.5, -0.25: a = [1, -0.25, -0.125]; cos w = (1 - a1 - a2)/2, -(1 + a1 - a2)/2")
add("order_two_resonant", expand([0.9 * cmath.exp(0.7j), 0.9 * cmath.exp(-0.7j)]),
    "roots 0.9 e^(+-0.7i): the order-2 closed form")
add("order_three", expand([0.5, 0.8 * cmath.exp(2j), 0.8 * cmath.exp(-2j)]),
    "roots 0.5, 0.8 e^(+-2i): 2x^2 + (a1 + a3)x + (a2 - 1) = 0 and cos w = (a3 - a1)/2")
add("order_three_mixed", expand([-0.3, 0.6 * cmath.exp(0.4j), 0.6 * cmath.exp(-0.4j)]),
    "roots -0.3, 0.6 e^(+-0.4i): the order-3 closed form")
add("order_three_flat", [1.0, 0.0, 0.0, 0.0],
    "A = 1: P = 1 + z^-4, Q = 1 - z^-4; 2x^2 - 1 = 0 and x = 0: w = pi/4, pi/2, 3 pi/4")


def err(cid, why, **args):
    cases.append({"id": f"line_spectral_frequencies.{cid}", "op": "line_spectral_frequencies",
                  "args": args, "error": "invalid_argument", "source": why})


err("a0_not_one", "coefficients[0] must be 1", coefficients=[2.0, 0.5])
err("order_zero", "the filter must have order at least 1", coefficients=[1.0])
err("not_minimum_phase", "A = 1 + 2 z^-1: F_P = 2 cos w + 4 > 0 and F_Q = 2 sin w > 0 on (0, pi)",
    coefficients=[1.0, 2.0])
err("nan_coefficient", "coefficients must be finite", coefficients=[1.0, "nan"])

doc = {
    "schema": 1,
    "suite": "line_spectral_frequencies",
    "description": "Line spectral frequencies (conventions: Line spectral frequencies; ADR 0208).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "line_spectral_frequencies.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/line_spectral_frequencies.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
