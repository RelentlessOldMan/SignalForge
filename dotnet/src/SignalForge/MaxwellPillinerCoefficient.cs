namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Maxwell-Pilliner coefficient of two binary records of 0 and 1: the
    /// cross-product difference over the sum of the two records' variances, from −1 to 1
    /// (conventions: the Maxwell-Pilliner coefficient; ADR 0458).</summary>
    /// <param name="truth">The first record, 0 or 1; at least 1.</param>
    /// <param name="decision">The second record, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>The coefficient, from −1 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double MaxwellPillinerCoefficient(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
    {
        if (truth.Length != decision.Length)
            throw new ArgumentException("truth and decision must be the same length", nameof(decision));
        if (truth.Length < 1)
            throw new ArgumentException("truth and decision must not be empty", nameof(truth));
        long tp = 0, fn = 0, fp = 0, tn = 0;
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
            else
                tn++;
        }
        long n = tp + fn + fp + tn, nt = tp + fn, nd = tp + fp;
        long den = (nt * (n - nt)) + (nd * (n - nd));
        if (den == 0)
            throw new ArgumentException("truth and decision must not both be constant", nameof(truth));
        return (double)(2 * ((tp * tn) - (fn * fp))) / (double)den;
    }
}
