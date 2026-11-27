"""Writes vectors/cases/temporal_centroid.json, stdlib only.

Each case is worked by hand in Fractions from the definition (conventions: Temporal centroid;
ADR 0147): weights |x[n]|^2 at t_n = n / fs. The centroid is an exact fraction, and the spread
is the square root of one. The generator checks both hand values against the definition.

Run from the repo root: python vectors/generators/temporal_centroid.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def definition(re, im, fs):
    p = [F(a) ** 2 + F(b) ** 2 for a, b in zip(re, im, strict=True)]
    t = [F(n) / F(fs) for n in range(len(p))]
    c = sum(x * y for x, y in zip(p, t, strict=True)) / sum(p)
    var = sum(x * (y - c) ** 2 for x, y in zip(p, t, strict=True)) / sum(p)
    return c, var


def case(cid, samples, fs, centroid, variance, why, im=None):
    re = samples
    got = definition(re, im if im is not None else [0] * len(re), fs)
    assert got == (centroid, variance), (cid, got)
    spread = math.sqrt(variance.numerator) / math.sqrt(variance.denominator)
    arg = [float(v) for v in re] if im is None else {
        "re": [float(v) for v in re], "im": [float(v) for v in im]}
    cases.append({"id": f"temporal_centroid.{cid}", "op": "temporal_centroid",
                  "args": {"samples": arg, "sample_rate": float(fs)},
                  "expected": {"centroid": float(centroid), "spread": spread},
                  "tol": TOL, "source": why})


def err(cid, samples, fs, why):
    cases.append({"id": f"temporal_centroid.{cid}", "op": "temporal_centroid",
                  "args": {"samples": samples, "sample_rate": fs},
                  "error": "invalid_argument", "source": why})


case("impulse", [0, 0, 5, 0], 1, F(2), F(0), "all energy at n = 2: centroid 2, spread 0")
case("symmetric", [1, 2, 1], 1, F(1), F(1, 3),
     "energies 1, 4, 1: centroid 1; variance (1 + 0 + 1)/6 = 1/3")
case("ramp", [1, 2, 3], 1, F(11, 7), F(19, 49),
     "energies 1, 4, 9 sum 14: centroid (0 + 4 + 18)/14 = 11/7; second moment "
     "(0 + 4 + 36)/14 = 20/7, less (11/7)^2, is 19/49")
case("complex", [3, 0, 0], 1, F(1, 13), F(25, 169),
     "energies |3+4i|^2 = 25, 0, |i|^2 = 1 sum 26: centroid 2/26 = 1/13; second moment "
     "4/26 = 2/13, less 1/169, is 25/169", im=[4, 0, 1])
case("sample_rate", [1, 1, 1, 1], 4, F(3, 8), F(5, 64),
     "equal energies at t = 0, 1/4, 1/2, 3/4: mean 3/8; variance of n is 5/4, over 4^2 is 5/64")

err("empty", [], 1.0, "needs at least one sample")
err("silent", [0.0, 0.0], 1.0, "the energy is 0")
err("nan", [1.0, "nan"], 1.0, "samples must be finite")
err("zero_rate", [1.0, 1.0], 0.0, "sample_rate must be positive")
err("negative_rate", [1.0, 1.0], -2.0, "sample_rate must be positive")
err("infinite_rate", [1.0, 1.0], "inf", "sample_rate must be finite")

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


scaled("huge", "temporal_centroid.ramp", 1000,
       "case ramp times 2^1000: squares of the samples overflow a double, but "
       "an energy-weighted time is unchanged by a scale, so the same value")
scaled("tiny", "temporal_centroid.ramp", -1000,
       "case ramp times 2^-1000: squares of the samples underflow to 0, but "
       "an energy-weighted time is unchanged by a scale, so the same value")
scaled("huge_complex", "temporal_centroid.complex", 1000,
       "case complex times 2^1000: squares of the samples overflow a double, but "
       "an energy-weighted time is unchanged by a scale, so the same value")
scaled("tiny_complex", "temporal_centroid.complex", -1000,
       "case complex times 2^-1000: squares of the samples underflow to 0, but "
       "an energy-weighted time is unchanged by a scale, so the same value")


doc = {
    "schema": 1,
    "suite": "temporal_centroid",
    "description": "Temporal centroid and spread (conventions: Temporal centroid; ADR 0147).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "temporal_centroid.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/temporal_centroid.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
