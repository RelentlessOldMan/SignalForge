namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Fowlkes–Mallows index of a binary <paramref name="decision"/> against the
    /// <paramref name="truth"/>, both records of 0 and 1: the geometric mean of precision and
    /// recall, from 0 to 1 (conventions: Fowlkes–Mallows index; ADR 0389).</summary>
    /// <param name="truth">The true classes, 0 or 1; at least 1.</param>
    /// <param name="decision">The decided classes, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>The index, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or a record holds no
    /// 1.</exception>
    public static double FowlkesMallowsIndex(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
    {
        if (truth.Length != decision.Length)
            throw new ArgumentException("truth and decision must be the same length", nameof(decision));
        if (truth.Length < 1)
            throw new ArgumentException("truth and decision must not be empty", nameof(truth));
        long tp = 0, decided = 0, actual = 0;
        for (int i = 0; i < truth.Length; i++)
        {
            double t = truth[i], d = decision[i];
            if (t is not (0 or 1))
                throw new ArgumentException("truth must hold only 0 and 1", nameof(truth));
            if (d is not (0 or 1))
                throw new ArgumentException("decision must hold only 0 and 1", nameof(decision));
            if (t == 1)
                actual++;
            if (d == 1)
                decided++;
            if (t == 1 && d == 1)
                tp++;
        }
        if (decided == 0 || actual == 0)
            throw new ArgumentException("truth and decision must each hold at least one 1", nameof(truth));
        return tp / Math.Sqrt((double)decided * actual);
    }
}
