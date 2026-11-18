"""Writes vectors/cases/bitcrush.json, stdlib only.

Bitcrusher (conventions: Bitcrusher; ADR 0266). Hold, then round half to even onto
k 2^(1 - bits) with |k| <= 2^(bits - 1) - 1, in exact rationals.

Run from the repo root: python vectors/generators/bitcrush.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 0.0, "rel": 0.0}
cases = []


def crush(x, bits, hold):
    step = Fr(1, 2 ** (bits - 1))
    top = 2 ** (bits - 1) - 1
    out = []
    for n in range(len(x)):
        v = Fr(x[hold * (n // hold)])
        k = round(v / step)  # Fraction rounds half to even
        out.append(step * max(-top, min(top, k)))
    return out


def add(cid, x, bits, why, hold=None):
    y = crush(x, bits, hold or 1)
    args = {"samples": x, "bits": bits}
    if hold is not None:
        args["hold"] = hold
    cases.append({"id": f"bitcrush.{cid}", "op": "bitcrush", "args": args,
                  "expected": [float(v) for v in y], "tol": TOL, "source": why})
    return y


y = add("two_bits", [-1.0, -0.3, -0.25, 0.0, 0.2, 0.25, 0.75, 1.0], 2,
        "2 bits: step 1/2, levels -1/2, 0, 1/2; ties 0.25 and -0.25 go to 0")
assert y == [Fr(-1, 2), Fr(-1, 2), 0, 0, 0, 0, Fr(1, 2), Fr(1, 2)]
y = add("four_bits", [0.1, -0.6, 0.95, -1.0, 0.0625, 0.1875], 4,
        "4 bits: step 1/8, at most 7/8; 1/16 rounds to 0, 3/16 to 1/4")
assert y[2] == Fr(7, 8) and y[3] == Fr(-7, 8) and y[4] == 0 and y[5] == Fr(1, 4)
y = add("hold", [0.1, 0.9, -0.4, 0.3, 0.7, -0.9, 0.2], 3,
        "3 bits, hold 3: x[0], x[3], x[6] rounded to quarters", hold=3)
assert y == [0, 0, 0, Fr(1, 4), Fr(1, 4), Fr(1, 4), Fr(1, 4)]
add("sixteen_bits", [0.123456789, -0.987654321, 0.5], 16, "16 bits: step 2^-15")


def err(cid, why, **args):
    base = {"samples": [0.5], "bits": 8}
    base.update(args)
    cases.append({"id": f"bitcrush.{cid}", "op": "bitcrush", "args": base,
                  "error": "invalid_argument", "source": why})


err("bits_low", "bits must be at least 2", bits=1)
err("bits_high", "bits must be at most 24", bits=25)
err("hold_zero", "hold must be at least 1", hold=0)
err("empty", "samples must not be empty", samples=[])
err("nan_sample", "samples must be finite", samples=["nan"])

doc = {
    "schema": 1,
    "suite": "bitcrush",
    "description": "Bitcrusher (conventions: Bitcrusher; ADR 0266).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "bitcrush.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/bitcrush.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
