namespace SignalForge;

/// <summary>Overlapping Allan deviations (conventions: Allan deviation; ADR 0327).</summary>
/// <param name="Taus">The averaging times in seconds, <c>m·τ₀</c>, in the factors' order.</param>
/// <param name="Deviations">The Allan deviation at each averaging time.</param>
public sealed record AllanDeviation(double[] Taus, double[] Deviations);

public static partial class Measurements
{
    /// <summary>The overlapping Allan deviation of fractional-frequency samples at
    /// <c>τ = m·sampleInterval</c> for each averaging factor <c>m</c> (conventions: Allan
    /// deviation; ADR 0327).</summary>
    /// <param name="fractionalFrequency">Fractional-frequency samples, finite, at least 2.</param>
    /// <param name="sampleInterval">The interval each sample averages over, in seconds, finite
    /// and positive.</param>
    /// <param name="averagingFactors">The factors <c>m</c>, at least one, each with
    /// <c>1 ≤ m</c> and <c>2m ≤ N</c>.</param>
    /// <returns>The averaging times and deviations.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static AllanDeviation AllanDeviation(ReadOnlySpan<double> fractionalFrequency, double sampleInterval,
        ReadOnlySpan<int> averagingFactors)
    {
        if (!(double.IsFinite(sampleInterval) && sampleInterval > 0))
            throw new ArgumentOutOfRangeException(nameof(sampleInterval), sampleInterval, "must be finite and positive");
        int size = fractionalFrequency.Length;
        if (size < 2)
            throw new ArgumentException("needs at least 2 samples", nameof(fractionalFrequency));
        foreach (double v in fractionalFrequency)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("fractionalFrequency must be finite", nameof(fractionalFrequency));
        }
        if (averagingFactors.IsEmpty)
            throw new ArgumentException("averagingFactors must not be empty", nameof(averagingFactors));
        foreach (int m in averagingFactors)
        {
            if (m < 1 || m > size / 2)
                throw new ArgumentException("each averaging factor m must be at least 1 with 2m <= N", nameof(averagingFactors));
        }
        var taus = new double[averagingFactors.Length];
        var deviations = new double[averagingFactors.Length];
        for (int f = 0; f < averagingFactors.Length; f++)
        {
            int m = averagingFactors[f];
            var means = new double[size - m + 1];
            for (int k = 0; k < means.Length; k++)
            {
                double s = 0;
                for (int i = k; i < k + m; i++)
                    s += fractionalFrequency[i];
                means[k] = s / m;
            }
            int terms = size - (2 * m) + 1;
            double sum = 0;
            for (int j = 0; j < terms; j++)
            {
                double d = means[j + m] - means[j];
                sum += d * d;
            }
            taus[f] = m * sampleInterval;
            deviations[f] = Math.Sqrt(sum / (2.0 * terms));
        }
        return new AllanDeviation(taus, deviations);
    }
}
