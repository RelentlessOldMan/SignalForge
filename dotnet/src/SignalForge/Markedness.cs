namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Markedness of a binary <paramref name="decision"/> against the
    /// <paramref name="truth"/>, both records of 0 and 1: the precision and the negative
    /// predictive value less 1, from −1 to 1 (conventions: Markedness; ADR 0395).</summary>
    /// <param name="truth">The true classes, 0 or 1; at least 1.</param>
    /// <param name="decision">The decided classes, 0 or 1, with at least one of each; the same
    /// length as <paramref name="truth"/>.</param>
    /// <returns>The markedness, from −1 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or the decision lacks
    /// a class.</exception>
    public static double Markedness(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
    {
        if (truth.Length != decision.Length)
            throw new ArgumentException("truth and decision must be the same length", nameof(decision));
        if (truth.Length < 1)
            throw new ArgumentException("truth and decision must not be empty", nameof(truth));
        long tp = 0, tn = 0, fp = 0, fn = 0;
        for (int i = 0; i < truth.Length; i++)
        {
            double t = truth[i], d = decision[i];
            if (t is not (0 or 1))
                throw new ArgumentException("truth must hold only 0 and 1", nameof(truth));
            if (d is not (0 or 1))
                throw new ArgumentException("decision must hold only 0 and 1", nameof(decision));
            if (t == 1)
            {
                if (d == 1)
                    tp++;
                else
                    fn++;
            }
            else if (d == 1)
            {
                fp++;
            }
            else
            {
                tn++;
            }
        }
        if (tp + fp == 0 || tn + fn == 0)
            throw new ArgumentException("decision must hold at least one 0 and one 1", nameof(decision));
        return (double)(tp * tn - fp * fn) / ((tp + fp) * (tn + fn));
    }
}
