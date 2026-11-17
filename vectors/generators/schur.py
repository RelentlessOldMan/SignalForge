"""Writes vectors/cases/schur.json, stdlib only.

Schur recursion (conventions: Schur recursion; ADR 0221). The reflection coefficients and the
error are computed by an independent Levinson-Durbin in exact fractions (complex cases in
complex), and each result is checked by rebuilding the order-p filter and its normal equations.

Run from the repo root: python vectors/generators/schur.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def conj(v):
    return v.conjugate() if isinstance(v, complex) else v


def mag2(v):
    return v * conj(v) if isinstance(v, Fr) else abs(v) ** 2


def at(r, m):
    return r[m] if m >= 0 else conj(r[-m])


def levinson(r, p):
    a = [1]
    e = r[0]
    k = []
    for m in range(1, p + 1):
        km = -sum(a[j] * r[m - j] for j in range(m)) / e
        k.append(km)
        a = a + [0]
        a = [a[j] + km * conj(a[m - j]) for j in range(m + 1)]
        e = e * (1 - mag2(km))
    for m in range(1, p + 1):
        assert abs(sum(a[j] * at(r, m - j) for j in range(p + 1))) < 1e-12
    assert abs(sum(a[j] * at(r, -j) for j in range(p + 1)) - e) < 1e-12
    return k, e


def enc(vs):
    if any(isinstance(v, complex) for v in vs):
        return {"re": [complex(v).real for v in vs], "im": [complex(v).imag for v in vs]}
    return [float(v) for v in vs]


def add(cid, r, p, why):
    k, e = levinson(r, p)
    cases.append({"id": f"schur.{cid}", "op": "schur", "args": {"r": enc(r), "order": p},
                  "expected": {"reflection": enc(k), "error": float(complex(e).real)},
                  "tol": TOL, "source": why})
    return k, e


k, e = add("adr_0214", [Fr(1), Fr(-1, 2), Fr(19, 40)], 2,
           "ADR 0214 in reverse: k = [1/2, -3/10], E = (3/4)(91/100) = 273/400")
assert k == [Fr(1, 2), Fr(-3, 10)] and e == Fr(273, 400)
k, e = add("first_order", [Fr(4), Fr(2)], 1, "k = -2/4 = -1/2, E = 4 (3/4) = 3")
assert k == [Fr(-1, 2)] and e == 3
k, e = add("ar1", [2 * Fr(-1, 2) ** m for m in range(5)], 4,
           "AR(1) r[m] = 2 (-1/2)^m: k = [1/2, 0, 0, 0], E = 3/2")
assert k == [Fr(1, 2), 0, 0, 0] and e == Fr(3, 2)
add("extra_lags", [Fr(3), Fr(1), Fr(-1, 2), Fr(1, 4), Fr(1, 8)], 2, "lags past the order ignored")
add("order_four", [Fr(5), Fr(2), Fr(-1), Fr(1, 2), Fr(1, 3)], 4, "order 4 in fractions")
add("complex", [2 + 0j, 0.5 + 0.5j, 0.25j, -0.1 + 0.2j], 3, "complex: conj in the recursion")


def err(cid, why, **args):
    cases.append({"id": f"schur.{cid}", "op": "schur", "args": args, "error": "invalid_argument",
                  "source": why})


err("not_positive_definite", "r = [1, 1]: k = -1", r=[1.0, 1.0], order=1)
err("zero_r0", "r[0] must be positive", r=[0.0, 0.0], order=1)
err("complex_r0", "r[0] must be real", r={"re": [1.0, 0.5], "im": [0.5, 0.0]}, order=1)
err("order_zero", "order must be at least 1", r=[1.0, 0.5], order=0)
err("too_few_lags", "r must have order + 1 lags", r=[1.0, 0.5], order=2)
err("nan", "r must be finite", r=[1.0, "nan"], order=1)

doc = {
    "schema": 1,
    "suite": "schur",
    "description": "Schur recursion (conventions: Schur recursion; ADR 0221).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "schur.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/schur.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
