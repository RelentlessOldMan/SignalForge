namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Dennis coefficient of two binary records of 0 and 1: the excess of the
    /// shared 1s over chance in units of its square root (conventions: Dennis coefficient;
    /// ADR 0437).</summary>
    /// <param name="truth">The first record, 0 or 1; at least 1.</param>
    /// <param name="decision">The second record, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>The coefficient; 0 for no association.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or a record holds
    /// no 1.</exception>
    public static double DennisCoefficient(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
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
        long nt = tp + fn, nd = tp + fp;
        if (nt == 0 || nd == 0)
            throw new ArgumentException("truth and decision must each hold at least one 1", nameof(truth));
        return (double)((tp * tn) - (fn * fp)) / Math.Sqrt((double)(truth.Length * nt * nd));
    }
}
