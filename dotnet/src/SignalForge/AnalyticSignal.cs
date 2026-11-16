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

    /// <summary>The instantaneous frequency <c>fs/(2π)·arg(z[n+1]·conj z[n])</c> in Hz, with
    /// <c>z</c> the analytic signal (conventions: Instantaneous frequency; ADR 0187).</summary>
    /// <param name="samples">Real samples, finite, at least two.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <returns><c>N − 1</c> values in Hz, in <c>(−fs/2, fs/2]</c>.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] InstantaneousFrequency(ReadOnlySpan<double> samples, double sampleRate)
    {
        Check.PositiveFinite(sampleRate, nameof(sampleRate));
        Complex[] z = AnalyticSignal(samples);
        if (z.Length < 2)
            throw new ArgumentException("samples must hold at least two values", nameof(samples));
        var f = new double[z.Length - 1];
        double scale = sampleRate / (2 * Math.PI);
        for (int n = 0; n < f.Length; n++)
        {
            Complex w = z[n + 1] * Complex.Conjugate(z[n]);
            f[n] = Math.Atan2(w.Imaginary, w.Real) * scale;
        }
        return f;
    }
}
