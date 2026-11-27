"""Writes vectors/cases/iacc.json, stdlib only.

Interaural cross-correlation (conventions: Interaural cross-correlation; ADR 0174):
max over integer lags |t| <= floor(max_lag fs + 1/2) of |sum l[n] r[n+t]| / sqrt(E_l E_r), as
exact hand sums in fractions with the square root in 50-digit decimal.

Run from the repo root: python vectors/generators/iacc.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from decimal import Decimal as D
from decimal import getcontext
from fractions import Fraction as F

getcontext().prec = 50
TOL = {"abs": 1e-15, "rel": 1e-13}
cases = []


def value(left, right, fs, max_lag):
    lv, rv = [F(v) for v in left], [F(v) for v in right]
    n = len(lv)
    reach = min(int(F(max_lag) * F(fs) + F(1, 2)), n - 1)
    best = max(abs(sum(lv[k] * rv[k + t] for k in range(max(0, -t), min(n, n - t))))
               for t in range(-reach, reach + 1))
    e = sum(v * v for v in lv) * sum(v * v for v in rv)
    return dec(best) / dec(e).sqrt() if best else D(0)


def dec(f):
    f = F(f)
    return D(f.numerator) / D(f.denominator)


def add(cid, left, right, fs, why, max_lag=None, expected=None):
    got = value(left, right, fs, 0.001 if max_lag is None else max_lag)
    if expected is not None:
        exp = expected if isinstance(expected, D) else dec(expected)
        assert abs(got - exp) < D(10) ** -40, (cid, got)
    args = {"left": left, "right": right, "sample_rate": fs}
    if max_lag is not None:
        args["max_lag"] = max_lag
    cases.append({"id": f"iacc.{cid}", "op": "iacc", "args": args, "expected": float(got),
                  "tol": TOL, "source": why})


PULSE = [1.0, 0.5, -0.25, 0.0, 0.0, 0.0]
DELAYED = [0.0, 0.0, 1.0, 0.5, -0.25, 0.0]
add("delayed_in_range", PULSE, DELAYED, 2000.0, "right = left delayed 2 samples, L = 2: exactly 1",
    expected=1)
add("delayed_out_of_range", PULSE, DELAYED, 1000.0,
    "the same pair, L = 1: best is lag 1, |0.5 - 0.125| = 0.375 over E = 1.3125", expected=F(2, 7))
add("inverted", [1.0, -2.0, 3.0], [-1.0, 2.0, -3.0], 48000.0, "right = -left: |R(0)| / E = 1",
    expected=1)
add("orthogonal", [1.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 1.0], 1000.0,
    "impulses 3 samples apart, L = 1: no overlap, 0", expected=0)
add("lag_zero_only", [1.0, 1.0], [1.0, -1.0], 1000.0, "max_lag 0: R(0) = 0", max_lag=0.0,
    expected=0)
add("rounding", [1.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 2.0], 1000.0,
    "max_lag 0.0026 s at 1 kHz: L = floor(3.1) = 3, the impulse pair aligns: 1", max_lag=0.0026,
    expected=1)
add("mixed", [3.0, 1.0, -2.0, 0.5], [1.0, 2.0, 0.0, -1.0], 1000.0,
    "a hand pair, L = 1: R(-1) = -3, R(0) = 4.5, R(1) = 8; E = 14.25 * 6: 8/sqrt(85.5)",
    expected=D(8) / D("85.5").sqrt())
add("long_lag_clipped", [1.0, 2.0], [2.0, 1.0], 100000.0,
    "L = 100 clipped to 1: R(1) = 1, R(0) = 4, R(-1) = 4; 4/5")


def err(cid, change, why):
    args = {"left": [1.0, 0.5], "right": [0.5, 1.0], "sample_rate": 1000.0}
    args.update(change)
    cases.append({"id": f"iacc.{cid}", "op": "iacc", "args": args,
                  "error": "invalid_argument", "source": why})


err("empty", {"left": [], "right": []}, "left and right must not be empty")
err("unequal", {"right": [1.0]}, "left and right must have equal length")
err("zero_left", {"left": [0.0, 0.0]}, "left must not be all zero")
err("zero_right", {"right": [0.0, 0.0]}, "right must not be all zero")
err("nan", {"left": [1.0, "nan"]}, "left must be finite")
err("negative_lag", {"max_lag": -0.001}, "max_lag must be non-negative")
err("zero_rate", {"sample_rate": 0.0}, "sample_rate must be positive")

def scaled(cid, base, k, why):
    """Case ``base`` with the signal arguments times 2**k: the measure is unchanged
    by that scale, and a power of 2 scales every value exactly, so the expected value
    is the base case's."""
    c = next(c for c in cases if c["id"] == base)
    s = 2.0**k

    def times(v):
        if isinstance(v, dict):
            return {part: times(v[part]) for part in ("re", "im")}
        assert all(u * s / s == u for u in v), cid
        return [u * s for u in v]

    args = {name: times(v) if name in ('left', 'right') else v
            for name, v in c["args"].items()}
    op = base.split(".")[0]
    cases.append({**c, "id": f"{op}.{cid}", "args": args, "source": why})


scaled("huge", "iacc.mixed", 1000,
       "case mixed times 2^1000: squares of the samples overflow a double, but "
       "a normalized correlation is unchanged by a scale, so the same value")
scaled("tiny", "iacc.mixed", -1000,
       "case mixed times 2^-1000: squares of the samples underflow to 0, but "
       "a normalized correlation is unchanged by a scale, so the same value")


doc = {
    "schema": 1,
    "suite": "iacc",
    "description": "Interaural cross-correlation (conventions: Interaural cross-correlation; ADR 0174).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "iacc.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/iacc.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
