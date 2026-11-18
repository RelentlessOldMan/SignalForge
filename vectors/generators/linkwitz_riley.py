"""Writes vectors/cases/linkwitz_riley.json, stdlib only.

Linkwitz-Riley crossover (conventions: Linkwitz-Riley crossover; ADR 0284). Each band is the
stdlib Butterworth biquads of conventions: Butterworth design (each pole pair's Q, prewarped K,
bilinear transform; the derivation vectors/generators/iir.py uses) twice over. The first high
section's numerator is negated when the Butterworth order is odd. The generator checks
|low + high| = 1 and |low| = |high| = 1/2 at the cutoff, numerically.

Run from the repo root: python vectors/generators/linkwitz_riley.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import cmath
import json
import math
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def butterworth(order, cutoff, fs, high):
    k = math.tan(math.pi * cutoff / fs)
    rows = []
    if order % 2:
        if high:
            rows.append([1 / (k + 1), -1 / (k + 1), 0.0, 1.0, (k - 1) / (k + 1), 0.0])
        else:
            rows.append([k / (k + 1), k / (k + 1), 0.0, 1.0, (k - 1) / (k + 1), 0.0])
    for i in range(order // 2 - 1, -1, -1):
        iq = 2 * math.sin(math.pi * (2 * i + 1) / (2 * order))
        d = k * k + k * iq + 1
        a = [1.0, 2 * (k * k - 1) / d, (k * k - k * iq + 1) / d]
        b = [1 / d, -2 / d, 1 / d] if high else [k * k / d, 2 * k * k / d, k * k / d]
        rows.append(b + a)
    return rows


def response(rows, f, fs):
    z = cmath.exp(-2j * math.pi * f / fs)
    h = 1
    for b0, b1, b2, a0, a1, a2 in rows:
        h *= (b0 + b1 * z + b2 * z * z) / (a0 + a1 * z + a2 * z * z)
    return h


def add(cid, order, fc, fs, why):
    n = order // 2
    lo, hi = butterworth(n, fc, fs, False), butterworth(n, fc, fs, True)
    low = [list(r) for r in lo + lo]
    high = [list(r) for r in hi + hi]
    if n % 2:
        high[0][:3] = [-v for v in high[0][:3]]
    for k in range(1, 40):
        f = fs / 2 * k / 40
        assert abs(abs(response(low, f, fs) + response(high, f, fs)) - 1) < 1e-12
    assert abs(abs(response(low, fc, fs)) - 0.5) < 1e-12
    assert abs(abs(response(high, fc, fs)) - 0.5) < 1e-12
    cases.append({"id": f"linkwitz_riley.{cid}", "op": "linkwitz_riley",
                  "args": {"order": order, "cutoff": fc, "sample_rate": fs},
                  "expected": {"low": low, "high": high}, "tol": TOL, "source": why})


add("lr2", 2, 1000.0, 48000.0, "LR2 at 1 kHz: first-order Butterworth squared, high inverted")
add("lr4", 4, 2500.0, 48000.0, "LR4 at 2.5 kHz: second-order Butterworth squared")
add("lr6", 6, 0.1, 1.0, "LR6 at 0.1 fs: third-order Butterworth squared, high inverted")
add("lr8", 8, 0.3, 1.0, "LR8 at 0.3 fs: fourth-order Butterworth squared")


def err(cid, why, **args):
    base = {"order": 4, "cutoff": 1.0, "sample_rate": 8.0}
    base.update(args)
    cases.append({"id": f"linkwitz_riley.{cid}", "op": "linkwitz_riley", "args": base,
                  "error": "invalid_argument", "source": why})


err("order_odd", "order must be even", order=3)
err("order_zero", "order must be at least 2", order=0)
err("cutoff_nyquist", "cutoff must be below fs/2", cutoff=4.0)

doc = {
    "schema": 1,
    "suite": "linkwitz_riley",
    "description": "Linkwitz-Riley crossover (conventions: Linkwitz-Riley crossover; ADR 0284).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "linkwitz_riley.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/linkwitz_riley.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
