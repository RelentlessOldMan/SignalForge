"""Writes vectors/cases/power_ccdf.json by counting, using only the Python standard library.

Every sample set here has small integer powers, so the mean power and every 0 dB threshold are
exact; the expected probabilities are the samples counted above each threshold, and the expected
levels are the sorted powers read off by hand (conventions: Power CCDF; ADR 0119). A level other
than 0 dB rounds differently between libraries, so the generator asserts every such threshold is
at least 0.1 % from every power.

Run from the repo root: python vectors/generators/power_ccdf.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []

# Real: powers 1, 1, 4, 0, 9, 1, 1, 1; sum 18, mean 9/4.
REAL = [1.0, -1.0, 2.0, 0.0, 3.0, -1.0, 1.0, 1.0]
# Complex: powers 2, 4, 0, 1, 5, 0; sum 12, mean 2.
CPLX = {"re": [1.0, 2.0, 0.0, 0.0, -1.0, 0.0], "im": [1.0, 0.0, 0.0, -1.0, 2.0, 0.0]}


def powers(x):
    if isinstance(x, dict):
        return [F(int(a)) ** 2 + F(int(b)) ** 2 for a, b in zip(x["re"], x["im"])]
    return [F(int(a)) ** 2 for a in x]


def ccdf(cid, x, levels, why):
    p = powers(x)
    mean = sum(p) / len(p)
    probs = []
    for lv in levels:
        if lv == 0:
            t = mean
        else:
            g = 10 ** (lv / 10)
            for v in p:
                assert abs(float(v) - float(mean) * g) > 1e-3 * float(mean) * g, (cid, lv, v)
            t = F(float(mean) * g)
        probs.append(sum(1 for v in p if v > t) / len(p))
    cases.append({"id": f"power_ccdf.{cid}", "op": "power_ccdf",
                  "args": {"samples": x, "levels_db": levels},
                  "expected": {"mean_power": float(mean), "levels_db": levels,
                               "probabilities": probs},
                  "tol": TOL, "source": why})


def level(cid, x, probability, why):
    p = sorted(powers(x), reverse=True)
    mean = sum(p) / len(p)
    m = math.floor(F(probability) * len(p))  # no product here is near a whole number
    t = p[m]
    want = 10 * math.log10(t / mean) if t > 0 else "-inf"
    cases.append({"id": f"power_ccdf_level.{cid}", "op": "power_ccdf_level",
                  "args": {"samples": x, "probability": probability},
                  "expected": want, "tol": TOL, "source": why})


def err(op, cid, args, why):
    cases.append({"id": f"{op}.{cid}", "op": op, "args": args, "error": "invalid_argument",
                  "source": why})


ccdf("real_counts", REAL, [0.0, -3.0, -10.0, 3.0, 6.0, 7.0, -20.0],
     "by hand: powers 1, 1, 4, 0, 9, 1, 1, 1, mean 2.25; above 2.25 (0 dB): 4 and 9; -3 dB "
     "(1.13): 4, 9; -10 dB (0.225): all but the 0; 3 dB (4.49): 9; 6 dB (8.96): 9; 7 dB (11.3): "
     "none; -20 dB (0.0225): all but the 0")
ccdf("complex_counts", CPLX, [0.0, 1.0, 4.0, -5.0],
     "by hand: powers 2, 4, 0, 1, 5, 0, mean 2; above 2 (0 dB, strict): 4 and 5; 1 dB (2.52): 4, "
     "5; 4 dB (5.02): none; -5 dB (0.632): 2, 4, 1, 5")
ccdf("constant_envelope_tie", [1.0, -1.0, 1.0, -1.0], [0.0, -0.5, 0.5],
     "by hand: every power is 1, the mean; strict, so none above 0 dB, all above -0.5 dB")
level("real_peak", REAL, 0.1,
      "by hand: floor(0.1 x 8) = 0, the largest power 9; 10 log10(9 / 2.25) = 10 log10 4 (PAPR)")
level("real_second", REAL, 0.125,
      "by hand: floor(0.125 x 8) = 1, the second largest power 4; 10 log10(4 / 2.25)")
level("real_tie", REAL, 0.3,
      "by hand: floor(0.3 x 8) = 2, the third largest power 1 (a tie with four others); "
      "10 log10(1 / 2.25)")
level("real_zero", REAL, 0.9,
      "by hand: floor(0.9 x 8) = 7, the eighth largest power 0, so -inf")
level("complex_half", CPLX, 0.5,
      "by hand: sorted powers 5, 4, 2, 1, 0, 0; floor(0.5 x 6) = 3, the fourth, 1; "
      "10 log10(1 / 2)")

err("power_ccdf", "empty", {"samples": [], "levels_db": [0.0]}, "at least one sample")
err("power_ccdf", "all_zero", {"samples": [0.0, 0.0], "levels_db": [0.0]},
    "the mean power must be positive")
err("power_ccdf", "sample_nan", {"samples": [1.0, "nan"], "levels_db": [0.0]},
    "samples must be finite")
err("power_ccdf", "no_levels", {"samples": REAL, "levels_db": []}, "at least one level")
err("power_ccdf", "level_inf", {"samples": REAL, "levels_db": [0.0, "inf"]},
    "levels must be finite")
err("power_ccdf_level", "probability_zero", {"samples": REAL, "probability": 0.0},
    "probability must be in (0, 1)")
err("power_ccdf_level", "probability_one", {"samples": REAL, "probability": 1.0},
    "probability must be in (0, 1)")
err("power_ccdf_level", "all_zero", {"samples": [0.0, 0.0], "probability": 0.5},
    "the mean power must be positive")

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

    args = {name: times(v) if name in ('samples',) else v
            for name, v in c["args"].items()}
    op = base.split(".")[0]
    cases.append({**c, "id": f"{op}.{cid}", "args": args, "source": why})


scaled("huge", "power_ccdf_level.real_second", 1000,
       "case real_second times 2^1000: squares of the samples overflow a double, but "
       "a level over the mean is unchanged by a scale, so the same value")
scaled("tiny", "power_ccdf_level.real_second", -1000,
       "case real_second times 2^-1000: squares of the samples underflow to 0, but "
       "a level over the mean is unchanged by a scale, so the same value")
scaled("huge_complex", "power_ccdf_level.complex_half", 1000,
       "case complex_half times 2^1000: squares of the samples overflow a double, but "
       "a level over the mean is unchanged by a scale, so the same value")
scaled("tiny_complex", "power_ccdf_level.complex_half", -1000,
       "case complex_half times 2^-1000: squares of the samples underflow to 0, but "
       "a level over the mean is unchanged by a scale, so the same value")


doc = {
    "schema": 1,
    "suite": "power_ccdf",
    "description": "Power CCDF and the level at a probability (conventions: Power CCDF; "
    "ADR 0119).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "power_ccdf.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/power_ccdf.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
