# ADR 0075: Pilots that correct the equalizer's cycle slips

Status: accepted, 2026-11-13

## Context

The phase loop inside the equalizer (ADR 0073) is decision-directed, so it can lock a symmetry
step off: π/4 for 8-PSK, π/2 for the square constellations. The preamble resolves the ambiguity
once, at the start; after a slip every decision is turned and the rest of the frame is lost. Over
ten seeds (80–89, 8-PSK at 12 dB, a 100-symbol preamble, the 0.9 echo, the least-squares start)
a slip costs 0.32–0.63 BER in five runs at gains `(0.01, 0.0001)` and in one at `(0.02, 0.0001)`
(seed 84), the gain ADR 0073 called safe from three seeds. A loop cannot tell a slip from a lock
by its decisions alone; known symbols in the data can.

## Decision

- `dfe_equalizer` gains `pilot_interval` [none] and `pilots`, both or neither, and
  `slip_window` [2]. With `T` training symbols and `N` outputs, output `n ≥ T` is a pilot when
  `(n − T) mod K = K − 1` (`K = pilot_interval`), so pilot `j` is output `T + (j + 1)·K − 1`;
  `pilots` holds the `⌊(N − T)/K⌋` known symbols.
- A pilot is that output's reference, in place of the decision.
- Slip correction: the outputs at the pilots, each times the conjugate of its pilot, are summed.
  After every `slip_window` pilots, `θ` steps by the multiple of the decision's symmetry step
  (π/2; π/4 for `"psk8"`) nearest to the sum's angle, and the sum starts again. A correct lock
  gives a sum near angle 0 and no step.
- Pilots need `phase_loop_gains` (the correction turns the loop's `θ`) and `decision` (its
  symmetry gives the step).
- The link gains `pilot_interval` [none], only with `equalizer_loop_gains`: every `K`-th data
  symbol after the preamble is a pilot, known to the receiver, and is left out of the bit errors
  and the EVM like the preamble. The window is the default 2.

## Consequences

Measured on the same ten seeds, BER with a pilot every 20 symbols (5 % of the data):

| gains | no pilots, P = 100 | pilots, window 2 | window 1 |
|---|---|---|---|
| (0.01, 0.0001) | 0.0013–0.63, five slips | 0.0012–0.0099 | 0.0013–0.0102 |
| (0.02, 0.0002) | 0.0004–0.33, one slip | 0.0004–0.0065 | 0.0004–0.0041 |
| (0.02, 0.0001) | 0.0003–0.33, one slip | 0.0003–0.0056 | 0.0003–0.0049 |

- A window of one pilot corrects on noise: runs that never slipped get worse (0.0002 to 0.0014 at
  `P = 200`). A window of two left every run that did not slip unchanged.
- What is left after a slip is the burst before it is caught, about `K·W` symbols, plus the
  equalizer settling after the step. Shorter intervals catch it sooner at more overhead.
- Using the pilots only to detect slips, with decisions as their references, measured the same.
  A known symbol is the better reference, so it is used.
- The transmitted frame does not change: the link's symbols are a known PRBS, and a pilot is a
  position whose symbol the receiver is allowed to use.
