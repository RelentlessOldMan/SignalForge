"""Writes vectors/cases/cepstral_distance.json, stdlib only.

Cepstral distance between AR models (conventions: Cepstral distance between AR models;
ADR 0218). Each filter is built from its poles, A = prod(1 - p z^-1), whose cepstrum of 1/A is
c_n = sum p^n / n in closed form (order 1: c_n = (-a1)^n / n). Real cases are exact fractions
under the square root.

Run from the repo root: python vectors/generators/cepstral_distance.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-12}
cases = []


def poly(poles):
    a = [1]
    for p in poles:
        a = [(a[j] if j < len(a) else 0) - (p * a[j - 1] if j >= 1 else 0)
             for j in range(len(a) + 1)]
    return a


def ceps(poles, n):
    return [sum(p**m for p in poles) / m for m in range(1, n + 1)]


def enc(vs):
    if any(isinstance(v, complex) for v in vs):
        return {"re": [complex(v).real for v in vs], "im": [complex(v).imag for v in vs]}
    return [float(v) for v in vs]


def add(cid, pr, pt, n, why):
    cr, ct = ceps(pr, n), ceps(pt, n)
    if any(isinstance(v, complex) for v in pr + pt):
        d = math.sqrt(sum(abs(complex(u) - complex(v)) ** 2 for u, v in zip(cr, ct)))
    else:
        d = math.sqrt(sum((u - v) ** 2 for u, v in zip(cr, ct)))
    cases.append({"id": f"cepstral_distance.{cid}", "op": "cepstral_distance",
                  "args": {"reference": enc(poly(pr)), "test": enc(poly(pt)),
                           "num_coefficients": n},
                  "expected": d, "tol": TOL, "source": why})
    return d


assert poly([Fr(-1, 2)]) == [1, Fr(1, 2)]
add("identical", [Fr(1, 2), Fr(-1, 3)], [Fr(1, 2), Fr(-1, 3)], 6, "equal models: 0")
d = add("order_one", [Fr(-1, 2)], [Fr(1, 4)], 3,
        "a = 1/2 vs -1/4: c = -1/2, 1/8, -1/24 and 1/4, 1/32, 1/192")
assert d == math.sqrt(float((Fr(-3, 4)) ** 2 + (Fr(3, 32)) ** 2 + (Fr(-9, 192)) ** 2))
add("one_coefficient", [Fr(-1, 2)], [Fr(1, 4)], 1, "L = 1: |c_1 difference| = 3/4")
add("order_two_vs_white", [Fr(1, 2), Fr(-1, 3)], [], 5,
    "poles 1/2, -1/3 (a = [1, -1/6, -1/6]) vs A = 1: c_n = ((1/2)^n + (-1/3)^n)/n")
add("order_two_vs_three", [Fr(3, 5), Fr(-2, 5)], [Fr(1, 4), Fr(1, 2), Fr(-7, 10)], 8,
    "real poles of orders 2 and 3")
add("complex", [0.5j], [0.3 + 0.4j, -0.2 + 0j], 6,
    "complex poles: A = 1 - 0.5j z^-1 vs (1 - (0.3 + 0.4j) z^-1)(1 + 0.2 z^-1)")
add("conjugate_pair", [0.6 + 0.3j, 0.6 - 0.3j], [Fr(1, 2)], 7,
    "a real filter with a complex-conjugate pole pair: c_n = 2 Re(p^n)/n")


def err(cid, why, **args):
    cases.append({"id": f"cepstral_distance.{cid}", "op": "cepstral_distance", "args": args,
                  "error": "invalid_argument", "source": why})


base = {"reference": [1.0, 0.5], "test": [1.0, -0.25], "num_coefficients": 4}
err("reference_not_minimum_phase", "a = [1, 0, 1] has k2 = 1",
    **{**base, "reference": [1.0, 0.0, 1.0]})
err("test_not_minimum_phase", "a = [1, 2] has k1 = 2", **{**base, "test": [1.0, 2.0]})
err("test_a0", "test[0] must be 1", **{**base, "test": [2.0, 0.5]})
err("reference_empty", "reference must not be empty", **{**base, "reference": []})
err("test_nan", "test must be finite", **{**base, "test": [1.0, "nan"]})
err("zero_coefficients", "num_coefficients must be at least 1", **{**base, "num_coefficients": 0})

doc = {
    "schema": 1,
    "suite": "cepstral_distance",
    "description": "Cepstral distance between AR models (conventions: Cepstral distance between"
    " AR models; ADR 0218).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "cepstral_distance.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/cepstral_distance.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
