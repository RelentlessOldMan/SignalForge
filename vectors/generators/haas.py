"""Writes vectors/cases/haas.json, stdlib only.

Haas widener (conventions: Haas widener; ADR 0276): one side is the input shifted late by a
whole number of samples, the other is the input. Every value is a copied sample or 0.

Run from the repo root: python vectors/generators/haas.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 0.0, "rel": 0.0}
cases = []


def add(cid, x, d, side, why):
    late = [0.0] * min(d, len(x)) + x[: max(len(x) - d, 0)]
    left, right = (late, list(x)) if side == "left" else (list(x), late)
    args = {"samples": x, "delay": d}
    if side is not None:
        args["side"] = side
    cases.append({"id": f"haas.{cid}", "op": "haas", "args": args,
                  "expected": {"left": left, "right": right}, "tol": TOL, "source": why})


X = [1.0, -0.5, 0.25, 2.0, -1.0, 0.75]
add("default_right", X, 2, None, "default side: right is x[n-2], left is x")
add("left", X, 3, "left", "left is x[n-3], right is x")
add("zero", X, 0, "right", "delay 0: two copies of x")
add("past_end", [0.5, -1.0], 4, "right", "delay past the end: the late side is all zero")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0], "delay": 1}
    base.update(args)
    cases.append({"id": f"haas.{cid}", "op": "haas", "args": base,
                  "error": "invalid_argument", "source": why})


err("delay_negative", "delay must be at least 0", delay=-1)
err("side_unknown", 'side must be "left" or "right"', side="centre")
err("empty", "samples must not be empty", samples=[])

doc = {
    "schema": 1,
    "suite": "haas",
    "description": "Haas widener (conventions: Haas widener; ADR 0276).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "haas.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/haas.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
