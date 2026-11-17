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
}
