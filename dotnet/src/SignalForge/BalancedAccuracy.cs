namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The balanced accuracy of a binary <paramref name="decision"/> against the
    /// <paramref name="truth"/>, both records of 0 and 1: the mean of the sensitivity and the
    /// specificity, from 0 to 1 (conventions: Balanced accuracy; ADR 0396).</summary>
    /// <param name="truth">The true classes, 0 or 1, with at least one of each.</param>
    /// <param name="decision">The decided classes, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>The balanced accuracy, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or the truth lacks a
    /// class.</exception>
    public static double BalancedAccuracy(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
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
        if (tp + fn == 0 || tn + fp == 0)
            throw new ArgumentException("truth must hold at least one 0 and one 1", nameof(truth));
        return (double)(tp * (tn + fp) + tn * (tp + fn)) / (2 * (tp + fn) * (tn + fp));
    }
}
