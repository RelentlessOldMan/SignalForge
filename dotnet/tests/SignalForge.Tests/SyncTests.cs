using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Synchronization estimators on a full shaped QPSK link with delay, carrier offset and noise.</summary>
public class SyncTests
{
    private const int Sps = 4;
    private const double Rs = 1000;

    /// <summary>Shaped QPSK at 4 samples per symbol, Rs = 1000, through delay, carrier offset and AWGN.</summary>
    private static (byte[] Bits, Complex[] Rx, int First) Link(int nsym, int delay, double df, double phase, double ebN0Db, int seed)
    {
        byte[] bits = Waveforms.Prbs(15, 2 * nsym);
        double[] h = Dsp.RrcTaps(0.35, Sps, 10);
        Complex[] shaped = Dsp.PulseShape(Modulation.QpskMap(bits), h, Sps);
        var tx = new Complex[delay + shaped.Length];
        shaped.CopyTo(tx, delay);
        tx = Channel.FrequencyOffset(tx, df, Rs * Sps, phase);
        double esN0Db = ebN0Db + 10 * Math.Log10(2);
        Complex[] rx = Dsp.Convolve(Channel.Awgn(tx, esN0Db, Sps, seed, signalPower: 1.0 / Sps), h);
        return (bits, rx, h.Length - 1 + delay);
    }

    private static Complex[] Sample(Complex[] rx, int first, int nsym)
    {
        double tau = Sync.TimingOffset(rx, Sps);
        Assert.True(Math.Abs(tau - first % Sps) < 0.1, $"tau {tau}");
        int start = first - first % Sps + (int)Math.Round(tau) % Sps; // the frame start comes from a preamble in practice
        return Enumerable.Range(0, nsym).Select(k => rx[start + k * Sps]).ToArray();
    }

    private static Complex[] Derotate(Complex[] sampled, byte[] bits)
    {
        double phi = Sync.QpskPhaseOffset(sampled);
        Complex[] z = Channel.FrequencyOffset(sampled, 0, 1, -phi);
        // resolve the π/2 ambiguity with the first 32 known symbols
        Complex[] known = Modulation.QpskMap(bits.AsSpan(0, 64));
        Complex s = Complex.Zero;
        for (int k = 0; k < known.Length; k++)
            s += Complex.Conjugate(known[k]) * z[k];
        int m = (int)Math.Round(s.Phase / (Math.PI / 2));
        return z.Select(v => v * Complex.FromPolarCoordinates(1, -m * Math.PI / 2)).ToArray();
    }

    [Fact]
    public void RecoversTimingAndPhaseAtTheoryBer()
    {
        const int nsym = 100_000;
        const double ebN0Db = 6.0;
        var (bits, rx, first) = Link(nsym, delay: 3, df: 0, phase: 2.0, ebN0Db, seed: 5);
        Complex[] z = Derotate(Sample(rx, first, nsym), bits);
        double ber = Metrics.BitErrors(bits, Modulation.QpskDemapHard(z)).Rate;
        double theory = Metrics.QpskBerTheory(ebN0Db); // 2.39e-3: about 480 errors
        Assert.True(Math.Abs(ber - theory) / theory < 0.15, $"ber {ber} vs theory {theory}");
    }

    [Fact]
    public void FrequencyEstimateAccuracy()
    {
        // The lag-1 estimator's error is about 0.2 Hz here (Rs = 1000, 100k symbols, Eb/N0 6 dB).
        const int nsym = 100_000;
        var (_, rx, first) = Link(nsym, delay: 1, df: 20, phase: 0, ebN0Db: 6, seed: 6);
        double f = Sync.QpskFrequencyOffset(Sample(rx, first, nsym), Rs);
        Assert.True(Math.Abs(f - 20) < 1, $"f {f}");
    }

