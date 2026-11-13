# 0004: NumPy is approved as a runtime dependency, GCC runtime exception included

Date: 2026-11-12. Status: accepted (approved by the user, 2026-11-12).

## Context

The license rule allows only MIT, BSD-2, BSD-3, Apache-2.0 and ISC. The rule behind the list:
**SignalForge must always be shippable commercially, under MIT, with no restrictions. Nothing we
use may ever require any SignalForge code to be licensed under the GPL or any other copyleft
license.**

NumPy is BSD-3-Clause, but its binary wheels bundle `libscipy_openblas`, a compiled library made of
OpenBLAS (BSD-3), LAPACK (BSD-3-Clause-Open-MPI) and the GCC Fortran runtime, which is
**GPL-3.0-or-later WITH GCC-exception-3.1**. The Windows wheel also bundles Microsoft's `msvcp140.dll`,
which Microsoft permits to be redistributed. All of this is listed in the wheel's own
`dist-info/licenses/LICENSE.txt` (checked on numpy 2.5.4).

## Why this is acceptable

- The GCC Runtime Library Exception exists so that code compiled with GCC can be distributed under
  any terms, including proprietary ones, even though the GCC runtime is linked into it. That is how
  OpenBLAS stays BSD with the runtime inside it.
- SignalForge does not compile against or link that library. It only calls NumPy's Python API. There
  is no path by which the GPL reaches SignalForge's code.
- **Shipping SignalForge as a package that depends on NumPy** redistributes no NumPy files at all:
  users install NumPy themselves. No obligations.
- **Shipping a bundle that contains NumPy** (installer, frozen executable, container image) means
  redistributing NumPy's files, which requires carrying NumPy's license notices, i.e. its
  `LICENSE.txt`, the same as for any BSD dependency. SignalForge's own license is unaffected.

Keeping NumPy test-only was considered and rejected: it would mean reimplementing array arithmetic in
pure Python to avoid an obligation that does not exist.

## Decision

- NumPy is approved as the Python runtime dependency.
- Any bundled distribution that includes NumPy carries NumPy's `LICENSE.txt` (and its bundled
  licenses) alongside our own.
- The approval covers this specific case, the GCC Runtime Library Exception on compiler runtime
  libraries inside a permissively licensed package. It is not a general approval of GPL code.
  Anything else GPL-labelled, or any change in what NumPy bundles, is checked again.
- SciPy gets the same check when it is proposed; its wheels bundle the same runtime, so the same
  reasoning is expected to apply.
- The C# library stays free of package dependencies, so it is unaffected.
