"""Writes vectors/cases/clock_offset.json from the definition, using only the Python standard library.

It does not import NumPy or SignalForge. It reads the input at n*r, r = 1 + ppm/1e6, with the
Kaiser-windowed sinc and an I0 power series of its own (conventions: Channel, Sample clock
offset). The by-hand cases are checked here against what they claim.

Run from the repo root: python vectors/generators/clock_offset.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write (numbers
within 1e-13, since C math libraries can differ in the last bit).
"""

import cmath
import json
import math
import pathlib
import sys

BETA = 8.0


def i0(x):
    q, term, total, k = x * x / 4, 1.0, 1.0, 1
    while term > total * 1e-18:
        term *= q / (k * k)
        total += term
        k += 1
    return total


def interpolate(y, t, half_width):
    b = math.floor(t)
    f = t - b
    acc = 0j
    for j in range(-half_width + 1, half_width + 1):
        m = b + j
        tt = f - j
        if not 0 <= m < len(y) or abs(tt) >= half_width:
            continue
        if tt == 0:
            s = 1.0
        elif f == 0:
            s = 0.0
        else:
            s = math.sin(math.pi * tt) / (math.pi * tt)
        w = i0(BETA * math.sqrt(max(1 - (tt / half_width) ** 2, 0.0))) / i0(BETA)
        acc += s * w * y[m]
    return acc


def clock(x, ppm, half_width):
    r = 1 + ppm / 1e6
    out, n = [], 0
    while n * r <= len(x) - 1:
        out.append(interpolate(x, n * r, half_width))
        n += 1
    return out


def C(xs):
    return {"re": [complex(z).real for z in xs], "im": [complex(z).imag for z in xs]}


cases = []
SRC = "read at n*r through the kernel, I0 by its power series (this generator)"


def add(name, x, ppm, half_width=None, source=SRC, tol=None, expected=None):
    args = {"samples": C(x), "ppm": ppm}
    if half_width is not None:
        args["half_width"] = half_width
    got = clock(x, ppm, 16 if half_width is None else half_width)
    if expected is not None:
        assert len(got) == len(expected) and all(abs(a - b) < 1e-15 for a, b in zip(got, expected))
    cases.append({"id": f"clock_offset.{name}", "op": "clock_offset", "args": args,
                  "expected": C(got), "tol": tol or {"abs": 1e-13, "rel": 0}, "source": source})


X = [complex(math.cos(0.7 * n) + 0.1 * n, math.sin(0.3 * n * n) - 0.5) for n in range(24)]
add("zero_ppm_by_hand", X, 0.0, expected=X, tol={"abs": 0, "rel": 0},
    source="by hand: r = 1 puts every read on the grid, where the kernel gives the sample itself")
add("slow_clock", X, 5e4)
add("fast_clock", X, -5e4, half_width=6)
add("limit_slow", X, 1e5, half_width=4)
add("limit_fast", X, -1e5, half_width=4)
add("ten_ppm", X, 10.0)
tone = [cmath.exp(2j * math.pi * 0.05 * n) for n in range(64)]
add("tone", tone, 3e4, half_width=8)
add("one_sample_by_hand", [2 - 1j], 7e4, expected=[2 - 1j], tol={"abs": 0, "rel": 0},
    source="by hand: only n = 0 fits, read on the grid")
add("empty_by_hand", [], 50.0, expected=[], source="by hand: no samples in, none out")
assert len(clock(X, 5e4, 16)) == 22 and len(clock(X, -5e4, 6)) == 25
for name, args, why in (("over_limit", {"ppm": 1.000001e5}, "|ppm| must be at most 1e5"),
                        ("under_limit", {"ppm": -2e5}, "|ppm| must be at most 1e5"),
                        ("nan_ppm", {"ppm": "nan"}, "ppm must be finite"),
                        ("zero_half_width", {"half_width": 0}, "half_width must be at least 1")):
    base = {"samples": C(X[:4]), "ppm": 10.0}
    cases.append({"id": f"clock_offset.{name}", "op": "clock_offset", "args": base | args,
                  "error": "invalid_argument", "source": why})

doc = {
    "schema": 1,
    "suite": "clock_offset",
    "description": "Sample clock offset through the fractional-delay kernel (conventions: "
    "Channel, Sample clock offset).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "clock_offset.json"


def same(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, int | float) and isinstance(b, int | float) and not isinstance(a, bool):
        return abs(a - b) <= 1e-13 * max(1.0, abs(b))
    return a == b


if "--check" in sys.argv[1:]:
    if not same(json.loads(out.read_text(encoding="utf-8")), json.loads(json.dumps(doc))):
        sys.exit(f"{out} is out of date: run python vectors/generators/clock_offset.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
