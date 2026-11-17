"""Writes vectors/cases/cross_correlation.json, stdlib only.

Cross-correlation (conventions: Cross-correlation; ADR 0190): r[k] = sum_n x[n+k] conj y[n] for
k = -(M-1) .. N-1, lag k at index k + M - 1, unscaled. Expected values are hand sums, each worked
in the source text and checked here against a direct double loop over the definition.

Run from the repo root: python vectors/generators/cross_correlation.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def direct(x, y):
    n_, m = len(x), len(y)
    out = []
    for k in range(-(m - 1), n_):
        out.append(sum(x[n + k] * y[n].conjugate() for n in range(m) if 0 <= n + k < n_))
    return out


def enc(v):
    if all(isinstance(c, (int, float)) for c in v):
        return v
    v = [complex(c) for c in v]
    return {"re": [c.real for c in v], "im": [c.imag for c in v]}


def add(cid, x, y, hand, why):
    got = direct([complex(c) for c in x], [complex(c) for c in y])
    assert len(got) == len(hand) and all(abs(g - h) < 1e-12 for g, h in zip(got, hand)), (cid, got)
    real = all(isinstance(c, (int, float)) for c in list(x) + list(y))
    cases.append({"id": f"cross_correlation.{cid}", "op": "cross_correlation",
                  "args": {"x": enc(x), "y": enc(y)},
                  "expected": [float(h) for h in hand] if real else enc(hand),
                  "tol": TOL, "source": why})


add("longer_x", [1.0, 2.0, 3.0], [1.0, 0.5], [0.5, 2.0, 3.5, 3.0],
    "lags -1..2: k=-1: x0 y1 = 0.5; k=0: x0 y0 + x1 y1 = 1 + 1 = 2; k=1: x1 y0 + x2 y1 = 2 + 1.5 "
    "= 3.5; k=2: x2 y0 = 3")
add("longer_y", [2.0, -1.0], [1.0, 3.0, 4.0], [8.0, 2.0, -1.0, -1.0],
    "lags -2..1: k=-2: x0 y2 = 8; k=-1: x0 y1 + x1 y2 = 6 - 4 = 2; k=0: x0 y0 + x1 y1 = 2 - 3 = "
    "-1; k=1: x1 y0 = -1")
add("single", [3.0], [-2.0], [-6.0], "1 x 1: lag 0 only, 3 * -2")
add("delayed", [0.0, 0.0, 1.0, 0.5, 0.0], [1.0, 0.5, 0.0],
    [0.0, 0.0, 0.0, 0.5, 1.25, 0.5, 0.0],
    "x[n] = y[n - 2], lags -2..4: k = 1: x1 y0 + x2 y1 = 0.5; k = 2: x2 y0 + x3 y1 = 1.25; "
    "k = 3: x3 y0 + x4 y1 = 0.5; every other lag 0. The peak is at lag 2, index 4")
add("complex", [1j, 2.0], [1.0, 1j], [1.0, -1j, 2.0],
    "lags -1..1: k=-1: x0 conj y1 = j(-j) = 1; k=0: x0 conj y0 + x1 conj y1 = j + 2(-j) = -j; "
    "k=1: x1 conj y0 = 2")
add("mixed", [1.0, 2.0], [1j, 1.0], [1.0, 2 - 1j, -2j],
    "real x, complex y: k=-1: x0 conj y1 = 1; k=0: x0 conj y0 + x1 conj y1 = -j + 2; k=1: x1 conj "
    "y0 = 2(-j) = -2j")


def err(cid, x, y, why):
    cases.append({"id": f"cross_correlation.{cid}", "op": "cross_correlation",
                  "args": {"x": x, "y": y}, "error": "invalid_argument", "source": why})


err("empty_x", [], [1.0], "x empty")
err("empty_y", [1.0], [], "y empty")
err("nan", [1.0, "nan"], [1.0], "not finite")

doc = {
    "schema": 1,
    "suite": "cross_correlation",
    "description": "Cross-correlation (conventions: Cross-correlation; ADR 0190).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "cross_correlation.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/cross_correlation.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
