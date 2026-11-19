namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Cronbach's alpha: the internal consistency of the items in the rows of
    /// <paramref name="scores"/> over the subjects in its columns, at most 1 (conventions:
    /// Cronbach's alpha; ADR 0380).</summary>
    /// <param name="scores">One row per item, at least 2, each with the same number of
    /// subjects, at least 2; finite.</param>
    /// <returns>Alpha, at most 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or the subject
    /// totals are all equal.</exception>
    public static double CronbachAlpha(double[][] scores)
    {
        ArgumentNullException.ThrowIfNull(scores);
        int k = scores.Length;
        if (k < 2)
            throw new ArgumentException("scores must have at least 2 items (rows)", nameof(scores));
        int n = scores[0]?.Length ?? 0;
        if (n < 2)
            throw new ArgumentException("scores must have at least 2 subjects (columns)", nameof(scores));
        var totals = new double[n];
        double items = 0;
        foreach (double[] row in scores)
        {
            if (row is null || row.Length != n)
                throw new ArgumentException("scores rows must all be the same length", nameof(scores));
            foreach (double v in row)
            {
                if (!double.IsFinite(v))
                    throw new ArgumentException("scores must be finite", nameof(scores));
            }
            items += SampleVariance(row);
            for (int j = 0; j < n; j++)
                totals[j] += row[j];
        }
        double total = SampleVariance(totals);
        if (total == 0)
            throw new ArgumentException("the subject totals must not all be equal", nameof(scores));
        return k / (k - 1.0) * (1 - items / total);

        static double SampleVariance(double[] v)
        {
            double mean = 0;
            foreach (double x in v)
                mean += x;
            mean /= v.Length;
            double ss = 0;
            foreach (double x in v)
                ss += (x - mean) * (x - mean);
            return ss / (v.Length - 1);
        }
    }
}
