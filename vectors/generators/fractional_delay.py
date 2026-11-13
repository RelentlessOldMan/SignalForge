"""Writes vectors/cases/fractional_delay.json from the definition, using only the Python standard
library.

It does not import NumPy or SignalForge. Each output sample is the conventions sum
y[n] = sum_m x[m] h(n - delay - m), evaluated term by term over every m in the input (not just the
2*half_width the libraries visit), with h the Kaiser-windowed sinc and I0 from its power series
summed here.

Run from the repo root: python vectors/generators/fractional_delay.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write (numbers
within 1e-14, since C math libraries can differ in the last bit).
"""

import json
import math
import pathlib
import sys

BETA = 8.0
TOL = {"abs": 1e-13, "rel": 0}


def i0(x):
    q, term, total, k = x * x / 4, 1.0, 1.0, 1
    while term > total * 1e-18:
        term *= q / (k * k)
        total += term
        k += 1
    return total


def h(t, half_width, on_grid):
    if abs(t) >= half_width:
        return 0.0
    if t == 0:
        s = 1.0
    elif on_grid:
        s = 0.0
    else:
        s = math.sin(math.pi * t) / (math.pi * t)
    return s * i0(BETA * math.sqrt(max(1 - (t / half_width) ** 2, 0.0))) / i0(BETA)


def delay(x, d, half_width):
    out = []
    for n in range(len(x)):
        pos = n - d
        frac = pos - math.floor(pos)
        out.append(sum(complex(x[m]) * h(pos - m, half_width, frac == 0) for m in range(len(x))))
    return out


def C(xs):
    return {"re": [complex(z).real for z in xs], "im": [complex(z).imag for z in xs]}


cases = []


def add(name, x, d, half_width, source, tol=TOL):
    args = {"samples": C(x), "delay": d}
    if half_width is not None:
        args["half_width"] = half_width
    cases.append({"id": f"fractional_delay.{name}", "op": "fractional_delay", "args": args,
                  "expected": C(delay(x, d, half_width or 16)), "tol": tol,
                  "source": source})


SUM = "the conventions sum over every input sample, I0 by its power series (this generator)"
REAL = [1, -2, 3, 0.5, -1, 2, 4, -3, 0, 1]
add("impulse_half", [0, 0, 0, 1, 0, 0, 0, 0], 0.5, 3, SUM + ": an impulse gives the taps")
add("quarter_h4", REAL, 0.25, 4, SUM)
add("late_h4", REAL, 2.75, 4, SUM)
add("advance_h4", REAL, -1.5, 4, SUM)
add("default_half_width", REAL, 0.6, None, SUM + ", half_width 16 by default")
add("complex_h2", [1 + 1j, -0.5j, 2, -1 - 2j, 0.25, 3j], 1.3, 2, SUM)
add("h1", REAL, 0.5, 1, SUM + ": half_width 1 uses the two nearest samples")
cases += [
    {"id": "fractional_delay.integer_by_hand", "op": "fractional_delay",
     "args": {"samples": C([1, 2, 3, 4, 5]), "delay": 2},
     "expected": C([0, 0, 1, 2, 3]), "tol": {"abs": 0, "rel": 0},
     "source": "by hand: a whole-sample delay is an exact shift"},
    {"id": "fractional_delay.integer_advance_by_hand", "op": "fractional_delay",
     "args": {"samples": C([1, 2, 3, 4, 5]), "delay": -1, "half_width": 3},
     "expected": C([2, 3, 4, 5, 0]), "tol": {"abs": 0, "rel": 0},
     "source": "by hand: a whole-sample advance is an exact shift"},
    {"id": "fractional_delay.past_end_by_hand", "op": "fractional_delay",
     "args": {"samples": C([1, 2, 3]), "delay": 100.5},
     "expected": C([0, 0, 0]), "tol": {"abs": 0, "rel": 0},
     "source": "by hand: every tap reads before the first sample"},
    {"id": "fractional_delay.empty_by_hand", "op": "fractional_delay",
     "args": {"samples": C([]), "delay": 0.5}, "expected": C([]), "tol": {"abs": 0, "rel": 0},
     "source": "by hand: no samples in, none out"},
]
for name, d, hw, why in (("nan_delay", "nan", 4, "delay must not be NaN"),
                         ("inf_delay", "inf", 4, "delay must be finite"),
                         ("zero_half_width", 0.5, 0, "half_width must be at least 1"),
                         ("negative_half_width", 0.5, -2, "half_width must be at least 1")):
    cases.append({"id": f"fractional_delay.{name}", "op": "fractional_delay",
                  "args": {"samples": C([1, 2]), "delay": d, "half_width": hw},
                  "error": "invalid_argument", "source": why})

doc = {
    "schema": 1,
    "suite": "fractional_delay",
    "description": "Fractional delay through a Kaiser-windowed sinc (conventions: Channel, "
    "Fractional delay).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "fractional_delay.json"


def same(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, int | float) and isinstance(b, int | float) and not isinstance(a, bool):
        return abs(a - b) <= 1e-14 * max(1.0, abs(b))
    return a == b


if "--check" in sys.argv[1:]:
    if not same(json.loads(out.read_text(encoding="utf-8")), json.loads(json.dumps(doc))):
        sys.exit(f"{out} is out of date: run python vectors/generators/fractional_delay.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
