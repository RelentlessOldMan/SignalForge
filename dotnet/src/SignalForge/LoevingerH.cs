namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Loevinger's H of two binary records of 0 and 1: their covariance over the
    /// largest the counts of 1 allow, at most 1 (conventions: Loevinger's H;
    /// ADR 0441).</summary>
    /// <param name="truth">The first record, 0 or 1; at least 1.</param>
    /// <param name="decision">The second record, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>H, at most 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or a record is
    /// constant.</exception>
    public static double LoevingerH(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
    {
        if (truth.Length != decision.Length)
            throw new ArgumentException("truth and decision must be the same length", nameof(decision));
        if (truth.Length < 1)
            throw new ArgumentException("truth and decision must not be empty", nameof(truth));
        long tp = 0, fn = 0, fp = 0;
        for (int i = 0; i < truth.Length; i++)
        {
            double t = truth[i], d = decision[i];
            if (t is not (0 or 1))
                throw new ArgumentException("truth must hold only 0 and 1", nameof(truth));
            if (d is not (0 or 1))
                throw new ArgumentException("decision must hold only 0 and 1", nameof(decision));
            if (t == 1 && d == 1)
                tp++;
            else if (t == 1)
                fn++;
            else if (d == 1)
                fp++;
        }
        long n = truth.Length, nt = tp + fn, nd = tp + fp;
        long den = (n * Math.Min(nt, nd)) - (nt * nd);
        if (den == 0)
            throw new ArgumentException("truth and decision must not be constant", nameof(truth));
        return (double)((n * tp) - (nt * nd)) / (double)den;
    }
}
