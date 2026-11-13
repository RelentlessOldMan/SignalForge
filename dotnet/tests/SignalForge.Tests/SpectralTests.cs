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
    public void FftOfRealSamplesMatchesDirectDft()
    {
        double[] r = [0.5, -1, 2, 3.25, 0];
        Assert.True(MaxError(Spectral.Fft(r), DirectDft(r.Select(v => new Complex(v, 0)).ToArray())) < 1e-13);
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
        // The end values are 1/I0(beta); I0(8.6) = 750.4611595631661 (power series, 80 terms;
        // NumPy's np.i0, a Chebyshev fit, gives 750.4611595631659).
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
        Assert.Throws<ArgumentOutOfRangeException>(() => Spectral.FftFrequencies(4, double.PositiveInfinity));
        Assert.Throws<ArgumentOutOfRangeException>(() => Spectral.FftFrequencies(4, double.NaN));
        Assert.Throws<ArgumentException>(() => Spectral.ChannelPower([0.0, double.NaN], [1.0, 1.0], 0, 1));
        Assert.Throws<ArgumentException>(() =>
            Spectral.OccupiedBandwidth([0.0, 1.0, 2.0], [1.0, 1.0, 1.0], span: (0.5, 2.0)));
    }

    [Fact]
    public void OneSidedSpanCountsDcAndNyquistInFull()
    {
        var x = Enumerable.Range(0, 64)
            .Select(n => 1 + Math.Cos(2 * Math.PI * n * 8 / 64) + 0.5 * Math.Cos(Math.PI * n)).ToArray();
        var p = Spectral.WelchPsd(x, 64, window: WindowType.Rectangular);
        Assert.Equal((0.0, 32.0), p.Span);
        double meanPower = x.Average(v => v * v);
        Assert.Equal(meanPower, Spectral.ChannelPower(p.Frequencies, p.Psd, 0, 32, p.Span), 1e-12 * meanPower);
        Assert.True(Spectral.ChannelPower(p.Frequencies, p.Psd, 0, 32) < meanPower);
        var obw = Spectral.OccupiedBandwidth(p.Frequencies, p.Psd, 1.0, p.Span);
        Assert.Equal((0.0, 32.0), (obw.Lower, obw.Upper));
    }

    [Fact]
    public void TwoSidedPsdHasNoSpan() =>
        Assert.Null(Spectral.WelchPsd(new Complex[8], 8).Span);

    [Fact]
    public void KaiserBetaLimit()
    {
        var w = Spectral.Window(WindowType.Kaiser, 9, symmetric: true, beta: Spectral.KaiserMaxBeta);
        Assert.All(w, v => Assert.True(double.IsFinite(v)));
        Assert.Equal(1.0, w[4]);
        foreach (double beta in new[] { Math.BitIncrement(Spectral.KaiserMaxBeta), double.PositiveInfinity, double.NaN, -1 })
            Assert.Throws<ArgumentException>(() => Spectral.Window(WindowType.Kaiser, 9, beta: beta));
    }

    [Fact]
    public void WelchPassesBetaToKaiser()
    {
        var x = Enumerable.Range(0, 16).Select(i => (double)i).ToArray();
        var p = Spectral.WelchPsd(x, 1, window: WindowType.Kaiser, beta: 6);
        var w = Spectral.Window(WindowType.Kaiser, 16, beta: 6);
        Assert.Equal(Spectral.WindowStats(w).EnbwBins / 16, p.EnbwHz, 1e-14);
    }

    [Theory]
    [InlineData(false, 16, null, WindowType.Hann)]
    [InlineData(false, 15, 3, WindowType.Blackman)]
    [InlineData(true, 16, 0, WindowType.Kaiser)]
    [InlineData(true, 9, 8, WindowType.Hann)]
    public void SpectrogramRowsAverageToWelch(bool complexInput, int nperseg, int? noverlap, WindowType window)
    {
        var rng = new Random(nperseg);
        double[] re = [.. Enumerable.Range(0, 200).Select(_ => rng.NextDouble() - 0.5)];
        double? beta = window == WindowType.Kaiser ? 6.0 : null;
        Spectrogram s;
        SpectralDensity w;
        if (complexInput)
        {
            Complex[] z = [.. re.Select(v => new Complex(v, rng.NextDouble() - 0.5))];
            (s, w) = (Spectral.Spectrogram(z, 1e3, nperseg, noverlap, window, beta), Spectral.WelchPsd(z, 1e3, nperseg, noverlap, window, beta));
        }
        else
            (s, w) = (Spectral.Spectrogram(re, 1e3, nperseg, noverlap, window, beta: beta), Spectral.WelchPsd(re, 1e3, nperseg, noverlap, window, beta: beta));
        Assert.Equal(w.NumSegments, s.Psd.Length);
        Assert.All(s.Psd, row => Assert.Equal(w.Frequencies.Length, row.Length));
        for (int k = 0; k < w.Psd.Length; k++)
        {
            double mean = s.Psd.Average(row => row[k]);
            Assert.True(Math.Abs(mean - w.Psd[k]) <= 1e-12 * w.Psd[k], $"bin {k}: {mean} vs {w.Psd[k]}");
        }
        Assert.Equal(w.Frequencies, s.Frequencies);
        Assert.Equal((w.OneSided, w.BinWidth, w.EnbwHz, w.Span), (s.OneSided, s.BinWidth, s.EnbwHz, s.Span));
        int step = nperseg - (noverlap ?? nperseg / 2);
        Assert.Equal([.. Enumerable.Range(0, s.NumSegments).Select(i => (i * step + nperseg / 2.0) / 1e3)], s.Times);
    }

    [Fact]
    public void SpectrogramTracksAFrequencyStep()
    {
        double[] x = [.. Enumerable.Range(0, 1024).Select(n => Math.Cos(2 * Math.PI * (n < 512 ? 125 : 250) * n / 1000.0))];
        var s = Spectral.Spectrogram(x, 1000, 64, noverlap: 0);
        double[] peaks = [.. s.Psd.Select(row => s.Frequencies[Array.IndexOf(row, row.Max())])];
        Assert.All(peaks[..8], f => Assert.Equal(125, f));
        Assert.All(peaks[8..], f => Assert.Equal(250, f));
    }
}
