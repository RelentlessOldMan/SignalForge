"""Writes vectors/cases/expand.json, stdlib only.

Downward expander (conventions: Downward expander; ADR 0258). The envelope comes
from the ADR 0238 recurrence in exact rationals; the level, the ADR 0256 gain and the factor
10^((g + makeup)/20) come from stdlib floats. Instant cases are checked against the closed form
|y| = 10^(T/20) (|x| / 10^(T/20))^R below the threshold.

Run from the repo root: python vectors/generators/expand.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-12}
cases = []


def envelope(mags, a, r):
    out, prev = [], Fr(0)
    for m in mags:
        m = Fr(m)
        c = Fr(a) if m > prev else Fr(r)
        prev = m + c * (prev - m)
        out.append(prev)
    return out


def gain(lv, t, r, w):
    d = lv - t
    s = r - 1
    if 2 * d > w:
        return 0.0
    if 2 * d < -w:
        return s * d
    if w == 0:
        return 0.0
    q = d - w / 2
    return -(s * q * q / (2 * w))


def run(mags, t, r, a, rel, w, mk):
    f = []
    for e in envelope(mags, a, rel):
        g = gain(20 * math.log10(float(e)), t, r, w) if e > 0 else 0.0
        f.append(10.0 ** ((g + mk) / 20))
    return f


def opt(args, w, mk):
    if w is not None:
        args["knee_db"] = w
    if mk is not None:
        args["makeup_db"] = mk
    return args


def add(cid, x, t, r, a, rel, why, w=None, mk=None):
    f = run([abs(v) for v in x], t, r, a, rel, w or 0.0, mk or 0.0)
    y = [v * k for v, k in zip(x, f)]
    args = opt({"samples": x, "threshold_db": t, "ratio": r, "attack": a, "release": rel}, w, mk)
    cases.append({"id": f"expand.{cid}", "op": "expand", "args": args, "expected": y,
                  "tol": TOL, "source": why})
    return y


def closed(v, t, r):
    lt = 10 ** (t / 20)
    return math.copysign(lt * (abs(v) / lt) ** r, v) if abs(v) < lt else v


x = [2.0, 1.0, 0.5, -0.25, 0.0, 0.125, -4.0]
y = add("instant", x, 0.0, 2.0, 0.0, 0.0, "attack = release = 0, T = 0 dB, R = 2: |y| = |x|^2 "
        "below 1, unchanged at and above")
for v, got in zip(x, y):
    assert abs(got - closed(v, 0.0, 2.0)) <= 1e-12 * abs(got)
x2 = [1.0, 0.25, 0.125, -0.0625, 2.0]
y = add("instant_threshold", x2, -6.0, 3.0, 0.0, 0.0, "instant, T = -6 dB, R = 3")
for v, got in zip(x2, y):
    assert abs(got - closed(v, -6.0, 3.0)) <= 1e-12 * abs(got) + 1e-15
add("soft_knee", [0.25, 0.5, 0.75, 1.0, 1.5, 2.0], 0.0, 3.0, 0.0, 0.0,
    "instant, R = 3, 6 dB knee", w=6.0)
add("smoothed", [0.0, 1.0, 1.0, 1.0, 0.25, 0.25, 0.25, 0.25, 0.0, 0.0625], -6.0, 2.0, 0.5,
    0.75, "attack 1/2, release 3/4: step up then down, T = -6 dB, R = 2")
y = add("makeup", [0.25, 1.0, 4.0], 0.0, 2.0, 0.0, 0.0, "instant, R = 2, 6 dB makeup", mk=6.0)
assert abs(y[2] / 4 - 10 ** 0.3) < 1e-14
y = add("ratio_one", [0.5, -3.0, 0.001], -20.0, 1.0, 0.25, 0.5, "R = 1: unchanged")
assert y == [0.5, -3.0, 0.001]

re = [0.375, 0.0, 3.0, -0.15]
im = [0.5, 0.25, 4.0, 0.2]
f = run([0.625, 0.25, 5.0, 0.25], 0.0, 2.0, 0.0, 0.0, 0.0, 0.0)
cases.append({"id": "expand.complex", "op": "expand",
              "args": {"samples": {"re": re, "im": im}, "threshold_db": 0.0, "ratio": 2.0,
                       "attack": 0.0, "release": 0.0},
              "expected": {"re": [v * k for v, k in zip(re, f)],
                           "im": [v * k for v, k in zip(im, f)]},
              "tol": TOL,
              "source": "complex by magnitude, instant, T = 0 dB, R = 2: |x| = 5/8, 1/4, 5, 1/4; "
                        "phase kept"})
assert abs(f[0] - 0.625) < 1e-14 and f[2] == 1.0


def err(cid, why, **args):
    base = {"samples": [1.0], "threshold_db": -10.0, "ratio": 2.0, "attack": 0.5,
            "release": 0.5}
    base.update(args)
    cases.append({"id": f"expand.{cid}", "op": "expand", "args": base,
                  "error": "invalid_argument", "source": why})


err("ratio_below_one", "ratio must be at least 1", ratio=0.5)
err("attack_one", "attack must be in [0, 1)", attack=1.0)
err("release_negative", "release must be in [0, 1)", release=-0.25)
err("knee_negative", "knee_db must be at least 0", knee_db=-1.0)
err("makeup_inf", "makeup_db must be finite", makeup_db="inf")
err("empty", "samples must not be empty", samples=[])
err("nan_sample", "samples must be finite", samples=[1.0, "nan"])

doc = {
    "schema": 1,
    "suite": "expand",
    "description": "Downward expander (conventions: Downward expander; ADR 0258).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "expand.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/compress.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
