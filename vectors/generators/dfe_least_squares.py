"""Writes vectors/cases/dfe_least_squares.json from the definition, using only the standard library.

It does not import NumPy or SignalForge. It builds the normal equations and solves them by the
elimination in the conventions (Synchronization, Least-squares equalizer taps). The by-hand cases
are checked here against the closed forms they rely on, and every solved case against the normal
equations themselves (the residual is orthogonal to every regressor).

Run from the repo root: python vectors/generators/dfe_least_squares.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write (numbers
within 1e-13).
"""

import json
import math
import pathlib
import sys

R2 = 1 / math.sqrt(2)
R10 = 1 / math.sqrt(10)


def regressors(x, t, taps, m, sps, center):
    c = (taps - 1) // 2 if center is None else center
    rows = []
    for n in range(len(t)):
        base = n * sps + c
        v = [x[base - i] if 0 <= base - i < len(x) else 0j for i in range(taps)]
        v += [t[n - j] if n - j >= 0 else 0j for j in range(1, m + 1)]
        rows.append(v)
    return rows


def solve(x, t, taps, m, sps=1, center=None):
    k_all = taps + m
    rows = regressors(x, t, taps, m, sps, center)
    g = [[0j] * k_all for _ in range(k_all)]
    h = [0j] * k_all
    for n, v in enumerate(rows):
        for k in range(k_all):
            ck = v[k].conjugate()
            for col in range(k_all):
                g[k][col] += ck * v[col]
            h[k] += ck * t[n]
    for k in range(k_all):
        r, big = k, -1.0
        for i in range(k, k_all):
            mag = g[i][k].real ** 2 + g[i][k].imag ** 2
            if mag > big:
                r, big = i, mag
        assert big > 0
        g[k], g[r] = g[r], g[k]
        h[k], h[r] = h[r], h[k]
        for i in range(k + 1, k_all):
            f = g[i][k] / g[k][k]
            for col in range(k + 1, k_all):
                g[i][col] -= f * g[k][col]
            h[i] -= f * h[k]
    th = [0j] * k_all
    for k in range(k_all - 1, -1, -1):
        acc = h[k]
        for col in range(k + 1, k_all):
            acc -= g[k][col] * th[col]
        th[k] = acc / g[k][k]
    # the normal equations: sum_n conj(v_n[k]) (t_n - theta . v_n) = 0 for every k
    for k in range(k_all):
        res = sum(v[k].conjugate() * (t[n] - sum(a * b for a, b in zip(th, v)))
                  for n, v in enumerate(rows))
        assert abs(res) < 1e-9 * max(1.0, sum(abs(z) ** 2 for v in rows for z in v)), res
    return th[:taps], th[taps:]


def C(xs):
    return {"re": [complex(z).real for z in xs], "im": [complex(z).imag for z in xs]}


def channel(a, h, sps=1):
    up = []
    for s in a:
        up += [s] + [0j] * (sps - 1)
    return [sum(h[j] * up[n - j] for j in range(len(h)) if 0 <= n - j < len(up))
            for n in range(len(up))]


def points(order, n, seed):
    pts = {"qpsk": [complex(re * R2, im * R2) for re in (1, -1) for im in (1, -1)],
           "qam16": [complex(i * R10, q * R10) for i in (-3, -1, 1, 3) for q in (-3, -1, 1, 3)]}
    out, s = [], seed
    for _ in range(n):
        s = (1103515245 * s + 12345) % 2**31
        out.append(pts[order][(s >> 16) % len(pts[order])])
    return out


cases = []
SRC = "the conventions elimination run step by step (this generator), checked on the normal equations"
OP = "dfe_least_squares"


def add(name, x, t, taps, m, source=SRC, tol=None, **kw):
    args = {"samples": C(x), "training": C(t), "num_taps": taps, "num_feedback": m}
    args |= {("samples_per_symbol" if k == "sps" else k): v for k, v in kw.items()}
    w, b = solve(x, t, taps, m, **kw)
    cases.append({"id": f"{OP}.{name}", "op": OP, "args": args,
                  "expected": {"taps": C(w), "feedback_taps": C(b)},
                  "tol": tol or {"abs": 1e-12, "rel": 1e-10}, "source": source})
    return w, b


G = complex(0.6, -0.8) * 1.5
A = points("qpsk", 12, 3)
w, b = add("scalar_gain_by_hand", [G * a for a in A], A, 1, 0,
           source="by hand: x_n = g a_n with one tap, so the error is 0 at w = 1/g",
           tol={"abs": 1e-14, "rel": 0})
assert abs(w[0] - 1 / G) < 1e-15 and b == []

H = complex(0.45, -0.3)
A = points("qpsk", 20, 5)
w, b = add("echo_inverse_by_hand", channel(A, [1 + 0j, H]), A, 1, 1,
           source="by hand: x_n = a_n + h a_{n-1} with one forward and one feedback tap on "
           "a_{n-1}, so the error is 0 at w = 1, b = -h", tol={"abs": 1e-14, "rel": 0})
assert abs(w[0] - 1) < 1e-14 and abs(b[0] + H) < 1e-14

H2 = [1 + 0j, complex(0.5, -0.25), complex(-0.2, 0.15), complex(0.1, 0)]
A = points("qpsk", 40, 7)
w, b = add("echo_tail_by_hand", channel(A, H2), A, 1, 3,
           source="by hand: a channel 1 + h1 z^-1 + h2 z^-2 + h3 z^-3 with one forward tap and "
           "three feedback taps on the past training: the error is 0 at w = 1, b = -h",
           tol={"abs": 1e-13, "rel": 0})
assert abs(w[0] - 1) < 1e-13 and all(abs(bj + hj) < 1e-13 for bj, hj in zip(b, H2[1:]))

HF = [0.1 + 0j, 0.9 + 0j, complex(0.3, 0.2), complex(-0.1, 0.15), complex(0.05, 0),
      complex(0.2, -0.1)]
A = points("qam16", 60, 11)
add("qam16_fractional", channel(A, HF, 2), A[:40], 7, 2, sps=2)
A = points("qpsk", 50, 13)
add("qpsk_center_given", channel(A, H2), A[:30], 4, 2, center=1)
add("qpsk_no_feedback", channel(A, H2), A[:25], 5, 0)

for name, args, why in (
    ("too_little_training", {"training": C([1, 1j, -1])},
     "training needs at least num_taps + num_feedback symbols (4)"),
    ("zero_input", {"samples": C([0] * 6), "num_feedback": 0},
     "the training does not determine the taps: every forward regressor is 0"),
    ("negative_feedback", {"num_feedback": -1}, "num_feedback must not be negative"),
    ("no_taps", {"num_taps": 0}, "num_taps must be at least 1"),
    ("training_too_long", {"training": C([1] * 7)}, "training is at most the output count (6)"),
    ("center_past_the_taps", {"center": 3}, "center must be below num_taps"),
):
    base = {"samples": C([1, 1j, -1, -1j, 0.5, 0.25j]), "training": C([1, -1, 1j, -1j, 1]),
            "num_taps": 3, "num_feedback": 1}
    cases.append({"id": f"{OP}.{name}", "op": OP, "args": base | args,
                  "error": "invalid_argument", "source": why})

doc = {
    "schema": 1,
    "suite": "dfe_least_squares",
    "description": "Least-squares forward and feedback equalizer taps on the training "
    "(conventions: Synchronization, Least-squares equalizer taps).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "dfe_least_squares.json"


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
        sys.exit(f"{out} is out of date: run python vectors/generators/dfe_least_squares.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
