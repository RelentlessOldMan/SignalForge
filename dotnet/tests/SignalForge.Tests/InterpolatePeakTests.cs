using Xunit;

namespace SignalForge.Tests;

/// <summary>Peak interpolation (conventions: Spectra, Peak interpolation; ADR 0136).</summary>
public class InterpolatePeakTests
{
    private static readonly double[] K = [.. Enumerable.Range(0, 16).Select(k => (double)k)];

    [Theory]
    [InlineData(6.5)]
    [InlineData(6.75)]
    [InlineData(7.0)]
    [InlineData(7.1)]
    [InlineData(7.49)]
    public void DbFitRecoversAGaussian(double mu)
    {
        double[] psd = [.. K.Select(k => 3 * Math.Exp(-(k - mu) * (k - mu) / 8))];
        var got = Spectral.InterpolatePeak(K, psd, (int)Math.Round(mu, MidpointRounding.ToEven));
        Assert.Equal(mu, got.Frequency, 1e-12);
        Assert.Equal(3.0, got.Height, 1e-12 * 3);
    }

    [Theory]
    [InlineData(PeakScale.Decibel)]
    [InlineData(PeakScale.Linear)]
    public void ScalingScalesTheHeight(PeakScale scale)
    {
        double[] psd = [0.4, 1, 2.5, 3, 1.2, 0.3];
        var baseline = Spectral.InterpolatePeak(K.AsSpan(0, 6), psd, 3, scale);
        var scaled = Spectral.InterpolatePeak(K.AsSpan(0, 6), [.. psd.Select(v => 7 * v)], 3, scale);
        Assert.Equal(baseline.Offset, scaled.Offset, 1e-12);
        Assert.Equal(7 * baseline.Height, scaled.Height, 1e-12 * scaled.Height);
    }

    [Fact]
    public void HannToneBetweenBins()
    {
        const int n = 1024;
        const double fs = 1024, f0 = 100.3;
        var x = new System.Numerics.Complex[n];
        for (int i = 0; i < n; i++)
            x[i] = Math.Cos(2 * Math.PI * f0 * i / fs) * (0.5 - 0.5 * Math.Cos(2 * Math.PI * i / (n - 1)));
        var spectrum = Spectral.Fft(x);
        double[] psd = [.. spectrum.Take(n / 2 + 1).Select(v => v.Magnitude * v.Magnitude)];
        double[] f = [.. Enumerable.Range(0, n / 2 + 1).Select(k => k * fs / n)];
        int peak = Array.IndexOf(psd, psd.Max());
        var got = Spectral.InterpolatePeak(f, psd, peak);
        Assert.InRange(got.Frequency, f0 - 0.05, f0 + 0.05);
    }
}
