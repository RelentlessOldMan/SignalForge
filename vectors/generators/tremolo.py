"""Writes vectors/cases/tremolo.json, stdlib only.

Tremolo (conventions: Tremolo; ADR 0261). The expected values come from the definition
x[n] (1 - depth (1 - cos((2 pi rate)(n / fs))) / 2) with the stdlib math.cos; the fs/4 case is
checked by hand against the gains 1, 1 - d/2, 1 - d, 1 - d/2.

Run from the repo root: python vectors/generators/tremolo.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def gains(size, rate, depth, fs):
    out = []
    for n in range(size):
        c = math.cos(2.0 * math.pi * rate * (n / fs))
        out.append(1 - depth * (1 - c) / 2)
    return out


def add(cid, x, rate, depth, fs, why):
    g = gains(len(x), rate, depth, fs)
    cases.append({"id": f"tremolo.{cid}", "op": "tremolo",
                  "args": {"samples": x, "rate": rate, "depth": depth, "sample_rate": fs},
                  "expected": [v * k for v, k in zip(x, g)], "tol": TOL, "source": why})
    return g


g = add("quarter", [1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 2.0], 250.0, 0.5, 1000.0,
        "rate fs/4, depth 1/2: gains 1, 3/4, 1/2, 3/4")
assert all(abs(a - b) < 1e-15 for a, b in zip(g, [1, 0.75, 0.5, 0.75] * 2))
g = add("full_depth", [1.0, -1.0, 0.5, 0.25], 4000.0, 1.0, 8000.0,
        "rate fs/2, depth 1: gains 1, 0, 1, 0")
assert all(abs(a - b) < 1e-15 for a, b in zip(g, [1, 0, 1, 0]))
g = add("zero_depth", [0.25, -1.5, 3.0], 7.0, 0.0, 1000.0, "depth 0: unchanged")
assert g == [1.0, 1.0, 1.0]
add("general", [0.5, -1.0, 1.5, 2.0, -0.25, 0.75, 1.0], 5.5, 0.75, 48.0, "general rate")

re = [1.0, 2.0, -3.0, 0.5]
im = [0.5, -1.0, 4.0, 0.0]
g = gains(4, 250.0, 1.0, 1000.0)
cases.append({"id": "tremolo.complex", "op": "tremolo",
              "args": {"samples": {"re": re, "im": im}, "rate": 250.0, "depth": 1.0,
                       "sample_rate": 1000.0},
              "expected": {"re": [v * k for v, k in zip(re, g)],
                           "im": [v * k for v, k in zip(im, g)]},
              "tol": TOL, "source": "complex scaled part by part, gains 1, 1/2, 0, 1/2"})


def err(cid, why, **args):
    base = {"samples": [1.0], "rate": 5.0, "depth": 0.5, "sample_rate": 1000.0}
    base.update(args)
    cases.append({"id": f"tremolo.{cid}", "op": "tremolo", "args": base,
                  "error": "invalid_argument", "source": why})


err("depth_above_one", "depth must be in [0, 1]", depth=1.5)
err("depth_negative", "depth must be in [0, 1]", depth=-0.25)
err("rate_inf", "rate must be finite", rate="inf")
err("sample_rate_zero", "sample_rate must be positive", sample_rate=0.0)
err("empty", "samples must not be empty", samples=[])
err("nan_sample", "samples must be finite", samples=[1.0, "nan"])

doc = {
    "schema": 1,
    "suite": "tremolo",
    "description": "Tremolo (conventions: Tremolo; ADR 0261).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "tremolo.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/tremolo.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
