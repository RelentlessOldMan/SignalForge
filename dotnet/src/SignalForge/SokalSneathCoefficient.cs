namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Sokal-Sneath coefficient of two binary records of 0 and 1: the items
    /// both mark 1 over those plus twice the items only one marks 1 (conventions:
    /// Sokal-Sneath coefficient; ADR 0427).</summary>
    /// <param name="truth">The first record, 0 or 1; at least 1.</param>
    /// <param name="decision">The second record, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>The coefficient, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or neither record
    /// holds a 1.</exception>
    public static double SokalSneathCoefficient(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
    {
        if (truth.Length != decision.Length)
            throw new ArgumentException("truth and decision must be the same length", nameof(decision));
        if (truth.Length < 1)
            throw new ArgumentException("truth and decision must not be empty", nameof(truth));
        long tp = 0, mismatch = 0;
        for (int i = 0; i < truth.Length; i++)
        {
            double t = truth[i], d = decision[i];
            if (t is not (0 or 1))
                throw new ArgumentException("truth must hold only 0 and 1", nameof(truth));
            if (d is not (0 or 1))
                throw new ArgumentException("decision must hold only 0 and 1", nameof(decision));
            if (t == 1 && d == 1)
                tp++;
            else if (t != d)
                mismatch++;
        }
        long den = tp + (2 * mismatch);
        if (den == 0)
            throw new ArgumentException("truth or decision must hold at least one 1", nameof(truth));
        return (double)tp / den;
    }
}
