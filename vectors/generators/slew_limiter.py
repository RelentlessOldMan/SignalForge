"""Writes vectors/cases/slew_limiter.json, stdlib only.

Slew-rate limiter (conventions: Slew-rate limiter; ADR 0242). The expected values run the
definition in exact rational arithmetic with binary-fraction limits, checked against the closed
form min(a, (n + 1) rise) for a step from rest. At a tie (d = rise or d = -fall) both
branches give x[n] exactly, which the generator asserts.

Run from the repo root: python vectors/generators/slew_limiter.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def slew(x, up, down):
    out = []
    prev = Fr(0)
    for v in x:
        d = v - prev
        nxt = prev + up if d > up else prev - down if d < -down else v
        assert d not in (up, -down) or nxt == v, "a tie must give x[n] either way"
        prev = nxt
        out.append(prev)
    return out


def add(cid, x, up, down, why):
    up, down = Fr(up), Fr(down)
    y = slew([Fr(v) for v in x], up, down)
    cases.append({"id": f"slew_limiter.{cid}", "op": "slew_limiter",
                  "args": {"samples": x, "rise": float(up), "fall": float(down)},
                  "expected": [float(v) for v in y], "tol": TOL, "source": why})
    return y


y = add("step_up", [3.0] * 8, 0.5, 1.0, "step to 3 from rest: min(3, (n + 1) / 2)")
assert y == [min(Fr(3), Fr(n + 1, 2)) for n in range(8)]
y = add("step_down", [-2.0] * 6, 1.0, 0.375, "step to -2: falls 3/8 per sample")
assert y == [max(Fr(-2), -Fr(3 * (n + 1), 8)) for n in range(6)]
y = add("within", [0.25, 0.5, 0.375, 0.125, -0.25], 0.5, 0.5, "small steps pass unchanged")
assert y == [Fr(1, 4), Fr(1, 2), Fr(3, 8), Fr(1, 8), Fr(-1, 4)]
add("square", [2.0, 2.0, 2.0, 2.0, -2.0, -2.0, -2.0, -2.0, -2.0, 2.0, 2.0], 0.75, 1.25,
    "square wave: asymmetric ramps")
add("mixed", [0.5, 1.5, -1.0, 2.25, 0.0, -0.75, 1.0, 3.0, -2.0, 0.25], 0.625, 0.875, "mixed")


def err(cid, why, **args):
    cases.append({"id": f"slew_limiter.{cid}", "op": "slew_limiter", "args": args,
                  "error": "invalid_argument", "source": why})


err("rise_zero", "rise must be positive", samples=[1.0], rise=0.0, fall=1.0)
err("fall_negative", "fall must be positive", samples=[1.0], rise=1.0, fall=-0.5)
err("empty", "samples must not be empty", samples=[], rise=1.0, fall=1.0)
err("nan_sample", "samples must be finite", samples=[1.0, "nan"], rise=1.0, fall=1.0)

doc = {
    "schema": 1,
    "suite": "slew_limiter",
    "description": "Slew-rate limiter (conventions: Slew-rate limiter; ADR 0242).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "slew_limiter.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/slew_limiter.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
