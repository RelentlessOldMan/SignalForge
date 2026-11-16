using Xunit;

namespace SignalForge.Tests;

/// <summary>Odd-to-even harmonic ratio (conventions: Spectra, Odd-to-even ratio; ADR 0141).</summary>
public class OddEvenRatioTests
{
    private static readonly double[] Heights = [5, 3, 2, 1, 0.5];
    private static readonly int[] Orders = [1, 2, 3, 4, 0];

    [Fact]
    public void ScalingHeightsLeavesItUnchanged()
    {
        double a = Spectral.OddEvenRatio(Heights, Orders);
        double b = Spectral.OddEvenRatio([.. Heights.Select(h => 6 * h)], Orders);
        Assert.Equal(a, b, 1e-12 * a);
    }

    [Fact]
    public void PermutingTonesLeavesItUnchanged()
    {
        int[] perm = [4, 2, 0, 3, 1];
        double a = Spectral.OddEvenRatio(Heights, Orders);
        double b = Spectral.OddEvenRatio([.. perm.Select(k => Heights[k])], [.. perm.Select(k => Orders[k])]);
        Assert.Equal(a, b, 1e-12 * a);
    }

    [Fact]
    public void ClippedSineIsOddOnly()
    {
        const int n = 4096;
        const double fs = 4096, f0 = 210.3;
        var x = new System.Numerics.Complex[n];
        for (int i = 0; i < n; i++)
            x[i] = Math.Clamp(Math.Sin(2 * Math.PI * f0 * i / fs), -0.7, 0.7) * (0.5 - 0.5 * Math.Cos(2 * Math.PI * i / (n - 1)));
        double[] psd = [.. Spectral.Fft(x).Take(n / 2 + 1).Select(v => v.Magnitude * v.Magnitude)];
        double[] f = [.. Enumerable.Range(0, n / 2 + 1).Select(k => k * fs / n)];
        var tones = Spectral.FindTones(f, psd, 4);
        var series = Spectral.HarmonicSeries([.. tones.Select(t => t.Frequency)], 1);
        Assert.Equal(double.PositiveInfinity, Spectral.OddEvenRatio([.. tones.Select(t => t.Height)], series.Orders));
    }
}
