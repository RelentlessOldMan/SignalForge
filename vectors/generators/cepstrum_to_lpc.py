"""Writes vectors/cases/cepstrum_to_lpc.json, stdlib only.

Cepstrum to prediction filter (conventions: Cepstrum to prediction filter; ADR 0222). From
chosen roots r_i, the cepstrum is c_n = (sum_i r_i^n)/n (c_0 = ln sigma, here an arbitrary
value since it is unused) and the expected filter is the coefficients of prod (1 - r_i z^-1), in
exact fractions (complex roots in complex).

Run from the repo root: python vectors/generators/cepstrum_to_lpc.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def poly(roots):
    a = [1]
    for r in roots:
        a = [(a[j] if j < len(a) else 0) - (r * a[j - 1] if j >= 1 else 0)
             for j in range(len(a) + 1)]
    return a


def cep(roots, c0, length):
    return [c0] + [sum(r**n for r in roots) / n for n in range(1, length)]


def enc(vs):
    if any(isinstance(v, complex) for v in vs):
        return {"re": [complex(v).real for v in vs], "im": [complex(v).imag for v in vs]}
    return [float(v) for v in vs]


def add(cid, c, a, why):
    cases.append({"id": f"cepstrum_to_lpc.{cid}", "op": "cepstrum_to_lpc",
                  "args": {"cepstrum": enc(c), "order": len(a) - 1}, "expected": enc(a),
                  "tol": TOL, "source": why})


roots = [Fr(-1, 2)]
add("order_one", cep(roots, Fr(1, 3), 2), poly(roots), "a1 = 1/2: c1 = -1/2, a = [1, 1/2]")
assert poly(roots) == [1, Fr(1, 2)]
roots = [Fr(1, 2), Fr(-1, 3)]
add("two_real_roots", cep(roots, Fr(0), 3), poly(roots),
    "roots 1/2, -1/3: c = [0, 1/6, 13/72], a = [1, -1/6, -1/6]")
assert poly(roots) == [1, Fr(-1, 6), Fr(-1, 6)]
assert cep(roots, 0, 3)[1:] == [Fr(1, 6), Fr(13, 72)]
roots = [Fr(1, 2), Fr(-1, 3)]
add("extra_values", cep(roots, Fr(-2), 8), poly(roots), "cepstrum longer than order + 1")
add("truncated", cep(roots, Fr(0), 3), [1, Fr(-1, 6)], "order 1 of an order-2 cepstrum: a1 = -c1")
roots = [Fr(3, 4), Fr(-1, 2), Fr(1, 5), Fr(2, 3)]
add("order_four", cep(roots, Fr(1, 2), 5), poly(roots), "roots 3/4, -1/2, 1/5, 2/3")
z = 0.3 + 0.4j
roots = [z, z.conjugate()]
a = poly(roots)
add("conjugate_pair", [0.0] + [v.real for v in cep(roots, 0, 3)[1:]], [v.real for v in a],
    "roots 0.3 +- 0.4j: a = [1, -0.6, 0.25]")
assert abs(a[1] + 0.6) < 1e-15 and abs(a[2] - 0.25) < 1e-15
roots = [0.5j, -0.25 + 0.25j]
add("complex", cep(roots, 0j, 4), poly(roots), "complex roots 0.5j, -0.25 + 0.25j")


def err(cid, why, **args):
    cases.append({"id": f"cepstrum_to_lpc.{cid}", "op": "cepstrum_to_lpc", "args": args,
                  "error": "invalid_argument", "source": why})


err("too_short", "cepstrum must have order + 1 values", cepstrum=[0.0, 0.5], order=2)
err("order_zero", "order must be at least 1", cepstrum=[0.0, 0.5], order=0)
err("empty", "cepstrum must not be empty", cepstrum=[], order=1)
err("nan", "cepstrum must be finite", cepstrum=[0.0, "nan"], order=1)

doc = {
    "schema": 1,
    "suite": "cepstrum_to_lpc",
    "description": "Cepstrum to prediction filter (conventions: Cepstrum to prediction filter;"
    " ADR 0222).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "cepstrum_to_lpc.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/cepstrum_to_lpc.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
