namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Fleiss' kappa: the chance-corrected agreement of raters who each put every
    /// subject in one category, from <paramref name="counts"/>[subject][category]
    /// (conventions: Fleiss' kappa; ADR 0382).</summary>
    /// <param name="counts">One row per subject, at least 1, each with the same number of
    /// categories, at least 2; whole numbers, not negative, every row summing to the same
    /// number of ratings, at least 2.</param>
    /// <returns>Kappa, at most 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or every rating is in
    /// the same category.</exception>
    public static double FleissKappa(double[][] counts)
    {
        ArgumentNullException.ThrowIfNull(counts);
        int subjects = counts.Length;
        if (subjects < 1)
            throw new ArgumentException("counts must have at least 1 subject (row)", nameof(counts));
        int q = counts[0]?.Length ?? 0;
        if (q < 2)
            throw new ArgumentException("counts must have at least 2 categories (columns)", nameof(counts));
        var columns = new double[q];
        double n = -1, observed = 0;
        foreach (double[] row in counts)
        {
            if (row is null || row.Length != q)
                throw new ArgumentException("counts rows must all be the same length", nameof(counts));
            double sum = 0, squares = 0;
            for (int j = 0; j < q; j++)
            {
                double v = row[j];
                if (!double.IsFinite(v) || v < 0 || v != Math.Floor(v))
                    throw new ArgumentException("counts must be whole numbers, not negative", nameof(counts));
                sum += v;
                squares += v * v;
                columns[j] += v;
            }
            if (n < 0)
                n = sum;
            else if (sum != n)
                throw new ArgumentException("every subject must have the same number of ratings", nameof(counts));
            if (n < 2)
                throw new ArgumentException("every subject must have at least 2 ratings", nameof(counts));
            observed += (squares - n) / (n * (n - 1));
        }
        observed /= subjects;
        double expected = 0;
        foreach (double c in columns)
        {
            double p = c / (subjects * n);
            expected += p * p;
        }
        if (expected == 1)
            throw new ArgumentException("every rating is in the same category", nameof(counts));
        return (observed - expected) / (1 - expected);
    }
}
