using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Spectral flatness (conventions: Spectra, Spectral flatness; ADR 0120).</summary>
public class SpectralFlatnessTests
{
    private static double Gauss(Random rng) =>
        Math.Sqrt(-2 * Math.Log(1 - rng.NextDouble())) * Math.Cos(2 * Math.PI * rng.NextDouble());

    private static double[] Axis(int n) => [.. Enumerable.Range(0, n).Select(k => (double)k)];

    [Theory]
    [InlineData(1.0, 10.0, 100)]
    [InlineData(0.5, 2.0, 37)]
    [InlineData(3.0, 1e-3, 250)]
    public void TwoLevelClosedForm(double x, double y, int count)
    {
        const int N = 1000;
        double[] psd = [.. Enumerable.Range(0, N).Select(k => k < count ? x : y)];
        double a = (double)count / N;
        double want = Math.Pow(x, a) * Math.Pow(y, 1 - a) / (a * x + (1 - a) * y);
        var r = Spectral.SpectralFlatness(Axis(N), psd);
        Assert.Equal(want, r.Flatness, want * 1e-12);
        Assert.Equal(10 * Math.Log10(want), r.FlatnessDb, 1e-10);
    }

    [Fact]
    public void AToneIsFarFromFlat()
    {
        const int N = 4096;
        var rng = new Random(120);
        double[] x = [.. Enumerable.Range(0, N).Select(n => Math.Cos(2 * Math.PI * 200 * n / N) + 1e-6 * Gauss(rng))];
        var d = Spectral.WelchPsd(x, 1.0, nperseg: N);
        Assert.True(Spectral.SpectralFlatness(d.Frequencies, d.Psd).Flatness < 1e-6);
    }

    [Fact]
    public void WhiteNoiseIsNearlyFlat()
    {
        // a periodogram bin of white noise is exponential, so E ln d = ln E d − Euler's γ
        const int N = 1 << 16;
        var rng = new Random(1200);
        var x = new Complex[N];
        for (int i = 0; i < N; i++)
            x[i] = new Complex(Gauss(rng), Gauss(rng));
        var d = Spectral.WelchPsd(x, 1.0, nperseg: N, window: WindowType.Rectangular);
        double want = Math.Exp(-0.5772156649);
        Assert.Equal(want, Spectral.SpectralFlatness(d.Frequencies, d.Psd).Flatness, want * 1e-2);
    }

    [Fact]
    public void ScalingThePsdLeavesTheFlatness()
    {
        var rng = new Random(3);
        double[] p = [.. Enumerable.Range(0, 64).Select(_ => 0.1 + 1.9 * rng.NextDouble())];
        double[] q = [.. p.Select(v => 1e6 * v)];
        var a = Spectral.SpectralFlatness(Axis(64), p, (10.3, 40.8));
        var b = Spectral.SpectralFlatness(Axis(64), q, (10.3, 40.8));
        Assert.Equal(a.Flatness, b.Flatness, a.Flatness * 1e-12);
        Assert.Equal(1e6 * a.ArithmeticMean, b.ArithmeticMean, 1e6 * a.ArithmeticMean * 1e-12);
    }

    [Fact]
    public void FlatnessIsAtMostOne()
    {
        var rng = new Random(4);
        for (int t = 0; t < 20; t++)
        {
            double[] p = [.. Enumerable.Range(0, 50).Select(_ => rng.NextDouble())];
            double f = Spectral.SpectralFlatness(Axis(50), p).Flatness;
            Assert.InRange(f, 0, 1 + 1e-15);
        }
    }
}
