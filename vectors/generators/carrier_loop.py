"""Writes vectors/cases/carrier_loop.json from the definition, using only the Python standard library.

It does not import NumPy or SignalForge. It runs the decision-directed QPSK, 8-PSK, 16-QAM and 64-QAM
carrier loops in the conventions (Synchronization, Tracking loops) step by step. The by-hand cases are checked here
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


def qpsk(re, im):
    return (1.0 if re >= 0 else -1.0, 1.0 if im >= 0 else -1.0)


C8 = 1 / math.sqrt(2)
PSK8 = [(1.0, 0.0), (C8, C8), (0.0, 1.0), (-C8, C8), (-1.0, 0.0), (-C8, -C8), (0.0, -1.0), (C8, -C8)]


def psk8(re, im):
    return PSK8[int(math.floor(math.atan2(im, re) / (math.pi / 4) + 0.5)) % 8]


INV10 = 1.0 / math.sqrt(10.0)
THR = 2.0 / math.sqrt(10.0)


def qam16(re, im):
    def level(v):
        m = 1.0 if abs(v) < THR else 3.0
        return (m if v >= 0 else -m) * INV10
    return (level(re), level(im))


INV42 = 1.0 / math.sqrt(42.0)
T2, T4, T6 = 2.0 / math.sqrt(42.0), 4.0 / math.sqrt(42.0), 6.0 / math.sqrt(42.0)


def qam64(re, im):
    """The point qam64_demap_hard decides, from its bit rules (bit 1 strictly inside)."""
    def level(v):
        a = abs(v)
        b1, b2 = a < T4, T2 < a < T6
        m = {(False, False): 7.0, (False, True): 5.0, (True, True): 3.0, (True, False): 1.0}[(b1, b2)]
        return (-m if v < 0 else m) * INV42
    return (level(re), level(im))


def loop(z, kp, ki, phase, decide=qpsk):
    out, phases, errors = [], [], []
    phi, v = phase, 0.0
    for x in z:
        x = complex(x)
        c, s = math.cos(phi), math.sin(phi)
        re = x.real * c + x.imag * s
        im = x.imag * c - x.real * s
        dre, dim = decide(re, im)
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



def add_m(op, decide, name, z, kp, ki, phase=None, source=SRC, tol=None):
    args = {"symbols": C(z), "kp": kp, "ki": ki}
    if phase is not None:
        args["phase"] = phase
    s, p, e = loop(z, kp, ki, 0.0 if phase is None else phase, decide)
    cases.append({"id": f"{op}.{name}", "op": op, "args": args,
                  "expected": {"symbols": C(s), "phases": p, "errors": e},
                  "tol": tol or {"abs": 1e-12, "rel": 0}, "source": source})
    return s, p, e


P8 = [cmath.rect(1, math.pi / 4 * ((3 * k + k // 2) % 8)) for k in range(40)]
op = "psk8_carrier_tracking"
s, p, e = add_m(op, psk8, "one_symbol_by_hand", [cmath.rect(1, 0.1)], 0.5, 0.1,
                source="by hand: a unit symbol at 0.1 rad decides 1, so e = sin(0.1)",
                tol={"abs": 1e-15, "rel": 0})
assert abs(e[0] - math.sin(0.1)) < 1e-15
s, p, e = add_m(op, psk8, "diagonal_by_hand", [cmath.rect(2, math.pi / 4 - 0.2)], 0.0, 0.0,
                source="by hand: 2 at pi/4 - 0.2 decides (1+j)/sqrt2, so e = 2*sin(-0.2)",
                tol={"abs": 1e-15, "rel": 0})
assert abs(e[0] - 2 * math.sin(-0.2)) < 1e-15
add_m(op, psk8, "static_rotation", [z * cmath.rect(1, 0.25) for z in P8], 0.2, 0.01)
add_m(op, psk8, "frequency_offset", [z * cmath.rect(0.9, -0.1 + 0.01 * k) for k, z in enumerate(P8)],
      0.15, 0.005, phase=-0.05)
add_m(op, psk8, "empty_by_hand", [], 0.1, 0.01, source="by hand: no symbols in, none out")
Q16 = [complex(a, b) * INV10 for a, b in
       [((3 * k) % 4 * 2 - 3, (5 * k + k // 4) % 4 * 2 - 3) for k in range(40)]]
op = "qam16_carrier_tracking"
s, p, e = add_m(op, qam16, "one_symbol_by_hand", [complex(3, 3) * INV10 * cmath.rect(1, 0.1)],
                0.5, 0.1, source="by hand: (3+3j)/sqrt10 turned 0.1 decides itself, so "
                "e = |s|^2*sin(0.1) = 1.8*sin(0.1)", tol={"abs": 1e-15, "rel": 0})
assert abs(e[0] - 1.8 * math.sin(0.1)) < 1e-15
add_m(op, qam16, "static_rotation", [z * cmath.rect(1, 0.15) for z in Q16], 0.2, 0.01)
add_m(op, qam16, "frequency_offset", [z * cmath.rect(1.1, 0.05 + 0.004 * k) for k, z in
                                      enumerate(Q16)], 0.1, 0.003, phase=0.02)
add_m(op, qam16, "ties_by_hand", [0, 2 * INV10 * 1, 1j * 2 * INV10], 0.0, 0.0,
      source="by hand: 0 decides (1+j)/sqrt10, so e = 0; 2/sqrt10 decides (3+j)/sqrt10, so "
      "e = -(1/sqrt10)*(2/sqrt10) = -0.2, and 2j/sqrt10 decides (1+3j)/sqrt10, so e = 0.2",
      tol={"abs": 1e-15, "rel": 0})
_, _, e = loop([0, 2 * INV10, 2j * INV10], 0, 0, 0.0, qam16)
assert e[0] == 0 and abs(e[1] + 0.2) < 1e-15 and abs(e[2] - 0.2) < 1e-15, e
Q64 = [complex(a, b) * INV42 for a, b in
       [((3 * k) % 8 * 2 - 7, (5 * k + k // 8) % 8 * 2 - 7) for k in range(64)]]
op = "qam64_carrier_tracking"
s, p, e = add_m(op, qam64, "one_symbol_by_hand", [complex(7, 7) * INV42 * cmath.rect(1, 0.1)],
                0.5, 0.1, source="by hand: (7+7j)/sqrt42 turned 0.1 decides itself, so "
                "e = |s|^2*sin(0.1) = (98/42)*sin(0.1)", tol={"abs": 1e-15, "rel": 0})
assert abs(e[0] - 98 / 42 * math.sin(0.1)) < 1e-15
add_m(op, qam64, "static_rotation", [z * cmath.rect(1, 0.12) for z in Q64], 0.2, 0.01)
add_m(op, qam64, "frequency_offset", [z * cmath.rect(0.95, -0.03 + 0.002 * k) for k, z in
                                      enumerate(Q64)], 0.1, 0.003, phase=-0.01)
add_m(op, qam64, "ties_by_hand", [0, T4, 1j * T6], 0.0, 0.0,
      source="by hand: 0 decides (1+j)/sqrt42, so e = 0; 4/sqrt42 decides (5+j)/sqrt42, so "
      "e = -(1/sqrt42)*(4/sqrt42) = -4/42, and 6j/sqrt42 decides (1+7j)/sqrt42, so e = 6/42",
      tol={"abs": 1e-15, "rel": 0})
_, _, e = loop([0, T4, 1j * T6], 0, 0, 0.0, qam64)
assert e[0] == 0 and abs(e[1] + 4 / 42) < 1e-15 and abs(e[2] - 6 / 42) < 1e-15, e
for op in ("psk8_carrier_tracking", "qam16_carrier_tracking", "qam64_carrier_tracking"):
    for name, args, why in (("negative_ki", {"ki": -0.1}, "ki must not be negative"),
                            ("nan_symbol", {"symbols": {"re": [1.0, "nan"], "im": [0.0, 0.0]}},
                             "symbols must be finite")):
        base = {"symbols": C(P8[:2]), "kp": 0.1, "ki": 0.01}
        cases.append({"id": f"{op}.{name}", "op": op, "args": base | args,
                      "error": "invalid_argument", "source": why})

doc = {
    "schema": 1,
    "suite": "carrier_loop",
    "description": "Decision-directed QPSK, 8-PSK, 16-QAM and 64-QAM carrier tracking (conventions: "
    "Synchronization, Tracking loops).",
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
