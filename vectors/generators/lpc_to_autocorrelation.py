"""Writes vectors/cases/lpc_to_autocorrelation.json, stdlib only.

Autocorrelation of a prediction-error filter (conventions: Autocorrelation of a
prediction-error filter; ADR 0220). The step-down gives k, then r[0] = s / prod(1 - |k|^2) and
Levinson solved for r (ADR 0214), all in exact fractions (complex cases in complex). Each case is
cross-checked against the normal equations sum_j a_j r[m - j] = 0 (1 <= m <= lags) and
sum_j a_j r[-j] = s, with r[-j] = conj r[j].

Run from the repo root: python vectors/generators/lpc_to_autocorrelation.py [--check]
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


def stepdown(a):
    cur = list(a)
    k = []
    for m in range(len(a) - 1, 0, -1):
        km = cur[m]
        k.insert(0, km)
        cur = [(cur[j] - km * conj(cur[m - j])) / (1 - mag2(km)) for j in range(m)]
    return k


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


def model(a, s, lags):
    if len(a) == 1:
        return [s] + [0] * lags
    k = stepdown(a)
    prod = 1
    for v in k:
        prod = prod * (1 - mag2(v))
    return autocorr(k, s / prod, lags)


def at(r, m):
    return r[m] if m >= 0 else conj(r[-m])


def enc(vs):
    if any(isinstance(v, complex) for v in vs):
        return {"re": [complex(v).real for v in vs], "im": [complex(v).imag for v in vs]}
    return [float(v) for v in vs]


def add(cid, a, s, lags, why):
    r = model(a, s, lags)
    p = len(a) - 1
    if lags >= p:
        for m in range(1, lags + 1):
            assert abs(sum(a[j] * at(r, m - j) for j in range(p + 1))) < 1e-12, (cid, m)
        assert abs(sum(a[j] * at(r, -j) for j in range(p + 1)) - s) < 1e-12, cid
    cases.append({"id": f"lpc_to_autocorrelation.{cid}", "op": "lpc_to_autocorrelation",
                  "args": {"coefficients": enc(a), "error": float(s), "lags": lags},
                  "expected": enc(r), "tol": TOL, "source": why})
    return r


r = add("order_two", [1, Fr(7, 20), Fr(-3, 10)], Fr(273, 400), 2,
        "ADR 0214's k = [1/2, -3/10], P = 1: s = (3/4)(91/100) = 273/400, r = [1, -1/2, 19/40]")
assert r == [1, Fr(-1, 2), Fr(19, 40)]
r = add("ar1", [1, Fr(1, 2)], Fr(3, 2), 4, "AR(1): r0 = s/(1 - 1/4) = 2, r[m] = 2 (-1/2)^m")
assert r == [2 * Fr(-1, 2) ** m for m in range(5)]
add("extended", [1, Fr(7, 20), Fr(-3, 10)], Fr(1), 7, "past the order: the AR extension")
add("fewer_lags", [1, Fr(1, 3), Fr(1, 4), Fr(-1, 8)], Fr(2), 1, "lags < order")
add("white", [1], Fr(5), 3, "order 0: [5, 0, 0, 0]")
add("burg_three_samples", [1, Fr(-144, 85), Fr(77, 85)], Fr(14, 3) * Fr(17, 81) * Fr(1296, 7225), 3,
    "ADR 0205's x = [1, 2, 3] model with r0 = 14/3")
add("complex", [1, -0.2 + 0.1j, 0.25j], 1.5, 4, "complex: the normal equations with conj")


def err(cid, why, **args):
    cases.append({"id": f"lpc_to_autocorrelation.{cid}", "op": "lpc_to_autocorrelation",
                  "args": args, "error": "invalid_argument", "source": why})


err("not_minimum_phase", "a = [1, 0, 1] has k2 = 1", coefficients=[1.0, 0.0, 1.0], error=1.0,
    lags=3)
err("a0", "coefficients[0] must be 1", coefficients=[2.0, 0.5], error=1.0, lags=3)
err("empty", "coefficients must not be empty", coefficients=[], error=1.0, lags=3)
err("nan", "coefficients must be finite", coefficients=[1.0, "nan"], error=1.0, lags=3)
err("zero_error", "error must be positive", coefficients=[1.0, 0.5], error=0.0, lags=3)
err("negative_lags", "lags must be at least 0", coefficients=[1.0, 0.5], error=1.0, lags=-1)

doc = {
    "schema": 1,
    "suite": "lpc_to_autocorrelation",
    "description": "Autocorrelation of a prediction-error filter (conventions: Autocorrelation of"
    " a prediction-error filter; ADR 0220).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "lpc_to_autocorrelation.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/lpc_to_autocorrelation.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
