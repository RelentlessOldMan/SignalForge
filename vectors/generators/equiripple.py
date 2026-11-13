"""Writes vectors/cases/equiripple.json from first principles, with only the standard library.

It does not import NumPy or SignalForge. Small cases are solved by hand (in each case's source).
The rest solve the same discrete minimax problem as the library (conventions: FIR filters,
Equiripple design) by a different route, in 50-digit decimal arithmetic: each Remez step solves
the (L+1)x(L+1) system in the cosine basis by Gaussian elimination, and P is evaluated by
Clenshaw's recurrence (the library uses barycentric interpolation in double precision). Each
result is then certified by the alternation theorem: the error alternates in sign at L + 1 grid
points with |E| = delta, and is nowhere larger on the grid (to 1e-25 relative), which makes it
the unique optimum whatever path found it.

Run from the repo root: python vectors/generators/equiripple.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write (numbers
within 1e-14, since C math libraries can differ in the last bit).
"""

import json
import math
import pathlib
import sys
from decimal import Decimal, getcontext

getcontext().prec = 50
TOL = {"abs": 1e-11, "rel": 1e-9}
CERTIFIED = (
    "discrete minimax optimum on the conventions' grid, solved in 50-digit decimal arithmetic "
    "(cosine-basis solves, Clenshaw evaluation) and certified by alternation: {alt} alternating "
    "extrema at |E| = delta = {delta:.6e}, no grid point larger"
)


def dec_pi():
    """Machin's formula: pi = 16 atan(1/5) - 4 atan(1/239)."""

    def atan_inv(n):
        n2, total, k, term = n * n, Decimal(0), 0, Decimal(1) / n
        while term != 0:
            total += term / (2 * k + 1) if k % 2 == 0 else -term / (2 * k + 1)
            term /= n2
            k += 1
        return total

    return 16 * atan_inv(5) - 4 * atan_inv(239)


PI = dec_pi()


def dec_cos(x):
    """cos by its power series, after reducing to [-pi, pi]."""
    x = x - 2 * PI * (x / (2 * PI)).to_integral_value()
    term, total, k = Decimal(1), Decimal(1), 0
    while True:
        k += 2
        term *= -x * x / (k * (k - 1))
        if abs(term) < Decimal(10) ** -60:
            return total
        total += term


def dec_sin(x):
    return dec_cos(x - PI / 2)


def grid(n, bands, desired, fs, weights, density, kind="filter"):
    """The grid points, in float exactly as the conventions define them."""
    odd, anti = n % 2 == 1, kind != "filter"
    big_l = (n - 1) // 2 if anti and odd else (n + 1) // 2 if odd else n // 2
    step = 0.5 / (density * big_l)
    pts = []
    for j in range(len(desired)):
        lo, hi = bands[2 * j] / fs, bands[2 * j + 1] / fs
        m = math.ceil((hi - lo) / step)
        for i in range(m + 1):
            v = hi if i == m else lo + (hi - lo) * i / m
            if (v == 0.5 and odd == anti) or (v == 0 and anti):
                continue  # Q = 0 there
            pts.append((v, desired[j], weights[j], j))
    return big_l, pts


def solve(a, b):
    """Gaussian elimination with partial pivoting, in place on copies."""
    n = len(b)
    a = [[*row, b[i]] for i, row in enumerate(a)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(a[r][c]))
        a[c], a[p] = a[p], a[c]
        for r in range(c + 1, n):
            f = a[r][c] / a[c][c]
            if f:
                for k in range(c, n + 1):
                    a[r][k] -= f * a[c][k]
    x = [Decimal(0)] * n
    for r in range(n - 1, -1, -1):
        x[r] = (a[r][n] - sum(a[r][k] * x[k] for k in range(r + 1, n))) / a[r][r]
    return x


def clenshaw(c, x):
    """sum c_k T_k(x), i.e. sum c_k cos(2 pi k nu) at x = cos(2 pi nu)."""
    b1 = b2 = Decimal(0)
    for ck in reversed(c[1:]):
        b1, b2 = 2 * x * b1 - b2 + ck, b1
    return x * b1 - b2 + c[0]


def chebyshev_row(x, n):
    row = [Decimal(1), x]
    while len(row) < n:
        row.append(2 * x * row[-1] - row[-2])
    return row[:n]


