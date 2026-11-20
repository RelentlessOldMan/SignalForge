namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Gilbert skill score (equitable threat score) of a binary decision
    /// against the truth: the threat score with the hits chance expects taken out
    /// (conventions: Gilbert skill score; ADR 0439).</summary>
    /// <param name="truth">The first record, 0 or 1; at least 1.</param>
    /// <param name="decision">The second record, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>The score, from −1/3 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or the records are
    /// the same constant record.</exception>
    public static double GilbertSkillScore(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
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
        long n = truth.Length;
        long chance = (tp + fn) * (tp + fp);
        long den = (n * (tp + fn + fp)) - chance;
        if (den == 0)
            throw new ArgumentException("truth and decision must not be the same constant record", nameof(truth));
        return (double)((n * tp) - chance) / (double)den;
    }
}
