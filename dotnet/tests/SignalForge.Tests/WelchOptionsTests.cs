using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Welch options: detrending is a projection, the median is unbiased for noise and resists
/// bursts, zero padding samples the same spectrum finer (conventions: Spectra, PSD).</summary>
public class WelchOptionsTests
{
    private static double[] Noise(int n, int seed)
    {
        var rng = new Random(seed);
        return [.. Enumerable.Range(0, n).Select(_ =>
            Math.Sqrt(-2 * Math.Log(1 - rng.NextDouble())) * Math.Cos(2 * Math.PI * rng.NextDouble()))];
    }

    private static void Close(double[] a, double[] b, double rel, double abs)
    {
        Assert.Equal(a.Length, b.Length);
        for (int i = 0; i < a.Length; i++)
            Assert.True(Math.Abs(a[i] - b[i]) <= abs + rel * Math.Abs(b[i]), $"{i}: {a[i]} vs {b[i]}");
    }

    [Theory]
    [InlineData(Detrend.Constant)]
    [InlineData(Detrend.Linear)]
    public void DetrendingIgnoresTheRemovedPart(Detrend detrend)
    {
        double[] x = Noise(96, 1);
        double[] moved = [.. x.Select((v, i) => v + 3.0 + (detrend == Detrend.Linear ? 0.2 * i : 0))];
        double[] a = Spectral.WelchPsd(x, 10, nperseg: 16, detrend: detrend).Psd;
        double[] b = Spectral.WelchPsd(moved, 10, nperseg: 16, detrend: detrend).Psd;
        Close(a, b, 1e-9, 1e-12);
        Assert.True(Spectral.WelchPsd(moved, 10, nperseg: 16).Psd[0] > 10 * b[0]);
    }

    [Fact]
    public void ComplexLinearDetrendRemovesAComplexLine()
    {
        double[] re = Noise(64, 2), im = Noise(64, 3);
        Complex[] x = [.. re.Select((v, i) => new Complex(v, im[i]))];
        Complex[] moved = [.. x.Select((v, i) => v + new Complex(1, -2) + new Complex(0.1, 0.3) * i)];
        Close(Spectral.WelchPsd(x, 1, nperseg: 16, detrend: Detrend.Linear).Psd,
            Spectral.WelchPsd(moved, 1, nperseg: 16, detrend: Detrend.Linear).Psd, 1e-9, 1e-12);
    }

    [Theory]
    [InlineData(255)]
    [InlineData(256)]
    public void MedianIsUnbiasedForWhiteNoise(int segments)
    {
        double[] x = Noise(64 * segments, 4);
        double[] med = Spectral.WelchPsd(x, 1, 64, 0, WindowType.Rectangular, average: WelchAverage.Median).Psd;
        double[] mean = Spectral.WelchPsd(x, 1, 64, 0, WindowType.Rectangular).Psd;
        double ratio = med[1..^1].Average() / mean[1..^1].Average();
        Assert.True(Math.Abs(ratio - 1) < 0.03, $"{ratio}");
    }

    [Fact]
    public void MedianOfASteadyToneReadsOneOverTheBiasHigh()
    {
        double[] x = [.. Enumerable.Range(0, 64 * 15).Select(i => Math.Cos(2 * Math.PI * 0.125 * i))];
        double[] med = Spectral.WelchPsd(x, 1, 64, 0, average: WelchAverage.Median).Psd;
        double[] mean = Spectral.WelchPsd(x, 1, 64, 0).Psd;
        double b15 = Enumerable.Range(8, 8).Sum(i => 1.0 / i); // by hand: b(K) for K = 15
        Assert.True(Math.Abs(med[8] * b15 / mean[8] - 1) < 1e-12);
    }

    [Fact]
    public void MedianResistsABurst()
    {
        double[] clean = [.. Enumerable.Range(0, 64 * 15).Select(i => Math.Cos(2 * Math.PI * 0.125 * i))];
        double[] x = [.. clean];
        for (int i = 64 * 7; i < 64 * 7 + 4; i++)
            x[i] += 50;
        double[] reference = Spectral.WelchPsd(clean, 1, 64, 0, average: WelchAverage.Median).Psd;
        double[] med = Spectral.WelchPsd(x, 1, 64, 0, average: WelchAverage.Median).Psd;
        double[] mean = Spectral.WelchPsd(x, 1, 64, 0).Psd;
        Assert.True(med[20..30].Max() < 1e-3 * mean[20..30].Max());
        Assert.True(Math.Abs(med[8] / reference[8] - 1) < 0.01);
    }

    [Fact]
    public void SpectrogramRowsAverageToTheDetrendedPsd()
    {
        double[] x = [.. Noise(80, 5).Select((v, i) => v + 0.05 * i)];
        var s = Spectral.Spectrogram(x, 1, 16, detrend: Detrend.Linear);
        double[] w = Spectral.WelchPsd(x, 1, nperseg: 16, detrend: Detrend.Linear).Psd;
        double[] avg = [.. Enumerable.Range(0, w.Length).Select(k => s.Psd.Average(row => row[k]))];
        Close(avg, w, 1e-12, 1e-15);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void PaddingSamplesTheSameSpectrumFiner(bool oneSided)
    {
        double[] x = Noise(100, 6);
        var plain = Spectral.WelchPsd(x, 8, nperseg: 20, oneSided: oneSided);
        var padded = Spectral.WelchPsd(x, 8, nperseg: 20, oneSided: oneSided, nfft: 80);
        // Bin 4k of 80 is bin k of 20 (shifted order: both start at -fs/2).
        Close([.. padded.Psd.Where((_, i) => i % 4 == 0)], plain.Psd, 1e-10, 1e-14);
        Close([.. padded.Frequencies.Where((_, i) => i % 4 == 0)], plain.Frequencies, 0, 1e-12);
        Assert.Equal(80, padded.Nfft);
        Assert.Equal(20, plain.Nfft);
        Assert.Equal(8.0 / 80, padded.BinWidth);
        Assert.Equal(plain.EnbwHz, padded.EnbwHz);
    }

    [Fact]
    public void PaddingKeepsTheTotalPower()
    {
        double[] re = Noise(64, 7), im = Noise(64, 8);
        Complex[] x = [.. re.Select((v, i) => new Complex(v, im[i]))];
        var baseline = Spectral.WelchPsd(x, 3, nperseg: 16);
        foreach (int nfft in new[] { 16, 17, 50 })
        {
            var d = Spectral.WelchPsd(x, 3, nperseg: 16, nfft: nfft);
            double ratio = d.Psd.Sum() * d.BinWidth / (baseline.Psd.Sum() * baseline.BinWidth);
            Assert.True(Math.Abs(ratio - 1) < 1e-12, $"{nfft}: {ratio}");
        }
    }

    [Fact]
    public void BadOptionsThrow()
    {
        double[] x = [1, 2, 3, 4];
        Assert.ThrowsAny<ArgumentException>(() => Spectral.WelchPsd(x, 1, 2, detrend: (Detrend)7));
        Assert.ThrowsAny<ArgumentException>(() => Spectral.WelchPsd(x, 1, 2, average: (WelchAverage)7));
        Assert.ThrowsAny<ArgumentException>(() => Spectral.Spectrogram(x, 1, 2, detrend: (Detrend)(-1)));
        Assert.ThrowsAny<ArgumentException>(() => Spectral.WelchPsd(x, 1, 2, nfft: 1));
        Assert.ThrowsAny<ArgumentException>(() => Spectral.Spectrogram(x, 1, 2, nfft: 1));
    }
}
