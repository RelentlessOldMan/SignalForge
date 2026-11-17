"""Writes vectors/cases/itakura_saito.json, stdlib only.

Itakura-Saito distance between AR models (conventions: Itakura-Saito distance between AR
models; ADR 0217). Real cases evaluate q / s_t - ln(s_r / s_t) - 1 exactly in fractions apart
from the log: q = sum_ij a_t[i] a_t[j] r_r[j - i], with r_r from the reflection coefficients of
the reference by Levinson solved for r (ADR 0214), k recovered by the step-down. Every case,
complex included, is cross-checked by integrating S_r/S_t - ln(S_r/S_t) - 1 numerically on a
4096-point grid, S = s / |A(e^jw)|^2.

Run from the repo root: python vectors/generators/itakura_saito.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import cmath
import json
import math
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


def closed(ar, sr, at, st):
    lags = len(at) - 1
    if len(ar) > 1:
        k = stepdown(ar)
        prod = 1
        for v in k:
            prod = prod * (1 - mag2(v))
        r = autocorr(k, sr / prod, lags)
    else:
        r = [sr] + [0] * lags
    q = 0
    for i in range(len(at)):
        for j in range(len(at)):
            rij = r[j - i] if j >= i else conj(r[i - j])
            q = q + at[i] * conj(at[j]) * rij
    return complex(q).real, float(q / st) if not isinstance(q, complex) else None


def numeric(ar, sr, at, st):
    grid = 4096
    total = 0.0
    for i in range(grid):
        w = 2 * math.pi * i / grid
        hr = sum(complex(c) * cmath.exp(-1j * w * j) for j, c in enumerate(ar))
        ht = sum(complex(c) * cmath.exp(-1j * w * j) for j, c in enumerate(at))
        ratio = (float(sr) / abs(hr) ** 2) / (float(st) / abs(ht) ** 2)
        total += ratio - math.log(ratio) - 1
    return total / grid


def enc(vs):
    if any(isinstance(v, complex) for v in vs):
        return {"re": [complex(v).real for v in vs], "im": [complex(v).imag for v in vs]}
    return [float(v) for v in vs]


def add(cid, ar, sr, at, st, why):
    q, ratio = closed(ar, sr, at, st)
    first = ratio if ratio is not None else q / float(st)
    d = first - math.log(float(sr) / float(st)) - 1
    assert abs(d - numeric(ar, sr, at, st)) < 1e-9, (cid, d, numeric(ar, sr, at, st))
    cases.append({"id": f"itakura_saito.{cid}", "op": "itakura_saito",
                  "args": {"reference": enc(ar), "reference_error": float(sr),
                           "test": enc(at), "test_error": float(st)},
                  "expected": d, "tol": TOL, "source": why})
    return d


d0 = add("identical", [1, Fr(1, 2)], Fr(1), [1, Fr(1, 2)], Fr(1),
         "equal models: q = r0 (1 - a^2) = s, d = 1 - 0 - 1 = 0")
assert abs(d0) < 1e-15
d1 = add("order_one", [1, Fr(1, 2)], Fr(1), [1, Fr(-1, 4)], Fr(2),
         "r0 = 4/3, r1 = -2/3; q = 4/3 (1 + 1/16) + 2(-1/4)(-2/3) = 7/4; d = 7/8 + ln 2 - 1")
assert abs(d1 - (-1 / 8 + math.log(2))) < 1e-15
add("order_one_swapped", [1, Fr(-1, 4)], Fr(2), [1, Fr(1, 2)], Fr(1),
    "the distance is not symmetric: the swapped pair")
add("white_test", [1, Fr(-3, 5)], Fr(1), [1], Fr(1),
    "a white test model: q = r0 = 1/(1 - 9/25) = 25/16, d = 25/16 - 1")
add("white_reference", [1], Fr(3), [1, Fr(1, 2), Fr(-1, 5)], Fr(2),
    "a white reference: q = 3 (1 + 1/4 + 1/25), d = q/2 - ln(3/2) - 1")
add("order_two_vs_three", [1, Fr(7, 20), Fr(-3, 10)], Fr(1, 2), [1, Fr(1, 3), Fr(1, 4), Fr(-1, 8)],
    Fr(3, 4), "orders 2 and 3 with the reference autocorrelation extended past its order")
add("complex", [1, 0.3 + 0.4j], 1.5, [1, -0.2 + 0.1j, 0.25j], 1.0,
    "complex models; the closed form agrees with the integral")


def err(cid, why, **args):
    cases.append({"id": f"itakura_saito.{cid}", "op": "itakura_saito", "args": args,
                  "error": "invalid_argument", "source": why})


base = {"reference": [1.0, 0.5], "reference_error": 1.0, "test": [1.0, -0.25], "test_error": 1.0}
err("reference_not_minimum_phase", "a = [1, 0, 1] has k2 = 1",
    **{**base, "reference": [1.0, 0.0, 1.0]})
err("test_not_minimum_phase", "a = [1, 2] has k1 = 2", **{**base, "test": [1.0, 2.0]})
err("test_a0", "test[0] must be 1", **{**base, "test": [2.0, 0.5]})
err("reference_empty", "reference must not be empty", **{**base, "reference": []})
err("reference_nan", "reference must be finite", **{**base, "reference": [1.0, "nan"]})
err("zero_reference_error", "reference_error must be positive", **{**base, "reference_error": 0.0})
err("inf_test_error", "test_error must be finite", **{**base, "test_error": "inf"})

doc = {
    "schema": 1,
    "suite": "itakura_saito",
    "description": "Itakura-Saito distance between AR models (conventions: Itakura-Saito"
    " distance between AR models; ADR 0217).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "itakura_saito.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/itakura_saito.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
