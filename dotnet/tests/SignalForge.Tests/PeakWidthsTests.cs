using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Peak widths (conventions: Spectra, Peak widths; ADR 0138).</summary>
public class PeakWidthsTests
{
    private static readonly double[] F = [.. Enumerable.Range(0, 12).Select(k => (double)k)];
    private static readonly double[] P = [0.5, 3, 1, 4, 3.5, 2, 6, 0.2, 1, 0.3, 2.5, 1.5];

    [Theory]
    [InlineData(0.25)]
    [InlineData(0.5)]
    [InlineData(1.0)]
    public void ScalingLeavesTheWidths(double rel)
    {
        var baseline = Spectral.PeakWidths(F, P, rel);
        var scaled = Spectral.PeakWidths(F, [.. P.Select(v => 8 * v)], rel);
        Assert.NotEmpty(baseline);
        for (int k = 0; k < baseline.Count; k++)
        {
            Assert.Equal(baseline[k].Width, scaled[k].Width, 1e-12 * baseline[k].Width);
            Assert.Equal(8 * baseline[k].Level, scaled[k].Level, 1e-12 * scaled[k].Level);
        }
    }

    [Fact]
    public void CrossingsBracketThePeak() =>
        Assert.All(Spectral.PeakWidths(F, P), w =>
        {
            Assert.InRange(F[w.Index], w.Left, w.Right);
            Assert.Equal(w.Right - w.Left, w.Width);
        });

    [Fact]
    public void HannHalfPowerWidth()
    {
        const int n = 256, pad = 32;
        var x = new Complex[n * pad];
        for (int i = 0; i < n; i++)
            x[i] = (0.5 - 0.5 * Math.Cos(2 * Math.PI * i / n)) * Complex.FromPolarCoordinates(1, 2 * Math.PI * 20 * i / n);
        double[] psd = [.. Spectral.Fft(x).Select(v => v.Magnitude * v.Magnitude)];
        double[] f = [.. Enumerable.Range(0, psd.Length).Select(k => (double)k / pad)];
        var main = Spectral.PeakWidths(f, psd).MaxBy(w => w.Level)!;
        Assert.Equal(1.4382, main.Width, 0.01);
    }
}
