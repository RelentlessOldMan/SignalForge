namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The dispersion coefficient of two binary records of 0 and 1: their
    /// covariance as 0/1 values, from −1/4 to 1/4 (conventions: the dispersion coefficient;
    /// ADR 0471).</summary>
    /// <param name="truth">The first record, 0 or 1; at least 1.</param>
    /// <param name="decision">The second record, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>The coefficient, from −1/4 to 1/4.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double DispersionCoefficient(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
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
        long n = truth.Length, tn = n - tp - fn - fp;
        return (double)((tp * tn) - (fn * fp)) / (n * n);
    }
}
