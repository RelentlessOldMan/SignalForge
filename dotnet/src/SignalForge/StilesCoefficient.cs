namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Stiles' coefficient of two binary records of 0 and 1: log10 of the
    /// continuity-corrected chi-square over n (conventions: Stiles' coefficient;
    /// ADR 0451).</summary>
    /// <param name="truth">The first record, 0 or 1; at least 1.</param>
    /// <param name="decision">The second record, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>The coefficient.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double StilesCoefficient(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
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
        if (nt == 0 || nt == n || nd == 0 || nd == n)
            throw new ArgumentException("truth and decision must not be constant", nameof(truth));
        long e = (2 * Math.Abs((n * tp) - (nt * nd))) - n;
        if (e == 0)
            throw new ArgumentException("|TP TN − FN FP| must not be n/2", nameof(truth));
        double fe = e;
        return Math.Log10((double)n * fe * fe / (4.0 * (double)(nt * nd) * (double)((n - nt) * (n - nd))));
    }
}
