"""Writes vectors/cases/rls.json from the definition, using only the Python standard library.

It does not import NumPy or SignalForge. It runs the exponentially weighted RLS equalizer in the
conventions (Synchronization, RLS equalizer) step by step, and checks the taps of every case with
every output trained against the closed form of the weighted, regularized least-squares problem
the recursion solves, found here by Gaussian elimination.

Run from the repo root: python vectors/generators/rls.py [--check]
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


def qpsk(y):
    return complex((-1.0 if y.real < 0 else 1.0) * R2, (-1.0 if y.imag < 0 else 1.0) * R2)


def qam16(y):
    def level(v):
        m = 1.0 if abs(v) < T10 else 3.0
        return (-m if v < 0 else m) * R10
    return complex(level(y.real), level(y.imag))


DECIDE = {"qpsk": qpsk, "qam16": qam16}


def regressor(x, n, taps, sps, c):
    base = n * sps + c
    return [x[base - i] if 0 <= base - i < len(x) else 0j for i in range(taps)]


def rls(x, t, taps, lam, delta=0.01, sps=1, center=None, decision=None, initial_taps=None):
    c = (taps - 1) // 2 if center is None else center
    w = [0j] * taps
    w[c] = 1 + 0j
    if initial_taps is not None:
        w = [complex(z) for z in initial_taps]
    p = [[complex(1 / delta if i == j else 0.0) for j in range(taps)] for i in range(taps)]
    ys, es = [], []
    for n in range(-(-len(x) // sps)):
        u = regressor(x, n, taps, sps, c)
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
        power = 0.0
        for ui in u:
            power += ui.real * ui.real + ui.imag * ui.imag
        if not power > 0:
            continue
        q = []
        for i in range(taps):
            qi = 0j
            for j in range(taps):
                qi += p[i][j] * u[j].conjugate()
            q.append(qi)
        s = complex(lam)
        for i in range(taps):
            s += u[i] * q[i]
        g = [qi / s for qi in q]
        w = [wi + gi * e for wi, gi in zip(w, g)]
        r = []
        for j in range(taps):
            rj = 0j
            for i in range(taps):
                rj += u[i] * p[i][j]
            r.append(rj)
        p = [[(p[i][j] - g[i] * r[j]) / lam for j in range(taps)] for i in range(taps)]
    return ys, es, w


def solve(a, b):
    """a z = b by Gaussian elimination with partial pivoting."""
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for k in range(n):
        piv = max(range(k, n), key=lambda i: abs(m[i][k]))
        m[k], m[piv] = m[piv], m[k]
        for i in range(k + 1, n):
            f = m[i][k] / m[k][k]
            for j in range(k, n + 1):
                m[i][j] -= f * m[k][j]
    z = [0j] * n
    for i in reversed(range(n)):
        z[i] = (m[i][n] - sum(m[i][j] * z[j] for j in range(i + 1, n))) / m[i][i]
    return z


def closed_form(x, t, taps, lam, delta=0.01, sps=1, center=None, initial_taps=None):
    """The taps minimizing lam^n delta |w - w0|^2 + sum_k lam^(n-k) |d_k - u_k^T w|^2 over the n
    updates (every output trained, none with a zero regressor)."""
    c = (taps - 1) // 2 if center is None else center
    w0 = [0j] * taps
    w0[c] = 1 + 0j
    if initial_taps is not None:
        w0 = [complex(z) for z in initial_taps]
    us = [regressor(x, n, taps, sps, c) for n in range(len(t))]
    us = [(u, d) for u, d in zip(us, t) if any(z != 0 for z in u)]
    n = len(us)
    a = [[complex(lam**n * delta if i == j else 0.0) for j in range(taps)] for i in range(taps)]
    b = [lam**n * delta * z for z in w0]
    for k, (u, d) in enumerate(us, 1):
        f = lam ** (n - k)
        for i in range(taps):
            b[i] += f * u[i].conjugate() * d
            for j in range(taps):
                a[i][j] += f * u[i].conjugate() * u[j]
    return solve(a, b)


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
           "qam16": [complex(i * R10, q * R10) for i in (-3, -1, 1, 3) for q in (-3, -1, 1, 3)]}
    out, s = [], seed
    for _ in range(n):
        s = (1103515245 * s + 12345) % 2**31
        out.append(pts[order][(s >> 16) % len(pts[order])])
    return out


def noise(n, seed, sigma):
    out, s = [], seed
    for _ in range(n):
        v = []
        for _ in range(2):
            s = (1103515245 * s + 12345) % 2**31
            v.append(((s >> 8) / 2**23 - 0.5) * 2 * sigma)
        out.append(complex(*v))
    return out


cases = []
SRC = "the conventions recurrence run step by step (this generator)"
CF = ("the conventions recurrence run step by step (this generator); its final taps are checked "
      "here against the closed-form weighted, regularized least-squares solution, within 1e-9")
OP = "rls_equalizer"


def add(name, x, t, taps, lam, source=SRC, tol=None, closed=False, **kw):
    args = {"samples": C(x), "training": C(t), "num_taps": taps, "forgetting": lam}
    args |= {("samples_per_symbol" if k == "sps" else k): C(v) if k == "initial_taps" else v
             for k, v in kw.items()}
    ys, es, w = rls(x, t, taps, lam, **kw)
    if closed:
        kc = {k: v for k, v in kw.items() if k != "decision"}
        wc = closed_form(x, t, taps, lam, **kc)
        assert max(abs(a - b) for a, b in zip(w, wc)) < 1e-9, (name, w, wc)
        source = CF
    cases.append({"id": f"{OP}.{name}", "op": OP, "args": args,
                  "expected": {"symbols": C(ys), "errors": C(es), "taps": C(w)},
                  "tol": tol or {"abs": 1e-10, "rel": 0}, "source": source})
    return ys, es, w


# one tap, lambda = 1, real gain 2 on unit symbols: P = 1/(delta + n|g|^2) and w is the
# regularized ratio (delta + sum conj(u) d)/(delta + sum |u|^2) after each update
A = points("qpsk", 6, 3)
ys, es, w = add("one_tap_gain_by_hand", [2 * a for a in A], A, 1, 1.0, delta=0.5,
                source="by hand: one tap on x = 2a, |a| = 1, lambda 1, delta 0.5: after n updates "
                "w = (0.5 + 2n)/(0.5 + 4n), so output n is 2a_n times that for n - 1",
                tol={"abs": 1e-14, "rel": 0})
for n in range(6):
    assert abs(ys[n] - 2 * A[n] * (0.5 + 2 * n) / (0.5 + 4 * n)) < 1e-14
assert abs(w[0] - (0.5 + 12) / (0.5 + 24)) < 1e-14

ys, es, w = add("zero_input_by_hand", [0j] * 4, points("qpsk", 4, 5), 3, 0.9,
                source="by hand: zero samples give output 0 and error d; the regressor is all "
                "zero, so neither the taps nor P change", tol={"abs": 0, "rel": 0})
assert ys == [0j] * 4 and w == [0j, 1 + 0j, 0j]

X = [complex(0.3 * k - 1, 0.7 - 0.2 * k * k % 1.3) for k in range(9)]
ys, es, w = add("no_training_no_decision_passes_through_by_hand", X, [], 5, 0.95, sps=2,
                source="by hand: with no reference nothing updates, so the taps stay a unit "
                "impulse at the center and output n is x[2n] with error 0",
                tol={"abs": 0, "rel": 0})
assert ys == X[::2] and es == [0j] * 5

H = [1 + 0j, 0.9 * cmath.exp(0.6j)]  # a zero at radius 0.9 (ADR 0076)
A = points("qpsk", 80, 7)
X = [a + z for a, z in zip(channel(A, H), noise(80, 9, 0.05))]
add("growing_window_matches_least_squares", X, A, 9, 1.0, center=2, closed=True)
add("forgetting_matches_weighted_least_squares", X, A, 9, 0.97, delta=0.1, center=2, closed=True)
A = points("qpsk", 120, 11)
X = [a + z for a, z in zip(channel(A, H), noise(120, 13, 0.05))]
ys, es, w = add("decisions_after_training", X, A[:30], 9, 0.99, center=2, decision="qpsk")
# converged on the decisions: 0.07 over the last 60 (9 taps leave that on this channel) from
# 0.33 over the training
assert sum(abs(e) ** 2 for e in es[60:]) / 60 < 0.1 < sum(abs(e) ** 2 for e in es[:30]) / 30
HF = [0.1 + 0j, 0.9 + 0j, complex(0.3, 0.2), complex(-0.1, 0.15), complex(0.05, 0)]
A = points("qam16", 60, 17)
add("qam16_fractional", channel(A, HF, 2), A, 8, 1.0, sps=2, closed=True)
add("qam16_fractional_decisions", channel(A, HF, 2), A[:30], 8, 0.98, sps=2, decision="qam16")
W0 = [complex(0.2, -0.1), complex(0.9, 0.3), complex(-0.15, 0.05)]
A = points("qpsk", 40, 19)
add("initial_taps", channel(A, H), A, 3, 0.95, initial_taps=W0, closed=True)
add("sps_not_dividing", channel(points("qpsk", 7, 23), H, 3)[:-1], points("qpsk", 7, 23)[:4], 4,
    0.9, sps=3)

for name, args, why in (
    ("forgetting_zero", {"forgetting": 0.0}, "forgetting must be in (0, 1]"),
    ("forgetting_above_one", {"forgetting": 1.01}, "forgetting must be in (0, 1]"),
    ("forgetting_not_finite", {"forgetting": "nan"}, "forgetting must be finite"),
    ("delta_zero", {"delta": 0.0}, "delta must be above 0"),
    ("delta_not_finite", {"delta": "inf"}, "delta must be finite"),
    ("unknown_decision", {"decision": "qam32"}, "decision must be a known modulation"),
    ("initial_taps_wrong_length", {"initial_taps": C([1, 0])}, "initial_taps must hold num_taps"),
    ("center_past_the_taps", {"center": 3}, "center must be below num_taps"),
    ("no_taps", {"num_taps": 0}, "num_taps must be at least 1"),
    ("training_too_long", {"training": C([1] * 5)}, "training is at most the output count (4)"),
    ("nan_sample", {"samples": {"re": [1.0, "nan", 0, 0], "im": [0, 0, 0, 0]}},
     "samples must be finite"),
):
    base = {"samples": C([1, 1j, -1, -1j]), "training": C([1]), "num_taps": 3, "forgetting": 0.99}
    cases.append({"id": f"{OP}.{name}", "op": OP, "args": base | args,
                  "error": "invalid_argument", "source": why})

doc = {
    "schema": 1,
    "suite": "rls",
    "description": "Exponentially weighted recursive-least-squares equalizer, fractionally "
    "spaced (conventions: Synchronization, RLS equalizer).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "rls.json"


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
        sys.exit(f"{out} is out of date: run python vectors/generators/rls.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
