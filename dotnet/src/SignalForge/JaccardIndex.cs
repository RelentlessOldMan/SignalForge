namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Jaccard index of two binary records of 0 and 1: the items both mark 1
    /// over the items either marks 1, from 0 to 1 (conventions: Jaccard index;
    /// ADR 0388).</summary>
    /// <param name="truth">The first record, 0 or 1; at least 1.</param>
    /// <param name="decision">The second record, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>The index, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or neither record
    /// holds a 1.</exception>
    public static double JaccardIndex(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
    {
        if (truth.Length != decision.Length)
            throw new ArgumentException("truth and decision must be the same length", nameof(decision));
        if (truth.Length < 1)
            throw new ArgumentException("truth and decision must not be empty", nameof(truth));
        long both = 0, either = 0;
        for (int i = 0; i < truth.Length; i++)
        {
            double t = truth[i], d = decision[i];
            if (t is not (0 or 1))
                throw new ArgumentException("truth must hold only 0 and 1", nameof(truth));
            if (d is not (0 or 1))
                throw new ArgumentException("decision must hold only 0 and 1", nameof(decision));
            if (t == 1 && d == 1)
                both++;
            if (t == 1 || d == 1)
                either++;
        }
        if (either == 0)
            throw new ArgumentException("truth or decision must hold at least one 1", nameof(truth));
        return (double)both / either;
    }
}
