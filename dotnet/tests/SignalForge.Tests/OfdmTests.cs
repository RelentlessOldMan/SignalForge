using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>OFDM modulate and demodulate (conventions: Bits and symbols, OFDM; ADR 0060).</summary>
public class OfdmTests
{
    // a 64-point plan with DC and guard bands empty
    private static readonly int[] Used = [.. Enumerable.Range(-26, 53).Where(k => k != 0)];

    private static Complex[] Qpsk(int n, int seed)
    {
        var rng = new Random(seed);
        return Modulation.QpskMap([.. Enumerable.Range(0, 2 * n).Select(_ => (byte)rng.Next(2))]);
    }

    [Fact]
    public void RoundTripAndLength()
    {
        Complex[] s = Qpsk(10 * Used.Length, 1);
        Complex[] x = Modulation.OfdmModulate(s, 64, 16, Used);
        Assert.Equal(10 * 80, x.Length);
        Complex[] r = Modulation.OfdmDemodulate(x, 64, 16, Used);
        Assert.All(r.Zip(s), p => Assert.True((p.First - p.Second).Magnitude < 1e-12));
    }

    [Fact]
    public void EnergyIsKept()
    {
        Complex[] s = Qpsk(4 * Used.Length, 2);
        Complex[] x = Modulation.OfdmModulate(s, 64, 0, Used);
        double ex = x.Sum(z => z.Magnitude * z.Magnitude), es = s.Sum(z => z.Magnitude * z.Magnitude);
        Assert.Equal(es, ex, 1e-9);
        Assert.Equal(Used.Length / 64.0, ex / x.Length, 1e-12);
    }

    [Fact]
    public void PrefixIsTheBlockTail()
    {
        Complex[] x = Modulation.OfdmModulate(Qpsk(3 * Used.Length, 3), 64, 16, Used);
        for (int b = 0; b < 3; b++)
            for (int n = 0; n < 16; n++)
                Assert.Equal(x[b * 80 + 64 + n], x[b * 80 + n]);
    }

    [Fact]
    public void MultipathWithinThePrefixIsOneGainPerSubcarrier()
    {
        int[] delays = [0, 3, 9];
        Complex[] gains = [1, new(0.4, -0.3), new(0, 0.15)];
        Complex[] s = Qpsk(6 * Used.Length, 4);
        Complex[] y = Channel.Multipath(Modulation.OfdmModulate(s, 64, 16, Used), delays, gains);
        Complex[] r = Modulation.OfdmDemodulate(y, 64, 16, Used);
        for (int i = 0; i < r.Length; i++)
        {
            int k = Used[i % Used.Length];
            Complex h = Enumerable.Range(0, 3).Aggregate(Complex.Zero,
                (acc, d) => acc + gains[d] * Complex.FromPolarCoordinates(1, -2 * Math.PI * k * delays[d] / 64));
            Assert.True((r[i] - s[i] * h).Magnitude < 1e-12);
        }
    }

    [Fact]
    public void DefaultSubcarriersAreAllAscending()
    {
        Complex[] s = Qpsk(8, 5);
        Complex[] a = Modulation.OfdmModulate(s, 8, 2), b = Modulation.OfdmModulate(s, 8, 2, [.. Enumerable.Range(-4, 8)]);
        Assert.Equal(a, b);
    }

    [Theory]
    [InlineData(0, 0)]
    [InlineData(4, 5)]
    [InlineData(4, -1)]
    public void RejectsBadSizes(int nfft, int cpLen) =>
        Assert.ThrowsAny<ArgumentException>(() => Modulation.OfdmModulate([1, 1, 1, 1], nfft, cpLen));
}
