# ADR 0275: Ping-pong delay

Status: accepted, 2026-11-17.

## Context

A ping-pong delay sends a mono signal's echoes to alternate sides: the first echo on the left,
the second on the right, and so on. Each bounce is quieter by the feedback gain. It is two delay
lines that feed each other.

## Decision

- **The API.**
  - Python: `ping_pong_delay(samples, delay, feedback, mix)` in `dsp`, returning a `LeftRight`
    (ADR 0264).
  - C#: `Dsp.PingPongDelay(samples, delay, feedback, mix)`, returning a `LeftRight`.
  - Real mono input only.
- **The value.** With `D = delay`, `g = feedback` and every signal 0 before time 0:
  - `a[n] = x[n − D] + g·b[n − D]` and `b[n] = g·a[n − D]`, evaluated in that order.
  - Echo `k ≥ 1` arrives `k·D` samples late with gain `g^(k−1)`; odd `k` in `a`, even `k` in
    `b`.
  - `left = x·(1 − mix) + a·mix` and `right = x·(1 − mix) + b·mix`.
- **The rules.**
  - `delay` must be an integer `≥ 1`.
  - `feedback` must be finite with `|feedback| < 1`, so the echoes die away.
  - `mix` must be finite and in `[0, 1]`.
  - The samples must be real, finite and at least one.
- **The output** has the input's length; echoes past the end are dropped.

## Consequences

- **Vectors.**
  - The expected values come from the echo sum `Σ g^(k−1)·x[n − k·D]`, not the recursion.
  - The tolerance is `abs 1e-14, rel 1e-13`.
- **Not here.** A stereo input, a different delay per side, and filtering in the loop would
  each be a later slice.
