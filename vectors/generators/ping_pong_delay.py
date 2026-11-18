"""Writes vectors/cases/ping_pong_delay.json, stdlib only.

Ping-pong delay (conventions: Ping-pong delay; ADR 0275): echo k >= 1 arrives k*D samples late
with gain g^(k-1), odd k on the left and even k on the right. The expected values are that echo
sum, not the recursion the implementations run.

Run from the repo root: python vectors/generators/ping_pong_delay.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def echoes(x, d, g, parity):
    out = []
    for n in range(len(x)):
        s = 0.0
        k = 1
        while k * d <= n:
            if k % 2 == parity:
                s += g ** (k - 1) * x[n - k * d]
            k += 1
        out.append(s)
    return out


def add(cid, x, d, g, mix, why):
    a, b = echoes(x, d, g, 1), echoes(x, d, g, 0)
    left = [v * (1 - mix) + e * mix for v, e in zip(x, a)]
    right = [v * (1 - mix) + e * mix for v, e in zip(x, b)]
    cases.append({"id": f"ping_pong_delay.{cid}", "op": "ping_pong_delay",
                  "args": {"samples": x, "delay": d, "feedback": g, "mix": mix},
                  "expected": {"left": left, "right": right}, "tol": TOL, "source": why})
    return left, right


imp = [1.0] + [0.0] * 12
left, right = add("impulse", imp, 3, 0.5, 1.0, "impulse, D 3, g 1/2, wet: 1 at 3 and 1/4 at 9 "
                  "on the left, 1/2 at 6 and 1/8 at 12 on the right")
assert left == [0, 0, 0, 1, 0, 0, 0, 0, 0, 0.25, 0, 0, 0]
assert right == [0, 0, 0, 0, 0, 0, 0.5, 0, 0, 0, 0, 0, 0.125]
add("negative_feedback", imp, 2, -0.75, 0.5, "impulse, D 2, g -3/4, mix 1/2")
add("music", [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6, 0.5, 1.3, -0.1, 0.05, 0.6, -0.2],
    2, 0.6, 0.35, "a short signal, D 2, g 0.6, mix 0.35")
add("short", [0.5, -1.0], 5, 0.9, 1.0, "delay past the end: no echoes")
add("dry", [0.5, -1.0, 2.0], 1, 0.3, 0.0, "mix 0: both sides are the dry signal")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0], "delay": 1, "feedback": 0.5, "mix": 0.5}
    base.update(args)
    cases.append({"id": f"ping_pong_delay.{cid}", "op": "ping_pong_delay", "args": base,
                  "error": "invalid_argument", "source": why})


err("delay_zero", "delay must be at least 1", delay=0)
err("feedback_one", "feedback must have magnitude below 1", feedback=1.0)
err("feedback_minus_one", "feedback must have magnitude below 1", feedback=-1.0)
err("mix_high", "mix must be at most 1", mix=1.5)
err("empty", "samples must not be empty", samples=[])

doc = {
    "schema": 1,
    "suite": "ping_pong_delay",
    "description": "Ping-pong delay (conventions: Ping-pong delay; ADR 0275).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "ping_pong_delay.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/ping_pong_delay.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
