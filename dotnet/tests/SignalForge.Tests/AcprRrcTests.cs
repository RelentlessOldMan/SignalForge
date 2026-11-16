using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>ACPR through a root-raised-cosine channel filter (conventions: Spectra, ACPR;
/// ADR 0111).</summary>
public class AcprRrcTests
{
    private static readonly double[] F = [.. Enumerable.Range(-256, 512).Select(k => k / 8.0)]; // 1/8 Hz bins
    private static readonly double[] Offsets = [5.0, 9.5];
    private static readonly double[] Ten = [10.0];

    [Theory]
    [InlineData(0.1, 0.0)]
    [InlineData(0.22, 0.03)]
    [InlineData(0.35, -1.3)]
    [InlineData(1.0, 2.0625)]
    public void FlatPsdReadsLevelTimesSymbolRateWhereverTheBinsFall(double alpha, double center)
    {
        // R/delta = 24 is whole, so the raised cosine's bin sum is exactly R (Poisson summation)
        Acpr r = Spectral.AcprRrc(F, [.. F.Select(_ => 0.5)], center, 3.0, alpha, Offsets);
        Assert.Equal(1.5, r.MainPower, 1e-12);
        foreach (double p in r.LowerPower.Concat(r.UpperPower))
            Assert.Equal(1.5, p, 1e-12);
    }

    [Theory]
    [InlineData(0.25)]
    [InlineData(1.0)]
    public void ASingleLineReadsTheSquaredCosineTaper(double alpha)
    {
        // G = cos^2(pi (|x| - (1 - a)R/2) / (2 a R)) on the taper: the same curve written differently
        const double rs = 4.0;
        double flat = (1 - alpha) * rs / 2, edge = (1 + alpha) * rs / 2;
        for (int k = 0; k < F.Length; k++)
        {
            double x = Math.Abs(F[k] - 10.0);
            if (x > edge + 1)
                continue;
            double[] psd = new double[F.Length];
            psd[256] = 1.0;
            psd[k] = 2.0;
            Acpr r = Spectral.AcprRrc(F, psd, 0.0, rs, alpha, Ten);
            double g = x >= edge ? 0 : x <= flat ? 1 : Math.Pow(Math.Cos(Math.PI * (x - flat) / (2 * alpha * rs)), 2);
            Assert.Equal(2.0 * 0.125 * g, r.UpperPower[0], 1e-15);
        }
    }

    [Fact]
    public void RrcQpskKeepsOneMinusAlphaOverFourAndLeaksNothingNextDoor()
    {
        // A transmit RRC gives a raised-cosine PSD; through the receive weight it integrates to
        // R (1 - alpha/4) of the total R
        const int sps = 8;
        const double alpha = 0.35;
        var rng = new Random(11);
        byte[] bits = [.. Enumerable.Range(0, 40000).Select(_ => (byte)rng.Next(2))];
        Complex[] x = Dsp.PulseShape(Modulation.QpskMap(bits), Dsp.RrcTaps(alpha, sps, 32), sps);
        SpectralDensity s = Spectral.WelchPsd(x, sps, nperseg: 1024, window: WindowType.BlackmanHarris);
        double total = s.Psd.Sum() * (s.Frequencies[1] - s.Frequencies[0]);
        Acpr r = Spectral.AcprRrc(s.Frequencies, s.Psd, 0.0, 1.0, alpha, [1.0 + alpha, 2.0]);
        Assert.InRange(r.MainPower / total, (1 - alpha / 4) * 0.99, (1 - alpha / 4) * 1.01);
        Assert.All(r.LowerDbc.Concat(r.UpperDbc), d => Assert.True(d < -40, $"{d}"));
    }

    [Theory]
    [InlineData(0.5, 0.0, -1.0, 5.0)]
    [InlineData(1.5, 0.0, 3.0, 5.0)]
    [InlineData(0.5, 0.0, 3.0, 40.0)]
    [InlineData(0.5, 31.0, 3.0, 5.0)]
    [InlineData(0.0, 0.0, 3.0, 5.0)]
    public void BadArgumentsThrow(double alpha, double center, double rs, double offset) =>
        Assert.ThrowsAny<ArgumentException>(() =>
            Spectral.AcprRrc(F, [.. F.Select(_ => 1.0)], center, rs, alpha, [offset]));
}
