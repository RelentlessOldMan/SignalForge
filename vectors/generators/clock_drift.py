"""Writes vectors/cases/clock_drift.json from the definition, using only the Python standard library.

It does not import NumPy or SignalForge. The read positions come from the recurrence
t[n+1] = r + (1 + d) t[n], t[0] = 0, run in exact rational arithmetic from the floating-point r and
d (conventions: Channel, Sample clock drift; ADR 0102), so they share nothing with the expm1 and
log1p route the implementations take. Each position is read with the Kaiser-windowed sinc and an
I0 power series of this generator's own. Equal offsets are checked against the clock offset
definition, n*r.

Run from the repo root: python vectors/generators/clock_drift.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write (numbers
within 1e-13, since C math libraries can differ in the last bit).
"""

import cmath
import json
import math
import pathlib
import sys
from fractions import Fraction

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


def positions(n_in, p0, p1):
    """t[n] by the exact recurrence, rounded once, while t[n] <= N - 1."""
    r = Fraction(1 + p0 / 1e6)
    d = Fraction((p1 - p0) / 1e6 / (n_in - 1)) if n_in > 1 else Fraction(0)
    out, t = [], Fraction(0)
    while t <= n_in - 1:
        # keep away from the end, where the languages' last bits could decide the length
        assert n_in - 1 - t > Fraction(1, 10**9) or t == n_in - 1, (n_in, p0, p1)
        out.append(float(t))
        t = r + (1 + d) * t
    return out


def C(xs):
    return {"re": [complex(z).real for z in xs], "im": [complex(z).imag for z in xs]}


cases = []
SRC = ("positions by the recurrence in exact rationals, read through the kernel with I0 by its "
       "power series (this generator)")


def add(name, x, p0, p1, half_width=None, source=SRC, tol=None, length=None, expected=None):
    args = {"samples": C(x), "ppm_start": p0, "ppm_end": p1}
    if half_width is not None:
        args["half_width"] = half_width
    hw = 16 if half_width is None else half_width
    got = [interpolate(x, t, hw) for t in positions(len(x), p0, p1)] if x else []
    if length is not None:
        assert len(got) == length, (name, len(got))
    if expected is not None:
        assert len(got) == len(expected) and all(abs(a - b) < 1e-15 for a, b in zip(got, expected))
    cases.append({"id": f"clock_drift.{name}", "op": "clock_drift", "args": args,
                  "expected": C(got), "tol": tol or {"abs": 1e-12, "rel": 0}, "source": source})


def clock_offset(x, ppm, half_width):
    r = 1 + ppm / 1e6
    out, n = [], 0
    while n * r <= len(x) - 1:
        out.append(interpolate(x, n * r, half_width))
        n += 1
    return out


X = [complex(math.cos(0.7 * n) + 0.1 * n, math.sin(0.3 * n * n) - 0.5) for n in range(24)]
add("equal_offsets", X, 5e4, 5e4, expected=clock_offset(X, 5e4, 16), tol={"abs": 1e-13, "rel": 0},
    source="clock offset definition: d = 0 reads at n*r (kernel and I0 of this generator)")
add("equal_offsets_fast", X, -3e4, -3e4, half_width=6, expected=clock_offset(X, -3e4, 6),
    tol={"abs": 1e-13, "rel": 0},
    source="clock offset definition: d = 0 reads at n*r (kernel and I0 of this generator)")
add("slow_to_fast", X, 4e4, -6e4)
add("fast_to_slow", X, -7e4, 2e4, half_width=8)
add("limits", X, -1e5, 1e5, half_width=4)
add("from_zero", X, 0.0, 250.0)
tone = [cmath.exp(2j * math.pi * 0.05 * n) for n in range(64)]
add("tone", tone, 1e4, 6e4, half_width=8)
add("length_by_hand", X[:11], 0.0, 1e5, length=10,
    source="length by hand: d = 0.01, t_n <= 10 needs 1.01^n <= 1.1, n <= 9.58, so 10 outputs; "
    "values by the exact recurrence and this generator's kernel")
add("one_sample_by_hand", [2 - 1j], 7e4, -3e4, expected=[2 - 1j], tol={"abs": 0, "rel": 0},
    source="by hand: N = 1 gives d = 0 and only n = 0, read on the grid")
add("empty_by_hand", [], 50.0, -50.0, expected=[], source="by hand: no samples in, none out")
for name, args, why in (
    ("start_over_limit", {"ppm_start": 1.000001e5}, "|ppm_start| must be at most 1e5"),
    ("end_over_limit", {"ppm_end": -2e5}, "|ppm_end| must be at most 1e5"),
    ("nan_start", {"ppm_start": "nan"}, "ppm_start must be finite"),
    ("inf_end", {"ppm_end": "inf"}, "ppm_end must be finite"),
    ("zero_half_width", {"half_width": 0}, "half_width must be at least 1"),
):
    base = {"samples": C(X[:4]), "ppm_start": 10.0, "ppm_end": 20.0}
    cases.append({"id": f"clock_drift.{name}", "op": "clock_drift", "args": base | args,
                  "error": "invalid_argument", "source": why})

doc = {
    "schema": 1,
    "suite": "clock_drift",
    "description": "Sample clock drift through the fractional-delay kernel (conventions: "
    "Channel, Sample clock drift; ADR 0102).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "clock_drift.json"


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
        sys.exit(f"{out} is out of date: run python vectors/generators/clock_drift.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
