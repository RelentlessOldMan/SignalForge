namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Johnson's rank preference index of the record of use <paramref name="x"/>
    /// against the record of availability <paramref name="available"/>, of values at least 0,
    /// each with a value above 0 and <paramref name="available"/> above 0 everywhere: for each
    /// kind its rank of use less its rank of availability, ranks from 1 for the largest, ties
    /// given their mean rank (conventions: Johnson's rank preference index;
    /// ADR 0608).</summary>
    /// <param name="x">The record of use, finite, at least 0, with a value above 0.</param>
    /// <param name="available">The record of availability, finite and above 0, the same
    /// length as x.</param>
    /// <returns>Johnson's rank preference index for each kind.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] JohnsonRankPreference(ReadOnlySpan<double> x, ReadOnlySpan<double> available)
    {
        PiankaTop(x, nameof(x));
        PiankaTop(available, nameof(available));
        foreach (double v in available)
        {
            if (!(v > 0))
                throw new ArgumentException("available must be above 0 everywhere", nameof(available));
        }
        if (x.Length != available.Length)
            throw new ArgumentException("x and available must have the same length", nameof(available));
        double[] use = JohnsonAscendingRanks(x);
        double[] result = JohnsonAscendingRanks(available);
        for (int i = 0; i < result.Length; i++)
            result[i] -= use[i];
        return result;
    }

    // Ranks from 1 for the smallest, ties given their mean rank; the rank from the largest
    // is n + 1 less this, so the difference of two rankings is the same either way.
    static double[] JohnsonAscendingRanks(ReadOnlySpan<double> values)
    {
        int n = values.Length;
        var order = new int[n];
        for (int i = 0; i < n; i++)
            order[i] = i;
        var keys = values.ToArray();
        Array.Sort(keys, order);
        var rank = new double[n];
        for (int i = 0; i < n;)
        {
            int j = i;
            while (j + 1 < n && keys[j + 1] == keys[i])
                j++;
            double mean = (i + j) / 2.0 + 1;
            for (int k = i; k <= j; k++)
                rank[order[k]] = mean;
            i = j + 1;
        }
        return rank;
    }
}
