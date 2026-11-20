namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Doolittle coefficient of two binary records of 0 and 1: the square of
    /// the phi coefficient, from 0 to 1 (conventions: the Doolittle coefficient;
    /// ADR 0466).</summary>
    /// <param name="truth">The first record, 0 or 1; at least 1.</param>
    /// <param name="decision">The second record, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>The coefficient, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double DoolittleCoefficient(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
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
        long n = truth.Length, na = tp + fn, nb = tp + fp;
        long u = na * nb, v = (n - na) * (n - nb);
        if (u == 0 || v == 0)
            throw new ArgumentException("truth and decision must each hold both 0 and 1", nameof(truth));
        double x = (n * tp) - u;
        return x * x / ((double)u * v);
    }
}
