namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The intraclass correlation ICC(3,1): the two-way consistency of a single
    /// rating, raters in the rows of <paramref name="ratings"/> and subjects in its columns
    /// (conventions: ICC(3,1); ADR 0381).</summary>
    /// <param name="ratings">One row per rater, at least 2, each with the same number of
    /// subjects, at least 2; finite.</param>
    /// <returns>ICC(3,1), from −1/(k − 1) to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or the subjects do
    /// not differ once the rater offsets are removed.</exception>
    public static double IccConsistency(double[][] ratings)
    {
        ArgumentNullException.ThrowIfNull(ratings);
        int k = ratings.Length;
        if (k < 2)
            throw new ArgumentException("ratings must have at least 2 raters (rows)", nameof(ratings));
        int n = ratings[0]?.Length ?? 0;
        if (n < 2)
            throw new ArgumentException("ratings must have at least 2 subjects (columns)", nameof(ratings));
        var rows = new double[k];
        var cols = new double[n];
        double grand = 0;
        for (int i = 0; i < k; i++)
        {
            double[] row = ratings[i];
            if (row is null || row.Length != n)
                throw new ArgumentException("ratings rows must all be the same length", nameof(ratings));
            for (int j = 0; j < n; j++)
            {
                if (!double.IsFinite(row[j]))
                    throw new ArgumentException("ratings must be finite", nameof(ratings));
                rows[i] += row[j];
                cols[j] += row[j];
                grand += row[j];
            }
        }
        for (int i = 0; i < k; i++)
            rows[i] /= n;
        for (int j = 0; j < n; j++)
            cols[j] /= k;
        grand /= (double)k * n;
        double ssS = 0, ssE = 0;
        foreach (double c in cols)
            ssS += (c - grand) * (c - grand);
        for (int i = 0; i < k; i++)
        {
            for (int j = 0; j < n; j++)
            {
                double e = ratings[i][j] - rows[i] - cols[j] + grand;
                ssE += e * e;
            }
        }
        double msS = k * ssS / (n - 1), msE = ssE / ((n - 1.0) * (k - 1));
        double denominator = msS + (k - 1) * msE;
        if (denominator == 0)
            throw new ArgumentException("the subjects do not differ once the rater offsets are removed", nameof(ratings));
        return (msS - msE) / denominator;
    }
}
