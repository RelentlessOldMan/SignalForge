namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The area under the ROC curve of a real <paramref name="score"/> against the
    /// binary <paramref name="truth"/>: the share of positive–negative pairs where the positive
    /// scores higher, ties counting half (conventions: ROC AUC; ADR 0393).</summary>
    /// <param name="truth">The true classes, 0 or 1, with at least one of each.</param>
    /// <param name="score">The scores, finite, higher meaning more likely positive; the same
    /// length as <paramref name="truth"/>.</param>
    /// <returns>The area, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or a class is
    /// missing.</exception>
    public static double RocAuc(ReadOnlySpan<double> truth, ReadOnlySpan<double> score)
    {
        if (truth.Length != score.Length)
            throw new ArgumentException("truth and score must be the same length", nameof(score));
        long n1 = 0;
        for (int i = 0; i < truth.Length; i++)
        {
            if (truth[i] is not (0 or 1))
                throw new ArgumentException("truth must hold only 0 and 1", nameof(truth));
            if (!double.IsFinite(score[i]))
                throw new ArgumentException("score must be finite", nameof(score));
            if (truth[i] == 1)
                n1++;
        }
        long n0 = truth.Length - n1;
        if (n1 == 0 || n0 == 0)
            throw new ArgumentException("truth must hold at least one 0 and one 1", nameof(truth));
        var rank = HoeffdingRanks(score);
        double r1 = 0;
        for (int i = 0; i < truth.Length; i++)
        {
            if (truth[i] == 1)
                r1 += rank[i];
        }
        return (r1 - n1 * (n1 + 1) / 2.0) / ((double)n1 * n0);
    }
}
