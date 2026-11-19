namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The F1 score of a binary <paramref name="decision"/> against the
    /// <paramref name="truth"/>, both records of 0 and 1: the harmonic mean of precision and
    /// recall, from 0 to 1 (conventions: F1 score; ADR 0386).</summary>
    /// <param name="truth">The true classes, 0 or 1; at least 1.</param>
    /// <param name="decision">The decided classes, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>F1, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or neither record
    /// holds a positive.</exception>
    public static double F1Score(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
    {
        if (truth.Length != decision.Length)
            throw new ArgumentException("truth and decision must be the same length", nameof(decision));
        if (truth.Length < 1)
            throw new ArgumentException("truth and decision must not be empty", nameof(truth));
        long tp = 0, wrong = 0;
        for (int i = 0; i < truth.Length; i++)
        {
            double t = truth[i], d = decision[i];
            if (t is not (0 or 1))
                throw new ArgumentException("truth must hold only 0 and 1", nameof(truth));
            if (d is not (0 or 1))
                throw new ArgumentException("decision must hold only 0 and 1", nameof(decision));
            if (t != d)
                wrong++;
            else if (t == 1)
                tp++;
        }
        if (2 * tp + wrong == 0)
            throw new ArgumentException("truth or decision must hold at least one positive", nameof(truth));
        return 2.0 * tp / (2 * tp + wrong);
    }
}
