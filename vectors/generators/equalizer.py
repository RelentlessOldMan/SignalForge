"""Writes vectors/cases/equalizer.json from the definition, using only the Python standard library.

It does not import NumPy or SignalForge. It runs the normalized LMS equalizer in the conventions
(Synchronization, LMS equalizer) step by step, with the hard decisions written out from the
demapper rules (conventions: Bits and symbols). The by-hand cases are checked here against the
closed forms they rely on.

Run from the repo root: python vectors/generators/equalizer.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write (numbers
within 1e-13, since C math libraries can differ in the last bit and the recursion carries that).
"""

import cmath
import json
import math
import pathlib
import sys

R2 = 1 / math.sqrt(2)
R10, T10 = 1 / math.sqrt(10), 2 / math.sqrt(10)
R42, T2, T4, T6 = 1 / math.sqrt(42), 2 / math.sqrt(42), 4 / math.sqrt(42), 6 / math.sqrt(42)


def qpsk(y):
    return complex((-1.0 if y.real < 0 else 1.0) * R2, (-1.0 if y.imag < 0 else 1.0) * R2)


def psk8(y):
    p = int(math.floor(math.atan2(y.imag, y.real) / (math.pi / 4) + 0.5)) % 8
    return cmath.exp(1j * (math.pi / 4) * p)


def qam16(y):
    def level(v):
        m = 1.0 if abs(v) < T10 else 3.0
        return (-m if v < 0 else m) * R10
    return complex(level(y.real), level(y.imag))


def qam64(y):
    def level(v):
        a = abs(v)
        m = 4 + (1 - 2 * (a < T4)) * (3 - 2 * (T2 < a < T6))
        return (-m if v < 0 else m) * R42
    return complex(level(y.real), level(y.imag))


DECIDE = {"qpsk": qpsk, "psk8": psk8, "qam16": qam16, "qam64": qam64}


