"""Writes vectors/cases/balance.json, stdlib only.

Stereo balance (conventions: Stereo balance; ADR 0277): the far side scaled by 1 - |p|, the
near side unchanged. With dyadic positions every product is exact.

Run from the repo root: python vectors/generators/balance.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 0.0, "rel": 0.0}
cases = []
L = [1.0, -0.5, 0.25, 2.0]
R = [0.5, 1.5, -2.0, -0.75]


def add(cid, p, why):
    gl = 1 - p if p > 0 else 1.0
    gr = 1 + p if p < 0 else 1.0
    cases.append({"id": f"balance.{cid}", "op": "balance",
                  "args": {"left": L, "right": R, "position": p},
                  "expected": {"left": [v * gl for v in L], "right": [v * gr for v in R]},
                  "tol": TOL, "source": why})


add("centre", 0.0, "centred: both sides unchanged")
add("right_half", 0.5, "position 1/2: left halved, right unchanged")
add("left_quarter", -0.25, "position -1/4: right scaled by 3/4, left unchanged")
add("hard_left", -1.0, "position -1: right muted")
add("hard_right", 1.0, "position 1: left muted")


def err(cid, why, **args):
    base = {"left": [1.0, 2.0], "right": [3.0, 4.0], "position": 0.0}
    base.update(args)
    cases.append({"id": f"balance.{cid}", "op": "balance", "args": base,
                  "error": "invalid_argument", "source": why})


err("position_high", "position must be at most 1", position=1.5)
err("position_low", "position must be at least -1", position=-2.0)
err("length", "left and right must have the same length", right=[1.0])
err("empty", "left must not be empty", left=[], right=[])

doc = {
    "schema": 1,
    "suite": "balance",
    "description": "Stereo balance (conventions: Stereo balance; ADR 0277).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "balance.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/balance.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
