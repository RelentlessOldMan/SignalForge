"""Writes vectors/cases/reflection_to_autocorrelation.json, stdlib only.

Autocorrelation of an AR model (conventions: Autocorrelation of an AR model; ADR 0214). The
expected values are the stated recursion in exact fractions (complex cases in complex). Each case
is cross-checked by a stdlib Levinson on the result, which must recover k and the error
P prod(1 - |k|^2); AR(1) is also checked against r[m] = P (-k)^m.

Run from the repo root: python vectors/generators/reflection_to_autocorrelation.py [--check]
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


def autocorr(k, power, lags):
    r = [power]
    a = [1]
    e = power
    for m in range(1, lags + 1):
        s = sum(a[j] * r[m - j] for j in range(1, len(a)))
        if m <= len(k):
            km = k[m - 1]
            r.append(-km * e - s)
            a = a + [0]
            a = [a[j] + km * conj(a[len(a) - 1 - j]) for j in range(len(a))]
            e = e * (1 - mag2(km))
        else:
            r.append(-s)
    return r


def levinson(r, p):
    a = [1]
    e = r[0]
    k = []
    for m in range(1, p + 1):
        km = -(r[m] + sum(a[j] * r[m - j] for j in range(1, m))) / e
        a = a + [0]
        a = [a[j] + km * conj(a[len(a) - 1 - j]) for j in range(len(a))]
        e = e * (1 - mag2(km))
        k.append(km)
    return k, e


def enc(vs):
    if any(isinstance(v, complex) for v in vs):
        return {"re": [complex(v).real for v in vs], "im": [complex(v).imag for v in vs]}
    return [float(v) for v in vs]


def add(cid, k, power, lags, why):
    r = autocorr(k, power, lags)
    p = min(len(k), lags)
    kk, e = levinson(r, p)
    assert all(abs(u - v) < 1e-12 for u, v in zip(kk, k)), cid
    prod = power
    for v in k[:p]:
        prod = prod * (1 - mag2(v))
    assert abs(e - prod) < 1e-12, cid
    cases.append({"id": f"reflection_to_autocorrelation.{cid}",
                  "op": "reflection_to_autocorrelation",
                  "args": {"reflection": enc(k), "power": float(power), "lags": lags},
                  "expected": enc(r), "tol": TOL, "source": why})
    return r


r1 = add("ar1", [Fr(-1, 2)], Fr(2), 4, "AR(1): r[m] = P (-k)^m = 2 (1/2)^m")
assert r1 == [Fr(2) * Fr(1, 2) ** m for m in range(5)]
add("lags_zero", [Fr(1, 3)], Fr(5), 0, "lags = 0: just r[0] = power")
r2 = add("order_two", [Fr(1, 2), Fr(-3, 10)], Fr(1), 2,
         "r1 = -k1 = -1/2; r2 = -k2 (1 - k1^2) + k1^2 = 9/40 + 1/4 = 19/40")
assert r2 == [1, Fr(-1, 2), Fr(19, 40)]
add("order_two_extended", [Fr(1, 2), Fr(-3, 10)], Fr(1), 6,
    "past p, r[m] = -(a1 r[m-1] + a2 r[m-2]) with a = [1, 7/20, -3/10]")
add("burg_three_samples", [Fr(-8, 9), Fr(77, 85)], Fr(14, 3), 3,
    "ADR 0205's x = [1, 2, 3] model, with power 14/3")
add("order_three", [Fr(1, 2), Fr(-1, 3), Fr(1, 4)], Fr(3), 5, "order 3 in exact fractions")
add("order_more_than_lags", [Fr(1, 2), Fr(-1, 3), Fr(1, 4)], Fr(1), 1,
    "lags < p: only k1 is used, r1 = -1/2")
add("complex", [0.3 + 0.4j, -0.2 + 0.1j], 2.0, 4, "complex k: the step-up uses conj")


def err(cid, why, **args):
    cases.append({"id": f"reflection_to_autocorrelation.{cid}",
                  "op": "reflection_to_autocorrelation", "args": args,
                  "error": "invalid_argument", "source": why})


err("unit_k", "every |k| < 1", reflection=[0.5, 1.0], power=1.0, lags=3)
err("empty", "reflection must not be empty", reflection=[], power=1.0, lags=3)
err("nan", "reflection must be finite", reflection=["nan"], power=1.0, lags=3)
err("zero_power", "power must be positive", reflection=[0.5], power=0.0, lags=3)
err("inf_power", "power must be finite", reflection=[0.5], power="inf", lags=3)
err("negative_lags", "lags must be at least 0", reflection=[0.5], power=1.0, lags=-1)

doc = {
    "schema": 1,
    "suite": "reflection_to_autocorrelation",
    "description": "Autocorrelation of an AR model (conventions: Autocorrelation of an AR model;"
    " ADR 0214).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "reflection_to_autocorrelation.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/reflection_to_autocorrelation.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
