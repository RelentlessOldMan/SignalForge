namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The large-sample standard error of Yule's Q of two binary records of 0 and 1:
    /// (1 - Q^2)/2 times the standard error of the log odds ratio, above 0 (conventions: the
    /// standard error of Yule's Q; ADR 0495).</summary>
    /// <param name="truth">The first record, 0 or 1; at least 1.</param>
    /// <param name="decision">The second record, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>The standard error, above 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double YuleQStandardError(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
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
        long tn = truth.Length - tp - fn - fp;
        if (tp == 0 || fn == 0 || fp == 0 || tn == 0)
            throw new ArgumentException("every cell of the table must be nonzero", nameof(decision));
        long x = tp * tn, y = fn * fp;
        long num = (fn * fp * tn) + (tp * fp * tn) + (tp * fn * tn) + (tp * fn * fp);
        double w = x + y;
        return 2.0 * Math.Sqrt((double)(x * y) * (double)num) / (w * w);
    }
}
