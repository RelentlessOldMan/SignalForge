# 0001: Two independent implementations, one contract

Date: 2026-11-12. Status: accepted.

## Context

SignalForge exists in Python and C#. Either could wrap the other (pythonnet, an embedded Python), or
one could be generated from the other.

## Decision

Two separate implementations with no runtime dependency on each other. What they share is the
contract: `docs/conventions.md` and the test vectors in `vectors/`. Internals may differ (NumPy
vectorization in Python, spans and loops in C#).

## Consequences

- Each can be installed and used alone.
- Every feature costs two implementations. In exchange, each implementation checks the other, and
  the vectors (with independently derived expected values) check both.
- A convention ambiguity shows up as a vector that one language fails, which is the point.
