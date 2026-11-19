namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Kendall's W, the coefficient of concordance: how well the raters in the rows
    /// of <paramref name="ratings"/> agree on the order of the items in its columns, from 0 to
    /// 1 (conventions: Kendall's W; ADR 0379).</summary>
    /// <param name="ratings">One row per rater, at least 2, each with the same number of
    /// items, at least 2; finite.</param>
    /// <returns>W, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or every rater gives
    /// every item the same value.</exception>
    public static double KendallW(double[][] ratings)
    {
        ArgumentNullException.ThrowIfNull(ratings);
        int m = ratings.Length;
        if (m < 2)
            throw new ArgumentException("ratings must have at least 2 raters (rows)", nameof(ratings));
        int n = ratings[0]?.Length ?? 0;
        if (n < 2)
            throw new ArgumentException("ratings must have at least 2 items (columns)", nameof(ratings));
        var rankSums = new double[n];
        long ties = 0;
        foreach (double[] row in ratings)
        {
            if (row is null || row.Length != n)
                throw new ArgumentException("ratings rows must all be the same length", nameof(ratings));
            foreach (double v in row)
            {
                if (!double.IsFinite(v))
                    throw new ArgumentException("ratings must be finite", nameof(ratings));
            }
            double[] ranks = HoeffdingRanks(row);
            for (int j = 0; j < n; j++)
                rankSums[j] += ranks[j];
            var sorted = (double[])row.Clone();
            Array.Sort(sorted);
            for (int i = 0; i < n;)
            {
                int k = i;
                while (k + 1 < n && sorted[k + 1] == sorted[i])
                    k++;
                long t = k - i + 1;
                ties += t * t * t - t;
                i = k + 1;
            }
        }
        double centre = m * (n + 1) / 2.0, s = 0;
        foreach (double r in rankSums)
            s += (r - centre) * (r - centre);
        long nn = n;
        long denominator = (long)m * m * (nn * nn * nn - nn) - m * ties;
        if (denominator == 0)
            throw new ArgumentException("every rater gives every item the same value", nameof(ratings));
        return 12 * s / denominator;
    }
}
