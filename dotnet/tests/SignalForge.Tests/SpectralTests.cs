using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

public class SpectralTests
{
    private static Complex[] DirectDft(Complex[] x)
    {
        int n = x.Length;
        var y = new Complex[n];
        for (int k = 0; k < n; k++)
            for (int t = 0; t < n; t++)
                y[k] += x[t] * Complex.FromPolarCoordinates(1, -2 * Math.PI * ((long)k * t % n) / n);
        return y;
    }

    private static Complex[] RandomComplex(int n, int seed)
    {
        var rng = new Random(seed);
        return Enumerable.Range(0, n).Select(_ => new Complex(rng.NextDouble() - 0.5, rng.NextDouble() - 0.5)).ToArray();
    }

    private static double MaxError(Complex[] a, Complex[] b) => a.Zip(b, (x, y) => Complex.Abs(x - y)).Max();

    [Fact]
    public void FftMatchesDirectDftForEveryLengthUpTo40()
    {
        for (int n = 1; n <= 40; n++)
        {
            var x = RandomComplex(n, n);
            Assert.True(MaxError(Spectral.Fft(x), DirectDft(x)) < 1e-12, $"n = {n}");
            Assert.True(MaxError(Spectral.Ifft(Spectral.Fft(x)), x) < 1e-13, $"n = {n}");
        }
    }

    [Theory]
    [InlineData(1009)] // prime: Bluestein
    [InlineData(4096)] // power of two: radix-2
    [InlineData(1000)]
    public void FftStaysAccurateAtLargerLengths(int n)
    {
        var x = RandomComplex(n, 7);
        Assert.True(MaxError(Spectral.Fft(x), DirectDft(x)) < 1e-10);
    }

    [Fact]
    public void FftOfRealSamplesEqualsComplexFft()
    {
        double[] r = [0.5, -1, 2, 3.25, 0];
        Assert.True(MaxError(Spectral.Fft(r), Spectral.Fft(r.Select(v => new Complex(v, 0)).ToArray())) == 0);
    }

    [Fact]
    public void PeriodicWindowIsTruncatedSymmetricWindowOneLonger()
    {
        foreach (var t in new[] { WindowType.Hann, WindowType.BlackmanHarris, WindowType.Flattop })
        {
            var p = Spectral.Window(t, 8);
            var s = Spectral.Window(t, 9, symmetric: true);
            for (int i = 0; i < 8; i++)
                Assert.Equal(s[i], p[i], 1e-15);
        }
        var kp = Spectral.Window(WindowType.Kaiser, 8, beta: 5);
        var ks = Spectral.Window(WindowType.Kaiser, 9, symmetric: true, beta: 5);
        for (int i = 0; i < 8; i++)
            Assert.Equal(ks[i], kp[i], 1e-15);
    }

    [Fact]
    public void KaiserIsSymmetricWithUnitPeak()
    {
        var w = Spectral.Window(WindowType.Kaiser, 11, symmetric: true, beta: 8.6);
        Assert.Equal(1.0, w[5], 1e-15);
        for (int i = 0; i < 11; i++)
            Assert.Equal(w[i], w[10 - i], 1e-15);
        // The end values are 1/I0(beta); I0(8.6) = 750.4611595631661 (power series, 80 terms).
        Assert.Equal(1 / 750.4611595631661, w[0], 1e-15);
    }

    [Fact]
    public void FlattopReadsToneAmplitudeBetweenBins()
    {
        const int n = 256;
        var x = Waveforms.Tone(n, n, 40.5);
        var w = Spectral.Window(WindowType.Flattop, n);
        var y = Spectral.Fft(x.Select((v, i) => v * w[i]).ToArray());
        double peak = y.Max(Complex.Abs) / (n * Spectral.WindowStats(w).CoherentGain);
        Assert.Equal(1.0, peak, 0.002);
    }

    [Fact]
    public void PsdOfNoiseIntegratesToMeanPower()
    {
        var rng = new Random(1);
        double Gauss() => Math.Sqrt(-2 * Math.Log(1 - rng.NextDouble())) * Math.Cos(2 * Math.PI * rng.NextDouble());
        var x = Enumerable.Range(0, 1 << 16).Select(_ => new Complex(Gauss(), Gauss())).ToArray();
        var p = Spectral.WelchPsd(x, 1e6, nperseg: 1024);
        double mean = x.Average(v => v.Real * v.Real + v.Imaginary * v.Imaginary);
        Assert.Equal(1.0, p.Psd.Sum() * p.BinWidth / mean, 0.02);
        Assert.Equal((x.Length - 1024) / 512 + 1, p.NumSegments);
        Assert.Equal(1.5 * 1e6 / 1024, p.EnbwHz, 1e-9);
    }

    [Fact]
    public void OneSidedAndTwoSidedAgreeForRealInput()
    {
        var rng = new Random(2);
        var x = Enumerable.Range(0, 4096).Select(_ => rng.NextDouble() - 0.5).ToArray();
        var one = Spectral.WelchPsd(x, 100, nperseg: 256);
        var two = Spectral.WelchPsd(x, 100, nperseg: 256, oneSided: false);
        Assert.Equal(two.Psd.Sum(), one.Psd.Sum(), 1e-12 * two.Psd.Sum());
        Assert.Equal(129, one.Psd.Length);
        Assert.Equal(256, two.Psd.Length);
    }

    [Fact]
    public void ObwAndChannelPowerOfAFlatBand()
    {
        var f = Spectral.FftFrequencies(1000, 100, shifted: true);
        var psd = f.Select(v => Math.Abs(Math.Abs(v) - 10) < 1e-9 ? 0.5 : Math.Abs(v) < 10 ? 1.0 : 0.0).ToArray();
        var obw = Spectral.OccupiedBandwidth(f, psd);
        Assert.Equal(19.8, obw.Bandwidth, 1e-9);
        Assert.Equal(-9.9, obw.Lower, 1e-9);
        Assert.Equal(20.0, Spectral.ChannelPower(f, psd, -10.05, 10.05), 1e-9);
    }

    [Fact]
    public void RejectsBadArguments()
    {
        Assert.Throws<ArgumentException>(() => Spectral.Fft(ReadOnlySpan<Complex>.Empty));
        Assert.Throws<ArgumentOutOfRangeException>(() => Spectral.FftFrequencies(0, 1));
        Assert.Throws<ArgumentException>(() => Spectral.Window(WindowType.Kaiser, 4));
        Assert.Throws<ArgumentException>(() => Spectral.Window((WindowType)99, 4));
        Assert.Throws<ArgumentException>(() => Spectral.WelchPsd(new double[3], 1, nperseg: 4));
        Assert.Throws<ArgumentException>(() => Spectral.OccupiedBandwidth([0.0, 1.0], [1.0, 1.0], 0));
    }
}
