"""Writes vectors/cases/weighting_filters.json, stdlib only.

The A and C weighting filters (conventions: Weighting filters; ADR 0165): the analog factors
s/(s + w) and w/(s + w), w = 2 pi f_k with the IEC 61672-1 poles, each by the bilinear transform
with K = 2 fs, two per section, the first section divided by the analog magnitude at
K tan(pi 1000/fs). In 60-digit decimal, with pi from Machin's formula and tan from Taylor sine
and cosine.

Run from the repo root: python vectors/generators/weighting_filters.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from decimal import Decimal as D
from decimal import getcontext

getcontext().prec = 60
TOL = {"abs": 1e-12, "rel": 1e-11}
cases = []
F1, F2, F3, F4 = D("20.598997"), D("107.65265"), D("737.86223"), D("12194.217")


def arctan_inv(x):
    """arctan(1/x) by its series."""
    total, term, k, sign = D(0), D(1) / x, 1, 1
    while term > D(10) ** -70:
        total += sign * term / k
        term /= x * x
        k += 2
        sign = -sign
    return total


PI = 4 * (4 * arctan_inv(5) - arctan_inv(239))
assert str(PI).startswith("3.14159265358979323846264338327950288419716939937510")


def _reduce(x):
    x = x % (2 * PI)
    return x - 2 * PI if x > PI else x


def cos(x):
    x = _reduce(x)
    total, term, k = D(1), D(1), 0
    while abs(term) > D(10) ** -70:
        k += 2
        term *= -x * x / ((k - 1) * k)
        total += term
    return total


def sin(x):
    x = _reduce(x)
    total, term, k = x, x, 1
    while abs(term) > D(10) ** -70:
        k += 2
        term *= -x * x / ((k - 1) * k)
        total += term
    return total


def design(fs, sections):
    fs = D(fs)
    k = 2 * fs
    x = PI * 1000 / fs
    big = k * sin(x) / cos(x)
    rows, mag = [], D(1)
    for pair in sections:
        fac = []
        for high, hz in pair:
            w = 2 * PI * hz
            d = k + w
            fac.append((k / d, -k / d, (w - k) / d) if high else (w / d, w / d, (w - k) / d))
            mag *= (big if high else w) / (big * big + w * w).sqrt()
        (p0, p1, pa), (q0, q1, qa) = fac
        rows.append([p0 * q0, p0 * q1 + p1 * q0, p1 * q1, D(1), pa + qa, pa * qa])
    rows[0][:3] = [v / mag for v in rows[0][:3]]
    return [[float(v) for v in row] for row in rows]


A = [[(True, F1), (True, F1)], [(True, F2), (True, F3)], [(False, F4), (False, F4)]]
C = [[(True, F1), (True, F1)], [(False, F4), (False, F4)]]
for op, secs, rates in (("a_weighting_sos", A, (48000.0, 44100.0, 8000.0, 192000.0)),
                        ("c_weighting_sos", C, (48000.0, 16000.0))):
    for fs in rates:
        cases.append({"id": f"{op}.fs_{int(fs)}", "op": op, "args": {"sample_rate": fs},
                      "expected": design(fs, secs), "tol": TOL,
                      "source": "bilinear transform of each analog factor in 60-digit decimal, "
                                "gain from the analog magnitude at K tan(pi 1000/fs)"})
    for cid, v, why in (("at_2000", 2000.0, "sample_rate must be above 2000 Hz"),
                        ("zero", 0.0, "sample_rate must be above 2000 Hz"),
                        ("negative", -48000.0, "sample_rate must be above 2000 Hz"),
                        ("nan", "nan", "sample_rate must be finite"),
                        ("inf", "inf", "sample_rate must be finite")):
        cases.append({"id": f"{op}.{cid}", "op": op, "args": {"sample_rate": v},
                      "error": "invalid_argument", "source": why})

doc = {
    "schema": 1,
    "suite": "weighting_filters",
    "description": "A and C weighting filters (conventions: Weighting filters; ADR 0165).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "weighting_filters.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/weighting_filters.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
