using System.Numerics;

namespace SignalForge;

/// <summary>Block synchronization estimators: symbol timing, QPSK carrier frequency and phase.
/// Definitions in docs/conventions.md (Synchronization).</summary>
public static class Sync
{
    /// <summary>Oerder–Meyr symbol timing estimate in samples, in [0, sps): the phase of the
    /// symbol-rate line in |y|².</summary>
    /// <param name="samples">Matched-filter output, at least one sample, all finite.</param>
    /// <param name="samplesPerSymbol">Samples per symbol, at least 2.</param>
    public static double TimingOffset(ReadOnlySpan<Complex> samples, int samplesPerSymbol)
    {
        ArgumentOutOfRangeException.ThrowIfLessThan(samplesPerSymbol, 2);
        CheckFinite(samples, 1, nameof(samples));
        Complex s = Complex.Zero;
        for (int n = 0; n < samples.Length; n++)
        {
            Complex y = samples[n];
            double p = y.Real * y.Real + y.Imaginary * y.Imaginary;
            s += p * Complex.FromPolarCoordinates(1, -2 * Math.PI * (n % samplesPerSymbol) / samplesPerSymbol);
        }
        double tau = -samplesPerSymbol * Arg(s) / (2 * Math.PI);
        if (tau < 0)
            tau += samplesPerSymbol;
        return tau >= samplesPerSymbol ? 0 : tau;
    }

    /// <summary>Carrier frequency offset of QPSK symbols in Hz, in (−Rs/8, Rs/8], from the mean phase
    /// step of z⁴.</summary>
    /// <param name="symbols">One complex value per symbol, at least two, all finite.</param>
    /// <param name="symbolRate">Symbol rate in Hz, positive and finite.</param>
    public static double QpskFrequencyOffset(ReadOnlySpan<Complex> symbols, double symbolRate)
    {
        Check.PositiveFinite(symbolRate, nameof(symbolRate));
        CheckFinite(symbols, 2, nameof(symbols));
        Complex s = Complex.Zero, prev = Fourth(symbols[0]);
        for (int k = 1; k < symbols.Length; k++)
        {
            Complex w = Fourth(symbols[k]);
            s += w * Complex.Conjugate(prev);
            prev = w;
        }
        return Arg(s) * symbolRate / (8 * Math.PI);
    }

    /// <summary>Carrier phase of QPSK symbols in radians, in (−π/4, π/4]; the true phase is this
    /// plus a multiple of π/2.</summary>
    /// <param name="symbols">One complex value per symbol, at least one, all finite.</param>
    public static double QpskPhaseOffset(ReadOnlySpan<Complex> symbols)
    {
        CheckFinite(symbols, 1, nameof(symbols));
        Complex s = Complex.Zero;
        foreach (var z in symbols)
            s += Fourth(z);
        return Arg(-s) / 4;
    }

    private static Complex Fourth(Complex z)
    {
        Complex z2 = z * z;
        return z2 * z2;
    }

    /// <summary>Phase in (−π, π]; 0 for an exact zero.</summary>
    private static double Arg(Complex s)
    {
        if (s == Complex.Zero)
            return 0;
        double a = Math.Atan2(s.Imaginary, s.Real);
        return a == -Math.PI ? Math.PI : a;
    }

    private static void CheckFinite(ReadOnlySpan<Complex> x, int minimum, string name)
    {
        if (x.Length < minimum)
            throw new ArgumentException($"needs at least {minimum} value(s)", name);
        foreach (var z in x)
            if (!double.IsFinite(z.Real) || !double.IsFinite(z.Imaginary))
                throw new ArgumentException("values must be finite", name);
    }
}
