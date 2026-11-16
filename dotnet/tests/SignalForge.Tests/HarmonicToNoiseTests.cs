using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Harmonic-to-noise ratio (conventions: Spectra, Harmonic-to-noise ratio; ADR 0143).</summary>
public class HarmonicToNoiseTests
{
    private static readonly double[] Freqs = [.. Enumerable.Range(0, 64).Select(k => 5.0 * k)];
    private static readonly double[] Psd = [.. Freqs.Select(f => 1 + Math.Pow(Math.Cos(f / 7), 2))];

    [Fact]
    public void ScalingPsdLeavesRatioUnchanged()
    {
        var a = Spectral.HarmonicToNoise(Freqs, Psd, 40, 5);
        var b = Spectral.HarmonicToNoise(Freqs, [.. Psd.Select(p => 9 * p)], 40, 5);
        Assert.Equal(a.Ratio, b.Ratio, 1e-12 * a.Ratio);
        Assert.Equal(9 * a.Harmonic, b.Harmonic, 1e-12 * b.Harmonic);
    }

    [Fact]
    public void SineInWhiteNoise()
    {
        // A unit sine on a bin has power 1/2; white noise of variance 0.01 spreads 0.01 over the
        // one-sided spectrum, so the ratio is about 50. The noise sum has a spread of about 2 %.
        const int n = 4096;
        const double fs = 4096, f0 = 1000, sigma = 0.1;
        var rng = new Random(143);
        var x = new Complex[n];
        for (int i = 0; i < n; i++)
        {
            double g = Math.Sqrt(-2 * Math.Log(1 - rng.NextDouble())) * Math.Cos(2 * Math.PI * rng.NextDouble());
            x[i] = Math.Sin(2 * Math.PI * f0 * i / fs) + sigma * g;
        }
        double[] psd = [.. Spectral.Fft(x).Take(n / 2 + 1).Select(v => 2 * v.Magnitude * v.Magnitude / ((double)n * n))];
        double[] f = [.. Enumerable.Range(0, n / 2 + 1).Select(k => k * fs / n)];
        var got = Spectral.HarmonicToNoise(f, psd, f0, 0);
        Assert.InRange(got.Ratio, 45, 55);
    }
}
