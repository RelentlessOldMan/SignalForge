using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>DPSS tapers and the multitaper PSD (conventions: Spectra, DPSS tapers, Multitaper PSD;
/// ADR 0078).</summary>
public sealed class MultitaperTests
{
    private static double Sinc(double w, int d) => d == 0 ? 2 * w : Math.Sin(2 * Math.PI * w * d) / (Math.PI * d);

    [Theory]
    [InlineData(8, 1.0, 1)]
    [InlineData(31, 2.5, 4)]
    [InlineData(128, 4.0, 7)]
    [InlineData(257, 3.5, 6)]
    public void TapersSolveTheConcentrationProblem(int n, double nw, int k)
    {
        TaperSet t = Spectral.DpssTapers(n, nw, k);
        double w = nw / n;
        Assert.Equal(k, t.Tapers.Length);
        for (int p = 0; p < k; p++)
        {
            for (int q = 0; q < k; q++)
            {
                double dot = 0;
                for (int i = 0; i < n; i++)
                    dot += t.Tapers[p][i] * t.Tapers[q][i];
                Assert.True(Math.Abs(dot - (p == q ? 1 : 0)) < 1e-12);
            }
            double[] v = t.Tapers[p];
            double vav = 0;
            for (int i = 0; i < n; i++)
            {
                double av = 0;
                for (int j = 0; j < n; j++)
                    av += Sinc(w, i - j) * v[j];
                Assert.True(Math.Abs(av - (t.Concentrations[p] * v[i])) < 1e-11);
                vav += v[i] * av;
            }
            Assert.True(Math.Abs(vav - t.Concentrations[p]) < 1e-12);
            if (p > 0)
                Assert.True(t.Concentrations[p] < t.Concentrations[p - 1]);
        }
    }

    [Fact]
    public void DefaultCountAndConcentration()
    {
        TaperSet t = Spectral.DpssTapers(256, 4.0);
        Assert.Equal(7, t.Tapers.Length);
        Assert.All(t.Concentrations, c => Assert.True(c > 0.9));
        Assert.True(t.Concentrations[0] > 1 - 1e-9);
        Assert.Single(Spectral.DpssTapers(10, 0.4).Tapers);
    }

    [Fact]
    public void SignRuleAndSymmetry()
    {
        TaperSet t = Spectral.DpssTapers(40, 3.0, 5);
        for (int k = 0; k < 5; k++)
        {
            double[] v = t.Tapers[k];
            double s = 0;
            for (int i = 0; i < 40; i++)
            {
                s += k % 2 == 0 ? v[i] : (19.5 - i) * v[i];
                Assert.True(Math.Abs(v[i] - ((k % 2 == 0 ? 1 : -1) * v[39 - i])) < 1e-12);
            }
            Assert.True(s > 0);
        }
    }

    [Fact]
    public void WhiteNoiseLevel()
    {
        var rng = new Random(5);
        const double fs = 500, sigma = 0.7;
        var x = new double[4096];
        for (int i = 0; i < x.Length; i++)
            x[i] = sigma * Math.Sqrt(-2 * Math.Log(1 - rng.NextDouble())) * Math.Cos(2 * Math.PI * rng.NextDouble());
        SpectralDensity p = Spectral.MultitaperPsd(x, fs, 4.0);
        Assert.Equal(7, p.NumSegments);
        Assert.Equal(8.0 / 4096 * fs, p.EnbwHz, 1e-12);
        double mean = p.Psd.Skip(1).SkipLast(1).Average();
        Assert.True(Math.Abs((mean / (2 * sigma * sigma / fs)) - 1) < 0.02);
    }

    [Fact]
    public void ComplexTwoSidedTone()
    {
        const int n = 512;
        const double fs = 1000;
        var x = new Complex[n];
        for (int i = 0; i < n; i++)
            x[i] = 2.0 * Complex.FromPolarCoordinates(1, 2 * Math.PI * 125.0 * i / fs);
        SpectralDensity p = Spectral.MultitaperPsd(x, fs, 3.0);
        Assert.False(p.OneSided);
        int peak = Array.IndexOf(p.Psd, p.Psd.Max());
        Assert.Equal(125.0, p.Frequencies[peak], 1e-9);
        Assert.Equal(4.0, p.Psd.Sum() * p.BinWidth, 1e-11);
        double band = 0;
        for (int i = 0; i < p.Psd.Length; i++)
        {
            if (Math.Abs(p.Frequencies[i] - 125.0) <= 3.0 / n * fs)
                band += p.Psd[i] * p.BinWidth;
        }
        Assert.True(band > 0.99 * 4.0); // measured 0.996
    }

    [Fact]
    public void LeakageNearTheBand()
    {
        // measured (ADR 0078 tests): the first taper at NW 4 leaks 4e-11 of the peak from 6 bins out,
        // Hann 1e-6; all seven tapers are near the rectangular window
        const int n = 1024;
        const double f0 = 0.1013;
        double[] x = [.. Enumerable.Range(0, n).Select(i => Math.Sin(2 * Math.PI * f0 * i))];
        static double Leak(SpectralDensity p, double bins)
        {
            double far = 0;
            for (int i = 0; i < p.Psd.Length; i++)
            {
                if (Math.Abs(p.Frequencies[i] - f0) > bins / n)
                    far = Math.Max(far, p.Psd[i]);
            }
            return far / p.Psd.Max();
        }
        SpectralDensity one = Spectral.MultitaperPsd(x, 1.0, 4.0, numTapers: 1);
        SpectralDensity hann = Spectral.WelchPsd(x, 1.0, nperseg: n);
        foreach (double bins in new[] { 6.0, 10.0 })
            Assert.True(Leak(one, bins) < 1e-2 * Leak(hann, bins));
        Assert.True(Leak(Spectral.MultitaperPsd(x, 1.0, 4.0), 6) < 1e-2);
    }

    [Fact]
    public void NfftPads()
    {
        double[] x = [.. Enumerable.Range(0, 50).Select(i => Math.Cos(0.4 * i))];
        SpectralDensity p = Spectral.MultitaperPsd(x, 2.0, 2.0, nfft: 128);
        Assert.Equal(128, p.Nfft);
        Assert.Equal(65, p.Psd.Length);
        Assert.Equal(2.0 / 128, p.BinWidth, 1e-15);
        Assert.Equal(64 * 2.0 / 128, p.Frequencies[64], 1e-12);
    }

    [Fact]
    public void Rejects()
    {
        double[] x = new double[16];
        Assert.ThrowsAny<ArgumentException>(() => Spectral.DpssTapers(0, 0.5));
        foreach (double nw in new[] { 0.0, -1.0, 8.0, double.NaN, double.PositiveInfinity })
            Assert.ThrowsAny<ArgumentException>(() => Spectral.DpssTapers(16, nw));
        Assert.ThrowsAny<ArgumentException>(() => Spectral.DpssTapers(16, 2.0, 0));
        Assert.ThrowsAny<ArgumentException>(() => Spectral.DpssTapers(16, 2.0, 17));
        Assert.ThrowsAny<ArgumentException>(() => Spectral.MultitaperPsd(Array.Empty<double>(), 1.0, 0.4));
        Assert.ThrowsAny<ArgumentException>(() => Spectral.MultitaperPsd(x, 1.0, 2.0, nfft: 15));
        Assert.ThrowsAny<ArgumentException>(() => Spectral.MultitaperPsd(x, 0.0, 2.0));
        Assert.ThrowsAny<ArgumentException>(() => Spectral.MultitaperPsd(x, 1.0, 8.0));
    }
}
