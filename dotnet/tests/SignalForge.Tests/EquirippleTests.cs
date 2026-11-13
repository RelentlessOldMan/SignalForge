using Xunit;

namespace SignalForge.Tests;

/// <summary>Equiripple FIR design (conventions: FIR filters, Equiripple design); the shared
/// vectors hold the exact optima, these check the design's properties.</summary>
public class EquirippleTests
{
    private static readonly double[] Lowpass = [0, 0.1, 0.15, 0.5];

    /// <summary>Largest |A(f) − want| on a dense grid over [lo, hi] (normalized frequency).</summary>
    private static double Worst(double[] taps, double lo, double hi, double want)
    {
        double worst = 0, c = (taps.Length - 1) / 2.0;
        for (int i = 0; i <= 4000; i++)
        {
            double f = lo + (hi - lo) * i / 4000, a = 0;
            for (int n = 0; n < taps.Length; n++)
                a += taps[n] * Math.Cos(2 * Math.PI * f * (n - c));
            worst = Math.Max(worst, Math.Abs(a - want));
        }
        return worst;
    }

    [Theory]
    [InlineData(40)]
    [InlineData(41)]
    public void ErrorsAreLevelAcrossBands(int n)
    {
        double[] h = Dsp.FirEquiripple(n, Lowpass, [1, 0], 1);
        for (int i = 0; i < n; i++)
            Assert.Equal(h[i], h[n - 1 - i], 15);
        double pass = Worst(h, 0, 0.1, 1), stop = Worst(h, 0.15, 0.5, 0);
        Assert.InRange(pass / stop, 0.98, 1.02);
        double[] w = Dsp.FirEquiripple(n, Lowpass, [1, 0], 1, [1, 10]);
        Assert.InRange(Worst(w, 0, 0.1, 1) / (10 * Worst(w, 0.15, 0.5, 0)), 0.98, 1.02);
        Assert.True(Worst(w, 0.15, 0.5, 0) < stop && stop < Worst(w, 0, 0.1, 1));
        if (n % 2 == 0)
            Assert.True(Math.Abs(h.Select((v, i) => i % 2 == 0 ? v : -v).Sum()) < 1e-15); // type II: H(fs/2) = 0
    }

    [Fact]
    public void BeatsAWindowedDesignAndImprovesWithLength()
    {
        double[] h = Dsp.FirEquiripple(41, Lowpass, [1, 0], 1), windowed = Dsp.FirLowpass(41, 0.125, 1);
        double worst = Math.Max(Worst(h, 0, 0.1, 1), Worst(h, 0.15, 0.5, 0));
        Assert.True(worst < Math.Max(Worst(windowed, 0, 0.1, 1), Worst(windowed, 0.15, 0.5, 0)));
        double[] longer = Dsp.FirEquiripple(61, Lowpass, [1, 0], 1);
        Assert.True(Math.Max(Worst(longer, 0, 0.1, 1), Worst(longer, 0.15, 0.5, 0)) < worst / 2);
    }

    [Fact]
    public void ScalesWithSampleRateAndDefaultsWeightsToOne()
    {
        double[] h = Dsp.FirEquiripple(31, Lowpass, [1, 0], 1);
        Assert.Equal(h, Dsp.FirEquiripple(31, Lowpass, [1, 0], 1, [1, 1]));
        double[] hz = Dsp.FirEquiripple(31, Lowpass.Select(b => b * 48000).ToArray(), [1, 0], 48000);
        for (int i = 0; i < h.Length; i++)
            Assert.Equal(h[i], hz[i], 15);
    }

    [Theory]
    [InlineData(45)]
    [InlineData(51)]
    [InlineData(61)]
    [InlineData(101)]
    [InlineData(301)]
    public void NearThePrecisionLimitRaisesOrMeetsItsBound(int n)
    {
        double[] h;
        try
        {
            h = Dsp.FirEquiripple(n, [0, 0.1, 0.4, 0.5], [1, 0], 1);
        }
        catch (ArgumentException e)
        {
            Assert.Contains("beyond double precision", e.Message, StringComparison.Ordinal);
            return;
        }
        Assert.True(Math.Max(Worst(h, 0, 0.1, 1), Worst(h, 0.4, 0.5, 0)) < 1e-9);
    }

