# ADR 0073: A phase loop inside the equalizer

Status: accepted, 2026-11-13

## Context

With a short preamble the link's frequency estimate (ADRs 0070, 0071) is 0.05 to 0.6 Hz off. Over
6000 symbols at 1 kHz that turns the constellation through part of a cycle or more. The
equalizer's taps can follow a slow turn, but at step 0.1 they follow it badly, and the decisions
fail (ADR 0072). The link's carrier loops (ADR 0046) run on the symbols without the equalizer, and
there the equalizer already takes the symbols, so they cannot be chained: the feedback taps
subtract past decisions in the unrotated frame.

## Decision

`dfe_equalizer` gains `phase_loop_gains=(kp, ki)` [none]: a second-order decision-directed loop
inside the equalizer, turning only the forward part.

- The output is `y = v·e^{−jθ} + Σ b_j·p_j`, with `v` the forward sum. The feedback taps act on
  past references, which are already in the decision frame, so they are not turned.
- The forward taps are updated with the error turned back, `e·e^{jθ}`, so they adapt in their own
  (unrotated) frame and do not chase the turn.
- The phase error is the angle between the turned forward part and what it should have been,
  `d − Σ b_j·p_j` (the feedback part before the update, the same one that formed `y`). Then
  `ν ← ν + ki·φ` and `θ ← θ + kp·φ + ν`, the loop of ADR 0043.
- With gains `(0, 0)` it is the equalizer without the loop, bit for bit.
- The link gains `equalizer_loop_gains` [none], passed through, only with `equalizer_taps`.
- No default gains: without them every existing result stays the same.

## Consequences

Measured in the link on `1 + 0.9·z⁻¹` (11 forward and 2 feedback taps, least-squares start, 6000
symbols, a 5 Hz offset, seeds 80–82), BER:

| gains | QPSK 8 dB, P = 100 | P = 200 | 16-QAM 14 dB, P = 100 | P = 200 | 8-PSK 12 dB, P = 100 | P = 200 |
|---|---|---|---|---|---|---|
| none | 0.01–0.55 | 0.0001–0.0003 | 0.002–0.007 | 0.008–0.06 | 0.48–0.49 | 0–0.002 |
| (0.01, 0.0001) | 0.0003–0.0014 | 0.0003–0.0007 | 0–0.0002 | 0–0.0001 | 0.001–0.32 | 0.0001–0.0003 |
| (0.02, 0.0001) | 0.0003–0.0013 | 0.0003–0.0007 | 0–0.0006 | 0–0.0001 | 0.0008–0.0013 | 0.0001–0.0002 |
| (0.02, 0.0002) | 0.0003–0.0011 | 0.0003–0.0007 | 0–0.0006 | 0–0.0002 | 0.0005–0.0008 | 0.0002–0.06 |
| (0.03, 0.0003) | 0.0001–0.0008 | 0.0004–0.0013 | 0–0.0006 | 0–0.0002 | 0.0004–0.0007 | 0.0002–0.006 |

- `(0.02, 0.0001)` decodes every run above; it is the gain the tests and link configs use.
- The single bad runs are 8-PSK cycle slips: its points are only π/4 apart, and a decision loop
  can lock a step off. A slip costs a burst of errors and is not detected; the frame has no pilots
  to resolve it.
- With the unit-impulse start the loop alone (at `(0.02, 0.0002)`) also rescues QPSK and 8-PSK
  at `P = 100` (0.001–0.004) but not 16-QAM, whose decisions fail before the taps converge.
- One `atan2`, a `cos` and a `sin` per symbol, small beside the taps.
