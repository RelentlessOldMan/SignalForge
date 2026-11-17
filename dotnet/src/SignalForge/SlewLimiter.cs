using System.Numerics;

namespace SignalForge;

public static partial class Dsp
{
    /// <summary>Limit each step to at most <paramref name="rise"/> up and
    /// <paramref name="fall"/> down, from rest (conventions: Slew-rate limiter; ADR 0242).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="rise">The largest step up per sample, finite and positive.</param>
    /// <param name="fall">The largest step down per sample, finite and positive.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] SlewLimiter(ReadOnlySpan<double> samples, double rise, double fall)
    {
        if (!double.IsFinite(rise) || !(rise > 0))
            throw new ArgumentOutOfRangeException(nameof(rise), "rise must be positive");
        if (!double.IsFinite(fall) || !(fall > 0))
            throw new ArgumentOutOfRangeException(nameof(fall), "fall must be positive");
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        var y = new double[samples.Length];
        double prev = 0;
        for (int n = 0; n < samples.Length; n++)
        {
            double d = samples[n] - prev;
            prev = d > rise ? prev + rise : d < -fall ? prev - fall : samples[n];
            y[n] = prev;
        }
        return y;
    }

    /// <summary>Comparator with hysteresis: 1 after a sample above <paramref name="high"/>, 0
    /// after one below <paramref name="low"/>, otherwise held, from 0 (conventions: Schmitt
    /// trigger; ADR 0244).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="low">The lower threshold, finite and below <paramref name="high"/>.</param>
    /// <param name="high">The upper threshold, finite.</param>
    /// <returns>The state, 0 or 1, after each sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static byte[] SchmittTrigger(ReadOnlySpan<double> samples, double low, double high)
    {
        if (!double.IsFinite(low))
            throw new ArgumentOutOfRangeException(nameof(low), "low must be finite");
        if (!double.IsFinite(high))
            throw new ArgumentOutOfRangeException(nameof(high), "high must be finite");
        if (!(low < high))
            throw new ArgumentException("low must be below high", nameof(low));
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        var y = new byte[samples.Length];
        byte state = 0;
        for (int n = 0; n < samples.Length; n++)
        {
            if (samples[n] > high)
                state = 1;
            else if (samples[n] < low)
                state = 0;
            y[n] = state;
        }
        return y;
    }

    /// <summary>Hold every <paramref name="period"/>-th real sample, from
    /// <paramref name="offset"/>, at the same rate; zeros before the first (conventions:
    /// Sample-and-hold; ADR 0245).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="period">The hold period <c>P</c>, at least 1.</param>
    /// <param name="offset">The index of the first sample taken, in <c>[0, P)</c>.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] SampleAndHold(ReadOnlySpan<double> samples, int period, int offset = 0) =>
        [.. SampleAndHold((ReadOnlySpan<Complex>)ToComplexArray(samples), period, offset).Select(v => v.Real)];

    /// <summary>Hold every <paramref name="period"/>-th complex sample, from
    /// <paramref name="offset"/>, at the same rate; zeros before the first (conventions:
    /// Sample-and-hold; ADR 0245).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="period">The hold period <c>P</c>, at least 1.</param>
    /// <param name="offset">The index of the first sample taken, in <c>[0, P)</c>.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Complex[] SampleAndHold(ReadOnlySpan<Complex> samples, int period, int offset = 0)
    {
        if (period < 1)
            throw new ArgumentOutOfRangeException(nameof(period), "period must be at least 1");
        if (offset < 0 || offset >= period)
            throw new ArgumentOutOfRangeException(nameof(offset), "offset must be in [0, period)");
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        foreach (Complex v in samples)
        {
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        var y = new Complex[samples.Length];
        for (int n = offset; n < y.Length; n++)
            y[n] = samples[offset + period * ((n - offset) / period)];
        return y;
    }

    /// <summary>Soft threshold: 0 where <c>|x| ≤ width</c>, otherwise <c>x</c> moved
    /// <paramref name="width"/> toward 0 (conventions: Dead zone; ADR 0246).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="width">The half-width of the zone, finite and at least 0.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] DeadZone(ReadOnlySpan<double> samples, double width)
    {
        if (!double.IsFinite(width) || !(width >= 0))
            throw new ArgumentOutOfRangeException(nameof(width), "width must be at least 0");
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        var y = new double[samples.Length];
        for (int n = 0; n < samples.Length; n++)
        {
            double v = samples[n];
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            y[n] = v > width ? v - width : v < -width ? v + width : 0;
        }
        return y;
    }
}
