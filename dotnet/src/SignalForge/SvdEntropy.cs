namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Shannon entropy of the normalized singular values of the delay-embedding
    /// matrix, over <c>ln(order)</c> (conventions: SVD entropy; ADR 0342).</summary>
    /// <param name="samples">Real samples, finite and not all 0.</param>
    /// <param name="order">The embedding dimension, from 2 to 32.</param>
    /// <param name="delay">The spacing of a row's samples, at least 1.</param>
    /// <returns>The SVD entropy, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double SvdEntropy(ReadOnlySpan<double> samples, int order, int delay = 1)
    {
        if (order < 2 || order > 32)
            throw new ArgumentOutOfRangeException(nameof(order), order, "must be from 2 to 32");
        if (delay < 1)
            throw new ArgumentOutOfRangeException(nameof(delay), delay, "must be at least 1");
        bool any = false;
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            any |= v != 0;
        }
        long rows = samples.Length - (long)(order - 1) * delay;
        if (rows < order)
            throw new ArgumentException("samples are too short: need Length - (order - 1)*delay >= order", nameof(samples));
        if (!any)
            throw new ArgumentException("samples must not all be 0", nameof(samples));
        int k = (int)rows;
        var columns = new double[order][];
        for (int j = 0; j < order; j++)
            columns[j] = samples.Slice(j * delay, k).ToArray();
        double[] s = SingularValuesByJacobi(columns);
        double total = 0;
        foreach (double v in s)
            total += v;
        double h = 0;
        foreach (double v in s)
        {
            double p = v / total;
            if (p > 0)
                h -= p * Math.Log(p);
        }
        return h / Math.Log(order);
    }

    // Hestenes' one-sided Jacobi: rotate column pairs until every pair is orthogonal; the
    // singular values are then the column norms. The columns are overwritten.
    private static double[] SingularValuesByJacobi(double[][] columns)
    {
        int n = columns.Length;
        for (int sweep = 0; sweep < 100; sweep++)
        {
            bool rotated = false;
            for (int p = 0; p < n - 1; p++)
            {
                for (int q = p + 1; q < n; q++)
                {
                    double[] a = columns[p], b = columns[q];
                    double alpha = 0, beta = 0, gamma = 0;
                    for (int i = 0; i < a.Length; i++)
                    {
                        alpha += a[i] * a[i];
                        beta += b[i] * b[i];
                        gamma += a[i] * b[i];
                    }
                    if (!(Math.Abs(gamma) > 1e-15 * Math.Sqrt(alpha * beta)))
                        continue;
                    rotated = true;
                    double zeta = (beta - alpha) / (2 * gamma);
                    double t = Math.Sign(zeta == 0 ? 1 : zeta) / (Math.Abs(zeta) + Math.Sqrt(1 + zeta * zeta));
                    double c = 1 / Math.Sqrt(1 + t * t), sn = c * t;
                    for (int i = 0; i < a.Length; i++)
                    {
                        double u = a[i], w = b[i];
                        a[i] = c * u - sn * w;
                        b[i] = sn * u + c * w;
                    }
                }
            }
            if (!rotated)
                break;
        }
        var s = new double[n];
        for (int j = 0; j < n; j++)
        {
            double sum = 0;
            foreach (double v in columns[j])
                sum += v * v;
            s[j] = Math.Sqrt(sum);
        }
        return s;
    }
}
