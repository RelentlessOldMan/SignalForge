"""Writes vectors/cases/timing_loop.json from the definition, using only the Python standard library.

It does not import NumPy or SignalForge. It runs the Gardner recurrence in the conventions
(Synchronization, Tracking loops) step by step, reading between samples with the Kaiser-windowed
sinc and an I0 power series of its own, and computes pi_loop_gains from its formulas. The
signals are short closed-form sequences, so every case is small enough to follow by hand.

Run from the repo root: python vectors/generators/timing_loop.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write (numbers
within 1e-13, since C math libraries can differ in the last bit and the loop carries that).
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


def gardner(y, sps, kp, ki, start, half_width):
    symbols, positions, errors = [], [], []
    tau, v = start, 0.0
    while tau <= len(y) - 1:
        z = interpolate(y, tau, half_width)
        e = 0.0
        if symbols:
            mid = interpolate(y, (positions[-1] + tau) / 2, half_width)
            d = z - symbols[-1]
            e = mid.real * d.real + mid.imag * d.imag
        symbols.append(z)
        positions.append(tau)
        errors.append(e)
        v += ki * e
        tau += min(max(sps - kp * e - v, sps / 2), 3 * sps / 2)
    return symbols, positions, errors


def C(xs):
    return {"re": [complex(z).real for z in xs], "im": [complex(z).imag for z in xs]}


def qpsk_like(n, sps, offset):
    """A band-limited stand-in for a shaped QPSK burst: symbols (+-1 +-j)/sqrt2 from a fixed
    pattern, each a sinc^2 pulse centred at offset + k*sps."""
    pattern = [(1, 1), (-1, 1), (-1, -1), (1, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    out = []
    for i in range(n):
        acc = 0j
        for k in range(n // sps + 2):
            a, b = pattern[(3 * k + k // 3) % 8]
            x = (i - offset - k * sps) / sps
            p = 1.0 if x == 0 else (math.sin(math.pi * x) / (math.pi * x)) ** 2
            acc += complex(a, b) / math.sqrt(2) * p
        out.append(acc)
    return out


cases = []
SRC = ("the conventions recurrence run step by step, the kernel and I0 by its power series "
       "(this generator)")


def add(name, y, sps, kp, ki, start=None, half_width=None, source=SRC, tol=None):
    args = {"samples": C(y), "samples_per_symbol": sps, "kp": kp, "ki": ki}
    if start is not None:
        args["start"] = start
    if half_width is not None:
        args["half_width"] = half_width
    s, p, e = gardner(y, sps, kp, ki, 0.0 if start is None else start,
                      8 if half_width is None else half_width)
    cases.append({"id": f"gardner_timing.{name}", "op": "gardner_timing", "args": args,
                  "expected": {"symbols": C(s), "positions": p, "errors": e},
                  "tol": tol or {"abs": 1e-12, "rel": 0}, "source": source})


ramp = [complex(n, -n / 2) for n in range(14)]
add("open_loop_on_grid_by_hand", ramp, 4, 0.0, 0.0, start=1.0,
    source="by hand: on the grid the kernel is exact, so the symbols are y[1], y[5], y[9], "
    "y[13], the midpoints y[3], y[7], y[11], and e = Re(conj(mid)*(z_k - z_k-1)) = 4*(n + n/4) "
    "at the midpoint n", tol={"abs": 1e-13, "rel": 0})
assert [round(z.real) for z in gardner(ramp, 4, 0, 0, 1.0, 8)[0]] == [1, 5, 9, 13]
assert gardner(ramp, 4, 0, 0, 1.0, 8)[2] == [0.0, 15.0, 35.0, 55.0]
burst = qpsk_like(96, 4, 2.6)
add("open_loop_fractional", burst, 4, 0.0, 0.0, start=2.0, half_width=4)
add("closed_loop", burst, 4, 0.2, 0.01, start=1.0)
add("closed_loop_sps2", qpsk_like(60, 2, 0.4), 2, 0.3, 0.02, start=0.0, half_width=3)
add("default_start_and_width", burst, 4, 0.1, 0.0)
add("step_held_both_ways", burst, 4, 40.0, 0.0, start=1.0,
    source=SRC + "; the gain is large enough that the step is held at both limits")
held = gardner(burst, 4, 40.0, 0.0, 1.0, 8)[1]
steps = [b - a for a, b in zip(held, held[1:])]
assert 2.0 in steps and 6.0 in steps, steps
add("start_past_end_by_hand", [1, 2, 3], 2, 0.1, 0.0, start=2.5,
    source="by hand: the first position is past the last sample, so nothing is taken")
add("empty_by_hand", [], 4, 0.1, 0.01, source="by hand: no samples in, none out")
for name, args, why in (
        ("sps_one", {"samples_per_symbol": 1}, "samples_per_symbol must be at least 2"),
        ("negative_kp", {"kp": -0.1}, "kp must not be negative"),
        ("nan_ki", {"ki": "nan"}, "ki must be finite"),
        ("negative_start", {"start": -1.0}, "start must not be negative"),
        ("zero_half_width", {"half_width": 0}, "half_width must be at least 1"),
        ("infinite_sample", {"samples": {"re": [1.0, "inf"], "im": [0.0, 0.0]}},
         "samples must be finite")):
    base = {"samples": C([1, 2, 3, 4]), "samples_per_symbol": 2, "kp": 0.1, "ki": 0.01}
    cases.append({"id": f"gardner_timing.{name}", "op": "gardner_timing", "args": base | args,
                  "error": "invalid_argument", "source": why})


def gains(bn, z, kd):
    theta = bn / (z + 1 / (4 * z))
    d = 1 + 2 * z * theta + theta * theta
    return [4 * z * theta / d / kd, 4 * theta * theta / d / kd]


GSRC = ("the standard second-order loop formulas (conventions: Synchronization, Tracking loops) "
        "evaluated by hand")
for name, bn, z, kd in (("critically_damped", 0.01, 1 / math.sqrt(2), 1.0),
                        ("unit_damping", 0.05, 1.0, 0.26), ("wide", 0.2, 0.5, 2.0)):
    cases.append({"id": f"pi_loop_gains.{name}", "op": "pi_loop_gains",
                  "args": {"loop_bandwidth": bn, "damping": z, "detector_gain": kd},
                  "expected": gains(bn, z, kd), "tol": {"abs": 0, "rel": 1e-15}, "source": GSRC})
for name, bn, z, kd, why in (("zero_bandwidth", 0.0, 1.0, 1.0, "loop_bandwidth must be positive"),
                             ("half_bandwidth", 0.5, 1.0, 1.0, "loop_bandwidth must be below 0.5"),
                             ("zero_damping", 0.01, 0.0, 1.0, "damping must be positive"),
                             ("negative_gain", 0.01, 1.0, -1.0, "detector_gain must be positive"),
                             ("nan_bandwidth", "nan", 1.0, 1.0, "loop_bandwidth must not be NaN")):
    cases.append({"id": f"pi_loop_gains.{name}", "op": "pi_loop_gains",
                  "args": {"loop_bandwidth": bn, "damping": z, "detector_gain": kd},
                  "error": "invalid_argument", "source": why})
assert cmath.isclose(gains(0.01, 1 / math.sqrt(2), 1.0)[0], 0.02631, rel_tol=1e-3)

doc = {
    "schema": 1,
    "suite": "timing_loop",
    "description": "Gardner timing recovery and PI loop gains (conventions: Synchronization, "
    "Tracking loops).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "timing_loop.json"


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
        sys.exit(f"{out} is out of date: run python vectors/generators/timing_loop.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
