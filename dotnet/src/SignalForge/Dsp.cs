using System.Numerics;

namespace SignalForge;

/// <summary>Convolution, upsampling and root-raised-cosine pulse shaping. Definitions in
/// docs/conventions.md (Pulse shaping).</summary>
public static class Dsp
{
    /// <summary>Full linear convolution y[n] = Σ h[k]·x[n−k], length len(x) + len(h) − 1.</summary>
    public static double[] Convolve(ReadOnlySpan<double> x, ReadOnlySpan<double> h)
    {
        CheckNonEmpty(x.Length, h.Length);
        var y = new double[x.Length + h.Length - 1];
        for (int i = 0; i < x.Length; i++)
            for (int k = 0; k < h.Length; k++)
                y[i + k] += x[i] * h[k];
        return y;
    }

    /// <summary>Full linear convolution of complex samples with real taps.</summary>
    public static Complex[] Convolve(ReadOnlySpan<Complex> x, ReadOnlySpan<double> h)
    {
        CheckNonEmpty(x.Length, h.Length);
        var y = new Complex[x.Length + h.Length - 1];
        for (int i = 0; i < x.Length; i++)
            for (int k = 0; k < h.Length; k++)
                y[i + k] += x[i] * h[k];
        return y;
    }

    /// <summary>Full linear convolution of complex samples with complex taps.</summary>
    public static Complex[] Convolve(ReadOnlySpan<Complex> x, ReadOnlySpan<Complex> h)
    {
        CheckNonEmpty(x.Length, h.Length);
        var y = new Complex[x.Length + h.Length - 1];
        for (int i = 0; i < x.Length; i++)
            for (int k = 0; k < h.Length; k++)
                y[i + k] += x[i] * h[k];
        return y;
    }

    /// <summary>Each sample followed by <paramref name="factor"/> − 1 zeros.</summary>
    public static double[] Upsample(ReadOnlySpan<double> x, int factor)
    {
        CheckUpsample(x.Length, factor);
        var y = new double[x.Length * factor];
        for (int i = 0; i < x.Length; i++)
            y[i * factor] = x[i];
        return y;
    }

    /// <summary>Each complex sample followed by <paramref name="factor"/> − 1 zeros.</summary>
    public static Complex[] Upsample(ReadOnlySpan<Complex> x, int factor)
    {
        CheckUpsample(x.Length, factor);
        var y = new Complex[x.Length * factor];
        for (int i = 0; i < x.Length; i++)
            y[i * factor] = x[i];
        return y;
    }

    /// <summary>Root-raised-cosine taps, span·sps + 1 of them, scaled to unit energy (Σh² = 1).</summary>
    /// <param name="beta">Roll-off, 0 to 1.</param>
    /// <param name="samplesPerSymbol">Samples per symbol, at least 1.</param>
    /// <param name="spanSymbols">Filter length in symbols, even and at least 2.</param>
    public static double[] RrcTaps(double beta, int samplesPerSymbol, int spanSymbols)
    {
        if (!(beta >= 0 && beta <= 1))
            throw new ArgumentOutOfRangeException(nameof(beta), beta, "must be in [0, 1]");
        ArgumentOutOfRangeException.ThrowIfLessThan(samplesPerSymbol, 1);
        if (spanSymbols < 2 || spanSymbols % 2 != 0)
            throw new ArgumentOutOfRangeException(nameof(spanSymbols), spanSymbols, "must be even and at least 2");
        int n = checked(spanSymbols * samplesPerSymbol + 1);
        var h = new double[n];
        double energy = 0;
        for (int i = 0; i < n; i++)
        {
            double t = (i - (n - 1) / 2.0) / samplesPerSymbol;
            if (t == 0)
            {
                h[i] = 1 - beta + 4 * beta / Math.PI;
            }
            else if (Math.Abs(4 * beta * Math.Abs(t) - 1) < 1e-9)
            {
                double a = Math.PI / (4 * beta);
                h[i] = beta / Math.Sqrt(2) * ((1 + 2 / Math.PI) * Math.Sin(a) + (1 - 2 / Math.PI) * Math.Cos(a));
            }
            else
            {
                double num = Math.Sin(Math.PI * t * (1 - beta)) + 4 * beta * t * Math.Cos(Math.PI * t * (1 + beta));
                double q = 4 * beta * t;
                h[i] = num / (Math.PI * t * (1 - q * q));
            }
            energy += h[i] * h[i];
        }
        double scale = 1 / Math.Sqrt(energy);
        for (int i = 0; i < n; i++)
            h[i] *= scale;
        return h;
    }

    /// <summary>Convolve(Upsample(symbols, sps), taps); symbol k peaks at k·sps + (N−1)/2.</summary>
    /// <param name="symbols">Symbols, at least one.</param>
    /// <param name="taps">Shaping filter taps, at least one.</param>
    /// <param name="samplesPerSymbol">Samples per symbol, at least 1.</param>
    public static Complex[] PulseShape(ReadOnlySpan<Complex> symbols, ReadOnlySpan<double> taps, int samplesPerSymbol) =>
        Convolve(Upsample(symbols, samplesPerSymbol), taps);

    /// <summary>Real-symbol form of <see cref="PulseShape(ReadOnlySpan{Complex}, ReadOnlySpan{double}, int)"/>.</summary>
    /// <param name="symbols">Symbols, at least one.</param>
    /// <param name="taps">Shaping filter taps, at least one.</param>
    /// <param name="samplesPerSymbol">Samples per symbol, at least 1.</param>
    public static double[] PulseShape(ReadOnlySpan<double> symbols, ReadOnlySpan<double> taps, int samplesPerSymbol) =>
        Convolve(Upsample(symbols, samplesPerSymbol), taps);

    private static void CheckNonEmpty(int nx, int nh)
    {
        if (nx == 0 || nh == 0)
            throw new ArgumentException("convolution needs non-empty inputs");
    }

    private static void CheckUpsample(int n, int factor)
    {
        if (n == 0)
            throw new ArgumentException("upsample needs at least one sample");
        ArgumentOutOfRangeException.ThrowIfLessThan(factor, 1);
        _ = checked(n * factor);
    }
}
