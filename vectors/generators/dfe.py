"""Writes vectors/cases/dfe.json from the definition, using only the Python standard library.

It does not import NumPy or SignalForge. It runs the decision-feedback equalizer in the
conventions (Synchronization, Decision-feedback equalizer) step by step, with the hard decisions
written out from the demapper rules (conventions: Bits and symbols). The by-hand cases are
checked here against the closed forms they rely on.

Run from the repo root: python vectors/generators/dfe.py [--check]
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


def dfe(x, t, taps, m, mu, sps=1, center=None, decision=None, initial_taps=None,
        initial_feedback=None):
    c = (taps - 1) // 2 if center is None else center
    w = [0j] * taps
    w[c] = 1 + 0j
    b = [0j] * m
    if initial_taps is not None:
        w = [complex(z) for z in initial_taps]
    if initial_feedback is not None:
        b = [complex(z) for z in initial_feedback]
    past = [0j] * m  # past[j - 1] is d_{n-j}
    ys, es = [], []
    for n in range(-(-len(x) // sps)):
        base = n * sps + c
        u = [x[base - i] if 0 <= base - i < len(x) else 0j for i in range(taps)]
        y = 0j
        for wi, ui in zip(w, u):
            y += wi * ui
        for bj, pj in zip(b, past):
            y += bj * pj
        ys.append(y)
        d = t[n] if n < len(t) else DECIDE[decision](y) if decision else None
        if d is None:
            es.append(0j)
            continue
        e = d - y
        es.append(e)
        p = 0.0
        for z in u + past:
            p += z.real * z.real + z.imag * z.imag
        if p > 0:
            g = mu / p
            w = [wi + g * e * ui.conjugate() for wi, ui in zip(w, u)]
            b = [bj + g * e * pj.conjugate() for bj, pj in zip(b, past)]
        if m:
            past = [d] + past[:-1]
    return ys, es, w, b


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
OP = "dfe_equalizer"


def add(name, x, t, taps, m, mu, source=SRC, tol=None, **kw):
    args = {"samples": C(x), "training": C(t), "num_taps": taps, "num_feedback": m, "step": mu}
    args |= {("samples_per_symbol" if k == "sps" else k):
             C(v) if k in ("initial_taps", "initial_feedback") else v for k, v in kw.items()}
    ys, es, w, b = dfe(x, t, taps, m, mu, **kw)
    cases.append({"id": f"{OP}.{name}", "op": OP, "args": args,
                  "expected": {"symbols": C(ys), "errors": C(es), "taps": C(w),
                               "feedback_taps": C(b)},
                  "tol": tol or {"abs": 1e-12, "rel": 0}, "source": source})
    return ys, es, w, b


D = complex(R2, R2)
ys, es, w, b = add("zero_input_feedback_learns_by_hand", [0j] * 4, [], 3, 1, 1.0,
                   decision="qpsk",
                   source="by hand: output 0 decides d = (1+j)/sqrt2 with no power to update; next "
                   "the regressor is (0, 0, 0; d), so b becomes d conj(d)/|d|^2 = 1, and from then "
                   "on the output is d with no error", tol={"abs": 1e-15, "rel": 0})
assert all(abs(y - z) < 1e-15 for y, z in zip(ys, [0j, 0j, D, D]))
assert all(abs(e - z) < 1e-15 for e, z in zip(es, [D, D, 0j, 0j]))
assert w == [0j, 1 + 0j, 0j] and abs(b[0] - 1) < 1e-15

X = [complex(0.3 * k - 1, 0.7 - 0.2 * k * k % 1.3) for k in range(9)]
ys, es, w, b = add("step_zero_passes_through_by_hand", X, X[:5], 5, 2, 0.0, sps=2,
                   source="by hand: with step 0 the forward taps stay a unit impulse and the "
                   "feedback taps 0, so output n is x[2n] and the error is t_n - x[2n]",
                   tol={"abs": 0, "rel": 0})
assert ys == X[::2] and es == [X[n] - X[2 * n] for n in range(5)]
assert w == [0j, 0j, 1 + 0j, 0j, 0j] and b == [0j, 0j]

# a pure post-cursor echo: one forward tap at 1 cannot remove it; the feedback tap learns -h
H = complex(0.45, -0.3)
A = points("qpsk", 120, 5)
X = channel(A, [1 + 0j, H])
ys, es, w, b = add("one_echo_cancelled_by_feedback", X, A[:10], 1, 1, 0.5, decision="qpsk")
assert abs(b[0] + H) < 1e-6 and abs(w[0] - 1) < 1e-6  # the closed form it converges to

H2 = [1 + 0j, complex(0.5, -0.25), complex(-0.2, 0.15), complex(0.1, 0)]
A = points("qpsk", 80, 7)
add("qpsk_symbol_spaced", channel(A, H2), A[:30], 5, 3, 0.3, decision="qpsk")
add("qpsk_training_covers_all", channel(A[:30], H2), A[:30], 3, 2, 0.4)
HF = [0.1 + 0j, 0.9 + 0j, complex(0.3, 0.2), complex(-0.1, 0.15), complex(0.05, 0),
      complex(0.2, -0.1)]
A = points("qam16", 60, 11)
add("qam16_fractional", channel(A, HF, 2), A[:40], 7, 2, 0.2, sps=2, decision="qam16")
A = points("psk8", 50, 13)
add("psk8_center_given", channel(A, H2), A[:30], 4, 2, 0.4, center=1, decision="psk8")
A = points("qam64", 70, 17)
add("qam64_fractional", channel(A, HF, 2), A[:50], 8, 3, 0.1, sps=2, decision="qam64")
A = points("qpsk", 40, 23)
add("no_feedback_is_lms", channel(A, H2), A[:20], 5, 0, 0.3, decision="qpsk",
    source="the conventions recurrence run step by step (this generator), with no feedback taps: "
    "the LMS equalizer's recurrence")
W0 = [complex(0.2, -0.1), complex(0.9, 0.3), complex(-0.15, 0.05)]
B0 = [complex(-0.4, 0.2)]
X = [complex(0.3 * k - 1, 0.7 - 0.2 * k * k % 1.3) for k in range(5)]
T = [complex(1, -1), complex(-1, 0.5), complex(0.25, 1), complex(0, -2), complex(1.5, 0)]
ys, es, w, b = add("initial_start_step_zero_by_hand", X, T, 3, 1, 0.0, initial_taps=W0,
                   initial_feedback=B0,
                   source="by hand: with step 0 the taps stay the given start, so output n is "
                   "w0[0] x[n+1] + w0[1] x[n] + w0[2] x[n-1] + b0 t[n-1] (0 outside)")
assert all(abs(ys[n] - sum(W0[i] * (X[n + 1 - i] if 0 <= n + 1 - i < 5 else 0)
                           for i in range(3)) - (B0[0] * T[n - 1] if n else 0)) < 1e-15
           for n in range(5))
assert w == W0 and b == B0
A = points("qam16", 60, 31)
add("initial_start_adapts", channel(A, H2), A[:20], 3, 2, 0.3, decision="qam16",
    initial_taps=W0, initial_feedback=[complex(-0.5, 0.25), 0j])

for name, args, why in (
    ("initial_feedback_wrong_length", {"initial_feedback": C([0])},
     "initial_feedback must hold num_feedback"),
    ("initial_taps_wrong_length", {"initial_taps": C([1, 0])}, "initial_taps must hold num_taps"),
    ("negative_feedback", {"num_feedback": -1}, "num_feedback must not be negative"),
    ("feedback_without_references", {"decision": None},
     "with feedback every output needs a reference: training covers 1 of 4, no decision"),
    ("step_above_two", {"step": 2.5}, "step must be between 0 and 2"),
    ("no_taps", {"num_taps": 0}, "num_taps must be at least 1"),
    ("training_too_long", {"training": C([1] * 5)}, "training is at most the output count (4)"),
):
    base = {"samples": C([1, 1j, -1, -1j]), "training": C([1]), "num_taps": 3,
            "num_feedback": 2, "step": 0.5, "decision": "qpsk"}
    a = {k: v for k, v in (base | args).items() if v is not None}
    cases.append({"id": f"{OP}.{name}", "op": OP, "args": a,
                  "error": "invalid_argument", "source": why})

doc = {
    "schema": 1,
    "suite": "dfe",
    "description": "Decision-feedback equalizer: normalized LMS over forward and feedback taps "
    "(conventions: Synchronization, Decision-feedback equalizer).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "dfe.json"


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
        sys.exit(f"{out} is out of date: run python vectors/generators/dfe.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
