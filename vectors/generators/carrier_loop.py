"""Writes vectors/cases/carrier_loop.json from the definition, using only the Python standard library.

It does not import NumPy or SignalForge. It runs the decision-directed QPSK carrier loop in the
conventions (Synchronization, Tracking loops) step by step. The by-hand cases are checked here
against the closed forms they rely on.

Run from the repo root: python vectors/generators/carrier_loop.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write (numbers
within 1e-13, since C math libraries can differ in the last bit and the loop carries that).
"""

import cmath
import json
import math
import pathlib
import sys


def loop(z, kp, ki, phase):
    out, phases, errors = [], [], []
    phi, v = phase, 0.0
    for x in z:
        x = complex(x)
        c, s = math.cos(phi), math.sin(phi)
        re = x.real * c + x.imag * s
        im = x.imag * c - x.real * s
        dre = 1.0 if re >= 0 else -1.0
        dim = 1.0 if im >= 0 else -1.0
        e = dre * im - dim * re
        out.append(complex(re, im))
        phases.append(phi)
        errors.append(e)
        v += ki * e
        phi = phi + kp * e + v
    return out, phases, errors


def C(xs):
    return {"re": [complex(z).real for z in xs], "im": [complex(z).imag for z in xs]}


R = 1 / math.sqrt(2)
POINTS = [complex(R, R), complex(-R, R), complex(-R, -R), complex(R, -R)]
SYMS = [POINTS[(5 * k + k // 2) % 4] for k in range(40)]

cases = []
SRC = "the conventions recurrence run step by step (this generator)"


def add(name, z, kp, ki, phase=None, source=SRC, tol=None):
    args = {"symbols": C(z), "kp": kp, "ki": ki}
    if phase is not None:
        args["phase"] = phase
    s, p, e = loop(z, kp, ki, 0.0 if phase is None else phase)
    cases.append({"id": f"qpsk_carrier_tracking.{name}", "op": "qpsk_carrier_tracking",
                  "args": args, "expected": {"symbols": C(s), "phases": p, "errors": e},
                  "tol": tol or {"abs": 1e-12, "rel": 0}, "source": source})
    return s, p, e


# On the constellation with phase 0 the detector is 0 every time (d.re*im = d.im*re = 1/sqrt2).
s, p, e = add("locked_by_hand", SYMS[:8], 0.1, 0.01,
              source="by hand: points (+-1 +-j)/sqrt2 at phase 0 give e = 0, so nothing moves",
              tol={"abs": 0, "rel": 0})
assert e == [0.0] * 8 and p == [0.0] * 8 and s == SYMS[:8]
# One symbol at angle pi/4 + 0.3 with the loop at 0: e = sqrt2*sin(0.3), and kp only acts after it.
one = cmath.rect(1, math.pi / 4 + 0.3)
s, p, e = add("one_symbol_by_hand", [one], 0.5, 0.1,
              source="by hand: a unit symbol at pi/4 + 0.3 gives e = sqrt2*sin(0.3); the phase "
              "used is the start", tol={"abs": 1e-15, "rel": 0})
assert abs(e[0] - math.sqrt(2) * math.sin(0.3)) < 1e-15 and p == [0.0]
# A start phase undoes a static rotation exactly when it equals it.
rot = [z * cmath.rect(1, 0.2) for z in SYMS[:6]]
add("start_phase_matches_rotation", rot, 0.0, 0.0, phase=0.2,
    source="by hand: removing the same 0.2 rad gives the points back and e = 0 up to rounding",
    tol={"abs": 1e-15, "rel": 0})
add("static_rotation", [z * cmath.rect(1, 0.5) for z in SYMS], 0.2, 0.01)
add("frequency_offset", [z * cmath.rect(1.3, 0.1 + 0.02 * k) for k, z in enumerate(SYMS)], 0.15,
    0.005, phase=0.05)
add("noisy_scale", [z * cmath.rect(0.8 + 0.05 * math.sin(k), -0.3 + 0.01 * math.cos(3 * k))
                    for k, z in enumerate(SYMS)], 0.1, 0.002, phase=-0.25)
add("ties_on_axes", [1, 1j, -1, -1j, 0, 0.5], 0.1, 0.0,
    source=SRC + "; points on the axes and at 0 test sgn(0) = +1")
add("empty_by_hand", [], 0.1, 0.01, source="by hand: no symbols in, none out")
for name, args, why in (("negative_kp", {"kp": -0.1}, "kp must not be negative"),
                        ("nan_ki", {"ki": "nan"}, "ki must be finite"),
                        ("infinite_phase", {"phase": "inf"}, "phase must be finite"),
                        ("nan_symbol", {"symbols": {"re": [1.0, "nan"], "im": [0.0, 0.0]}},
                         "symbols must be finite")):
    base = {"symbols": C(SYMS[:2]), "kp": 0.1, "ki": 0.01}
    cases.append({"id": f"qpsk_carrier_tracking.{name}", "op": "qpsk_carrier_tracking",
                  "args": base | args, "error": "invalid_argument", "source": why})

doc = {
    "schema": 1,
    "suite": "carrier_loop",
    "description": "Decision-directed QPSK carrier tracking (conventions: Synchronization, "
    "Tracking loops).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "carrier_loop.json"


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
        sys.exit(f"{out} is out of date: run python vectors/generators/carrier_loop.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
