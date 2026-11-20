"""Writes vectors/cases/hamming_distance.json, stdlib only.

The Hamming distance (conventions: Hamming distance; ADR 0421): the differences counted
directly.

Run from the repo root: python vectors/generators/hamming_distance.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys

cases = []


def add(cid, x, y, why):
    n = sum(1 for a, b in zip(x, y) if a != b)
    cases.append(
        {
            "id": f"hamming_distance.{cid}",
            "op": "hamming_distance",
            "args": {"x": x, "y": y},
            "expected": n,
            "source": why,
        }
    )
    return n


got = add("same", [1.0, -2.0, 3.0], [1.0, -2.0, 3.0], "equal vectors: 0")
assert got == 0
got = add("all", [1.0, 2.0], [2.0, 1.0], "every index differs: 2")
assert got == 2
got = add("signed_zero", [0.0, 1.0, 2.0], [-0.0, 1.0, 5.0], "0.0 equals -0.0; one other differs: 1")
assert got == 1
got = add(
    "symbols",
    [0.0, 1.0, 2.0, 3.0, 0.0, 1.0, 2.0, 3.0],
    [0.0, 1.0, 3.0, 3.0, 0.0, 2.0, 2.0, 3.0],
    "8 QPSK symbol indices, 2 in error",
)
assert got == 2
got = add("near", [1.0], [1.0000000000000002], "one ulp apart still differs: 1")
assert got == 1
rng = random.Random(421)
x = [float(rng.randint(0, 3)) for _ in range(32)]
y = [v if rng.random() < 0.8 else float(rng.randint(0, 3)) for v in x]
add("random", x, y, "32 symbols from random.Random(421), about a fifth redrawn")


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "y": [2.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"hamming_distance.{cid}",
            "op": "hamming_distance",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "x needs a value", x=[], y=[])
err("lengths", "x and y must match", y=[1.0, 1.0])
err("nan", "values must be finite", x=[1.0, "nan", 1.0])
err("inf", "values must be finite", y=[1.0, "inf", 1.0])

doc = {
    "schema": 1,
    "suite": "hamming_distance",
    "description": "The Hamming distance (conventions: Hamming distance; ADR 0421).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "hamming_distance.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/hamming_distance.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
