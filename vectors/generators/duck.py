"""Writes vectors/cases/duck.json, stdlib only.

Sidechain compressor (conventions: Sidechain compressor; ADR 0278): the feed-forward compressor
(ADR 0257) with its envelope taken from the key. The envelope comes from the ADR 0238 recurrence
in exact rationals; the level, the ADR 0254 gain and the factor 10^((g + makeup)/20) come from
stdlib floats. Instant cases are checked against the closed form gain.

Run from the repo root: python vectors/generators/duck.py [--check]
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
    s = 1 / r - 1
    if 2 * d < -w:
        return 0.0
    if 2 * d > w:
        return s * d
    if w == 0:
        return 0.0
    q = d + w / 2
    return s * q * q / (2 * w)


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


def add(cid, x, key, t, r, a, rel, why, w=None, mk=None):
    f = run([abs(v) for v in key], t, r, a, rel, w or 0.0, mk or 0.0)
    args = opt({"samples": x, "key": key, "threshold_db": t, "ratio": r, "attack": a,
                "release": rel}, w, mk)
    if isinstance(x, dict):
        y = {"re": [v * k for v, k in zip(x["re"], f)], "im": [v * k for v, k in zip(x["im"], f)]}
    else:
        y = [v * k for v, k in zip(x, f)]
    cases.append({"id": f"duck.{cid}", "op": "duck", "args": args, "expected": y,
                  "tol": TOL, "source": why})
    return y, f


music = [0.5, -0.25, 0.75, -0.5, 0.25, 0.5]
voice = [0.0, 4.0, 16.0, 0.5, 0.0, 100.0]
y, f = add("instant", music, voice, 0.0, 2.0, 0.0, 0.0,
           "attack = release = 0, T = 0 dB, R = 2: gain 1/sqrt|key| above 1, 1 at and below")
for k, got in zip(voice, f):
    want = 1 / math.sqrt(abs(k)) if abs(k) > 1 else 1.0
    assert abs(got - want) <= 1e-12 * want
add("smoothed", [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6],
    [0.1, 2.0, 3.0, 2.5, 0.2, 0.1, 0.05, 1.5], -6.0, 4.0, 0.25, 0.75,
    "T -6 dB, R 4, attack 1/4, release 3/4, knee 6 dB, makeup 2 dB", w=6.0, mk=2.0)
add("silent_key", [0.5, -1.0, 2.0], [0.0, 0.0, 0.0], -20.0, 8.0, 0.5, 0.5,
    "silent key: gain 0 dB, only the makeup", mk=-6.0)
add("complex", {"re": [1.0, 0.0, -0.5, 0.25], "im": [0.0, 1.0, 0.5, -2.0]},
    [0.5, 3.0, 8.0, 0.25], 0.0, 3.0, 0.0, 0.5, "complex samples, part by part, R 3")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0], "key": [1.0, 2.0], "threshold_db": 0.0, "ratio": 2.0,
            "attack": 0.5, "release": 0.5}
    base.update(args)
    cases.append({"id": f"duck.{cid}", "op": "duck", "args": base,
                  "error": "invalid_argument", "source": why})


err("length", "samples and key must have the same length", key=[1.0])
err("ratio_low", "ratio must be at least 1", ratio=0.5)
err("attack_one", "attack must be below 1", attack=1.0)
err("empty_key", "key must not be empty", samples=[], key=[])

doc = {
    "schema": 1,
    "suite": "duck",
    "description": "Sidechain compressor (conventions: Sidechain compressor; ADR 0278).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "duck.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/duck.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
