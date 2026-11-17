"""Writes vectors/cases/burg.json, stdlib only.

Burg AR fit (conventions: Burg AR fit; ADR 0205). The 3-sample case comes from exact fractions,
order 1 from its closed form, and the rest from the forward/backward error recursion written out
here with plain lists.

Run from the repo root: python vectors/generators/burg.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def fit(x, p):
    f = [complex(v) for v in x]
    b = list(f)
    a = [1 + 0j]
    err = sum(abs(v) ** 2 for v in f) / len(f)
    ks = []
    for _ in range(p):
        fw, bw = f[1:], b[:-1]
        k = -2 * sum(u * v.conjugate() for u, v in zip(fw, bw)) / sum(
            abs(u) ** 2 + abs(v) ** 2 for u, v in zip(fw, bw))
        f = [u + k * v for u, v in zip(fw, bw)]
        b = [v + k.conjugate() * u for u, v in zip(fw, bw)]
        a = a + [0j]
        a = [a[j] + k * a[len(a) - 1 - j].conjugate() for j in range(len(a))]
        err *= 1 - abs(k) ** 2
        ks.append(k)
    return a, ks, err


def enc(vs, is_complex):
    if is_complex:
        return {"re": [complex(v).real for v in vs], "im": [complex(v).imag for v in vs]}
    return [complex(v).real for v in vs]


def add(cid, x, p, why, a, ks, err):
    is_complex = any(isinstance(v, complex) for v in x)
    cases.append({"id": f"burg.{cid}", "op": "burg",
                  "args": {"samples": enc(x, True) if is_complex else x, "order": p},
                  "expected": {"coefficients": enc(a, is_complex), "reflection": enc(ks, is_complex),
                               "error": float(err)},
                  "tol": TOL, "source": why})


k1, k2 = Fr(-8, 9), Fr(77, 85)
add("three_samples", [1.0, 2.0, 3.0], 2,
    "x = [1, 2, 3]: k1 = -2(2 + 6)/(4 + 1 + 9 + 4) = -8/9; f = [2 - 8/9, 3 - 16/9], b = [1 - 16/9,"
    " 2 - 24/9]: k2 = 77/85; a = [1, -8/9 (1 + 77/85), 77/85]; sigma^2 = (14/3)(1 - k1^2)"
    "(1 - k2^2)",
    [1, k1 * (1 + k2), k2], [k1, k2], Fr(14, 3) * (1 - k1**2) * (1 - k2**2))

xo = [0.5, -1.0, 2.0, 1.5]
ko = -2 * sum(xo[i] * xo[i - 1] for i in range(1, 4)) / sum(xo[i] ** 2 + xo[i - 1] ** 2
                                                           for i in range(1, 4))
add("order_one", xo, 1, "closed form: k = -2 sum x[n] x[n-1] / sum (x[n]^2 + x[n-1]^2), "
    "sigma^2 = mean x^2 (1 - k^2)", [1, ko], [ko], sum(v * v for v in xo) / 4 * (1 - ko**2))

xc = [1 + 0j, 1j, -0.5 + 0.5j]
kc = -2 * sum(xc[i] * xc[i - 1].conjugate() for i in range(1, 3)) / sum(
    abs(xc[i]) ** 2 + abs(xc[i - 1]) ** 2 for i in range(1, 3))
add("complex_order_one", xc, 1, "closed form: k = -2 sum x[n] conj x[n-1] / sum (|x[n]|^2 + "
    "|x[n-1]|^2)", [1, kc], [kc], sum(abs(v) ** 2 for v in xc) / 3 * (1 - abs(kc) ** 2))

xr = [3.0, 1.0, -2.0, 0.0, 1.0, 2.5, -1.5]
add("order_three", xr, 3, "order 3 by the error recursion", *fit(xr, 3))
xz = [1 + 1j, -0.5 + 2j, 1.5 - 1j, 0.25j, -1 + 0j]
add("complex_order_two", xz, 2, "complex order 2 by the error recursion, conj(k) in the backward"
    " update", *fit(xz, 2))

a3, k3, e3 = fit([1.0, 2.0, 3.0], 2)
assert abs(k3[0] - k1) < 1e-15 and abs(k3[1] - k2) < 1e-15
assert abs(e3 - float(Fr(14, 3) * (1 - k1**2) * (1 - k2**2))) < 1e-15
assert abs(fit(xc, 1)[1][0] - kc) < 1e-15


def err(cid, why, **args):
    cases.append({"id": f"burg.{cid}", "op": "burg", "args": args, "error": "invalid_argument",
                  "source": why})


err("order_zero", "order must be at least 1", samples=[1.0, 2.0], order=0)
err("order_too_big", "order must be below the input length", samples=[1.0, 2.0], order=2)
err("all_zero", "the error energy is 0", samples=[0.0, 0.0, 0.0], order=1)
err("predictable", "x = [1, -1]: k = -2(-1)/2 = 1", samples=[1.0, -1.0], order=1)
err("nan_sample", "samples must be finite", samples=[1.0, "nan", 2.0], order=1)

doc = {
    "schema": 1,
    "suite": "burg",
    "description": "Burg AR fit (conventions: Burg AR fit; ADR 0205).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "burg.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/burg.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
