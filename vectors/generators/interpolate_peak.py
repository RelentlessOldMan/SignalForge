"""Writes vectors/cases/interpolate_peak.json, stdlib only.

Each case samples a peak whose vertex is known analytically (conventions: Spectra, Peak
interpolation; ADR 0136):

- a parabola `h − (k − μ)²`, for the linear scale;
- a Gaussian `h·exp(−(k − μ)²/(2σ²))`, whose dB is a parabola, for the dB scale.

The expected values are the vertex `μ` and the height `h`, not a run of the fit.

Run from the repo root: python vectors/generators/interpolate_peak.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def case(cid, freqs, psd, index, want, why, scale=None):
    args = {"frequencies": freqs, "psd": psd, "index": index}
    if scale is not None:
        args["scale"] = scale
    frequency, height, offset = want
    cases.append({"id": f"interpolate_peak.{cid}", "op": "interpolate_peak", "args": args,
                  "expected": {"frequency": frequency, "height": height, "offset": offset},
                  "tol": TOL, "source": why})


def err(cid, args, why):
    cases.append({"id": f"interpolate_peak.{cid}", "op": "interpolate_peak", "args": args,
                  "error": "invalid_argument", "source": why})


def parabola(h, mu, n):
    return [h - (k - mu) ** 2 for k in range(n)]


def gaussian(h, mu, sigma, n):
    return [h * math.exp(-((k - mu) ** 2) / (2 * sigma**2)) for k in range(n)]


K5 = [0.0, 1.0, 2.0, 3.0, 4.0]
case("parabola_right", K5, parabola(10.0, 2.3, 5), 2, (2.3, 10.0, 0.3),
     "10 - (k - 2.3)^2 on the linear scale: vertex 2.3, height 10", scale="linear")
case("parabola_left", K5, parabola(10.0, 1.75, 5), 2, (1.75, 10.0, -0.25),
     "10 - (k - 1.75)^2, exact in binary: vertex 1.75, height 10", scale="linear")
H100 = [100.0 * k for k in range(10)]
case("gaussian_db", H100, gaussian(4.0, 5.2, 1.5, 10), 5, (520.0, 4.0, 0.2),
     "4 exp(-(k - 5.2)^2/4.5) on 100 Hz bins, dB scale: vertex 520 Hz, height 4", scale="db")
case("gaussian_default", H100, gaussian(4.0, 4.6, 1.5, 10), 5, (460.0, 4.0, -0.4),
     "the default scale is dB: 4 exp(-(k - 4.6)^2/4.5), vertex 460 Hz, height 4")
case("symmetric", [0.0, 1.0, 2.0], [1.0, 3.0, 1.0], 1, (1.0, 3.0, 0.0),
     "equal neighbours: offset 0, height 3", scale="linear")
case("two_top_bins", K5[:4], [1.0, 2.0, 2.0, 1.0], 1, (1.5, 2 ** (9 / 8), 0.5),
     "dB values 0, D, D with D = 10 log10 2: offset 1/2, vertex D + D/8, so height 2^(9/8)")
case("two_top_linear", K5[:4], [1.0, 2.0, 2.0, 1.0], 1, (1.5, 2.125, 0.5),
     "linear 1, 2, 2: curvature -1, offset 1/2, height 2 + 1/8", scale="linear")
case("zero_neighbour", [0.0, 1.0, 2.0], [0.0, 1.0, 0.5], 1, (1.0 + 1 / 6, 1 + 1 / 48, 1 / 6),
     "linear 0, 1, 1/2 lie on -3k^2/4 + 7k/4: vertex 7/6, height 49/48", scale="linear")

T = {"frequencies": [0.0, 1.0, 2.0, 3.0], "psd": [1.0, 2.0, 3.0, 2.0]}
err("first_bin", {**T, "index": 0}, "the first bin has one neighbour")
err("last_bin", {**T, "index": 3}, "the last bin has one neighbour")
err("past_end", {**T, "index": 9}, "index past the end")
err("not_a_maximum", {**T, "index": 1}, "bin 1 is lower than bin 2")
err("flat", {"frequencies": [0.0, 1.0, 2.0], "psd": [2.0, 2.0, 2.0], "index": 1},
    "three equal bins have no curvature")
err("zero_in_db", {"frequencies": [0.0, 1.0, 2.0], "psd": [0.0, 1.0, 0.5], "index": 1},
    "a zero bin has no dB value")
err("unknown_scale", {**T, "index": 2, "scale": "log"}, 'scale must be "db" or "linear"')

doc = {
    "schema": 1,
    "suite": "interpolate_peak",
    "description": "Peak interpolation (conventions: Spectra, Peak interpolation; ADR 0136).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "interpolate_peak.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/interpolate_peak.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
