"""Writes vectors/cases/autocorrelation_pitch.json, stdlib only.

Each case is worked from the definition in Fractions (conventions: Autocorrelation pitch;
ADR 0150). The samples are integers, so the autocorrelation sums, the parabola offset and the
voicing are exact. The 1/N scaling cancels in every ratio. The simple cases also carry hand
values, and the generator checks those against the definition.

Run from the repo root: python vectors/generators/autocorrelation_pitch.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def definition(x, fs, fmin, fmax):
    n = len(x)
    r = [sum(x[i + k] * x[i] for i in range(n - k)) for k in range(n)]
    lo, hi = math.ceil(F(fs) / F(fmax)), math.floor(F(fs) / F(fmin))
    best = lo
    for k in range(lo + 1, hi + 1):
        if r[k] > r[best]:
            best = k
    left, peak, right = r[best - 1], r[best], r[best + 1]
    curve = left - 2 * peak + right
    delta = F(left - right, 2 * curve) if peak >= left and peak >= right and curve < 0 else F(0)
    lag = best + delta
    return F(fs) / lag, lag, F(peak, r[0])


def case(cid, x, fs, fmin, fmax, why, hand=None, *, refined=None):
    got = definition(x, fs, fmin, fmax)
    if hand is not None:
        assert got == hand, (cid, got)
    if refined is not None:
        assert (got[1] != int(got[1])) == refined, (cid, got)
    cases.append({"id": f"autocorrelation_pitch.{cid}", "op": "autocorrelation_pitch",
                  "args": {"samples": [float(v) for v in x], "sample_rate": float(fs),
                           "min_frequency": float(fmin), "max_frequency": float(fmax)},
                  "expected": {"frequency": float(got[0]), "lag": float(got[1]),
                               "voicing": float(got[2])},
                  "tol": TOL, "source": why})


def err(cid, args, why):
    full = {"samples": [1.0, 0.0, -1.0, 0.0] * 3, "sample_rate": 12.0, "min_frequency": 2.0,
            "max_frequency": 6.0}
    full.update(args)
    cases.append({"id": f"autocorrelation_pitch.{cid}", "op": "autocorrelation_pitch",
                  "args": full, "error": "invalid_argument", "source": why})


SQ = [1, 0, -1, 0] * 3
R = ("x = 1, 0, -1, 0 three times, fs = 12: N·r = 6, 0, -5, 0, 4, 0, -3, ... at lags 0, 1, 2, "
     "...")
case("symmetric_peak", SQ, 12, 2, 6,
     R + "; lags 2..6: r4 = 4 is highest, neighbours 0 and 0 give delta 0; f = 12/4 = 3, "
     "voicing 4/6", (F(3), F(4), F(2, 3)))
case("range_edge", SQ, 12, 4, 6,
     R + "; lags 2..3: r3 = 0 beats r2 = -5, but r4 = 4 > r3, so no parabola; f = 12/3 = 4, "
     "voicing 0", (F(4), F(3), F(0)))
case("tie", SQ, 12, 4, 12,
     R + "; lags 1..3: r1 = r3 = 0 tie, the smaller lag wins, r0 = 6 > r1 so no parabola; "
     "f = 12/1, voicing 0", (F(12), F(1), F(0)))
case("asymmetric_peak", [4, 2, 1, 0, 0, 4, 2, 1, 0, 0, 0, 4, 2, 1, 0, 0, 4, 2], 15, 2, 5,
     "x = 4, 2, 1 pulses with gaps of 5, 6 and 5, fs = 15, lags 3..7: the peak has unequal "
     "neighbours, so the parabola moves it off the whole lag; worked from the "
     "definition in Fractions", refined=True)

err("silent", {"samples": [0.0] * 12}, "the energy is 0")
err("too_short", {"samples": [1.0, -1.0], "min_frequency": 6.0, "max_frequency": 12.0},
    "needs at least three samples")
err("min_above_max", {"min_frequency": 7.0}, "min_frequency must not exceed max_frequency")
err("empty_range", {"min_frequency": 5.0, "max_frequency": 5.0},
    "fs/f = 2.4: lags from ceil 3 to floor 2 is empty")
err("lag_too_long", {"min_frequency": 1.0}, "fs/min = 12 > N - 2 = 10")
err("zero_min", {"min_frequency": 0.0}, "min_frequency must be positive")
err("zero_rate", {"sample_rate": 0.0}, "sample_rate must be positive")
err("nan", {"samples": [1.0, "nan"] + [0.0] * 10}, "samples must be finite")

doc = {
    "schema": 1,
    "suite": "autocorrelation_pitch",
    "description": "Autocorrelation pitch (conventions: Autocorrelation pitch; ADR 0150).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "autocorrelation_pitch.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/autocorrelation_pitch.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
