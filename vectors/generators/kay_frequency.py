"""Writes vectors/cases/kay_frequency.json, stdlib only.

Kay's estimator averages the phase steps of a complex tone with weights that sum to 1
(conventions: Single-tone frequency (Kay); ADR 0123). Hand cases use samples on the axes, so
every step is exactly 0 or +-pi/2 and the weights are short fractions (asserted here). Tone
cases are made with cos and sin at a known frequency; the expected value is that frequency,
since every step of a noiseless tone is the same.

Run from the repo root: python vectors/generators/kay_frequency.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-9, "rel": 1e-12}
cases = []


def weights(n):
    half = F(n, 2)
    return [F(3 * n, 2 * (n * n - 1)) * (1 - ((k - (half - 1)) / half) ** 2) for k in range(n - 1)]


assert weights(3) == [F(1, 2), F(1, 2)]
assert weights(5) == [F(1, 5), F(3, 10), F(3, 10), F(1, 5)]
assert all(sum(weights(n)) == 1 for n in range(2, 40))


def cx(values):
    return {"re": [float(v.real) for v in values], "im": [float(v.imag) for v in values]}


def case(cid, samples, fs, want, why):
    cases.append({"id": f"kay_frequency.{cid}", "op": "kay_frequency",
                  "args": {"samples": cx(samples), "sample_rate": fs},
                  "expected": want, "tol": TOL, "source": why})


def tone(cid, n, fs, f, amp, phase):
    xs = [amp * complex(math.cos(2 * math.pi * f * k / fs + phase),
                        math.sin(2 * math.pi * f * k / fs + phase)) for k in range(n)]
    case(cid, xs, fs, f, f"noiseless tone at {f} Hz, fs {fs}, amplitude {amp}, phase {phase}: "
         "every phase step is 2 pi f / fs, and the weights sum to 1")


def err(cid, args, why):
    cases.append({"id": f"kay_frequency.{cid}", "op": "kay_frequency", "args": args,
                  "error": "invalid_argument", "source": why})


case("quarter_steps", [1, 1j, -1, -1j], 4.0, 1.0,
     "steps of pi/2 at fs 4: f = 4 x (pi/2) / (2 pi) = 1")
case("quarter_steps_down", [1, -1j, -1, 1j], 4.0, -1.0,
     "steps of -pi/2 at fs 4: f = -1")
case("mixed_three", [1, 1, 1j], 8.0, 1.0,
     "steps 0 and pi/2, weights 1/2 and 1/2: f = 8 x (pi/4) / (2 pi) = 1")
case("mixed_five", [1, 1j, 1j, 1j, -1], 10.0, 1.0,
     "steps pi/2, 0, 0, pi/2, weights 0.2, 0.3, 0.3, 0.2: f = 10 x 0.4 x (pi/2) / (2 pi) = 1")
case("two_samples", [2, 2j], 1.0, 0.25, "one step of pi/2, weight 1: f = 1/4 of fs")
tone("tone_fine", 64, 1000.0, 123.456, 1.0, 0.3)
tone("tone_negative", 50, 48000.0, -7321.5, 0.01, -2.0)
tone("tone_near_half", 33, 1.0, 0.45, 3.0, 1.0)

ONE = {"re": [1.0], "im": [0.0]}
err("one_sample", {"samples": ONE, "sample_rate": 1.0}, "needs at least two samples")
err("zero_sample", {"samples": {"re": [1.0, 0.0, 1.0], "im": [0.0, 0.0, 0.0]},
                    "sample_rate": 1.0}, "samples must be non-zero")
err("nan_sample", {"samples": {"re": [1.0, "nan"], "im": [0.0, 0.0]}, "sample_rate": 1.0},
    "samples must be finite")
err("rate_zero", {"samples": {"re": [1.0, 0.0], "im": [0.0, 1.0]}, "sample_rate": 0.0},
    "sample_rate must be positive")
err("rate_inf", {"samples": {"re": [1.0, 0.0], "im": [0.0, 1.0]}, "sample_rate": "inf"},
    "sample_rate must be finite")

doc = {
    "schema": 1,
    "suite": "kay_frequency",
    "description": "Single-tone frequency by Kay's estimator (conventions: Single-tone "
    "frequency (Kay); ADR 0123).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "kay_frequency.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/kay_frequency.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
