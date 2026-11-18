"""Writes vectors/cases/ring_modulate.json, stdlib only.

Ring modulator (conventions: Ring modulator; ADR 0260). The expected values come from the
definition x[n] cos((2 pi f)(n / fs) + phase) with the stdlib math.cos; the fs/4 and fs/2
carriers are checked by hand against 1, 0, -1, 0 and +-1.

Run from the repo root: python vectors/generators/ring_modulate.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def carrier(size, f, fs, ph):
    return [math.cos(2.0 * math.pi * f * (n / fs) + ph) for n in range(size)]


def opt(args, ph):
    if ph is not None:
        args["phase"] = ph
    return args


def add(cid, x, f, fs, why, ph=None):
    c = carrier(len(x), f, fs, ph or 0.0)
    args = opt({"samples": x, "frequency": f, "sample_rate": fs}, ph)
    cases.append({"id": f"ring_modulate.{cid}", "op": "ring_modulate", "args": args,
                  "expected": [v * k for v, k in zip(x, c)], "tol": TOL, "source": why})
    return c


c = add("quarter", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0], 250.0, 1000.0,
        "f = fs/4: carrier 1, 0, -1, 0, ...")
assert all(abs(a - b) < 1e-15 for a, b in zip(c, [1, 0, -1, 0, 1, 0, -1, 0]))
c = add("half", [0.5, 0.5, -0.25, 0.25], 4000.0, 8000.0, "f = fs/2: carrier +-1")
assert all(abs(a - b) < 1e-15 for a, b in zip(c, [1, -1, 1, -1]))
c = add("phase", [1.0, 1.0, 1.0, 1.0], 250.0, 1000.0, "f = fs/4, phase pi/2: 0, -1, 0, 1",
        ph=math.pi / 2)
assert all(abs(a - b) < 1e-15 for a, b in zip(c, [0, -1, 0, 1]))
add("general", [0.25, -1.5, 2.0, 0.75, -0.5, 1.25, 3.0], 1234.5, 44100.0,
    "general carrier frequency")
add("negative_frequency", [1.0, -2.0, 0.5, 1.5], -300.0, 1000.0, "negative f, cos is even",
    ph=0.25)

re = [1.0, 2.0, -3.0, 0.5]
im = [0.5, -1.0, 4.0, 0.0]
c = carrier(4, 250.0, 1000.0, 0.0)
cases.append({"id": "ring_modulate.complex", "op": "ring_modulate",
              "args": {"samples": {"re": re, "im": im}, "frequency": 250.0,
                       "sample_rate": 1000.0},
              "expected": {"re": [v * k for v, k in zip(re, c)],
                           "im": [v * k for v, k in zip(im, c)]},
              "tol": TOL, "source": "complex scaled part by part by the real fs/4 carrier"})


def err(cid, why, **args):
    base = {"samples": [1.0], "frequency": 100.0, "sample_rate": 1000.0}
    base.update(args)
    cases.append({"id": f"ring_modulate.{cid}", "op": "ring_modulate", "args": base,
                  "error": "invalid_argument", "source": why})


err("sample_rate_zero", "sample_rate must be positive", sample_rate=0.0)
err("frequency_inf", "frequency must be finite", frequency="inf")
err("phase_nan", "phase must be finite", phase="nan")
err("empty", "samples must not be empty", samples=[])
err("nan_sample", "samples must be finite", samples=[1.0, "nan"])

doc = {
    "schema": 1,
    "suite": "ring_modulate",
    "description": "Ring modulator (conventions: Ring modulator; ADR 0260).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "ring_modulate.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/ring_modulate.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
