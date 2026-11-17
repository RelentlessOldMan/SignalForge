"""Writes vectors/cases/lpc_cepstrum.json, stdlib only.

LPC cepstrum (conventions: LPC cepstrum; ADR 0207). Each case picks the roots r_i of
A(z) = prod (1 - r_i z^-1); then -ln A = sum_n (sum_i r_i^n)/n z^-n, so c_n = (sum_i r_i^n)/n
for n >= 1 and c_0 = ln(error)/2. The coefficients a are the expanded product.

Run from the repo root: python vectors/generators/lpc_cepstrum.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import cmath
import json
import math
import pathlib
import sys

TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def expand(roots):
    a = [1 + 0j]
    for r in roots:
        a = [x - r * y for x, y in zip(a + [0j], [0j] + a)]
    return a


def add(cid, roots, error, num, why, real_out):
    a = expand(roots)
    c = [complex(0.5 * math.log(error))] + [sum(r**n for r in roots) / n for n in range(1, num)]
    if real_out:
        assert all(abs(v.imag) < 1e-15 for v in a + c)
        coeffs = [v.real for v in a]
        exp = [v.real for v in c]
    else:
        coeffs = {"re": [v.real for v in a], "im": [v.imag for v in a]}
        exp = {"re": [v.real for v in c], "im": [v.imag for v in c]}
    cases.append({"id": f"lpc_cepstrum.{cid}", "op": "lpc_cepstrum",
                  "args": {"coefficients": coeffs, "error": error, "num_coefficients": num},
                  "expected": exp, "tol": TOL, "source": why})


add("order_one", [-0.5], 2.0, 6, "A = 1 + 0.5 z^-1: c_n = (-a_1)^n/n = (-0.5)^n/n, c_0 = ln(2)/2",
    True)
add("order_two_real_roots", [0.5, -0.25], 1.0, 8,
    "roots 0.5 and -0.25, a = [1, -0.25, -0.125]: c_n = (0.5^n + (-0.25)^n)/n, c_0 = 0", True)
rc = 0.6 * cmath.exp(1j)
add("order_two_conjugate_roots", [rc, rc.conjugate()], 0.3, 10,
    "roots 0.6 e^(+-i): c_n = 2 (0.6^n) cos(n)/n, c_0 = ln(0.3)/2", True)
add("complex_roots", [0.5j, 0.3], 1.5, 7,
    "roots 0.5i and 0.3, complex a: c_n = ((0.5i)^n + 0.3^n)/n, c_0 = ln(1.5)/2", False)
add("only_c0", [0.9], 4.0, 1, "num_coefficients = 1: just c_0 = ln(4)/2", True)
add("fewer_than_order", [0.5, -0.25, 0.1], 1.0, 3, "order 3, two terms past c_0", True)
cases.append({"id": "lpc_cepstrum.unit_filter", "op": "lpc_cepstrum",
              "args": {"coefficients": [1.0], "error": 1.0, "num_coefficients": 4},
              "expected": [0.0, 0.0, 0.0, 0.0], "tol": TOL,
              "source": "A = 1, error 1: ln 1 = 0, every c_n = 0"})


def err(cid, why, **args):
    cases.append({"id": f"lpc_cepstrum.{cid}", "op": "lpc_cepstrum", "args": args,
                  "error": "invalid_argument", "source": why})


err("a0_not_one", "coefficients[0] must be 1", coefficients=[2.0, 0.5], error=1.0,
    num_coefficients=3)
err("empty", "coefficients must not be empty", coefficients=[], error=1.0, num_coefficients=3)
err("zero_error", "error must be positive", coefficients=[1.0, 0.5], error=0.0, num_coefficients=3)
err("zero_count", "num_coefficients must be at least 1", coefficients=[1.0, 0.5], error=1.0,
    num_coefficients=0)
err("nan_coefficient", "coefficients must be finite", coefficients=[1.0, "nan"], error=1.0,
    num_coefficients=3)

doc = {
    "schema": 1,
    "suite": "lpc_cepstrum",
    "description": "LPC cepstrum (conventions: LPC cepstrum; ADR 0207).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "lpc_cepstrum.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/lpc_cepstrum.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
