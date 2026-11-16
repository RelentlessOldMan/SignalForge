using System.Numerics;

namespace SignalForge;

public static partial class Spectral
{
    /// <summary>The analytic signal <c>ifft(fft(x)·W)</c> with Marple's weights: 1 at DC and at
    /// N/2, 2 for the positive bins, 0 for the negative (conventions: Analytic signal;
    /// ADR 0185).</summary>
    /// <param name="samples">Real samples, finite, not empty.</param>
    /// <returns>The analytic signal, as long as the input; its real part is the input up to
    /// rounding.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Complex[] AnalyticSignal(ReadOnlySpan<double> samples)
    {
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        Complex[] x = Fft(samples);
        int n = x.Length;
        for (int k = 1; k < n; k++)
            x[k] *= 2 * k < n ? 2 : 2 * k == n ? 1 : 0;
        return Ifft(x);
    }
}
