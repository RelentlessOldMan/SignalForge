namespace SignalForge;

public static partial class Dsp
{
    /// <summary>Savitzky–Golay weights <c>c[k + h]</c>, <c>k = −h … h</c>: the
    /// <paramref name="derivative"/>-th derivative at offset <paramref name="position"/> of the
    /// least-squares polynomial of degree <paramref name="order"/>, applied as
    /// <c>Σ c[k + h]·x[k]</c> (conventions: Savitzky–Golay; ADR 0233).</summary>
    /// <param name="length">The window length, odd and at least 1.</param>
    /// <param name="order">The polynomial degree, 0 to <c>length − 1</c>.</param>
    /// <param name="derivative">The derivative, 0 to <paramref name="order"/>.</param>
    /// <param name="position">The offset to evaluate at, <c>−h</c> to <c>h</c>.</param>
    /// <returns><paramref name="length"/> weights.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] SavgolCoefficients(int length, int order, int derivative = 0, int position = 0)
    {
        if (length < 1 || length % 2 == 0)
            throw new ArgumentOutOfRangeException(nameof(length), "length must be odd and at least 1");
        if (order < 0 || order >= length)
            throw new ArgumentOutOfRangeException(nameof(order), "order must be in 0 ... length - 1");
        if (derivative < 0 || derivative > order)
            throw new ArgumentOutOfRangeException(nameof(derivative), "derivative must be in 0 ... order");
        int h = (length - 1) / 2;
        if (Math.Abs(position) > h)
            throw new ArgumentOutOfRangeException(nameof(position), "position must be in -h ... h");
        return Savgol(length, order, derivative, position);
    }

    private static double[] Savgol(int m, int p, int d, int pos)
    {
        int h = (m - 1) / 2;
        double s = Math.Max(h, 1);
        var q = new double[p + 1][];
        for (int i = 0; i <= p; i++)
        {
            q[i] = new double[m];
            for (int k = 0; k < m; k++)
                q[i][k] = Math.Pow((k - h) / s, i);
        }
        var r = new double[p + 1, p + 1];
        for (int j = 0; j <= p; j++)
        {
            double[] v = q[j];
            for (int i = 0; i < j; i++)
            {
                double dot = 0;
                for (int k = 0; k < m; k++)
                    dot += q[i][k] * v[k];
                r[i, j] = dot;
                for (int k = 0; k < m; k++)
                    v[k] -= dot * q[i][k];
            }
            double sq = 0;
            for (int k = 0; k < m; k++)
                sq += v[k] * v[k];
            double nrm = Math.Sqrt(sq);
            r[j, j] = nrm;
            for (int k = 0; k < m; k++)
                v[k] /= nrm;
        }
        var z = new double[p + 1];
        for (int i = 0; i <= p; i++)
        {
            double rhs = 0;
            if (i >= d)
            {
                double fact = 1;
                for (int f = i - d + 1; f <= i; f++)
                    fact *= f;
                rhs = fact * Math.Pow(pos / s, i - d) / Math.Pow(s, d);
            }
            double acc = rhs;
            for (int j = 0; j < i; j++)
                acc -= r[j, i] * z[j];
            z[i] = acc / r[i, i];
        }
        var c = new double[m];
        for (int k = 0; k < m; k++)
        {
            double acc = 0;
            for (int i = 0; i <= p; i++)
                acc += q[i][k] * z[i];
            c[k] = acc;
        }
        return c;
    }

    /// <summary>Savitzky–Golay smoothing (<paramref name="derivative"/> 0) or derivative of real
    /// samples, with the edge outputs taken from the fit to the first or last window (conventions:
    /// Savitzky–Golay; ADR 0233).</summary>
    /// <param name="samples">Finite samples, at least <paramref name="length"/>.</param>
    /// <param name="length">The window length, odd and at least 1.</param>
    /// <param name="order">The polynomial degree, 0 to <c>length − 1</c>.</param>
    /// <param name="derivative">The derivative, 0 to <paramref name="order"/>.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] SavgolFilter(ReadOnlySpan<double> samples, int length, int order, int derivative = 0)
    {
        double[] c0 = SavgolCoefficients(length, order, derivative);
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        if (samples.Length < length)
            throw new ArgumentException("samples must be at least length long", nameof(samples));
        int h = (length - 1) / 2;
        int n = samples.Length;
        var y = new double[n];
        for (int i = 0; i < n; i++)
        {
            double[] c;
            int start;
            if (i < h)
            {
                c = Savgol(length, order, derivative, i - h);
                start = 0;
            }
            else if (i >= n - h)
            {
                c = Savgol(length, order, derivative, i - (n - 1 - h));
                start = n - length;
            }
            else
            {
                c = c0;
                start = i - h;
            }
            double acc = 0;
            for (int j = 0; j < length; j++)
                acc += c[j] * samples[start + j];
            y[i] = acc;
        }
        return y;
    }
}