    [Fact]
    public void ShortBlockWithEveryImpairment()
    {
        const int nsym = 2000;
        var (bits, rx, first) = Link(nsym, delay: 2, df: 37, phase: -1.2, ebN0Db: 20, seed: 7);
        Complex[] z = Sample(rx, first, nsym);
        z = Channel.FrequencyOffset(z, -Sync.QpskFrequencyOffset(z, Rs), Rs);
        z = Derotate(z, bits);
        Assert.Equal(0, Metrics.BitErrors(bits, Modulation.QpskDemapHard(z)).Errors);
    }

    [Fact]
    public void EstimatesAreInRange()
    {
        var rng = new Random(0);
        for (int i = 0; i < 50; i++)
        {
            Complex[] z = Enumerable.Range(0, 16).Select(_ => new Complex(rng.NextDouble() - 0.5, rng.NextDouble() - 0.5)).ToArray();
            Assert.InRange(Sync.TimingOffset(z, 4), 0, 4 - 1e-15);
            Assert.InRange(Sync.QpskFrequencyOffset(z, 1000), -125 + 1e-12, 125);
            Assert.InRange(Sync.QpskPhaseOffset(z), -Math.PI / 4 + 1e-15, Math.PI / 4);
        }
    }

    [Fact]
    public void RejectsBadArguments()
    {
        Complex[] ones = [Complex.One, Complex.One];
        Assert.ThrowsAny<ArgumentException>(() => Sync.TimingOffset(ones, 1));
        Assert.ThrowsAny<ArgumentException>(() => Sync.TimingOffset([], 4));
        Assert.ThrowsAny<ArgumentException>(() => Sync.QpskFrequencyOffset([Complex.One], 1000));
        Assert.ThrowsAny<ArgumentException>(() => Sync.QpskFrequencyOffset(ones, double.NaN));
        Assert.ThrowsAny<ArgumentException>(() => Sync.QpskPhaseOffset([new Complex(0, double.PositiveInfinity)]));
    }

    /// <summary>A burst delayed by part of a sample: Oerder–Meyr finds the delay, and undoing its
    /// fraction with FractionalDelay gives the AWGN error rate back.</summary>
    [Theory]
    [InlineData(0.3)]
    [InlineData(1.7)]
    [InlineData(2.5)]
    [InlineData(3.9)]
    public void FractionalTimingEndToEnd(double delay)
    {
        const int sps = 4, nsym = 50_000;
        byte[] bits = Waveforms.Prbs(15, 2 * nsym);
        double[] h = Dsp.RrcTaps(0.35, sps, 10);
        Complex[] tx = [.. Dsp.PulseShape(Modulation.QpskMap(bits), h, sps), .. new Complex[64]];
        double esN0Db = 4.0 + 10 * Math.Log10(2);
        Complex[] rx = Dsp.Convolve(Channel.Awgn(Channel.FractionalDelay(tx, delay), esN0Db, sps, seed: 7, signalPower: 1.0 / sps), h);
        double first = h.Length - 1 + delay;
        double tau = Sync.TimingOffset(rx, sps);
        Assert.True(Math.Abs((tau - first % sps + 2 + sps) % sps - 2) < 0.05, $"tau {tau}");
        double frac = tau % 1;
        int start = (int)Math.Round(first - frac); // the whole-sample part comes from a preamble in practice
        Complex[] fixedRx = Channel.FractionalDelay(rx, -frac);
        double theory = Metrics.QpskBerTheory(4.0);
        double ber = Metrics.BitErrors(bits, Modulation.QpskDemapHard(Every(fixedRx, start, nsym))).Rate;
        // 100 000 bits, about 1250 errors: 3 sigma is about 8.5 %
        Assert.True(Math.Abs(ber - theory) / theory < 0.1, $"ber {ber} vs theory {theory}");
        if (delay % 1 > 0.45) // sampled half a sample or more off, it is clearly worse
            Assert.True(Metrics.BitErrors(bits, Modulation.QpskDemapHard(Every(rx, (int)Math.Floor(first), nsym))).Rate > 1.3 * theory);
    }

    private static Complex[] Every(Complex[] x, int start, int nsym) =>
        [.. Enumerable.Range(0, nsym).Select(k => x[start + k * 4])];
}
