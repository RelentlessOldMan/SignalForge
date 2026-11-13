using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Pulse shaping, channel and link metrics: properties that the vectors cannot check.</summary>
public class LinkTests
{
    private static Complex[] Every(Complex[] x, int start, int step, int count) =>
        Enumerable.Range(0, count).Select(k => x[start + k * step]).ToArray();

    [Theory]
    [InlineData(0.35, 4, 8)]
    [InlineData(0.25, 4, 4)]
    [InlineData(1.0, 2, 6)]
    public void RrcHasUnitEnergyAndIsSymmetric(double beta, int sps, int span)
    {
        double[] h = Dsp.RrcTaps(beta, sps, span);
        Assert.Equal(span * sps + 1, h.Length);
        Assert.Equal(1.0, h.Sum(v => v * v), 1e-14);
        for (int i = 0; i < h.Length; i++)
            Assert.Equal(h[h.Length - 1 - i], h[i], 1e-15);
    }

    [Fact]
    public void MatchedFilterIsNearlyNyquist()
    {
        const int sps = 8, span = 16;
        double[] h = Dsp.RrcTaps(0.35, sps, span);
        double[] rc = Dsp.Convolve(h, h);
        int center = h.Length - 1;
        Assert.Equal(1.0, rc[center], 1e-14);
        for (int k = -span; k <= span; k++)
            if (k != 0)
                Assert.True(Math.Abs(rc[center + k * sps]) < 2e-3);
    }

    [Fact]
    public void ShapedQpskRoundTrips()
    {
        const int sps = 4;
        byte[] bits = Waveforms.Prbs(9, 400);
        Complex[] symbols = Modulation.QpskMap(bits);
        double[] h = Dsp.RrcTaps(0.35, sps, 10);
        Complex[] rx = Dsp.Convolve(Dsp.PulseShape(symbols, h, sps), h);
        Complex[] sampled = Every(rx, h.Length - 1, sps, symbols.Length);
        Assert.True(Metrics.Evm(sampled, symbols).Rms < 0.02);
        Assert.Equal(bits, Modulation.QpskDemapHard(sampled));
    }

    [Fact]
    public void ShapedEnergyPerSymbolIsOne()
    {
        Complex[] symbols = Modulation.QpskMap(Waveforms.Prbs(11, 4000));
        Complex[] tx = Dsp.PulseShape(symbols, Dsp.RrcTaps(0.35, 4, 10), 4);
        double energy = tx.Sum(z => z.Real * z.Real + z.Imaginary * z.Imaginary);
        Assert.InRange(energy / symbols.Length, 0.97, 1.03);
    }

    [Fact]
    public void AwgnHasTheRequestedVarianceAndIsSeeded()
    {
        var x = Enumerable.Repeat(Complex.One, 200_000).ToArray();
        Complex[] y = Channel.Awgn(x, 10.0, 1, seed: 1);
        var noise = y.Select((v, i) => v - x[i]).ToArray();
        double power = noise.Average(z => z.Real * z.Real + z.Imaginary * z.Imaginary);
        Assert.InRange(power, 0.099, 0.101);
        double vi = noise.Average(z => z.Real * z.Real), vq = noise.Average(z => z.Imaginary * z.Imaginary);
        Assert.InRange(vi / vq, 0.98, 1.02);
        Assert.True(Math.Abs(noise.Average(z => z.Real * z.Imaginary)) < 1e-3);
        Assert.InRange(Math.Abs(noise.Average(z => z.Real)), 0, 3e-3);
        Assert.Equal(y, Channel.Awgn(x, 10.0, 1, seed: 1));
        Assert.NotEqual(y, Channel.Awgn(x, 10.0, 1, seed: 2));
    }

    [Fact]
    public void AwgnUsesSignalPowerAndSamplesPerSymbol()
    {
        var x = Enumerable.Repeat(new Complex(0.5, 0), 100_000).ToArray();
        static double NoisePower(Complex[] x, Complex[] y) =>
            y.Select((v, i) => v - x[i]).Average(z => z.Real * z.Real + z.Imaginary * z.Imaginary);
        Assert.InRange(NoisePower(x, Channel.Awgn(x, 0.0, 4, seed: 3, signalPower: 2.0)), 8.0 * 0.98, 8.0 * 1.02);
        double expected = 0.5 / Math.Pow(10, 0.3);
        Assert.InRange(NoisePower(x, Channel.Awgn(x, 3.0, 2, new Random(7))), expected * 0.98, expected * 1.02);
    }

