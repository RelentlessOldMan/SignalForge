namespace SignalForge;

/// <summary>The number of runs above and below the mean and its z-score against a random
/// record (conventions: Runs test; ADR 0361).</summary>
/// <param name="Runs">The number of blocks of samples on the same side of the mean.</param>
/// <param name="Z">The z-score of <paramref name="Runs"/> against
/// <c>2n₁n₂/n + 1</c> and the Wald–Wolfowitz variance.</param>
public sealed record RunsTest(int Runs, double Z);

public static partial class Measurements
{
    /// <summary>The Wald–Wolfowitz runs test about the mean: the number of runs of samples
    /// above and below it, those equal to it dropped, and the z-score of that number
    /// (conventions: Runs test; ADR 0361).</summary>
    /// <param name="samples">Real samples, finite.</param>
    /// <returns>The number of runs and its z-score.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or the runs variance is 0.</exception>
    public static RunsTest RunsTest(ReadOnlySpan<double> samples)
    {
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        double sum = 0;
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            sum += v;
        }
        double mean = sum / samples.Length;
        long n1 = 0, n2 = 0;
        int runs = 0, last = 0;
        foreach (double v in samples)
        {
            if (v == mean)
                continue;
            int label = v > mean ? 1 : -1;
            if (label > 0)
                n1++;
            else
                n2++;
            if (label != last)
                runs++;
            last = label;
        }
        long n = n1 + n2;
        double p = 2.0 * n1 * n2;
        if (!(n > 1 && p > n))
            throw new ArgumentException("the runs variance must be above 0", nameof(samples));
        double variance = p * (p - n) / ((double)n * n * (n - 1));
        return new RunsTest(runs, (runs - p / n - 1) / Math.Sqrt(variance));
    }
}
