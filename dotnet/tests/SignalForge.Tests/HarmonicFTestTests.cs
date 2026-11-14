using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Thomson's harmonic F-test (conventions: Spectra, Harmonic F-test; ADR 0080).</summary>
public sealed class HarmonicFTestTests
{
    private static double[] Gaussian(Random rng, int n)
    {
        var x = new double[n];
        for (int i = 0; i < n; i++)
            x[i] = Math.Sqrt(-2 * Math.Log(1 - rng.NextDouble())) * Math.Cos(2 * Math.PI * rng.NextDouble());
        return x;
    }

    [Fact]
    public void ExactBinComplexLineGivesItsAmplitude()
    {
        // by hand: X_j = A U_j at the line's bin, so μ = A and the residual is rounding
        const int n = 64;
        var a = new Complex(1.5, -0.5);
        Complex[] x = [.. Enumerable.Range(0, n).Select(i => a * Complex.FromPolarCoordinates(1, 2 * Math.PI * 5 * i / n))];
        HarmonicFTestResult r = Spectral.HarmonicFTest(x, 1.0, 3.0);
        int peak = Array.IndexOf(r.FStatistic, r.FStatistic.Max());
        Assert.Equal(5.0 / n, r.Frequencies[peak], 1e-15);
        Assert.True((r.Amplitudes[peak] - a).Magnitude < 1e-12);
        Assert.True(r.FStatistic[peak] > 1e20);
        Assert.Equal(5, r.NumTapers);
        Assert.Equal(n, r.Frequencies.Length); // complex input: the whole two-sided axis
    }

    [Fact]
    public void RealCosineGivesHalfItsAmplitude()
    {
        // measured: the −f image leaks 4.6e-6 into +f through the higher tapers at NW 4
        const int n = 1024;
        double[] x = [.. Enumerable.Range(0, n).Select(i => 0.8 * Math.Cos((2 * Math.PI * 100 * i / n) + 0.7))];
        HarmonicFTestResult r = Spectral.HarmonicFTest(x, 1.0, 4.0);
        Assert.Equal((n / 2) + 1, r.Frequencies.Length);
        Assert.True((r.Amplitudes[100] - Complex.FromPolarCoordinates(0.4, 0.7)).Magnitude < 1e-5);
    }

    [Fact]
    public void PValuesAreUniformUnderWhiteNoise()
    {
        // measured over 20 runs of 1024: 1.07% below 0.01, 5.22% below 0.05, 49.96% below 0.5
        var rng = new Random(1);
        var p = new List<double>();
        for (int run = 0; run < 20; run++)
            p.AddRange(Spectral.HarmonicFTest(Gaussian(rng, 1024), 1.0, 4.0).PValues[5..^5]);
        foreach (double level in new[] { 0.05, 0.2, 0.5 })
            Assert.True(Math.Abs((p.Count(v => v < level) / (double)p.Count) - level) < 0.015);
    }

    [Fact]
    public void FindsALineInNoise()
    {
        const int n = 4096;
        double[] y = Gaussian(new Random(2), n);
        for (int i = 0; i < n; i++)
            y[i] += 0.3 * Math.Cos(2 * Math.PI * 800 * i / n);
        HarmonicFTestResult r = Spectral.HarmonicFTest(y, 1.0, 4.0);
        Assert.Equal(800, Array.IndexOf(r.PValues, r.PValues.Min()));
        Assert.True(r.PValues[800] < 1e-5);
        Assert.True(Math.Abs(r.Amplitudes[800].Magnitude - 0.15) < 0.03);
    }

    [Fact]
    public void Rejects()
    {
        double[] x = [.. Enumerable.Repeat(1.0, 16)];
        Assert.ThrowsAny<ArgumentException>(() => Spectral.HarmonicFTest(x, 1.0, 2.0, numTapers: 1));
        Assert.ThrowsAny<ArgumentException>(() => Spectral.HarmonicFTest(x, 1.0, 1.0)); // default K = 1
        Assert.ThrowsAny<ArgumentException>(() => Spectral.HarmonicFTest(Array.Empty<double>(), 1.0, 1.0));
        Assert.ThrowsAny<ArgumentException>(() => Spectral.HarmonicFTest(x, 1.0, 2.0, nfft: 15));
        Assert.ThrowsAny<ArgumentException>(() => Spectral.HarmonicFTest(x, 0.0, 2.0));
        Assert.ThrowsAny<ArgumentException>(() => Spectral.HarmonicFTest(x, 1.0, 8.0));
    }
}
