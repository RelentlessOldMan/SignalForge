"""Writes vectors/cases/lateral_fraction.json, stdlib only.

Lateral energy fraction (conventions: Lateral energy fraction; ADR 0175): sum over
Na <= n < Nb of h8^2 over sum n < Nb of ho^2, N = floor(t fs + 1/2), as exact hand sums in
fractions and, for geometric decays, the window sums (q^a - q^b)/(1 - q) in 50-digit decimal.

Run from the repo root: python vectors/generators/lateral_fraction.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from decimal import Decimal as D
from decimal import getcontext
from fractions import Fraction as F

getcontext().prec = 50
TOL = {"abs": 1e-15, "rel": 1e-12}
cases = []


def add(cid, omni, eight, fs, expected, why, **opts):
    args = {"omni": omni, "figure_eight": eight, "sample_rate": fs}
    args.update(opts)
    cases.append({"id": f"lateral_fraction.{cid}", "op": "lateral_fraction", "args": args,
                  "expected": expected, "tol": TOL, "source": why})


def window(r, a, b):
    q = D(r) ** 2
    return (q ** a - q ** b) / (1 - q)


add("geometric", [0.99 ** n for n in range(200)], [0.5 * 0.98 ** n for n in range(200)], 1000.0,
    float(D("0.25") * window("0.98", 5, 80) / window("0.99", 0, 80)),
    "ho = 0.99^n, h8 = 0.5 0.98^n at 1 kHz: Na = 5, Nb = 80, 0.25 S(0.9604; 5, 80) / S(0.9801; 0, 80)")
add("hand", [2.0, 1.0, 1.0, 1.0], [1.0, 1.0, 2.0, 3.0], 100.0, float(F(5, 6)),
    "Na = floor(1.5) = 1, Nb = floor(3.5) = 3: (1 + 4)/(4 + 1 + 1) = 5/6", start=0.01, stop=0.03)
add("above_one", [1.0, 0.0, 0.0], [0.0, 2.0, 0.0], 100.0, 4.0,
    "Na = 1, Nb = 3: 4/1 = 4, not clamped", start=0.01, stop=0.03)
add("from_zero", [1.0, 1.0], [1.0, 1.0], 100.0, 1.0, "start 0, Nb = 2: 2/2", start=0.0,
    stop=0.02)
add("past_the_end", [1.0, 2.0, 2.0], [3.0, 1.0, 1.0], 1000.0, float(F(2, 9)),
    "start 0.001: Na = floor(1.5) = 1; Nb = 80 clipped to 3: (1 + 1)/(1 + 4 + 4) = 2/9",
    start=0.001, stop=0.08)
add("rounding", [1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0], 100.0, float(F(1, 3)),
    "start 0.016: Na = floor(2.1) = 2; stop 0.026: Nb = floor(3.1) = 3: 1/(1 + 1 + 1)",
    start=0.016, stop=0.026)
add("empty_window", [1.0, 1.0], [5.0, 5.0], 100.0, 0.0,
    "start 0.005, stop 0.006 at 100 Hz: Na = Nb = 1, numerator empty", start=0.005, stop=0.006)


def err(cid, change, why):
    args = {"omni": [1.0, 0.5], "figure_eight": [0.5, 1.0], "sample_rate": 100.0,
            "start": 0.0, "stop": 0.02}
    args.update(change)
    cases.append({"id": f"lateral_fraction.{cid}", "op": "lateral_fraction", "args": args,
                  "error": "invalid_argument", "source": why})


err("empty", {"omni": [], "figure_eight": []}, "the responses must not be empty")
err("unequal", {"figure_eight": [1.0]}, "the responses must have equal length")
err("nan", {"figure_eight": [1.0, "nan"]}, "figure_eight must be finite")
err("no_omni_energy", {"omni": [0.0, 0.0]}, "omni has no energy before stop")
err("start_at_stop", {"start": 0.02}, "start must be below stop")
err("negative_start", {"start": -0.01}, "start must be non-negative")
err("stop_rounds_to_zero", {"stop": 0.004}, "0.004 * 100 + 0.5 = 0.9 rounds to 0 samples")
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

    args = {name: times(v) if name in ('omni', 'figure_eight') else v
            for name, v in c["args"].items()}
    op = base.split(".")[0]
    cases.append({**c, "id": f"{op}.{cid}", "args": args, "source": why})


scaled("huge", "lateral_fraction.hand", 1000,
       "case hand times 2^1000: squares of the samples overflow a double, but "
       "a ratio of energies is unchanged by a scale, so the same value")
scaled("tiny", "lateral_fraction.hand", -1000,
       "case hand times 2^-1000: squares of the samples underflow to 0, but "
       "a ratio of energies is unchanged by a scale, so the same value")


doc = {
    "schema": 1,
    "suite": "lateral_fraction",
    "description": "Lateral energy fraction (conventions: Lateral energy fraction; ADR 0175).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "lateral_fraction.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/lateral_fraction.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