def lms(x, t, taps, mu, sps=1, center=None, decision=None):
    c = (taps - 1) // 2 if center is None else center
    w = [0j] * taps
    w[c] = 1 + 0j
    ys, es = [], []
    for n in range(-(-len(x) // sps)):
        base = n * sps + c
        u = [x[base - i] if 0 <= base - i < len(x) else 0j for i in range(taps)]
        y = 0j
        for wi, ui in zip(w, u):
            y += wi * ui
        ys.append(y)
        d = t[n] if n < len(t) else DECIDE[decision](y) if decision else None
        if d is None:
            es.append(0j)
            continue
        e = d - y
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
    pts = {"qpsk": [qpsk(complex(re, im)) for re in (1, -1) for im in (1, -1)],
           "psk8": [cmath.exp(1j * math.pi / 4 * p) for p in range(8)],
           "qam16": [complex(i * R10, q * R10) for i in (-3, -1, 1, 3) for q in (-3, -1, 1, 3)],
           "qam64": [complex(i * R42, q * R42) for i in range(-7, 8, 2) for q in range(-7, 8, 2)]}
    out, s = [], seed
    for _ in range(n):
        s = (1103515245 * s + 12345) % 2**31
        out.append(pts[order][(s >> 16) % len(pts[order])])
    return out


cases = []
SRC = "the conventions recurrence run step by step (this generator)"
OP = "lms_equalizer"


def add(name, x, t, taps, mu, source=SRC, tol=None, **kw):
    args = {"samples": C(x), "training": C(t), "num_taps": taps, "step": mu}
    args |= {("samples_per_symbol" if k == "sps" else k): v for k, v in kw.items()}
    ys, es, w = lms(x, t, taps, mu, **kw)
    cases.append({"id": f"{OP}.{name}", "op": OP, "args": args,
                  "expected": {"symbols": C(ys), "errors": C(es), "taps": C(w)},
                  "tol": tol or {"abs": 1e-12, "rel": 0}, "source": source})
    return ys, es, w


X = [complex(0.3 * k - 1, 0.7 - 0.2 * k * k % 1.3) for k in range(9)]
ys, es, w = add("step_zero_passes_through_by_hand", X, X[:2], 5, 0.0, sps=2,
                source="by hand: with step 0 the taps stay a unit impulse at the center, so "
                "output n is x[2n] and the error is t_n - x[2n]", tol={"abs": 0, "rel": 0})
assert ys == X[::2] and es[:2] == [X[0] - X[0], X[1] - X[2]] and es[2:] == [0j] * 3
assert w == [0j, 0j, 1 + 0j, 0j, 0j]

G = complex(0.6, -0.8) * 1.7
A = points("qpsk", 6, 3)
ys, es, w = add("one_tap_inverts_a_gain_by_hand", [G * a for a in A], A[:1], 1, 1.0,
                source="by hand: one tap at step 1 becomes t_0/x_0 = 1/g after the first symbol, "
                "so every later output is the symbol itself", tol={"abs": 1e-15, "rel": 0})
assert all(abs(y - a) < 1e-15 for y, a in zip(ys[1:], A[1:])) and abs(w[0] - 1 / G) < 1e-15

ys, es, _ = add("zero_input_by_hand", [0j] * 4, [], 3, 1.0, decision="qpsk",
                source="by hand: zero samples give output 0, which decides (1+j)/sqrt2; the "
                "regressor power is 0, so the taps never move", tol={"abs": 0, "rel": 0})
assert ys == [0j] * 4 and es == [complex(R2, R2)] * 4

H2 = [1 + 0j, complex(0.35, -0.2), complex(-0.1, 0.05)]
A = points("qpsk", 80, 7)
add("qpsk_symbol_spaced", channel(A, H2), A[:30], 7, 0.3, decision="qpsk")
add("qpsk_training_only_holds", channel(A[:40], H2), A[:20], 5, 0.5)
HF = [0.1 + 0j, 0.9 + 0j, complex(0.3, 0.2), complex(-0.1, 0.15), complex(0.05, 0)]
A = points("qam16", 60, 11)
add("qam16_fractional", channel(A, HF, 2), A[:40], 9, 0.2, sps=2, decision="qam16")
A = points("psk8", 50, 13)
add("psk8_center_given", channel(A, H2), A[:30], 6, 0.4, center=1, decision="psk8")
A = points("qam64", 70, 17)
add("qam64_fractional", channel(A, HF, 2), A[:50], 8, 0.1, sps=2, decision="qam64")
add("sps_not_dividing", channel(points("qpsk", 7, 19), H2, 3)[:-1], points("qpsk", 3, 19), 4,
    0.7, sps=3, decision="qpsk")

for name, args, why in (
    ("step_above_two", {"step": 2.5}, "step must be between 0 and 2"),
    ("negative_step", {"step": -0.1}, "step must be between 0 and 2"),
    ("center_past_the_taps", {"center": 3}, "center must be below num_taps"),
    ("no_taps", {"num_taps": 0}, "num_taps must be at least 1"),
    ("no_samples", {"samples": C([]), "training": C([])}, "samples needs at least 1"),
    ("training_too_long", {"training": C([1] * 5)}, "training is at most the output count (4)"),
    ("unknown_decision", {"decision": "bpsk"}, "decision must be a known modulation"),
    ("zero_sps", {"samples_per_symbol": 0}, "samples_per_symbol must be at least 1"),
    ("nan_sample", {"samples": {"re": [1.0, "nan", 0, 0], "im": [0, 0, 0, 0]}},
     "samples must be finite"),
):
    base = {"samples": C([1, 1j, -1, -1j]), "training": C([1]), "num_taps": 3, "step": 0.5}
    cases.append({"id": f"{OP}.{name}", "op": OP, "args": base | args,
                  "error": "invalid_argument", "source": why})

doc = {
    "schema": 1,
    "suite": "equalizer",
    "description": "Normalized LMS equalizer, fractionally spaced, trained then decision-directed "
    "(conventions: Synchronization, LMS equalizer).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "equalizer.json"


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
        sys.exit(f"{out} is out of date: run python vectors/generators/equalizer.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
