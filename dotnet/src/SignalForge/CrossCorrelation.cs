using System.Numerics;

namespace SignalForge;

public static partial class Dsp
{
    /// <summary><c>r[k] = Σ x[n+k]·y[n]</c> for lags <c>−(M−1) … N−1</c>, lag 0 at index
    /// <c>M − 1</c>, unscaled (conventions: Cross-correlation; ADR 0190).</summary>
    /// <param name="x">Real samples, finite, not empty.</param>
    /// <param name="y">Real samples, finite, not empty.</param>
    /// <returns><c>N + M − 1</c> values.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] CrossCorrelation(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        CheckCorrelationInputs(x.Length, y.Length);
        foreach (double v in x)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("x must be finite", nameof(x));
        }
        foreach (double v in y)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("y must be finite", nameof(y));
        }
        int m = y.Length;
        var r = new double[x.Length + m - 1];
        for (int i = 0; i < r.Length; i++)
        {
            int k = i - (m - 1);
            double s = 0;
            for (int n = Math.Max(0, -k); n < m && n + k < x.Length; n++)
                s += x[n + k] * y[n];
            r[i] = s;
        }
        return r;
    }

    /// <summary><c>r[k] = Σ x[n+k]·conj(y[n])</c> for lags <c>−(M−1) … N−1</c>, lag 0 at index
    /// <c>M − 1</c>, unscaled (conventions: Cross-correlation; ADR 0190).</summary>
    /// <param name="x">Complex samples, finite, not empty.</param>
    /// <param name="y">Complex samples, finite, not empty.</param>
    /// <returns><c>N + M − 1</c> values.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Complex[] CrossCorrelation(ReadOnlySpan<Complex> x, ReadOnlySpan<Complex> y)
    {
        CheckCorrelationInputs(x.Length, y.Length);
        foreach (Complex v in x)
        {
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("x must be finite", nameof(x));
        }
        foreach (Complex v in y)
        {
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("y must be finite", nameof(y));
        }
        int m = y.Length;
        var r = new Complex[x.Length + m - 1];
        for (int i = 0; i < r.Length; i++)
        {
            int k = i - (m - 1);
            Complex s = Complex.Zero;
            for (int n = Math.Max(0, -k); n < m && n + k < x.Length; n++)
                s += x[n + k] * Complex.Conjugate(y[n]);
            r[i] = s;
        }
        return r;
    }

    private static void CheckCorrelationInputs(int x, int y)
    {
        if (x == 0)
            throw new ArgumentException("x must not be empty", nameof(x));
        if (y == 0)
            throw new ArgumentException("y must not be empty", nameof(y));
    }
}
