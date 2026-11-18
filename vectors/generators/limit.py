"""Writes vectors/cases/limit.json, stdlib only.

Lookahead peak limiter (conventions: Lookahead peak limiter; ADR 0269), transcribed from the
definition with stdlib floats. Complex magnitudes are 3-4-5 binary fractions, so |x| is exact.

Run from the repo root: python vectors/generators/limit.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys

TOL = {"abs": 1e-15, "rel": 1e-14}
cases = []


def gains(mag, t, la, rel):
    c = [t / m if m > t else 1.0 for m in mag]
    g, prev = [], 1.0
    for n in range(len(c)):
        a = min(c[n:min(n + la, len(c) - 1) + 1])
        prev = a if a < prev else a + rel * (prev - a)
        g.append(prev)
    return g


def add(cid, x, t, la, rel, why):
    g = gains([abs(v) for v in x], t, la, rel)
    y = [v * k for v, k in zip(x, g)]
    assert all(abs(v) <= t * (1 + 1e-15) for v in y)
    cases.append({"id": f"limit.{cid}", "op": "limit",
                  "args": {"samples": x, "threshold": t, "lookahead": la, "release": rel},
                  "expected": y, "tol": TOL, "source": why})
    return y, g


X = [0.25, 0.5, 2.0, -0.5, 0.25, 0.25, 0.25, 0.25]
y, g = add("no_lookahead", X, 1.0, 0, 0.5,
           "lookahead 0: gain 1/2 at the peak, then recovers 1/2 of the way each sample")
assert g == [1.0, 1.0, 0.5, 0.75, 0.875, 0.9375, 0.96875, 0.984375]
y, g = add("lookahead_2", X, 1.0, 2, 0.5, "lookahead 2: gain falls to 1/2 two samples early")
assert g[:4] == [0.5, 0.5, 0.5, 0.75]
y, g = add("hold_release", X, 1.0, 1, 0.0, "release 0: gain back to 1 at once")
assert g == [1.0, 0.5, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0]
y, g = add("quiet", [0.1, -0.2, 0.3], 0.5, 4, 0.9, "below threshold: unchanged")
assert y == [0.1, -0.2, 0.3]
add("dense", [0.9, -1.3, 1.7, -0.4, 2.2, 0.6, -0.8, 1.1, 0.3, -1.9, 0.05], 0.8, 3, 0.75,
    "threshold 0.8, lookahead 3, release 0.75 on a busy signal")
add("lookahead_past_end", [0.5, 0.5, 4.0], 1.0, 10, 0.5, "lookahead longer than the signal")

re_, im_ = [0.3, 0.75, 0.0, 0.1875], [0.4, 1.0, 0.5, 0.25]
# |x| = 1/2, 5/4, 1/2, 5/16
mag = [0.5, 1.25, 0.5, 0.3125]
assert all(abs(complex(r, i)) == m for r, i, m in zip(re_, im_, mag))
g = gains(mag, 1.0, 1, 0.5)
cases.append({"id": "limit.complex", "op": "limit",
              "args": {"samples": {"re": re_, "im": im_}, "threshold": 1.0, "lookahead": 1,
                       "release": 0.5},
              "expected": {"re": [r * k for r, k in zip(re_, g)],
                           "im": [i * k for i, k in zip(im_, g)]},
              "tol": TOL, "source": "complex, |x| 5/4 at sample 1: gain 4/5 from sample 0"})


def err(cid, why, **args):
    base = {"samples": [1.0, -2.0], "threshold": 1.0, "lookahead": 1, "release": 0.5}
    base.update(args)
    cases.append({"id": f"limit.{cid}", "op": "limit", "args": base,
                  "error": "invalid_argument", "source": why})


err("threshold_zero", "threshold must be positive", threshold=0.0)
err("lookahead_negative", "lookahead must be at least 0", lookahead=-1)
err("release_one", "release must be below 1", release=1.0)
err("release_negative", "release must be at least 0", release=-0.25)
err("empty", "samples must not be empty", samples=[])
err("nan_sample", "samples must be finite", samples=[1.0, "nan"])

doc = {
    "schema": 1,
    "suite": "limit",
    "description": "Lookahead peak limiter (conventions: Lookahead peak limiter; ADR 0269).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "limit.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/limit.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
