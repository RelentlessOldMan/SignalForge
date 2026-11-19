namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The average precision of a real <paramref name="score"/> against the binary
    /// <paramref name="truth"/>: the precision at each distinct score, weighted by the
    /// positives first reached there (conventions: Average precision; ADR 0394).</summary>
    /// <param name="truth">The true classes, 0 or 1, with at least one 1.</param>
    /// <param name="score">The scores, finite, higher meaning more likely positive; the same
    /// length as <paramref name="truth"/>.</param>
    /// <returns>The average precision, at most 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or there is no
    /// positive.</exception>
    public static double AveragePrecision(ReadOnlySpan<double> truth, ReadOnlySpan<double> score)
    {
        if (truth.Length != score.Length)
            throw new ArgumentException("truth and score must be the same length", nameof(score));
        int n = truth.Length;
        long n1 = 0;
        for (int i = 0; i < n; i++)
        {
            if (truth[i] is not (0 or 1))
                throw new ArgumentException("truth must hold only 0 and 1", nameof(truth));
            if (!double.IsFinite(score[i]))
                throw new ArgumentException("score must be finite", nameof(score));
            if (truth[i] == 1)
                n1++;
        }
        if (n1 == 0)
            throw new ArgumentException("truth must hold at least one 1", nameof(truth));
        var keys = new double[n];
        var cls = truth.ToArray();
        for (int i = 0; i < n; i++)
            keys[i] = -score[i];
        Array.Sort(keys, cls);
        double total = 0;
        long hits = 0;
        for (int i = 0; i < n;)
        {
            long k = 0;
            int j = i;
            while (j < n && keys[j] == keys[i])
            {
                if (cls[j] == 1)
                    k++;
                j++;
            }
            hits += k;
            if (k > 0)
                total += (double)(k * hits) / j;
            i = j;
        }
        return total / n1;
    }
}
