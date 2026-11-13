# 0002: One package per language until a module earns its own

Date: 2026-11-12. Status: accepted.

## Context

The brief lists about fourteen conceptual modules (Core, Numerics, Waveforms, DSP, …). Fourteen
.NET projects and fourteen Python distributions on day one would be mostly empty scaffolding.

## Decision

One Python package (`signalforge`) and one .NET assembly (`SignalForge`), with the modules as
submodules / namespaces. A module splits into its own package or project when it brings a dependency
the rest must not carry (hardware, plotting, a native library) or needs its own release cadence
(standards).

## Consequences

- Fewer moving parts while the core settles.
- Module boundaries are enforced by review, not by the build, until the split. Keep imports one-way:
  Core ← Units ← Waveforms/Measurements/Modulation/Metrics; nothing low imports anything high.
