namespace SignalForge;

/// <summary>Special functions .NET does not provide. See docs/adr/0007-pulse-shaping-channel-evm.md.</summary>
internal static class SpecialFunctions
{
    private static readonly double InvSqrtPi = 1 / Math.Sqrt(Math.PI);

    /// <summary>
    /// Complementary error function. Below x = 1.5, 1 − erf(x) with erf from its series
    /// erf(x) = (2/√π)·e^{−x²}·Σ 2ⁿx^{2n+1} / (1·3·…·(2n+1)), whose terms are all positive. From 1.5
    /// up, Laplace's continued fraction erfc(x) = (e^{−x²}/√π) / (x + (1/2)/(x + 1/(x + (3/2)/(x + …)))),
    /// evaluated with the modified Lentz method. Negative x uses erfc(−x) = 2 − erfc(x). Relative
    /// error below 1e-13 against the C library wherever the result is a normal double.
    /// </summary>
    public static double Erfc(double x)
    {
        if (double.IsNaN(x))
            return double.NaN;
        if (x < 0)
            return 2 - Erfc(-x);
        if (x < 1.5)
            return 1 - ErfSeries(x);
        if (x > 27.3)
            return 0; // e^{−x²} underflows
        const double tiny = 1e-300;
        double f = x, c = x, d = 0;
        for (int n = 1; n < 10_000; n++)
        {
            double a = n / 2.0;
            d = x + a * d;
            if (d == 0) d = tiny;
            c = x + a / c;
            if (c == 0) c = tiny;
            d = 1 / d;
            double delta = c * d;
            f *= delta;
            if (Math.Abs(delta - 1) < 1e-16)
                break;
        }
        return ExpMinusSquare(x) * InvSqrtPi / f;
    }

    private static double ErfSeries(double x)
    {
        double x2 = x * x, term = x, sum = x;
        for (int n = 1; n < 200; n++)
        {
            term *= 2 * x2 / (2 * n + 1);
            sum += term;
            if (term < sum * 1e-17)
                break;
        }
        return 2 * InvSqrtPi * ExpMinusSquare(x) * sum;
    }

    /// <summary>e^{−x²} without the rounding error of x²: with z = x rounded down to a multiple of
    /// 1/16, z² is exact and e^{−x²} = e^{−z²}·e^{(z−x)(z+x)}.</summary>
    private static double ExpMinusSquare(double x)
    {
        double z = Math.Floor(x * 16) / 16;
        return Math.Exp(-z * z) * Math.Exp((z - x) * (z + x));
    }
}
