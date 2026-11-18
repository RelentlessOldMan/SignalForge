"""Writes vectors/cases/phaser.json, stdlib only.

Phaser (conventions: Phaser; ADR 0274): a chain of first-order allpasses (ADR 0033) whose break
frequency sweeps under a cosine LFO, mixed with the dry signal, transcribed with the stdlib
math.cos and math.tan.

Run from the repo root: python vectors/generators/phaser.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def coeffs(length, low, high, rate, fs):
    w = 2.0 * math.pi * rate
    c = []
    for n in range(length):
        fc = low + (high - low) * ((1 - math.cos(w * (n / fs))) / 2)
        t = math.tan(math.pi * fc / fs)
        c.append((t - 1) / (t + 1))
    return c


def chain(v, c, stages):
    for _ in range(stages):
        x1 = y1 = 0.0
        out = []
        for cn, xn in zip(c, v):
            yn = cn * xn + x1 - cn * y1
            x1, y1 = xn, yn
            out.append(yn)
        v = out
    return v


def mixed(x, wet, mix):
    return [a * (1 - mix) + b * mix for a, b in zip(x, wet)]


def add(cid, x, stages, low, high, rate, fs, mix, why):
    y = mixed(x, chain(x, coeffs(len(x), low, high, rate, fs), stages), mix)
    cases.append({"id": f"phaser.{cid}", "op": "phaser",
                  "args": {"samples": x, "stages": stages, "low": low, "high": high,
                           "rate": rate, "sample_rate": fs, "mix": mix},
                  "expected": y, "tol": TOL, "source": why})
    return y


X = [1.0, -0.5, 0.25, 2.0, -1.0, 0.75, 0.5, -0.25]
y = add("quarter_rate", X, 2, 2.0, 2.0, 1.0, 8.0, 1.0,
        "low = high = fs/4: c is about 0, so two stages are about x[n-2]")
assert all(abs(a - b) < 1e-15 for a, b in zip(y, [0.0, 0.0] + X[:-2]))
add("fixed", X, 1, 0.5, 0.5, 3.0, 8.0, 1.0, "one fixed allpass at fs/16, wet only")
add("swept", [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6, 0.5, 1.3, -0.1, 0.05],
    4, 0.2, 3.5, 0.9, 10.0, 0.5, "4 stages swept 0.2 to 3.5 Hz at 0.9 Hz, fs 10 Hz, mix 1/2")
add("dry", X, 3, 1.0, 3.0, 1.0, 8.0, 0.0, "mix 0: the dry signal")

cre, cim = [1.0, 0.0, -2.0, 0.5, 0.25], [0.0, 1.0, 0.5, -1.0, 2.0]
c = coeffs(5, 0.5, 1.5, 1.0, 5.0)
yr, yi = mixed(cre, chain(cre, c, 2), 0.5), mixed(cim, chain(cim, c, 2), 0.5)
cases.append({"id": "phaser.complex", "op": "phaser",
              "args": {"samples": {"re": cre, "im": cim}, "stages": 2, "low": 0.5,
                       "high": 1.5, "rate": 1.0, "sample_rate": 5.0, "mix": 0.5},
              "expected": {"re": yr, "im": yi},
              "tol": TOL, "source": "complex, part by part, 2 stages"})


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0], "stages": 2, "low": 1.0, "high": 3.0, "rate": 1.0,
            "sample_rate": 8.0, "mix": 0.5}
    base.update(args)
    cases.append({"id": f"phaser.{cid}", "op": "phaser", "args": base,
                  "error": "invalid_argument", "source": why})


err("stages_zero", "stages must be at least 1", stages=0)
err("low_zero", "low must be positive", low=0.0)
err("high_below_low", "high must be at least low", low=3.0, high=2.0)
err("high_nyquist", "high must be below fs/2", high=4.0)
err("mix_negative", "mix must be at least 0", mix=-0.5)
err("empty", "samples must not be empty", samples=[])

doc = {
    "schema": 1,
    "suite": "phaser",
    "description": "Phaser (conventions: Phaser; ADR 0274).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "phaser.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/phaser.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
