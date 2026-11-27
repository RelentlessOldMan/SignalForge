using System.Numerics;

namespace SignalForge;

public static partial class Dsp
{
    /// <summary>RMS of the <paramref name="length"/> real samples ending at each sample, zeros
    /// before the start (conventions: Moving RMS; ADR 0239).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="length">The window length <c>N</c>, at least 1.</param>
    /// <returns>One RMS value per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] MovingRms(ReadOnlySpan<double> samples, int length) =>
        MovingRms((ReadOnlySpan<Complex>)ToComplexArray(samples), length);

    /// <summary>RMS of the <paramref name="length"/> complex samples ending at each sample, zeros
    /// before the start (conventions: Moving RMS; ADR 0239).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="length">The window length <c>N</c>, at least 1.</param>
    /// <returns>One RMS value per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] MovingRms(ReadOnlySpan<Complex> samples, int length)
    {
        if (length < 1)
            throw new ArgumentOutOfRangeException(nameof(length), "length must be at least 1");
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        var a = new double[samples.Length];
        for (int n = 0; n < samples.Length; n++)
        {
            Complex v = samples[n];
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("samples must be finite", nameof(samples));
            a[n] = Complex.Abs(v);
        }
        var y = new double[samples.Length];
        for (int n = 0; n < samples.Length; n++)
        {
            // each window at the power of 2 of its largest magnitude, exactly (ADR 0634)
            int start = Math.Max(0, n - length + 1);
            double top = 0;
            for (int k = start; k <= n; k++)
                top = Math.Max(top, a[k]);
            int e = top > 0 ? Math.ILogB(top) : 0;
            double acc = 0;
            for (int k = start; k <= n; k++)
            {
                double s = Math.ScaleB(a[k], -e);
                acc += s * s;
            }
            y[n] = Math.ScaleB(Math.Sqrt(acc / length), e);
        }
        return y;
    }

    /// <summary>Mean of the <paramref name="length"/> real samples ending at each sample, zeros
    /// before the start (conventions: Moving average; ADR 0241).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="length">The window length <c>N</c>, at least 1.</param>
    /// <returns>One mean per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] MovingAverage(ReadOnlySpan<double> samples, int length) =>
        [.. MovingAverage((ReadOnlySpan<Complex>)ToComplexArray(samples), length).Select(v => v.Real)];

    /// <summary>Mean of the <paramref name="length"/> complex samples ending at each sample, zeros
    /// before the start (conventions: Moving average; ADR 0241).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="length">The window length <c>N</c>, at least 1.</param>
    /// <returns>One mean per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Complex[] MovingAverage(ReadOnlySpan<Complex> samples, int length)
    {
        if (length < 1)
            throw new ArgumentOutOfRangeException(nameof(length), "length must be at least 1");
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        foreach (Complex v in samples)
        {
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        var y = new Complex[samples.Length];
        for (int n = 0; n < samples.Length; n++)
        {
            int start = Math.Max(0, n - length + 1);
            Complex acc = samples[start];
            for (int k = start + 1; k <= n; k++)
                acc += samples[k];
            y[n] = acc / length;
        }
        return y;
    }
}
