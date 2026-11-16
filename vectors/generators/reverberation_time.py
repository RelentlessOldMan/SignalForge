"""Writes vectors/cases/reverberation_time.json, stdlib only.

Reverberation time (conventions: Reverberation time; ADR 0171). For h[n] = c r^n (|r| < 1) over
N samples the Schroeder tail is exactly geometric, E[n]/E[0] = (q^n - q^N)/(1 - q^N), q = |r|^2;
the curve and the least-squares slope over n1 <= n < n2 are worked in 50-digit decimal. Sums of
two such decays use the same exact tails. Every curve value is kept at least 1e-6 dB from the
fit levels so the threshold samples are unambiguous.

Run from the repo root: python vectors/generators/reverberation_time.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from decimal import Decimal as D
from decimal import getcontext

getcontext().prec = 50
TOL = {"abs": 1e-11, "rel": 1e-11}
cases = []


def tails(parts, length):
    """E[n] for h[n] = sum_j c_j r_j^n with real r_j, from the exact geometric sums of every
    cross term c_i c_j (r_i r_j)^n."""
    out = []
    for n in range(length):
        e = D(0)
        for ci, ri in parts:
            for cj, rj in parts:
                q = D(ri) * D(rj)
                e += D(ci) * D(cj) * (q ** n - q ** length) / (1 - q)
        out.append(e)
    return out


def curve(energy):
    return [(e / energy[0]).log10() * 10 if e > 0 else None for e in energy]


def fit(d, fs, a, b):
    for v in d:
        assert v is None or abs(v - D(a)) > D("1e-6") and abs(v - D(b)) > D("1e-6"), v
    n1 = next(i for i, v in enumerate(d) if v <= a)
    n2 = next(i for i, v in enumerate(d) if v <= b)
    ns = range(n1, n2)
    mn = D(sum(ns)) / len(ns)
    my = sum(d[n] for n in ns) / len(ns)
    m = sum((n - mn) * (d[n] - my) for n in ns) / sum((n - mn) ** 2 for n in ns) * D(fs)
    return -60 / m


def samples(parts, length):
    return [sum(c * r ** n for c, r in parts) for n in range(length)]


def decay_case(cid, ir, d, why):
    cases.append({"id": f"reverberation_time.{cid}", "op": "schroeder_decay",
                  "args": {"impulse_response": ir},
                  "expected": [float(v) if v is not None else "-inf" for v in d],
                  "tol": TOL, "source": why})


def rt_case(cid, parts, length, fs, why, a=-5.0, b=-25.0, ideal=None, complex_turn=None):
    d = curve(tails(parts, length))
    t = fit(d, fs, a, b)
    if ideal is not None:
        assert abs(t / D(ideal) - 1) < D("0.002"), (cid, t, ideal)
    x = samples(parts, length)
    if complex_turn is not None:
        ir = {"re": [v * math.cos(complex_turn * n) for n, v in enumerate(x)],
              "im": [v * math.sin(complex_turn * n) for n, v in enumerate(x)]}
    else:
        ir = x
    args = {"impulse_response": ir, "sample_rate": fs}
    if a != -5.0:
        args["start_db"] = a
    if b != -25.0:
        args["stop_db"] = b
    cases.append({"id": f"reverberation_time.{cid}", "op": "reverberation_time", "args": args,
                  "expected": float(t), "tol": TOL, "source": why})


q = [D(1), D("0.25"), D("0.0625"), D("0.015625")]
decay_case("decay_half", [1.0, 0.5, 0.25, 0.125],
           [(sum(q[n:]) / sum(q)).log10() * 10 for n in range(4)],
           "h = 0.5^n: E = 1.328125, 0.328125, 0.078125, 0.015625; 10 log10(E[n]/E[0])")
decay_case("decay_zero_tail", [2.0, 1.0, 0.0, 0.0],
           [D(0), (D(1) / 5).log10() * 10, None, None], "energies 5, 1, 0, 0: 0, 10 log10(1/5), -inf, -inf")
decay_case("decay_complex", {"re": [0.0, 1.0], "im": [1.0, 0.0]},
           [D(0), (D(1) / 2).log10() * 10], "|h|^2 = 1, 1: 0 and 10 log10(1/2)")

rt_case("t20_r09", [(1.0, 0.9)], 60, 100.0,
        "h = 0.9^n, 60 samples at 100 Hz, T20 from the exact geometric tail and least squares")
rt_case("t20_long", [(1.0, 0.99)], 2000, 1000.0,
        "h = 0.99^n, 2000 samples: close to 60/(-20 log10 0.99 fs)",
        ideal=60 / (-20 * math.log10(0.99) * 1000.0))
rt_case("t30", [(1.0, 0.995)], 3000, 8000.0,
        "h = 0.995^n, T30 (-5 to -35 dB) from the exact tail", b=-35.0,
        ideal=60 / (-20 * math.log10(0.995) * 8000.0))
rt_case("two_slopes", [(1.0, 0.9), (0.3, 0.97)], 400, 1000.0,
        "h = 0.9^n + 0.3 (0.97)^n: a bent decay, from the exact cross-term tails")
rt_case("complex", [(1.0, 0.98)], 600, 2000.0,
        "h = (0.98 e^(j 0.7))^n: the same curve as the real decay", complex_turn=0.7,
        ideal=60 / (-20 * math.log10(0.98) * 2000.0))


def err(cid, op, change, why):
    args = {"impulse_response": [0.9 ** n for n in range(60)]}
    if op == "reverberation_time":
        args["sample_rate"] = 100.0
    args.update(change)
    cases.append({"id": f"reverberation_time.{cid}", "op": op, "args": args,
                  "error": "invalid_argument", "source": why})


err("decay_empty", "schroeder_decay", {"impulse_response": []}, "impulse_response must not be empty")
err("decay_zero", "schroeder_decay", {"impulse_response": [0.0, 0.0]}, "impulse_response must not be all zero")
err("decay_nan", "schroeder_decay", {"impulse_response": [1.0, "nan"]}, "impulse_response must be finite")
err("never_reaches", "reverberation_time", {"impulse_response": [0.9 ** n for n in range(10)]},
    "h = 0.9^n over 10 samples ends near -15 dB, above -25 dB")
err("too_few", "reverberation_time", {"impulse_response": [1.0, 0.01, 0.0001], "start_db": -1.0, "stop_db": -2.0},
    "the curve drops past both levels at n = 1: no sample between them")
err("start_positive", "reverberation_time", {"start_db": 1.0}, "start_db must be at most 0")
err("stop_above_start", "reverberation_time", {"start_db": -25.0, "stop_db": -5.0}, "stop_db must be below start_db")
err("zero_rate", "reverberation_time", {"sample_rate": 0.0}, "sample_rate must be positive")
err("nan_stop", "reverberation_time", {"stop_db": "nan"}, "stop_db must be finite")

doc = {
    "schema": 1,
    "suite": "reverberation_time",
    "description": "Schroeder decay and reverberation time (conventions: Reverberation time; ADR 0171).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "reverberation_time.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/reverberation_time.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
