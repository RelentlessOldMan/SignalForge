namespace SignalForge;

public static partial class Dsp
{
    /// <summary>The denominator <c>a</c> (<c>a[0] = 1</c>) of the Thiran allpass
    /// <c>z^(−N)·A(1/z)/A(z)</c>, whose group delay is maximally flat at DC and equal to
    /// <paramref name="delay"/> there (conventions: Thiran allpass; ADR 0227).</summary>
    /// <param name="delay">The DC group delay <c>D</c> in samples, finite and greater than
    /// <c>order − 1</c>.</param>
    /// <param name="order">The filter order <c>N</c>, at least 1.</param>
    /// <returns>The <c>N + 1</c> denominator coefficients; the numerator is them reversed.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] ThiranAllpass(double delay, int order)
    {
        if (order < 1)
            throw new ArgumentOutOfRangeException(nameof(order), "order must be at least 1");
        if (!(double.IsFinite(delay) && delay > order - 1))
            throw new ArgumentOutOfRangeException(nameof(delay), "delay must be finite and greater than order - 1");
        var a = new double[order + 1];
        a[0] = 1.0;
        for (int k = 1; k <= order; k++)
        {
            double v = k % 2 == 1 ? -1.0 : 1.0;
            for (int i = 1; i <= k; i++)
                v *= (double)(order - k + i) / i;
            for (int m = 0; m <= order; m++)
                v *= (delay - order + m) / (delay - order + k + m);
            a[k] = v;
        }
        return a;
    }
}
