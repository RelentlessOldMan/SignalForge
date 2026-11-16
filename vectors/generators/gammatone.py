"""Writes vectors/cases/gammatone.json, stdlib only.

Gammatone taps (conventions: Gammatone; ADR 0161): g(t) = t^(N-1) exp(-2 pi b ERB t)
cos(2 pi f_c t) at t = n/fs, with ERB = 24.7 (4.37 f_c/1000 + 1) (ADR 0160), divided by
|sum g e^(-j w_c n)|. Everything is in 60-digit decimal: pi from Machin's formula, cos and sin
from their Taylor series after reduction to [-pi, pi], exp from Decimal.exp.

Run from the repo root: python vectors/generators/gammatone.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from decimal import Decimal as D
from decimal import getcontext

getcontext().prec = 60
TOL = {"abs": 1e-13, "rel": 1e-11}
cases = []


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


assert abs(cos(PI / 3) - D(1) / 2) < D(10) ** -55 and abs(sin(PI / 6) - D(1) / 2) < D(10) ** -55


def taps(fc, fs, length, order, b):
    fc, fs, b = D(fc), D(fs), D(b)
    erb = D("24.7") * (D("4.37") * fc / 1000 + 1)
    g = []
    for n in range(length):
        t = n / fs
        power = D(1) if order == 1 else t ** (order - 1)
        g.append(power * (-2 * PI * b * erb * t).exp() * cos(2 * PI * fc * t))
    w = 2 * PI * fc / fs
    re = sum(v * cos(w * n) for n, v in enumerate(g))
    im = sum(v * sin(w * n) for n, v in enumerate(g))
    gain = (re * re + im * im).sqrt()
    return [v / gain for v in g]


def case(cid, fc, fs, length, why, order=4, b=1.019):
    out = taps(fc, fs, length, order, b)
    args = {"center_frequency": fc, "sample_rate": fs, "length": length}
    if order != 4:
        args["order"] = order
    if b != 1.019:
        args["bandwidth_factor"] = b
    cases.append({"id": f"gammatone.{cid}", "op": "gammatone", "args": args,
                  "expected": [float(v) for v in out], "tol": TOL, "source": why})


case("order4", 1000.0, 16000.0, 48, "N = 4, b = 1.019, f_c = 1 kHz at 16 kHz, 48 taps, closed form")
case("order1", 500.0, 8000.0, 24, "N = 1: a decaying cosine starting at t^0 = 1", order=1)
case("order2_wide", 3000.0, 16000.0, 32, "N = 2 with b = 2", order=2, b=2.0)
case("high_center", 6000.0, 16000.0, 40, "N = 4, f_c = 6 kHz near fs/2 = 8 kHz")
case("single_tap", 1000.0, 8000.0, 1, "N = 1 with one tap: [1]/|1| = [1]", order=1)
assert taps(1000.0, 8000.0, 1, 1, 1.019) == [1]


def err(cid, change, why):
    args = {"center_frequency": 1000.0, "sample_rate": 16000.0, "length": 32}
    args.update(change)
    cases.append({"id": f"gammatone.{cid}", "op": "gammatone", "args": args,
                  "error": "invalid_argument", "source": why})


err("zero_response", {"length": 1}, "N = 4 with one tap: t^3 = 0 at t = 0, so the gain is 0")
err("center_zero", {"center_frequency": 0.0}, "center_frequency must be above 0")
err("center_nyquist", {"center_frequency": 8000.0}, "center_frequency must be below fs/2")
err("zero_rate", {"sample_rate": 0.0}, "sample_rate must be positive")
err("zero_length", {"length": 0}, "length must be at least 1")
err("zero_order", {"order": 0}, "order must be at least 1")
err("zero_bandwidth", {"bandwidth_factor": 0.0}, "bandwidth_factor must be positive")
err("nan_center", {"center_frequency": "nan"}, "center_frequency must be finite")

doc = {
    "schema": 1,
    "suite": "gammatone",
    "description": "Gammatone impulse response (conventions: Gammatone; ADR 0161).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "gammatone.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/gammatone.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
