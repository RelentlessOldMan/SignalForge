"""Writes vectors/cases/reverse_delay.json, stdlib only.

Reverse delay (conventions: Reverse delay; ADR 0298), transcribed from the rule: with
n = q B + r, wet[n] = x[(q - 1) B + (B - 1 - r)] for q >= 1 and 0 in the first block; the output
is x (1 - mix) + wet mix in stdlib floats.

Run from the repo root: python vectors/generators/reverse_delay.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-15, "rel": 1e-15}
cases = []


def wet(x, b):
    out = []
    for n in range(len(x)):
        q, r = divmod(n, b)
        out.append(x[(q - 1) * b + (b - 1 - r)] if q >= 1 else 0.0)
    return out


def add(cid, x, b, mix, why):
    w = wet(x, b)
    y = [v * (1 - mix) + u * mix for v, u in zip(x, w)]
    cases.append({"id": f"reverse_delay.{cid}", "op": "reverse_delay",
                  "args": {"samples": x, "block": b, "mix": mix}, "expected": y, "tol": TOL,
                  "source": why})
    return w


RAMP = [float(n + 1) for n in range(14)]
w = add("ramp_wet", RAMP, 4, 1.0, "blocks of 4, fully wet; the last block is cut short")
assert w == [0.0] * 4 + [4.0, 3.0, 2.0, 1.0, 8.0, 7.0, 6.0, 5.0, 12.0, 11.0]
M = [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6, 0.5, 1.3, -0.1, 0.05, 0.9, -0.4, 0.6, -1.0]
add("blend", M, 5, 0.35, "blocks of 5, 35% wet")
assert add("block_one", M, 1, 1.0, "block 1: a one-sample delay") == [0.0] + M[:-1]
add("block_long", M, 20, 0.5, "a block longer than the signal: the wet signal is silent")
add("dry", M, 3, 0.0, "mix 0: the input")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0], "block": 2, "mix": 0.5}
    base.update(args)
    cases.append({"id": f"reverse_delay.{cid}", "op": "reverse_delay", "args": base,
                  "error": "invalid_argument", "source": why})


err("block_zero", "block must be at least 1", block=0)
err("mix_negative", "mix must be at least 0", mix=-0.1)
err("empty", "samples must not be empty", samples=[])

doc = {
    "schema": 1,
    "suite": "reverse_delay",
    "description": "Reverse delay (conventions: Reverse delay; ADR 0298).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "reverse_delay.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/reverse_delay.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
