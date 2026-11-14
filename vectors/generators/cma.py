"""Writes vectors/cases/cma.json from the definition, using only the Python standard library.

It does not import NumPy or SignalForge. It runs the normalized constant-modulus equalizer in the
conventions (Synchronization, Constant-modulus equalizer) step by step. The by-hand cases are
checked here against the closed forms they rely on.

Run from the repo root: python vectors/generators/cma.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write (numbers
within 1e-13, since C math libraries can differ in the last bit and the recursion carries that).
"""

import cmath
import json
import math
import pathlib
import sys

R2 = 1 / math.sqrt(2)
R10 = 1 / math.sqrt(10)


def cma(x, taps, mu, sps=1, center=None, modulus=1.0, initial_taps=None):
    c = (taps - 1) // 2 if center is None else center
    w = [0j] * taps
    w[c] = 1 + 0j
    if initial_taps is not None:
        w = [complex(z) for z in initial_taps]
    ys, es = [], []
    for n in range(-(-len(x) // sps)):
        base = n * sps + c
        u = [x[base - i] if 0 <= base - i < len(x) else 0j for i in range(taps)]
        y = 0j
        for wi, ui in zip(w, u):
            y += wi * ui
        ys.append(y)
        e = y * (modulus - (y.real * y.real + y.imag * y.imag))
        es.append(e)
        p = 0.0
        for ui in u:
            p += ui.real * ui.real + ui.imag * ui.imag
        if p > 0:
            g = mu / p
            w = [wi + g * e * ui.conjugate() for wi, ui in zip(w, u)]
    return ys, es, w


def C(xs):
    return {"re": [complex(z).real for z in xs], "im": [complex(z).imag for z in xs]}


def channel(a, h, sps=1):
    """The symbols at sps samples each (zeros between), through the taps h."""
    up = []
    for s in a:
        up += [s] + [0j] * (sps - 1)
    return [sum(h[j] * up[n - j] for j in range(len(h)) if 0 <= n - j < len(up))
            for n in range(len(up))]


def points(order, n, seed):
    """A fixed pseudo-random sequence of the modulation's points, from a linear congruence."""
    pts = {"qpsk": [complex(re * R2, im * R2) for re in (1, -1) for im in (1, -1)],
           "psk8": [cmath.exp(1j * math.pi / 4 * p) for p in range(8)],
           "qam16": [complex(i * R10, q * R10) for i in (-3, -1, 1, 3) for q in (-3, -1, 1, 3)]}
    out, s = [], seed
    for _ in range(n):
        s = (1103515245 * s + 12345) % 2**31
        out.append(pts[order][(s >> 16) % len(pts[order])])
    return out


cases = []
SRC = "the conventions recurrence run step by step (this generator)"
OP = "cma_equalizer"


def add(name, x, taps, mu, source=SRC, tol=None, **kw):
    args = {"samples": C(x), "num_taps": taps, "step": mu}
    args |= {("samples_per_symbol" if k == "sps" else k): C(v) if k == "initial_taps" else v
             for k, v in kw.items()}
    ys, es, w = cma(x, taps, mu, **kw)
    cases.append({"id": f"{OP}.{name}", "op": OP, "args": args,
                  "expected": {"symbols": C(ys), "errors": C(es), "taps": C(w)},
                  "tol": tol or {"abs": 1e-12, "rel": 0}, "source": source})
    return ys, es, w


X = [complex(0.3 * k - 1, 0.7 - 0.2 * k * k % 1.3) for k in range(9)]
ys, es, w = add("step_zero_passes_through_by_hand", X, 5, 0.0, sps=2,
                source="by hand: with step 0 the taps stay a unit impulse at the center, so "
                "output n is x[2n] and the error is x[2n] (1 - |x[2n]|^2)",
                tol={"abs": 1e-15, "rel": 0})
assert ys == X[::2] and w == [0j, 0j, 1 + 0j, 0j, 0j]
assert all(abs(e - y * (1 - abs(y) ** 2)) < 1e-15 for e, y in zip(es, ys))

G = complex(0.6, -0.8) * 1.7
A = points("qpsk", 5, 3)
ys, es, w = add("one_tap_scalar_gain_by_hand", [G * a for a in A], 1, 0.5,
                source="by hand: one tap on x = g a with |a| = 1 goes w -> w (1 + mu (1 - |w g|^2)) "
                "each symbol, from w = 1", tol={"abs": 1e-14, "rel": 0})
wh = 1 + 0j
for _ in A:
    wh = wh * (1 + 0.5 * (1 - abs(wh * G) ** 2))
assert abs(w[0] - wh) < 1e-14

ys, es, w = add("one_tap_on_the_modulus_holds_by_hand", [cmath.exp(0.3j * k) for k in range(6)],
                1, 1.0, source="by hand: unit-magnitude input at R = 1 gives error 0, so the tap "
                "stays 1 and the output is the input", tol={"abs": 1e-15, "rel": 0})
assert all(abs(e) < 1e-15 for e in es) and abs(w[0] - 1) < 1e-15

ys, es, w = add("zero_input_by_hand", [0j] * 4, 3, 1.0,
                source="by hand: zero samples give output 0 and error 0; the regressor power is "
                "0, so the taps never move", tol={"abs": 0, "rel": 0})
assert ys == [0j] * 4 and es == [0j] * 4 and w == [0j, 1 + 0j, 0j]

H2 = [1 + 0j, complex(0.35, -0.2), complex(-0.1, 0.05)]
TURN = cmath.exp(0.7j)
A = points("qpsk", 120, 7)
add("qpsk_symbol_spaced", [TURN * z for z in channel(A, H2)], 7, 0.03, center=3)
HF = [0.1 + 0j, 0.9 + 0j, complex(0.3, 0.2), complex(-0.1, 0.15), complex(0.05, 0)]
A = points("qam16", 80, 11)
add("qam16_fractional_modulus", channel(A, HF, 2), 9, 0.03, sps=2, modulus=1.32)
A = points("psk8", 60, 13)
add("psk8_center_given", channel(A, H2), 6, 0.05, center=1)
add("sps_not_dividing", channel(points("qpsk", 7, 19), H2, 3)[:-1], 4, 0.1, sps=3)
W0 = [complex(0.2, -0.1), complex(0.9, 0.3), complex(-0.15, 0.05)]
A = points("qpsk", 60, 29)
add("initial_taps_adapts", channel(A, H2), 3, 0.05, initial_taps=W0)
add("large_modulus", channel(points("qpsk", 30, 31), H2), 3, 0.2, modulus=4.0)

for name, args, why in (
    ("initial_taps_wrong_length", {"initial_taps": C([1, 0])}, "initial_taps must hold num_taps"),
    ("step_above_two", {"step": 2.5}, "step must be between 0 and 2"),
    ("negative_step", {"step": -0.1}, "step must be between 0 and 2"),
    ("zero_modulus", {"modulus": 0.0}, "modulus must be above 0"),
    ("modulus_not_finite", {"modulus": "inf"}, "modulus must be finite"),
    ("center_past_the_taps", {"center": 3}, "center must be below num_taps"),
    ("no_taps", {"num_taps": 0}, "num_taps must be at least 1"),
    ("no_samples", {"samples": C([])}, "samples needs at least 1"),
    ("zero_sps", {"samples_per_symbol": 0}, "samples_per_symbol must be at least 1"),
    ("nan_sample", {"samples": {"re": [1.0, "nan", 0, 0], "im": [0, 0, 0, 0]}},
     "samples must be finite"),
):
    base = {"samples": C([1, 1j, -1, -1j]), "num_taps": 3, "step": 0.5}
    cases.append({"id": f"{OP}.{name}", "op": OP, "args": base | args,
                  "error": "invalid_argument", "source": why})

doc = {
    "schema": 1,
    "suite": "cma",
    "description": "Blind constant-modulus equalizer, normalized, fractionally spaced "
    "(conventions: Synchronization, Constant-modulus equalizer).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "cma.json"


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
        sys.exit(f"{out} is out of date: run python vectors/generators/cma.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
