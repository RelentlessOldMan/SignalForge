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

    /// <summary>ln Γ(x) for x &gt; 0: shifted up to at least 15 by Γ(x+1) = x·Γ(x), then Stirling's
    /// series through the B₁₄ term (ADR 0201).</summary>
    public static double LogGamma(double x)
    {
        double product = 1;
        while (x < 15)
        {
            product *= x;
            x += 1;
        }
        double z2 = 1 / (x * x);
        double series = (1.0 / 12 + z2 * (-1.0 / 360 + z2 * (1.0 / 1260 + z2 * (-1.0 / 1680 + z2 * (1.0 / 1188
            + z2 * (-691.0 / 360360 + z2 * (1.0 / 156))))))) / x;
        return (x - 0.5) * Math.Log(x) - x + 0.5 * Math.Log(2 * Math.PI) + series - Math.Log(product);
    }

    /// <summary>The regularized incomplete gammas (P(a, x), Q(a, x)), a &gt; 0, x ≥ 0: the power series
    /// below a + 1, else Lentz's continued fraction for Q (ADR 0201).</summary>
    public static (double P, double Q) GammaPQ(double a, double x)
    {
        if (x <= 0)
            return (0, 1);
        double logPre = a * Math.Log(x) - x - LogGamma(a);
        if (x < a + 1)
        {
            double term = 1 / a, total = term;
            for (int n = 1; n < 100000 && Math.Abs(term) > Math.Abs(total) * 1e-17; n++)
            {
                term *= x / (a + n);
                total += term;
            }
            double p = total * Math.Exp(logPre);
            return (p, 1 - p);
        }
        const double Tiny = 1e-300;
        double b = x + 1 - a, c = 1 / Tiny, d = 1 / b, h = d;
        for (int i = 1; i < 100000; i++)
        {
            double an = -i * (i - a);
            b += 2;
            d = an * d + b;
            if (Math.Abs(d) < Tiny)
                d = Tiny;
            c = b + an / c;
            if (Math.Abs(c) < Tiny)
                c = Tiny;
            d = 1 / d;
            double delta = d * c;
            h *= delta;
            if (Math.Abs(delta - 1) < 1e-16)
                break;
        }
        double q = Math.Exp(logPre) * h;
        return (1 - q, q);
    }

    /// <summary>The chi-squared quantile 2y with P(dof/2, y) = p, by safeguarded Newton (ADR 0201).</summary>
    public static double ChiSquaredQuantile(double p, double dof)
    {
        double a = dof / 2;
        bool upper = p > 0.5;
        double G(double y)
        {
            var (lower, uq) = GammaPQ(a, y);
            return upper ? (1 - p) - uq : lower - p;
        }
        double lo = 0, hi = Math.Max(a, 1);
        while (G(hi) < 0)
        {
            lo = hi;
            hi *= 2;
        }
        double yv = 0.5 * (lo + hi), lg = LogGamma(a);
        for (int it = 0; it < 400; it++)
        {
            double v = G(yv);
            if (v == 0)
                break;
            if (v < 0)
                lo = yv;
            else
                hi = yv;
            double dens = Math.Exp((a - 1) * Math.Log(yv) - yv - lg);
            double yn = dens > 0 ? yv - v / dens : 0.5 * (lo + hi);
            if (!(yn > lo && yn < hi))
                yn = 0.5 * (lo + hi);
            if (Math.Abs(yn - yv) <= 1e-15 * yn || hi - lo <= 1e-15 * hi)
            {
                yv = yn;
                break;
            }
            yv = yn;
        }
        return 2 * yv;
    }
}
