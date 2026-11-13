using System.Numerics;

namespace SignalForge;

public static partial class Dsp
{
    /// <summary>Bessel (maximally flat delay) low-pass by the bilinear transform, as second-order
    /// sections <c>[b0, b1, b2, a0, a1, a2]</c>, −3 dB at the cutoff (conventions: IIR filters).</summary>
    /// <param name="order">Filter order, 1 to 10.</param>
    /// <param name="cutoff">−3 dB frequency in Hz, between 0 and sampleRate/2.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    public static double[][] BesselLowpass(int order, double cutoff, double sampleRate) =>
        Bessel(order, cutoff, sampleRate, false);

    /// <summary>Bessel high-pass by the bilinear transform, as second-order sections
    /// <c>[b0, b1, b2, a0, a1, a2]</c>, −3 dB at the cutoff (conventions: IIR filters).</summary>
    /// <param name="order">Filter order, 1 to 10.</param>
    /// <param name="cutoff">−3 dB frequency in Hz, between 0 and sampleRate/2.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    public static double[][] BesselHighpass(int order, double cutoff, double sampleRate) =>
        Bessel(order, cutoff, sampleRate, true);

    /// <summary>Bessel band-pass from the low-pass prototype of that order, by the bilinear
    /// transform, as <paramref name="order"/> second-order sections <c>[b0, b1, b2, a0, a1, a2]</c>,
    /// −3 dB at low and high (conventions: IIR filters).</summary>
    /// <param name="order">Order of the low-pass prototype, 1 to 10; the filter's order is twice it.</param>
    /// <param name="low">Lower −3 dB frequency in Hz, between 0 and sampleRate/2.</param>
    /// <param name="high">Upper −3 dB frequency in Hz, above <paramref name="low"/> and below sampleRate/2.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    public static double[][] BesselBandpass(int order, double low, double high, double sampleRate) =>
        BesselBand(order, low, high, sampleRate, false);

    /// <summary>Bessel band-stop from the low-pass prototype of that order, by the bilinear
    /// transform, as <paramref name="order"/> second-order sections <c>[b0, b1, b2, a0, a1, a2]</c>,
    /// −3 dB at low and high (conventions: IIR filters).</summary>
    /// <param name="order">Order of the low-pass prototype, 1 to 10; the filter's order is twice it.</param>
    /// <param name="low">Lower −3 dB frequency in Hz, between 0 and sampleRate/2.</param>
    /// <param name="high">Upper −3 dB frequency in Hz, above <paramref name="low"/> and below sampleRate/2.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    public static double[][] BesselBandstop(int order, double low, double high, double sampleRate) =>
        BesselBand(order, low, high, sampleRate, true);

    private static Complex[] BesselPoles(int order)
    {
        if (order is < 1 or > 10)
            throw new ArgumentOutOfRangeException(nameof(order), order, "must be between 1 and 10: higher Bessel poles are lost to rounding");
        return BesselPrototype(order);
    }

    private static double[][] Bessel(int order, double cutoff, double sampleRate, bool high)
    {
        Complex[] poles = BesselPoles(order);
        return Cascade(order, cutoff, sampleRate, high, i => poles[i]);
    }

    private static double[][] BesselBand(int order, double low, double high, double sampleRate, bool stop)
    {
        Complex[] poles = BesselPoles(order);
        return Band(order, low, high, sampleRate, stop, i => poles[i]);
    }

    /// <summary>The reverse Bessel polynomial and its derivative at s, by the recurrence.</summary>
    private static (Complex T, Complex D) BesselTheta(int n, Complex s)
    {
        Complex t0 = 1, t1 = s + 1, d0 = 0, d1 = 1;
        for (int k = 2; k <= n; k++)
            (t0, t1, d0, d1) = (t1, (2 * k - 1) * t1 + s * s * t0, d1, (2 * k - 1) * d1 + 2 * s * t0 + s * s * d0);
        return (t1, d1);
    }

    /// <summary>The Bessel prototype's poles normalized to −3 dB at 1 (conventions: Bessel design):
    /// pair i's upper pole for i &lt; n/2, from the highest Q, then the real pole for an odd n.</summary>
    private static Complex[] BesselPrototype(int n)
    {
        double a0 = 1; // (2n)!/(2^n n!) = (n+1)(n+2)...(2n)/2^n, exact in double for n ≤ 10
        for (int k = n + 1; k <= 2 * n; k++)
            a0 *= k;
        a0 /= Math.Pow(2, n);
        double r = Math.Pow(a0, 1.0 / n); // the roots' geometric mean; Aberth starts on Butterworth's angles
        var z = new Complex[n];
        for (int i = 0; i < n; i++)
            z[i] = r * Complex.Exp(Complex.ImaginaryOne * Theta(i, n));
        var steps = new Complex[n];
        for (int it = 0; it < 100; it++)
        {
            for (int i = 0; i < n; i++)
            {
                var (t, dt) = BesselTheta(n, z[i]);
                Complex w = t / dt, sum = 0;
                for (int j = 0; j < n; j++)
                {
                    if (j != i)
                        sum += 1 / (z[i] - z[j]);
                }
                steps[i] = w / (1 - w * sum);
            }
            double worst = 0;
            for (int i = 0; i < n; i++)
            {
                z[i] -= steps[i];
                worst = Math.Max(worst, Complex.Abs(steps[i]) / Complex.Abs(z[i]));
            }
            if (worst <= 1e-15)
                break;
        }
        for (int i = 0; i < n; i++)
        {
            var (t, dt) = BesselTheta(n, z[i]);
            z[i] -= t / dt; // a Newton step
        }
        double lo = 0, hi = 1; // ω0: |θ(jω)|² = 2θ(0)², increasing in ω
        while (Math.Pow(Complex.Abs(BesselTheta(n, new Complex(0, hi)).T), 2) < 2 * a0 * a0)
            hi *= 2;
        for (double mid = (lo + hi) / 2; lo < mid && mid < hi; mid = (lo + hi) / 2)
        {
            if (Math.Pow(Complex.Abs(BesselTheta(n, new Complex(0, mid)).T), 2) < 2 * a0 * a0)
                lo = mid;
            else
                hi = mid;
        }
        double w0 = (lo + hi) / 2;
        var pairs = z.Where(p => p.Imaginary > 1e-12 * Complex.Abs(p)).OrderBy(p => p.Imaginary / p.Real).Select(p => p / w0);
        var real = z.Where(p => Math.Abs(p.Imaginary) <= 1e-12 * Complex.Abs(p)).Select(p => new Complex(p.Real / w0, 0));
        return [.. pairs, .. real];
    }
}
