using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Multitaper line removal (conventions: Spectra, Multitaper line removal; ADR 0083).</summary>
public sealed class MultitaperLineRemovalTests
{
    private static Func<double> Gauss(int seed)
    {
        var rng = new Random(seed);
        return () => Math.Sqrt(-2 * Math.Log(1 - rng.NextDouble())) * Math.Cos(2 * Math.PI * rng.NextDouble());
    }

    private static double[] NoisyLine(int seed, int n = 256)
    {
        var g = Gauss(seed);
        return [.. Enumerable.Range(0, n).Select(t => (2 * Math.Cos((2 * Math.PI * 40 / n * t) + 0.3)) + (0.1 * g()))];
    }

    private static Complex[] PaddedFft(IEnumerable<Complex> x, int m)
    {
        var buf = new Complex[m];
        int i = 0;
        foreach (var v in x)
            buf[i++] = v;
        return Spectral.Fft(buf);
    }

    [Fact]
    public void FindsTheLineAndRestoresTheFloor()
    {
        double[] x = NoisyLine(1);
        var r = Spectral.MultitaperLineRemoval(x, 1.0, 4.0, probability: 1e-6);
        Assert.Equal([40 / 256.0], r.LineFrequencies);
        Assert.True(Complex.Abs(r.LineAmplitudes[0] - Complex.FromPolarCoordinates(1, 0.3)) < 0.02); // A/2 e^{iφ}
        double[] before = Spectral.MultitaperPsd(x, 1.0, 4.0).Psd[36..45];
        double[] after = r.Spectrum.Psd[36..45];
        Assert.True(before.Min() > 100 * 0.02 && after.Max() < 4 * 0.02); // one-sided floor 2σ²
    }

    [Fact]
    public void RemovalIsSubtractionFromEveryEigencoefficient()
    {
        double[] x = NoisyLine(2, 64);
        const int m = 80;
        var r = Spectral.MultitaperLineRemoval(x, 1.0, 3.0, probability: 1e-6, nfft: m);
        int b = (int)Math.Round(Assert.Single(r.LineFrequencies) * m);
        Complex mu = r.LineAmplitudes[0];
        foreach (double[] v in Spectral.DpssTapers(x.Length, 3.0).Tapers)
        {
            Complex[] got = PaddedFft(v.Zip(r.Residual, (a, y) => new Complex(a * y, 0)), m);
            Complex[] xs = PaddedFft(v.Zip(x, (a, y) => new Complex(a * y, 0)), m);
            Complex[] up = PaddedFft(v.Select((a, n) => a * Complex.FromPolarCoordinates(1, 2 * Math.PI * b * n / m)), m);
            Complex[] down = PaddedFft(v.Select((a, n) => a * Complex.FromPolarCoordinates(1, -2 * Math.PI * b * n / m)), m);
            for (int i = 0; i < m; i++)
                Assert.True(Complex.Abs(got[i] - (xs[i] - (mu * up[i]) - (Complex.Conjugate(mu) * down[i]))) < 1e-12);
        }
    }

    [Fact]
    public void OneLinePerPeakWhenPadded()
    {
        const int n = 128;
        var g = Gauss(3);
        Complex[] z = [.. Enumerable.Range(0, n).Select(t => (1.5 * Complex.FromPolarCoordinates(1, 2 * Math.PI * 0.2137 * t)) + (0.05 * g()))];
        var test = Spectral.HarmonicFTest(z, 1.0, 4.0, nfft: 8 * n);
        Assert.True(test.PValues.Count(p => p < 1e-6) > 1); // several padded bins pass the threshold alone
        var r = Spectral.MultitaperLineRemoval(z, 1.0, 4.0, probability: 1e-6, nfft: 8 * n);
        Assert.True(Math.Abs(Assert.Single(r.LineFrequencies) - 0.2137) <= 0.5 / (8 * n));
    }

    [Fact]
    public void NoLinesLeavesTheInput()
    {
        var g = Gauss(4);
        double[] x = [.. Enumerable.Range(0, 50).Select(_ => g())];
        var r = Spectral.MultitaperLineRemoval(x, 2.0, 2.5, probability: 1e-9, adaptive: true);
        Assert.Empty(r.LineFrequencies);
        Assert.Empty(r.LineAmplitudes);
        Assert.Equal(x, r.Residual);
        Assert.Equal(Spectral.MultitaperPsd(x, 2.0, 2.5, adaptive: true).Psd, r.Spectrum.Psd);
    }

    [Fact]
    public void Rejects()
    {
        double[] x = NoisyLine(5, 32);
        foreach (double p in new[] { 0.0, 1.5, double.NaN })
            Assert.ThrowsAny<ArgumentException>(() => Spectral.MultitaperLineRemoval(x, 1.0, 2.0, probability: p));
        Assert.ThrowsAny<ArgumentException>(() => Spectral.MultitaperLineRemoval(x, 1.0, 2.0, numTapers: 1));
        Assert.ThrowsAny<ArgumentException>(() => Spectral.MultitaperLineRemoval(x, 1.0, 2.0, nfft: 31));
    }
}
