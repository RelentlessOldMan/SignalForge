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
        double top = 0;
        foreach (double v in samples)
            top = Math.Max(top, Math.Abs(v));
        int e = top >= 2 ? Math.ILogB(top) : 0; // scaled down only, past 2 (ADR 0633)
        double[] scaled = new double[samples.Length];
        for (int i = 0; i < scaled.Length; i++)
            scaled[i] = Math.ScaleB(samples[i], -e);
        Complex[] x = Fft(scaled);
        int n = x.Length;
        for (int k = 1; k < n; k++)
            x[k] *= 2 * k < n ? 2 : 2 * k == n ? 1 : 0;
        Complex[] z = Ifft(x);
        for (int i = 0; i < n; i++)
            z[i] = new Complex(Math.ScaleB(z[i].Real, e), Math.ScaleB(z[i].Imaginary, e));
        return z;
    }

    /// <summary><paramref name="z"/> times the power of 2 that brings its larger real or
    /// imaginary magnitude into [1, 2), zero unchanged, so no product of two values overflows
    /// or underflows; the scaling is exact and leaves the angle as it was (ADR 0633).</summary>
    internal static Complex ByPowerOf2(Complex z)
    {
        double top = Math.Max(Math.Abs(z.Real), Math.Abs(z.Imaginary));
        if (!(top > 0) || double.IsInfinity(top))
            return z;
        int e = Math.ILogB(top);
        return new Complex(Math.ScaleB(z.Real, -e), Math.ScaleB(z.Imaginary, -e));
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
            Complex w = ByPowerOf2(z[n + 1]) * Complex.Conjugate(ByPowerOf2(z[n]));
            f[n] = Math.Atan2(w.Imaginary, w.Real) * scale;
        }
        return f;
    }

    /// <summary>Moves every component by <paramref name="shift"/> Hz:
    /// <c>Re(z·e^{j2π·shift·n/fs})</c> with <c>z</c> the analytic signal (conventions: Frequency
    /// shifter; ADR 0301).</summary>
    /// <param name="samples">Real samples, finite, not empty.</param>
    /// <param name="shift">The shift in Hz, finite, of either sign.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] FrequencyShift(ReadOnlySpan<double> samples, double shift, double sampleRate)
    {
        if (!double.IsFinite(shift))
            throw new ArgumentOutOfRangeException(nameof(shift), "shift must be finite");
        Check.PositiveFinite(sampleRate, nameof(sampleRate));
        Complex[] z = AnalyticSignal(samples);
        var y = new double[z.Length];
        double w = 2 * Math.PI * shift;
        for (int n = 0; n < y.Length; n++)
        {
            double theta = w * (n / sampleRate);
            y[n] = (z[n].Real * Math.Cos(theta)) - (z[n].Imaginary * Math.Sin(theta));
        }
        return y;
    }
}
