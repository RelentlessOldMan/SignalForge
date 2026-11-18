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

    /// <summary>The modified Allan deviation of fractional-frequency samples at
    /// <c>τ = m·sampleInterval</c> for each averaging factor <c>m</c> (conventions: Modified
    /// Allan deviation; ADR 0328).</summary>
    /// <param name="fractionalFrequency">Fractional-frequency samples, finite, at least 2.</param>
    /// <param name="sampleInterval">The interval each sample averages over, in seconds, finite
    /// and positive.</param>
    /// <param name="averagingFactors">The factors <c>m</c>, at least one, each with
    /// <c>1 ≤ m</c> and <c>3m ≤ N + 1</c>.</param>
    /// <returns>The averaging times and deviations.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static AllanDeviation ModifiedAllanDeviation(ReadOnlySpan<double> fractionalFrequency, double sampleInterval,
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
            if (m < 1 || m > (size + 1) / 3)
                throw new ArgumentException("each averaging factor m must be at least 1 with 3m <= N + 1", nameof(averagingFactors));
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
            var d = new double[size - (2 * m) + 1];
            for (int i = 0; i < d.Length; i++)
                d[i] = means[i + m] - means[i];
            int terms = size - (3 * m) + 2;
            double sum = 0;
            for (int j = 0; j < terms; j++)
            {
                double s = 0;
                for (int i = j; i < j + m; i++)
                    s += d[i];
                sum += s * s;
            }
            taus[f] = m * sampleInterval;
            deviations[f] = Math.Sqrt(sum / (2.0 * m * m * terms));
        }
        return new AllanDeviation(taus, deviations);
    }

    /// <summary>The overlapping Hadamard deviation of fractional-frequency samples at
    /// <c>τ = m·sampleInterval</c> for each averaging factor <c>m</c> (conventions: Hadamard
    /// deviation; ADR 0329).</summary>
    /// <param name="fractionalFrequency">Fractional-frequency samples, finite, at least 3.</param>
    /// <param name="sampleInterval">The interval each sample averages over, in seconds, finite
    /// and positive.</param>
    /// <param name="averagingFactors">The factors <c>m</c>, at least one, each with
    /// <c>1 ≤ m</c> and <c>3m ≤ N</c>.</param>
    /// <returns>The averaging times and deviations.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static AllanDeviation HadamardDeviation(ReadOnlySpan<double> fractionalFrequency, double sampleInterval,
        ReadOnlySpan<int> averagingFactors)
    {
        if (!(double.IsFinite(sampleInterval) && sampleInterval > 0))
            throw new ArgumentOutOfRangeException(nameof(sampleInterval), sampleInterval, "must be finite and positive");
        int size = fractionalFrequency.Length;
        if (size < 3)
            throw new ArgumentException("needs at least 3 samples", nameof(fractionalFrequency));
        foreach (double v in fractionalFrequency)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("fractionalFrequency must be finite", nameof(fractionalFrequency));
        }
        if (averagingFactors.IsEmpty)
            throw new ArgumentException("averagingFactors must not be empty", nameof(averagingFactors));
        foreach (int m in averagingFactors)
        {
            if (m < 1 || m > size / 3)
                throw new ArgumentException("each averaging factor m must be at least 1 with 3m <= N", nameof(averagingFactors));
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
            int terms = size - (3 * m) + 1;
            double sum = 0;
            for (int j = 0; j < terms; j++)
            {
                double d = (means[j + (2 * m)] - means[j + m]) - (means[j + m] - means[j]);
                sum += d * d;
            }
            taus[f] = m * sampleInterval;
            deviations[f] = Math.Sqrt(sum / (6.0 * terms));
        }
        return new AllanDeviation(taus, deviations);
    }

    /// <summary>The time deviation <c>(τ/√3)·MDEV(τ)</c> in seconds for each averaging factor
    /// (conventions: Time deviation; ADR 0331).</summary>
    /// <param name="fractionalFrequency">Fractional-frequency samples, finite, at least 2.</param>
    /// <param name="sampleInterval">The interval each sample averages over, in seconds, finite
    /// and positive.</param>
    /// <param name="averagingFactors">The factors <c>m</c>, at least one, each with
    /// <c>1 ≤ m</c> and <c>3m ≤ N + 1</c>.</param>
    /// <returns>The averaging times and the time deviations in seconds.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static AllanDeviation TimeDeviation(ReadOnlySpan<double> fractionalFrequency, double sampleInterval,
        ReadOnlySpan<int> averagingFactors)
    {
        AllanDeviation mod = ModifiedAllanDeviation(fractionalFrequency, sampleInterval, averagingFactors);
        var deviations = new double[mod.Taus.Length];
        for (int f = 0; f < deviations.Length; f++)
            deviations[f] = mod.Taus[f] / Math.Sqrt(3) * mod.Deviations[f];
        return new AllanDeviation(mod.Taus, deviations);
    }
}
