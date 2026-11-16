# ADR 0105: Noise figure by the Y-factor method

Status: accepted, 2026-11-16.

## Context

The brief lists noise figure among the RF measurements. The usual bench method is the Y-factor
method. A noise source is switched between hot and cold. The output noise power is measured for
each state, and the device's own noise is found from their ratio `Y`. The arithmetic is short,
but several forms are in use. A common one assumes the cold source sits at the reference
temperature, and it is wrong when the cold load is warmer or cooler than that. So the form has
to be fixed here.

## Decision

- Python `noise_figure_y_factor(hot_power, cold_power, enr_db, *, cold_temperature=290.0)`, and
  C# `Measurements.NoiseFigureYFactor(hotPower, coldPower, enrDb, coldTemperature = 290)`. Both
  return a `NoiseFigure` result with these fields:
  - `y_factor`
  - `noise_factor`
  - `noise_figure_db`
  - `noise_temperature`
- The two powers are linear, in any one unit, since only their ratio is used. `enr_db` is the
  source's excess noise ratio, `ENR = (T_h − T₀)/T₀`, as calibration tables give it.
  `cold_temperature` is in kelvin.
- The reference temperature is fixed at `T₀ = 290 K`, the IEEE standard value. It is not an
  argument.
- With `Y = hot/cold` and `T_h = T₀(1 + ENR)`, the device's noise temperature is
  `T_e = (T_h − Y·T_c)/(Y − 1)`. That gives:
  - `F = 1 + T_e/T₀ = (ENR − Y·(T_c/T₀ − 1))/(Y − 1)`
  - `noise_figure_db = 10·log10 F`
  - `noise_temperature = T₀(F − 1)`

  When `T_c = T₀`, this reduces to the familiar `F = ENR/(Y − 1)`.
- Arguments:
  - `cold_power` must be finite and positive.
  - `hot_power` must be finite and greater than `cold_power`, so `Y > 1`.
  - `enr_db` must be finite.
  - `cold_temperature` must be finite and positive.

  A measurement whose `F` comes out non-positive or not finite is `invalid_argument`. That
  happens with a cold load hot enough to swamp the ENR, or a ratio that overflows. `0 < F < 1`
  (a negative noise temperature) is returned as it is, because it is what the numbers say, and
  a caller checking a bench result needs to see it.
- No second-stage correction. Removing the noise contribution of the meter (Friis) is a
  separate cascade calculation and gets its own function later:
  [ADR 0106](0106-noise-figure-cascade.md).

## Consequences

- The vectors are hand derivations. A textbook case (ENR 15 dB, Y 10 dB) gives `F = 10^1.5/9`,
  `NF = 15 − 10·log10 9 ≈ 5.46 dB`. Cold loads at `T₀/2`, `2T₀` and 77 K are worked from the
  formula, and the rejected arguments are covered.
- The tests also simulate a device with a known `T_e`. They set `P = k(T_source + T_e)` for each
  state, and check that the measurement returns `T_e`.
