using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Find tones (conventions: Spectra, Find tones; ADR 0137).</summary>
public class FindTonesTests
{
    private static readonly double[] F = [.. Enumerable.Range(0, 12).Select(k => (double)k)];
    private static readonly double[] P = [0.5, 3, 1, 4, 3.5, 2, 6, 0.2, 1, 0.3, 2.5, 1.5];

    [Theory]
    [InlineData(PeakScale.Decibel)]
    [InlineData(PeakScale.Linear)]
    public void TonesAreTheInterpolatedTopPeaks(PeakScale scale)
    {
        var peaks = Spectral.SpectralPeaks(F, P).OrderByDescending(p => p.Prominence).Take(3).ToList();
        var got = Spectral.FindTones(F, P, 3, 0, scale);
        Assert.Equal(peaks.Select(p => p.Index), got.Select(t => t.Index));
        for (int k = 0; k < got.Count; k++)
        {
            var v = Spectral.InterpolatePeak(F, P, peaks[k].Index, scale);
            Assert.Equal(new Tone(peaks[k].Index, v.Frequency, v.Height, peaks[k].Prominence), got[k]);
        }
    }

    [Fact]
    public void TwoTonesInNoise()
    {
        const int n = 2048;
        const double fs = 2048;
        var rng = new Random(137);
        var x = new Complex[n];
        for (int i = 0; i < n; i++)
        {
            double t = i / fs;
            double noise = Math.Sqrt(-2 * Math.Log(1 - rng.NextDouble())) * Math.Cos(2 * Math.PI * rng.NextDouble());
            double s = 2 * Math.Cos(2 * Math.PI * 300.27 * t) + 0.5 * Math.Cos(2 * Math.PI * 611.6 * t) + 1e-3 * noise;
            x[i] = s * (0.5 - 0.5 * Math.Cos(2 * Math.PI * i / (n - 1)));
        }
        var spectrum = Spectral.Fft(x);
        double[] psd = [.. spectrum.Take(n / 2 + 1).Select(v => v.Magnitude * v.Magnitude)];
        double[] f = [.. Enumerable.Range(0, n / 2 + 1).Select(k => k * fs / n)];
        var got = Spectral.FindTones(f, psd, 2);
        Assert.InRange(got[0].Frequency, 300.27 - 0.05, 300.27 + 0.05);
        Assert.InRange(got[1].Frequency, 611.6 - 0.05, 611.6 + 0.05);
    }
}