    [Fact]
    public void AwgnRejectsBadArguments()
    {
        Complex[] ones = [Complex.One, Complex.One];
        Assert.Throws<ArgumentException>(() => Channel.Awgn([], 10, 1, 0));
        Assert.Throws<ArgumentException>(() => Channel.Awgn([new Complex(double.NaN, 0)], 10, 1, 0));
        Assert.ThrowsAny<ArgumentException>(() => Channel.Awgn(ones, 10, 1, 0, signalPower: 0));
        Assert.ThrowsAny<ArgumentException>(() => Channel.Awgn(ones, 10, 1, 0, signalPower: double.PositiveInfinity));
        Assert.ThrowsAny<ArgumentException>(() => Channel.Awgn(ones, 10, 0, 0));
        Assert.ThrowsAny<ArgumentException>(() => Channel.Awgn(ones, double.NaN, 1, 0));
        Assert.ThrowsAny<ArgumentException>(() => Channel.Awgn([Complex.Zero], 10, 1, 0));
        Assert.Throws<ArgumentNullException>(() => Channel.Awgn(ones, 10, 1, (Random)null!));
    }

    [Fact]
    public void FrequencyOffsetMovesTheSpectrum()
    {
        const int n = 64;
        var ones = Enumerable.Repeat(Complex.One, n).ToArray();
        static int PeakBin(Complex[] y)
        {
            Complex[] s = Spectral.Fft(y);
            return Array.IndexOf(s, s.MaxBy(Complex.Abs));
        }
        Assert.Equal(5, PeakBin(Channel.FrequencyOffset(ones, 5.0, n)));
        Assert.Equal(n - 3, PeakBin(Channel.FrequencyOffset(ones, -3.0, n)));
    }

    [Fact]
    public void QpskLinkBerMatchesTheory()
    {
        const int sps = 4;
        byte[] bits = Waveforms.Prbs(15, 200_000);
        Complex[] symbols = Modulation.QpskMap(bits);
        double[] h = Dsp.RrcTaps(0.35, sps, 10);
        const double ebN0Db = 4.0;
        double esN0Db = ebN0Db + 10 * Math.Log10(2);
        Complex[] tx = Dsp.PulseShape(symbols, h, sps);
        Complex[] rx = Dsp.Convolve(Channel.Awgn(tx, esN0Db, sps, seed: 11, signalPower: 1.0 / sps), h);
        Complex[] sampled = Every(rx, h.Length - 1, sps, symbols.Length);
        double ber = Metrics.BitErrors(bits, Modulation.QpskDemapHard(sampled)).Rate;
        double theory = Metrics.QpskBerTheory(ebN0Db); // 0.0125
        // ~2500 errors expected: 3 sigma is about 6 %; the truncated filter adds a little ISI
        Assert.True(Math.Abs(ber - theory) / theory < 0.08, $"ber {ber} vs theory {theory}");
    }

    // Reference values: Python's math.erfc (the C library), 0.5 * erfc(sqrt(10**(db/10))).
    [Theory]
    [InlineData(-20.0, 0.4437685419908576)]
    [InlineData(3.0, 0.02287840756108532)]
    [InlineData(3.5218, 0.016947685355227313)]
    [InlineData(3.5219, 0.016946658438830878)]
    [InlineData(7.0, 0.0007726748153784444)]
    [InlineData(11.0, 2.6130679535751977e-07)]
    [InlineData(20.0, 1.0442437918812724e-45)]
    public void QpskBerTheoryMatchesTheCLibrary(double db, double expected) =>
        Assert.Equal(expected, Metrics.QpskBerTheory(db), expected * 1e-13);

    [Fact]
    public void QpskBerTheoryLimits()
    {
        Assert.Equal(0.5, Metrics.QpskBerTheory(double.NegativeInfinity));
        Assert.Equal(0.0, Metrics.QpskBerTheory(double.PositiveInfinity));
        Assert.Throws<ArgumentOutOfRangeException>(() => Metrics.QpskBerTheory(double.NaN));
    }

    [Fact]
    public void EvmPeakAndDb()
    {
        Complex[] reference = Modulation.QpskMap(Waveforms.Prbs(7, 20));
        Complex[] measured = (Complex[])reference.Clone();
        measured[3] += new Complex(0, 0.3);
        measured[7] += 0.1;
        Evm r = Metrics.Evm(measured, reference);
        Assert.Equal(3, r.PeakIndex);
        Assert.Equal(0.3, r.Peak, 1e-14);
        Assert.Equal(Math.Sqrt(0.1 / 10), r.Rms, 1e-14);
        Assert.Equal(20 * Math.Log10(r.Rms), r.RmsDb, 1e-12);
        Assert.Throws<ArgumentException>(() => Metrics.Evm([new Complex(double.NaN, 0)], [Complex.One]));
    }

    [Fact]
    public void DspRejectsBadArguments()
    {
        Assert.Throws<ArgumentException>(() => Dsp.Convolve(ReadOnlySpan<double>.Empty, [1.0]));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Upsample([1.0], 0));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.RrcTaps(double.NaN, 4, 4));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.RrcTaps(0.35, 4, 3));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.RrcTaps(0.35, 0, 4));
        Assert.Throws<OverflowException>(() => Dsp.RrcTaps(0.35, int.MaxValue / 2, 4));
    }
}
