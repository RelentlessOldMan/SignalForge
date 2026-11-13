using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Continuous-phase M-FSK, noncoherent detection and theory (conventions: Bits and symbols, FSK;
/// EVM and BER; ADR 0054).</summary>
public class FskTests
{
    private static byte[] RandomBits(int seed, int n)
    {
        var rng = new Random(seed);
        return [.. Enumerable.Range(0, n).Select(_ => (byte)rng.Next(2))];
    }

    [Theory]
    [InlineData(2, 1, 4)]
    [InlineData(4, 2, 8)]
    [InlineData(8, 3, 16)]
    [InlineData(16, 4, 32)]
    public void ConstantEnvelopeAndContinuousPhase(int order, int k, int sps)
    {
        byte[] bits = RandomBits(order, 60 * k);
        Complex[] x = Modulation.FskModulate(bits, order, sps, 1.0);
        Assert.Equal(60 * sps, x.Length);
        Assert.All(x, v => Assert.Equal(1.0, v.Magnitude, 1e-15));
        for (int t = 0; t + 1 < x.Length; t++)
        {
            int i = t / sps, m = 0;
            for (int b = 0; b < k; b++)
                m = 2 * m + bits[i * k + b];
            double step = (x[t + 1] * Complex.Conjugate(x[t])).Phase;
            Assert.Equal(Math.PI * (2 * m - (order - 1)) / sps, step, 1e-9);
        }
    }

    [Theory]
    [InlineData(2, 1, 4)]
    [InlineData(4, 2, 8)]
    [InlineData(8, 3, 16)]
    [InlineData(16, 4, 32)]
    public void NoiselessRoundTripWithPhaseAndGain(int order, int k, int sps)
    {
        byte[] bits = RandomBits(7, 200 * k);
        Complex g = Complex.FromPolarCoordinates(0.3, 1.1);
        Complex[] x = [.. Modulation.FskModulate(bits, order, sps, 1.0).Select(v => v * g)];
        Assert.Equal(bits, Modulation.FskDemodNoncoherent(x, order, sps, 1.0));
    }

    // About 500 symbol errors each, so 15 % is more than 3 standard deviations.
    [Theory]
    [InlineData(2, 10.0, 150000)]
    [InlineData(4, 8.0, 200000)]
    [InlineData(8, 6.0, 70000)]
    public void MonteCarloMatchesTheory(int order, double db, int symbols)
    {
        int k = (int)Math.Round(Math.Log2(order));
        int sps = 2 * order;
        byte[] bits = RandomBits(order + 100, symbols * k);
        Complex[] x = Modulation.FskModulate(bits, order, sps, 1.0);
        Complex[] y = Channel.Awgn(x, db + 10 * Math.Log10(k), sps, order, signalPower: 1.0);
        byte[] got = Modulation.FskDemodNoncoherent(y, order, sps, 1.0);
        int bitErrors = 0, symbolErrors = 0;
        for (int i = 0; i < symbols; i++)
        {
            int e = 0;
            for (int b = 0; b < k; b++)
                e += got[i * k + b] != bits[i * k + b] ? 1 : 0;
            bitErrors += e;
            symbolErrors += e > 0 ? 1 : 0;
        }
        double pb = Metrics.FskBerTheory(db, order), ps = Metrics.FskSerTheory(db, order);
        Assert.InRange((double)bitErrors / bits.Length, 0.85 * pb, 1.15 * pb);
        Assert.InRange((double)symbolErrors / symbols, 0.85 * ps, 1.15 * ps);
    }

    [Fact]
    public void Theory()
    {
        Assert.Equal(0.5 * Math.Exp(-5), Metrics.FskBerTheory(10.0), 1e-17);
        Assert.Equal(15 / 16.0, Metrics.FskSerTheory(double.NegativeInfinity, 16), 1e-13);
        Assert.Equal(0.0, Metrics.FskBerTheory(double.PositiveInfinity, 8));
        foreach (int order in new[] { 4, 8, 16 })
            Assert.True(Metrics.FskBerTheory(10.0, order) < Metrics.FskBerTheory(10.0, order / 2));
    }

    [Theory]
    [InlineData(1)]
    [InlineData(3)]
    [InlineData(32)]
    public void BadOrder(int order)
    {
        Assert.ThrowsAny<ArgumentException>(() => Modulation.FskModulate([0, 1], order, 8, 1.0));
        Assert.ThrowsAny<ArgumentException>(() => Modulation.FskDemodNoncoherent(new Complex[8], order, 8, 1.0));
        Assert.ThrowsAny<ArgumentException>(() => Metrics.FskBerTheory(4.0, order));
    }

    [Fact]
    public void BadArguments()
    {
        Assert.ThrowsAny<ArgumentException>(() => Modulation.FskModulate([0], 2, 0, 1.0));
        Assert.ThrowsAny<ArgumentException>(() => Modulation.FskModulate([0], 2, 4, -1.0));
        Assert.ThrowsAny<ArgumentException>(() => Modulation.FskModulate([0], 2, 4, double.PositiveInfinity));
        Assert.ThrowsAny<ArgumentException>(() => Modulation.FskModulate([0, 1, 1], 4, 4, 1.0));
        Assert.ThrowsAny<ArgumentException>(() => Modulation.FskDemodNoncoherent(new Complex[5], 2, 4, 1.0));
        Assert.ThrowsAny<ArgumentException>(() => Modulation.FskDemodNoncoherent([1, double.PositiveInfinity], 2, 2, 1.0));
        Assert.ThrowsAny<ArgumentException>(() => Metrics.FskSerTheory(double.NaN, 4));
    }
}
