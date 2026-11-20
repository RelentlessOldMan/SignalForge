namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The relative risk of two binary records of 0 and 1, the decision as the
    /// exposure: the share of truth 1s where the decision is 1 over the share where it is 0,
    /// at least 0 (conventions: the relative risk; ADR 0484).</summary>
    /// <param name="truth">The first record, 0 or 1; at least 1.</param>
    /// <param name="decision">The second record, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>The ratio, at least 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double RelativeRisk(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
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
        if (tp + fp == 0)
            throw new ArgumentException("decision must hold a 1", nameof(decision));
        if (fn == 0)
            throw new ArgumentException("the decision must have a false negative", nameof(decision));
        return (double)(tp * (fn + tn)) / (double)((tp + fp) * fn);
    }
}
