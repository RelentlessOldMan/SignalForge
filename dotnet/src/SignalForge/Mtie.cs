namespace SignalForge;

/// <summary>Maximum time interval errors (conventions: Maximum time interval error;
/// ADR 0337).</summary>
/// <param name="Taus">The observation intervals in seconds, <c>n·τ₀</c>, in the sizes' order.</param>
/// <param name="Values">The MTIE at each interval, in seconds.</param>
public sealed record Mtie(double[] Taus, double[] Values);

public static partial class Measurements
{
    /// <summary>The maximum time interval error: the largest peak-to-peak time error over every
    /// window of <c>n + 1</c> samples, at <c>τ = n·τ₀</c> (conventions: Maximum time interval
    /// error; ADR 0337).</summary>
    /// <param name="timeError">Time-error samples in seconds, finite, at least 2.</param>
    /// <param name="sampleInterval">The spacing of the samples in seconds, finite and positive.</param>
    /// <param name="windowSizes">The sizes <c>n</c>, at least one, each from 1 to
    /// <c>N − 1</c>.</param>
    /// <returns>The observation intervals and the MTIE at each.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Mtie Mtie(ReadOnlySpan<double> timeError, double sampleInterval, ReadOnlySpan<int> windowSizes)
    {
        if (!(double.IsFinite(sampleInterval) && sampleInterval > 0))
            throw new ArgumentOutOfRangeException(nameof(sampleInterval), sampleInterval, "must be finite and positive");
        int size = timeError.Length;
        if (size < 2)
            throw new ArgumentException("needs at least 2 samples", nameof(timeError));
        foreach (double v in timeError)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("timeError must be finite", nameof(timeError));
        }
        if (windowSizes.IsEmpty)
            throw new ArgumentException("windowSizes must not be empty", nameof(windowSizes));
        foreach (int n in windowSizes)
        {
            if (n < 1 || n > size - 1)
                throw new ArgumentException("each window size n must be from 1 to N − 1", nameof(windowSizes));
        }
        var taus = new double[windowSizes.Length];
        var values = new double[windowSizes.Length];
        for (int f = 0; f < windowSizes.Length; f++)
        {
            int n = windowSizes[f];
            double worst = 0;
            for (int k = 0; k + n < size; k++)
            {
                double hi = timeError[k], lo = timeError[k];
                for (int i = k + 1; i <= k + n; i++)
                {
                    hi = Math.Max(hi, timeError[i]);
                    lo = Math.Min(lo, timeError[i]);
                }
                worst = Math.Max(worst, hi - lo);
            }
            taus[f] = n * sampleInterval;
            values[f] = worst;
        }
        return new Mtie(taus, values);
    }
}
