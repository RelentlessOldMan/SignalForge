using Xunit;

namespace SignalForge.Tests;

/// <summary>Harmonic series (conventions: Spectra, Harmonic series; ADR 0139).</summary>
public class HarmonicSeriesTests
{
    private static readonly double[] Tones = [151, 299.5, 452, 601, 1000];

    [Fact]
    public void OrderOfTonesDoesNotMatter()
    {
        var a = Spectral.HarmonicSeries(Tones, 3);
        int[] perm = [3, 0, 4, 2, 1];
        var b = Spectral.HarmonicSeries([.. perm.Select(k => Tones[k])], 3);
        Assert.Equal(a.Fundamental, b.Fundamental, 1e-12 * a.Fundamental);
        Assert.Equal(perm.Select(k => a.Orders[k]), b.Orders);
        Assert.Equal(4, a.Matched);
        Assert.Equal(4, b.Matched);
    }

    [Fact]
    public void ScalingScalesTheFundamental()
    {
        var a = Spectral.HarmonicSeries(Tones, 3);
        var b = Spectral.HarmonicSeries([.. Tones.Select(v => 2.5 * v)], 7.5);
        Assert.Equal(2.5 * a.Fundamental, b.Fundamental, 1e-12 * b.Fundamental);
        Assert.Equal(a.Orders, b.Orders);
    }

    [Fact]
    public void ClippedSineFromFindTones()
    {
        const int n = 4096;
        const double fs = 4096, f0 = 210.3;
        var x = new System.Numerics.Complex[n];
        for (int i = 0; i < n; i++)
            x[i] = Math.Clamp(Math.Sin(2 * Math.PI * f0 * i / fs), -0.7, 0.7) * (0.5 - 0.5 * Math.Cos(2 * Math.PI * i / (n - 1)));
        double[] psd = [.. Spectral.Fft(x).Take(n / 2 + 1).Select(v => v.Magnitude * v.Magnitude)];
        double[] f = [.. Enumerable.Range(0, n / 2 + 1).Select(k => k * fs / n)];
        var tones = Spectral.FindTones(f, psd, 4);
        var got = Spectral.HarmonicSeries([.. tones.Select(t => t.Frequency)], 1);
        Assert.Equal(4, got.Matched);
        Assert.All(got.Orders, o => Assert.Equal(1, o % 2)); // a symmetric clip adds odd harmonics
        Assert.Equal(f0, got.Fundamental, 0.02);
    }
}
