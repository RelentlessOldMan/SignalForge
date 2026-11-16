"""Writes vectors/cases/early_decay_time.json, stdlib only.

Early decay time (conventions: Early decay time; ADR 0181): the reverberation time fitted from
0 to -10 dB of the Schroeder decay. For h[n] = sum_j c_j r_j^n over N samples the tail is the
exact geometric sum of every cross term; the curve and the least-squares slope over
0 <= n < n2 (n2 the first sample at or below -10 dB) are worked in 50-digit decimal, with
every curve value kept at least 1e-6 dB from -10 dB.

Run from the repo root: python vectors/generators/early_decay_time.py [--check]
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


def edt(parts, length, fs):
    energy = []
    for n in range(length):
        e = D(0)
        for ci, ri in parts:
            for cj, rj in parts:
                q = D(ri) * D(rj)
                e += D(ci) * D(cj) * (q ** n - q ** length) / (1 - q)
        energy.append(e)
    d = [(e / energy[0]).log10() * 10 if e > 0 else None for e in energy]
    for v in d:
        assert v is None or abs(v + 10) > D("1e-6"), v
    n2 = next(i for i, v in enumerate(d) if v is not None and v <= -10)
    ns = range(n2)
    mn = D(sum(ns)) / len(ns)
    my = sum(d[n] for n in ns) / len(ns)
    m = sum((n - mn) * (d[n] - my) for n in ns) / sum((n - mn) ** 2 for n in ns) * D(fs)
    return -60 / m


def add(cid, parts, length, fs, why, turn=None, ideal=None):
    t = edt(parts, length, fs)
    if ideal is not None:
        assert abs(t / D(ideal) - 1) < D("1e-9"), (cid, t, ideal)
    x = [sum(c * r ** n for c, r in parts) for n in range(length)]
    if turn is None:
        ir = x
    else:
        ir = {"re": [v * math.cos(turn * n) for n, v in enumerate(x)],
              "im": [v * math.sin(turn * n) for n, v in enumerate(x)]}
    cases.append({"id": f"early_decay_time.{cid}", "op": "early_decay_time",
                  "args": {"impulse_response": ir, "sample_rate": fs},
                  "expected": float(t), "tol": TOL, "source": why})


add("single", [(1.0, 0.99)], 3000, 1000.0,
    "h = 0.99^n, 3000 samples at 1 kHz: exact tail, slope over 0 <= n < 115; "
    "close to -3/(fs log10 0.99) = 0.687 s", ideal=-3 / (1000 * math.log10(0.99)))
add("scaled", [(0.25, 0.995)], 4000, 8000.0,
    "h = 0.25 * 0.995^n at 8 kHz: the scale cancels; close to -3/(fs log10 0.995)",
    ideal=-3 / (8000 * math.log10(0.995)))
add("complex", [(1.0, 0.99)], 3000, 1000.0,
    "h = 0.99^n e^(0.3jn): |h| is the single case's, so the same EDT", turn=0.3,
    ideal=-3 / (1000 * math.log10(0.99)))
add("two_slope", [(1.0, 0.9), (0.2, 0.995)], 4000, 1000.0,
    "a fast decay plus a weak slow one: the exact tail of the sum with its cross term; the "
    "early fit is steeper than the late decay")


def err(cid, ir, fs, why):
    cases.append({"id": f"early_decay_time.{cid}", "op": "early_decay_time",
                  "args": {"impulse_response": ir, "sample_rate": fs},
                  "error": "invalid_argument", "source": why})


err("never_reaches", [1.0, 0.9], 1000.0, "the decay ends at 10 log10(0.81/1.81) > -10 dB")
err("too_few", [1.0, 0.01], 1000.0, "only sample 0 lies above -10 dB: fewer than two samples")
err("silent", [0.0, 0.0, 0.0], 1000.0, "all zero")
err("empty", [], 1000.0, "empty")
err("zero_rate", [0.99 ** n for n in range(400)], 0.0, "sample_rate must be positive")
err("nan", [1.0, "nan", 0.5], 1000.0, "not finite")

doc = {
    "schema": 1,
    "suite": "early_decay_time",
    "description": "Early decay time (conventions: Early decay time; ADR 0181).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "early_decay_time.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/early_decay_time.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
