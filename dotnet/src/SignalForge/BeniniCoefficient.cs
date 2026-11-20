namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Benini coefficient of two binary records of 0 and 1: the excess of
    /// shared 1s over chance as a share of its most, at most 1, 0 at independence
    /// (conventions: the Benini coefficient; ADR 0465).</summary>
    /// <param name="truth">The first record, 0 or 1; at least 1.</param>
    /// <param name="decision">The second record, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>The coefficient, at most 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double BeniniCoefficient(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
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
        long den = (n * Math.Min(na, nb)) - (na * nb);
        if (den == 0)
            throw new ArgumentException("truth and decision must each hold both 0 and 1", nameof(truth));
        return (double)((n * tp) - (na * nb)) / (double)den;
    }
}
