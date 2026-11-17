"""Writes vectors/cases/envelope_follower.json, stdlib only.

Envelope follower (conventions: Envelope follower; ADR 0238). The expected values run the
definition in exact rational arithmetic (binary-fraction coefficients, complex samples with exact
magnitudes such as 3 + 4i), checked against the closed forms r (1 - attack^(n+1)) for a constant
from rest and release^k after a drop to 0. No comparison is a tie.

Run from the repo root: python vectors/generators/envelope_follower.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def follow(mags, a, r):
    out = []
    prev = Fr(0)
    for v in mags:
        assert v != prev or v == 0, "tie"
        c = a if v > prev else r
        prev = v + c * (prev - v)
        out.append(prev)
    return out


def add(cid, mags, a, r, why, samples=None):
    a, r = Fr(a), Fr(r)
    y = follow([Fr(v) for v in mags], a, r)
    args = {"samples": samples if samples is not None else [float(v) for v in mags],
            "attack": float(a), "release": float(r)}
    cases.append({"id": f"envelope_follower.{cid}", "op": "envelope_follower", "args": args,
                  "expected": [float(v) for v in y], "tol": TOL, "source": why})
    return y


y = add("constant_rise", [2.0] * 8, 0.75, 0.5, "constant 2 from rest: 2 (1 - 0.75^(n+1))")
assert y == [2 * (1 - Fr(3, 4) ** (n + 1)) for n in range(8)]
y = add("drop", [4.0, 0.0, 0.0, 0.0, 0.0, 0.0], 0.0, 0.875, "instant attack, then release^k")
assert y == [4 * Fr(7, 8) ** k for k in range(6)]
signed = [1.0, -3.0, 2.0, -0.5, 0.25, 4.0, -1.0, 0.0, 0.5, -2.0]
add("signed", [abs(v) for v in signed], 0.5, 0.9375,
    "signed real samples: the magnitude is followed", samples=signed)
y = add("passthrough", [1.0, 3.0, 2.0, 0.5], 0.0, 0.0, "both 0: |x| itself")
assert y == [1, 3, 2, Fr(1, 2)]
add("complex", [5.0, 13.0, 0.0, 10.0, 1.0], 0.25, 0.75, "complex samples with exact magnitudes",
    samples={"re": [3.0, 5.0, 0.0, -6.0, 0.0], "im": [4.0, -12.0, 0.0, 8.0, -1.0]})


def err(cid, why, **args):
    cases.append({"id": f"envelope_follower.{cid}", "op": "envelope_follower", "args": args,
                  "error": "invalid_argument", "source": why})


err("attack_one", "attack must be below 1", samples=[1.0], attack=1.0, release=0.5)
err("release_negative", "release must be at least 0", samples=[1.0], attack=0.5, release=-0.1)
err("empty", "samples must not be empty", samples=[], attack=0.5, release=0.5)
err("nan_sample", "samples must be finite", samples=[1.0, "nan"], attack=0.5, release=0.5)

doc = {
    "schema": 1,
    "suite": "envelope_follower",
    "description": "Envelope follower (conventions: Envelope follower; ADR 0238).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "envelope_follower.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/envelope_follower.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
