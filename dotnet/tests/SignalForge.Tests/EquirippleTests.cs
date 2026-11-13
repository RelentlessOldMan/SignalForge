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
