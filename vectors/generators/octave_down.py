"""Writes vectors/cases/octave_down.json, stdlib only.

Octave-down effect (conventions: Octave-down effect; ADR 0291), transcribed from the rule: a
sign starting at +1 flips before sample n >= 1 when x[n-1] < 0 <= x[n]; wet[n] = s |x[n]|; the
output is x (1 - mix) + wet mix in stdlib floats.

Run from the repo root: python vectors/generators/octave_down.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-15, "rel": 1e-15}
cases = []


def wet(x):
    s, out = 1.0, []
    for n, v in enumerate(x):
        if n > 0 and x[n - 1] < 0 <= v:
            s = -s
        out.append(s * abs(v))
    return out


def add(cid, x, mix, why):
    w = wet(x)
    y = [v * (1 - mix) + u * mix for v, u in zip(x, w)]
    cases.append({"id": f"octave_down.{cid}", "op": "octave_down",
                  "args": {"samples": x, "mix": mix}, "expected": y, "tol": TOL, "source": why})
    return w


# A sine at fs/8 offset by a quarter sample so no sample is exactly 0.
S8 = [math.sin(2 * math.pi * (n + 0.25) / 8) for n in range(24)]
w = add("sine_wet", S8, 1.0, "sine at fs/8, fully wet: |x| with the sign flipping every 8 samples")
assert all(abs(w[n] + w[n + 8]) < 1e-14 for n in range(8))
add("sine_blend", S8, 0.5, "sine at fs/8, half wet")
add("zero_counts_as_rising", [-1.0, 0.0, 2.0, -3.0, 0.5, -0.25, 0.0], 1.0,
    "x[n-1] < 0 <= x[n] at n = 1 and n = 4 and n = 6; 0 to 2 is not a crossing")
add("first_sample", [0.5, -0.5, 0.25], 1.0, "the first sample never flips the sign")
add("dry", S8, 0.0, "mix 0: the input")


def err(cid, why, **args):
    base = {"samples": [1.0, -2.0], "mix": 0.5}
    base.update(args)
    cases.append({"id": f"octave_down.{cid}", "op": "octave_down", "args": base,
                  "error": "invalid_argument", "source": why})


err("mix_high", "mix must be at most 1", mix=1.01)
err("empty", "samples must not be empty", samples=[])

doc = {
    "schema": 1,
    "suite": "octave_down",
    "description": "Octave-down effect (conventions: Octave-down effect; ADR 0291).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "octave_down.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/octave_down.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