    [Fact]
    public void WithLargeCoefficientsStillDesigns()
    {
        // Wide unweighted gaps make the taps reach about 1e4, so rounding in the final check is
        // about 5e-6 of the ripple: the design is usable and must not be rejected (found by a
        // random sweep).
        double[] b = [0, 0.23, 0.274, 0.289, 0.476, 0.4786], d = [1.46, 0, 0.556], w = [70.7, 2.78, 1.24];
        double[] h = Dsp.FirEquiripple(52, b, d, 1, w);
        double[] errs = [.. Enumerable.Range(0, 3).Select(j => w[j] * Worst(h, b[2 * j], b[2 * j + 1], d[j]))];
        Assert.True(errs.Max() < 1.3 * errs.Min()); // level, up to the grid effect between grid points
    }

    [Fact]
    public void WideGapsStartFromASmallerDesign()
    {
        // The index start gives this design a first δ below rounding and the exchange cycled until
        // it raised, though the optimum ripple is 6.5e-7; reference scaling starts it near the
        // extrema (found by a random sweep).
        double[] b = [0.045842972619715705, 0.18121475027229406, 0.22904058535303767, 0.27596522538729434, 0.35395230478805423, 0.4455572971806905, 0.4698891486665091, 0.47147747032588316];
        double[] d = [0, 1, 1, 1.1481133446514442];
        double[] h = Dsp.FirEquiripple(168, b, d, 1, gridDensity: 32);
        double[] errs = [.. Enumerable.Range(0, 4).Select(j => Worst(h, b[2 * j], b[2 * j + 1], d[j]))];
        Assert.True(errs.Min() > 6e-7 && errs.Max() < 1.3 * errs.Min());
    }

    [Fact]
    public void HilbertTransformerTurnsCosineIntoSine()
    {
        double[] h = Dsp.FirEquiripple(101, [0.02, 0.48], [1], 1, kind: EquirippleKind.Hilbert);
        Assert.Equal(h, h.Reverse().Select(v => -v));
        double[] x = [.. Enumerable.Range(0, 600).Select(n => Math.Cos(2 * Math.PI * 0.13 * n))];
        double[] y = Dsp.Convolve(x, h);
        for (int n = 200; n < 600; n++)
            Assert.True(Math.Abs(y[n] - Math.Sin(2 * Math.PI * 0.13 * (n - 50))) < 1e-3); // ripple 6.3e-4
    }

    [Theory]
    [InlineData(31)]
    [InlineData(32)]
    public void DifferentiatorGivesTheDerivativePerSample(int taps)
    {
        double[] h = Dsp.FirEquiripple(taps, [0, 0.4], [2], 1, kind: EquirippleKind.Differentiator);
        Assert.Equal(h, h.Reverse().Select(v => -v));
        double[] x = [.. Enumerable.Range(0, 400).Select(n => Math.Sin(2 * Math.PI * 0.1 * n))];
        double[] y = Dsp.Convolve(x, h);
        double c = (taps - 1) / 2.0, slope = 2 * 2 * Math.PI * 0.1;
        for (int n = 100; n < 400; n++)
            Assert.True(Math.Abs(y[n] - slope * Math.Cos(2 * Math.PI * 0.1 * (n - c))) < 1e-3 * slope);
    }

    [Fact]
    public void AntisymmetricBadArgumentsThrow()
    {
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirEquiripple(21, [0.1, 0.4], [1], 1, kind: (EquirippleKind)7));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirEquiripple(1, [0.1, 0.4], [1], 1, kind: EquirippleKind.Hilbert));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirEquiripple(21, [0, 0.4], [1], 1, kind: EquirippleKind.Hilbert));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirEquiripple(21, [0, 0.5], [1], 1, kind: EquirippleKind.Differentiator));
    }

    [Fact]
    public void BadArgumentsThrow()
    {
        Assert.Throws<ArgumentNullException>(() => Dsp.FirEquiripple(21, null!, [1, 0], 1));
        Assert.Throws<ArgumentNullException>(() => Dsp.FirEquiripple(21, Lowpass, null!, 1));
        Assert.Throws<ArgumentException>(() => Dsp.FirEquiripple(21, [0, 0.1, double.NaN, 0.5], [1, 0], 1));
        Assert.Throws<ArgumentException>(() => Dsp.FirEquiripple(21, Lowpass, [1, double.PositiveInfinity], 1));
        Assert.Throws<ArgumentException>(() => Dsp.FirEquiripple(21, Lowpass, [1, 0], 1, [1, double.NaN]));
        Assert.Throws<ArgumentOutOfRangeException>(() => Dsp.FirEquiripple(21, Lowpass, [1, 0], 1, gridDensity: 0));
    }
}