def remez(n, bands, desired, fs, weights=None, density=16, kind="filter"):
    weights = weights or [1.0] * len(desired)
    big_l, pts = grid(n, bands, desired, fs, weights, density, kind)
    odd, anti = n % 2 == 1, kind != "filter"
    x, dp, wp, band = [], [], [], []
    for v, d, w, j in pts:
        nu = Decimal(v)
        if anti:
            q = dec_sin((2 if odd else 1) * PI * nu)
        else:
            q = Decimal(1) if odd else dec_cos(PI * nu)
        t, wt = Decimal(d), Decimal(w)
        if kind == "differentiator" and d != 0:  # target -2 pi nu D, error relative to the slope
            t, wt = -2 * PI * nu * t, wt / (2 * PI * nu)
        x.append(dec_cos(2 * PI * nu))
        dp.append(t / q)
        wp.append(wt * q)
        band.append(j)
    g = len(x)
    ext = [(i * (g - 1)) // big_l for i in range(big_l + 1)]
    for _ in range(100):
        a = [
            [*chebyshev_row(x[k], big_l), Decimal((-1) ** i) / wp[k]]
            for i, k in enumerate(ext)
        ]
        sol = solve(a, [dp[k] for k in ext])
        c, delta = sol[:big_l], sol[big_l]
        e = [wp[i] * (dp[i] - clenshaw(c, x[i])) for i in range(g)]
        top = max(abs(v) for v in e)
        if top <= abs(delta) * (1 + Decimal(10) ** -30):
            break
        # Exchange: in-band local extrema, alternating, the L + 1 largest by the usual rules.
        # The old set's points always count, with their sign (-1)^i sign(delta), even at delta = 0.
        sgn = [v > 0 for v in e]
        for i, k in enumerate(ext):
            sgn[k] = (i % 2 == 0) == (delta >= 0)
        cand = []
        for i in range(g):
            nbr = [e[k] for k in (i - 1, i + 1) if 0 <= k < g and band[k] == band[i]]
            up = e[i] > 0 and all(e[i] >= v for v in nbr)
            if up or (e[i] < 0 and all(e[i] <= v for v in nbr)) or i in ext:
                if cand and sgn[cand[-1]] == sgn[i]:
                    if abs(e[i]) > abs(e[cand[-1]]):
                        cand[-1] = i
                else:
                    cand.append(i)
        while len(cand) > big_l + 1:
            if abs(e[cand[0]]) <= abs(e[cand[-1]]):
                cand.pop(0)
            else:
                cand.pop()
        ext = cand
    else:
        raise SystemExit(f"no convergence for {n} {bands}")
    # Certify: alternation at L + 1 points with |E| = |delta|, nothing larger on the grid.
    d = abs(delta)
    signs = [e[k] > 0 for k in ext]
    assert all(signs[i] != signs[i + 1] for i in range(big_l)), "no alternation"
    assert all(abs(abs(e[k]) - d) <= d * Decimal(10) ** -25 for k in ext), "not level"
    assert max(abs(v) for v in e) <= d * (1 + Decimal(10) ** -25), "not optimal"
    taps = (anti_taps if anti else taps_from)(n, [float(v) for v in c])
    return taps, float(d), big_l + 1


def anti_taps(n, c):
    """Types III and IV: taps from the cosine coefficients of P, A = Q P expanded in sines
    (sin(w) cos(kw) and sin(w/2) cos(kw) by the product formulas; conventions)."""
    big_l = len(c)
    z = [*c, 0.0, 0.0]
    if n % 2:
        a = [c[0] - z[2] / 2] + [(z[m - 1] - z[m + 1]) / 2 for m in range(2, big_l + 1)]
        return [-v / 2 for v in a[::-1]] + [0.0] + [v / 2 for v in a]
    b = [c[0] - z[1] / 2] + [(z[m - 1] - z[m]) / 2 for m in range(2, big_l + 1)]
    return [-v / 2 for v in b[::-1]] + [v / 2 for v in b]


def taps_from(n, c):
    """Taps from the cosine coefficients of P (conventions), A = Q P."""
    if n % 2:
        return [v / 2 for v in c[:0:-1]] + [c[0]] + [v / 2 for v in c[1:]]
    big_l = len(c)
    beta = [c[0] + (c[1] / 2 if big_l > 1 else 0.0)]
    beta += [(c[k] + c[k + 1]) / 2 for k in range(1, big_l - 1)]
    if big_l > 1:
        beta.append(c[-1] / 2)
    return [v / 2 for v in beta[::-1]] + [v / 2 for v in beta]


def certified(case_id, args, tol=TOL, note=""):
    taps, delta, alt = remez(
        args["num_taps"],
        args["bands"],
        args["desired"],
        args["sample_rate"],
        args.get("weights"),
        args.get("grid_density", 16),
        args.get("kind", "filter"),
    )
    return {
        "id": case_id,
        "op": "fir_equiripple",
        "args": args,
        "expected": taps,
        "tol": tol,
        "source": CERTIFIED.format(alt=alt, delta=delta) + note,
    }


def hand(case_id, args, taps, why):
    tol = {"abs": 1e-13, "rel": 1e-12}
    return {"id": case_id, "op": "fir_equiripple", "args": args, "expected": taps, "tol": tol,
            "source": why}  # fmt: skip


def err(case_id, args, why):
    full = {
        "num_taps": 21,
        "bands": [0, 0.1, 0.2, 0.5],
        "desired": [1, 0],
        "sample_rate": 1,
    }
    full.update(args)
    return {"id": case_id, "op": "fir_equiripple", "args": full, "error": "invalid_argument",
            "source": why}  # fmt: skip


LP = [0, 0.1, 0.4, 0.5]
c5 = math.cos(math.pi / 5)
s3 = 1 / (1 + c5)
h2 = 1 / (2 * (math.cos(math.pi / 10) + math.cos(2 * math.pi / 5)))
h2w = 1 / (2 * (math.cos(math.pi / 10) + 10 * math.cos(2 * math.pi / 5)))

# Antisymmetric, L = 1: A = a sin(2 pi nu) (N = 3) or a sin(pi nu) (N = 2), one free value.
hil3 = 2 / (math.sin(0.2 * math.pi) + 1)
hil2 = 2 / (math.sin(0.1 * math.pi) + 1)
dif3 = -2 / (math.sin(math.pi / 16) / (math.pi / 16) + 2 / math.pi)
ANTI_HAND = [
    hand(
        "fir_equiripple.hilbert_3_by_hand",
        {"num_taps": 3, "bands": [0.1, 0.4], "desired": [1], "sample_rate": 1,
         "kind": "hilbert"},
        [-hil3 / 2, 0.0, hil3 / 2],
        "by hand: type III, L = 1, A = a sin(2 pi nu) with a = 2 h[2]; the error 1 - a sin is "
        "largest at the band ends (sin(0.2 pi)) and at 0.25 (sin = 1, a grid point), so the "
        "optimum levels them: a = 2/(sin(0.2 pi) + 1)",
    ),  # fmt: skip
    hand(
        "fir_equiripple.hilbert_2_by_hand",
        {"num_taps": 2, "bands": [0.1, 0.5], "desired": [1], "sample_rate": 1,
         "kind": "hilbert"},
        [-hil2 / 2, hil2 / 2],
        "by hand: type IV, L = 1, A = a sin(pi nu) with a = 2 h[1], which keeps nu = 0.5 "
        "(sin = 1); levelling 1 - a sin at 0.1 and 0.5: a = 2/(sin(0.1 pi) + 1)",
    ),  # fmt: skip
    hand(
        "fir_equiripple.differentiator_3_by_hand",
        {"num_taps": 3, "bands": [0, 0.25], "desired": [1], "sample_rate": 1,
         "kind": "differentiator"},
        [-dif3 / 2, 0.0, dif3 / 2],
        "by hand: type III, L = 1, grid 1/32 apart with nu = 0 dropped; target -2 pi nu, "
        "relative error -1 - a sin(w)/w (w = 2 pi nu), sin(w)/w falling from sin(pi/16)/(pi/16) "
        "at nu = 1/32 to 2/pi at 0.25; levelled: a = -2/(sin(pi/16)/(pi/16) + 2/pi), "
        "h[2] = a/2",
    ),  # fmt: skip
    hand(
        "fir_equiripple.hilbert_all_zero_exact",
        {"num_taps": 6, "bands": [0, 0.2, 0.3, 0.5], "desired": [0, 0], "sample_rate": 1,
         "kind": "hilbert"},
        [0.0] * 6,
        "conventions: every desired value 0 gives zero taps, without iteration",
    ),  # fmt: skip
]


def anti(case_id, args, note=""):
    return certified(case_id, {"sample_rate": 1, **args}, note=note)


ANTI = [
    anti("fir_equiripple.hilbert_31",
         {"num_taps": 31, "bands": [0.05, 0.45], "desired": [1], "kind": "hilbert"}),
    anti("fir_equiripple.hilbert_30",
         {"num_taps": 30, "bands": [0.05, 0.5], "desired": [1], "kind": "hilbert"}),
    anti("fir_equiripple.hilbert_101",
         {"num_taps": 101, "bands": [0.02, 0.48], "desired": [1], "kind": "hilbert"},
         "; L = 50, so the library starts from the L = 25 design (reference scaling)"),
    anti("fir_equiripple.hilbert_stopbands",
         {"num_taps": 41, "bands": [0, 0.05, 0.1, 0.4, 0.45, 0.5], "desired": [0, 1, 0],
          "weights": [10, 1, 10], "kind": "hilbert"}),
    anti("fir_equiripple.differentiator_31",
         {"num_taps": 31, "bands": [0, 0.4], "desired": [1], "kind": "differentiator"}),
    anti("fir_equiripple.differentiator_32_full_band",
         {"num_taps": 32, "bands": [0, 0.5], "desired": [1], "kind": "differentiator"}),
    anti("fir_equiripple.differentiator_stopband_hz",
         {"num_taps": 40, "bands": [0, 1600, 2400, 4000], "desired": [2.5, 0],
          "weights": [1, 10], "sample_rate": 8000, "kind": "differentiator"}),
    anti("fir_equiripple.differentiator_61_density_8",
         {"num_taps": 61, "bands": [0.02, 0.47], "desired": [1], "kind": "differentiator",
          "grid_density": 8}),
    anti("fir_equiripple.filter_kind_explicit",
         {"num_taps": 21, "bands": [0, 0.1, 0.2, 0.5], "desired": [1, 0], "kind": "filter"}),
]  # fmt: skip

cases = [
    hand(
        "fir_equiripple.three_taps_analytic",
        {"num_taps": 3, "bands": LP, "desired": [1, 0], "sample_rate": 1},
        [s3 / 2, 0.5, s3 / 2],
        "hand: A = b + s*cos(2 pi nu), s = 2a; the error alternates at the four band edges "
        "(cos 2 pi nu = 1, cos(pi/5), -cos(pi/5), -1), all on the grid; so b = 1/2 and "
        "s = 1/(1 + cos(pi/5)), delta = 1/2 - s cos(pi/5)",
    ),
    hand(
        "fir_equiripple.two_taps_analytic",
        {"num_taps": 2, "bands": LP, "desired": [1, 0], "sample_rate": 1},
        [h2, h2],
        "hand: A = 2h cos(pi nu); L = 1 needs two alternation points, the inner band edges: "
        "1 - 2h cos(pi/10) = 2h cos(2pi/5), so h = 1/(2(cos(pi/10) + cos(2pi/5)))",
    ),
    hand(
        "fir_equiripple.two_taps_weighted",
        {
            "num_taps": 2,
            "bands": LP,
            "desired": [1, 0],
            "sample_rate": 1,
            "weights": [1, 10],
        },
        [h2w, h2w],
        "hand: as two_taps_analytic with stopband weight 10: 1 - 2h cos(pi/10) = 10*2h cos(2pi/5)",
    ),
    hand(
        "fir_equiripple.zero_delta_start",
        {
            "num_taps": 1,
            "bands": [0, 0.2, 0.25, 0.35, 0.4, 0.5],
            "desired": [0, 1, 0],
            "sample_rate": 1,
        },
        [0.5],
        "hand: a constant c minimizing max(|c|, |1 - c|) is 1/2; the first extremal set (the "
        "first and last grid points) lies only in the 0 bands, so the first delta is 0 and the "
        "old set's points must still count as extrema",
    ),
    hand(
        "fir_equiripple.one_tap",
        {"num_taps": 1, "bands": LP, "desired": [1, 0], "sample_rate": 1},
        [0.5],
        "hand: a constant c minimizing max(|1 - c|, |c|) is 1/2",
    ),
    hand(
        "fir_equiripple.one_tap_weighted",
        {
            "num_taps": 1,
            "bands": LP,
            "desired": [1, 0],
            "sample_rate": 1,
            "weights": [1, 3],
        },
        [0.25],
        "hand: |1 - c| = 3|c| gives c = 1/4",
    ),
    hand(
        "fir_equiripple.constant_exact",
        {"num_taps": 5, "bands": [0, 0.5], "desired": [2], "sample_rate": 1},
        [0, 0, 2, 0, 0],
        "conventions: odd num_taps with all desired equal is exact, 2 at the center",
    ),
    hand(
        "fir_equiripple.all_zero_even",
        {
            "num_taps": 4,
            "bands": [0, 0.2, 0.3, 0.5],
            "desired": [0, 0],
            "sample_rate": 1,
        },
        [0, 0, 0, 0],
        "conventions: every desired value 0 gives zero taps",
    ),
    certified(
        "fir_equiripple.lowpass_21",
        {
            "num_taps": 21,
            "bands": [0, 0.1, 0.2, 0.5],
            "desired": [1, 0],
            "sample_rate": 1,
        },
    ),
    certified(
        "fir_equiripple.lowpass_24_even",
        {
            "num_taps": 24,
            "bands": [0, 0.1, 0.2, 0.5],
            "desired": [1, 0],
            "sample_rate": 1,
        },
    ),
    certified(
        "fir_equiripple.lowpass_21_density_4",
        {
            "num_taps": 21,
            "bands": [0, 0.1, 0.2, 0.5],
            "desired": [1, 0],
            "sample_rate": 1,
            "grid_density": 4,
        },
    ),
    certified(
        "fir_equiripple.bandpass_31_hz",
        {
            "num_taps": 31,
            "bands": [0, 6000, 9000, 18000, 21000, 48000],
            "desired": [0, 1, 0],
            "sample_rate": 96000,
        },
    ),
    certified(
        "fir_equiripple.weighted_lowpass_37",
        {
            "num_taps": 37,
            "bands": [0, 0.1, 0.15, 0.5],
            "desired": [1, 0],
            "sample_rate": 1,
            "weights": [1, 100],
        },
    ),
    certified(
        "fir_equiripple.multiband_45",
        {
            "num_taps": 45,
            "bands": [0, 0.05, 0.1, 0.2, 0.25, 0.3, 0.35, 0.5],
            "desired": [0, 1, 0.5, 0],
            "sample_rate": 1,
            "weights": [2, 1, 1, 3],
        },
    ),
    certified(
        "fir_equiripple.highpass_33",
        {
            "num_taps": 33,
            "bands": [0, 0.3, 0.35, 0.5],
            "desired": [0, 1],
            "sample_rate": 1,
        },
    ),
    certified(
        "fir_equiripple.even_bandpass_not_from_dc",
        {
            "num_taps": 26,
            "bands": [1000, 4000, 6000, 12000],
            "desired": [0, 1],
            "sample_rate": 30000,
        },
    ),
    certified(
        "fir_equiripple.wide_transition_31",
        {"num_taps": 31, "bands": LP, "desired": [1, 0], "sample_rate": 1},
        {"abs": 1e-10, "rel": 1e-9},
        "; abs tolerance 1e-10: near the precision limit the taps are ill-determined in double "
        "(a 2e-11 change in them leaves the largest error the same to 7 digits)",
    ),
    err("fir_equiripple.zero_taps", {"num_taps": 0}, "conventions: 1 <= num_taps"),
    err(
        "fir_equiripple.too_many_taps",
        {"num_taps": 1002},
        "conventions: num_taps <= 1001",
    ),
    err(
        "fir_equiripple.odd_edges", {"bands": [0, 0.1, 0.2]}, "conventions: edge pairs"
    ),
    err(
        "fir_equiripple.no_bands",
        {"bands": [], "desired": []},
        "conventions: at least one band",
    ),
    err(
        "fir_equiripple.edges_touch",
        {"bands": [0, 0.1, 0.1, 0.5]},
        "conventions: bands do not touch",
    ),
    err(
        "fir_equiripple.edges_reversed",
        {"bands": [0, 0.2, 0.1, 0.5]},
        "conventions: increasing edges",
    ),
    err(
        "fir_equiripple.edge_negative",
        {"bands": [-0.1, 0.1, 0.2, 0.5]},
        "conventions: 0 <= b_0",
    ),
    err(
        "fir_equiripple.edge_above_nyquist",
        {"bands": [0, 0.1, 0.2, 0.6]},
        "conventions: <= fs/2",
    ),
    err(
        "fir_equiripple.desired_count",
        {"desired": [1]},
        "conventions: one desired value per band",
    ),
    err(
        "fir_equiripple.weights_count",
        {"weights": [1]},
        "conventions: one weight per band",
    ),
    err(
        "fir_equiripple.weight_zero",
        {"weights": [1, 0]},
        "conventions: positive weights",
    ),
    err(
        "fir_equiripple.weight_negative",
        {"weights": [-1, 1]},
        "conventions: positive weights",
    ),
    err(
        "fir_equiripple.density_zero",
        {"grid_density": 0},
        "conventions: 1 <= grid_density",
    ),
    err(
        "fir_equiripple.density_too_big",
        {"grid_density": 65},
        "conventions: grid_density <= 64",
    ),
    err(
        "fir_equiripple.sample_rate_zero",
        {"sample_rate": 0},
        "sample_rate must be positive",
    ),
    err(
        "fir_equiripple.even_taps_gain_at_nyquist",
        {"num_taps": 20, "bands": [0, 0.3, 0.35, 0.5], "desired": [0, 1]},
        "conventions: an even num_taps has zero gain at fs/2, so desired there must be 0",
    ),
    err(
        "fir_equiripple.too_few_grid_points",
        {"num_taps": 101, "bands": [0, 0.001, 0.002, 0.003]},
        "conventions: step 0.5/(16*51); two intervals per band gives 6 points, "
        "fewer than L + 1 = 52",
    ),
    *ANTI_HAND,
    *ANTI,
    err("fir_equiripple.kind_unknown", {"kind": "bandpass"}, "conventions: unknown kind"),
    err("fir_equiripple.hilbert_one_tap", {"num_taps": 1, "bands": [0.1, 0.4], "desired": [1],
        "kind": "hilbert"}, "conventions: 2 <= num_taps for the antisymmetric kinds"),
    err("fir_equiripple.hilbert_gain_at_zero", {"bands": [0, 0.4], "desired": [1],
        "kind": "hilbert"}, "conventions: antisymmetric A(0) = 0, so the target there must be 0"),
    err("fir_equiripple.hilbert_odd_gain_at_nyquist", {"bands": [0.1, 0.5], "desired": [1],
        "kind": "hilbert"}, "conventions: type III has A(fs/2) = 0"),
    err("fir_equiripple.differentiator_odd_to_nyquist", {"bands": [0, 0.5], "desired": [1],
        "kind": "differentiator"}, "conventions: type III has A(fs/2) = 0, but the target "
        "there is -pi"),
]  # fmt: skip

doc = {
    "schema": 1,
    "suite": "equiripple",
    "description": "Equiripple (Parks-McClellan) FIR design (conventions: FIR filters, "
    "Equiripple design).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "equiripple.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]


def same(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b, strict=True))
    if (
        isinstance(a, int | float)
        and isinstance(b, int | float)
        and not isinstance(a, bool)
    ):
        return abs(a - b) <= 1e-14 * max(1.0, abs(b))
    return a == b


if "--check" in sys.argv[1:]:
    if not same(
        json.loads(out.read_text(encoding="utf-8")), json.loads(json.dumps(doc))
    ):
        sys.exit(f"{out} is out of date: run python vectors/generators/equiripple.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(
    head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n"
)

# Self-check: the hand cases agree with the certified solver.
for c in cases[:5]:
    a = c["args"]
    got = remez(
        a["num_taps"], a["bands"], a["desired"], a["sample_rate"], a.get("weights")
    )[0]
    assert all(abs(g - e) < 1e-14 for g, e in zip(got, c["expected"], strict=True)), c[
        "id"
    ]
for c in ANTI_HAND[:3]:
    a = c["args"]
    got = remez(
        a["num_taps"], a["bands"], a["desired"], a["sample_rate"], None, 16, a["kind"]
    )[0]
    assert all(abs(g - e) < 1e-14 for g, e in zip(got, c["expected"], strict=True)), c["id"]
print(f"wrote {out} ({len(cases)} cases)")
