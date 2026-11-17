"""Writes vectors/cases/peak_hold.json, stdlib only.

Peak hold (conventions: Peak hold; ADR 0243). The expected values run the definition in exact
rational arithmetic with binary-fraction release values (ties give the same value on either
branch), checked against the closed form for an impulse: a for hold + 1 samples, then
a release^k.

Run from the repo root: python vectors/generators/peak_hold.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def run(mags, hold, rel):
    out = []
    p, c = Fr(0), 0
    for r in mags:
        if r >= p:
            p, c = r, 0
        elif c < hold:
            c += 1
        else:
            p = max(rel * p, r)
        out.append(p)
    return out


def add(cid, mags, hold, rel, why, samples=None):
    rel = Fr(rel)
    y = run([Fr(v) for v in mags], hold, rel)
    args = {"samples": samples if samples is not None else [float(v) for v in mags],
            "hold": hold, "release": float(rel)}
    cases.append({"id": f"peak_hold.{cid}", "op": "peak_hold", "args": args,
                  "expected": [float(v) for v in y], "tol": TOL, "source": why})
    return y


y = add("impulse", [4.0] + [0.0] * 9, 3, 0.5, "impulse 4: held 4 samples, then 4 / 2^k")
assert y == [4] * 4 + [4 * Fr(1, 2) ** k for k in range(1, 7)]
y = add("no_hold", [2.0, 0.0, 0.0, 0.0], 0, 0.75, "hold 0: decays at once")
assert y == [2, Fr(3, 2), Fr(9, 8), Fr(27, 32)]
add("floor", [8.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0], 1, 0.5,
    "decay stops at the input, then follows it")
signed = [1.0, -3.0, 2.0, -0.5, 0.25, 4.0, -1.0, 0.0, 0.5, -2.0, 0.0, 0.0]
add("signed", [abs(v) for v in signed], 2, 0.875, "signed real samples: the magnitude is held",
    samples=signed)
add("retrigger", [2.0, 0.0, 3.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0], 2, 0.25,
    "a larger peak during the hold restarts it")
add("complex", [5.0, 0.0, 13.0, 1.0, 0.0, 0.0], 1, 0.5, "complex samples with exact magnitudes",
    samples={"re": [3.0, 0.0, 5.0, 0.0, 0.0, 0.0], "im": [4.0, 0.0, -12.0, -1.0, 0.0, 0.0]})


def err(cid, why, **args):
    cases.append({"id": f"peak_hold.{cid}", "op": "peak_hold", "args": args,
                  "error": "invalid_argument", "source": why})


err("hold_negative", "hold must be at least 0", samples=[1.0], hold=-1, release=0.5)
err("release_one", "release must be below 1", samples=[1.0], hold=1, release=1.0)
err("empty", "samples must not be empty", samples=[], hold=1, release=0.5)
err("nan_sample", "samples must be finite", samples=[1.0, "nan"], hold=1, release=0.5)

doc = {
    "schema": 1,
    "suite": "peak_hold",
    "description": "Peak hold (conventions: Peak hold; ADR 0243).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "peak_hold.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/peak_hold.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
