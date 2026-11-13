using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>8-PSK and 16-QAM: round trips, unit energy, Gray neighbors, decisions under small noise
/// (conventions: Bits and symbols).</summary>
public class Psk8Qam16Tests
{
    private static byte[] AllLabels(int k) =>
        [.. Enumerable.Range(0, 1 << k).SelectMany(m => Enumerable.Range(0, k).Select(i => (byte)((m >> (k - 1 - i)) & 1)))];

    private static Complex[] Map(int k, byte[] bits) => k == 3 ? Modulation.Psk8Map(bits) : Modulation.Qam16Map(bits);

    private static byte[] Demap(int k, Complex[] s) => k == 3 ? Modulation.Psk8DemapHard(s) : Modulation.Qam16DemapHard(s);

    [Theory]
    [InlineData(3)]
    [InlineData(4)]
    public void RoundTripAndUnitEnergy(int k)
    {
        Complex[] pts = Map(k, AllLabels(k));
        Assert.Equal(1.0, pts.Average(x => x.Magnitude * x.Magnitude), 1e-15);
        byte[] bits = Waveforms.Prbs(9, 511 * k);
        Assert.Equal(bits, Demap(k, Map(k, bits)));
    }

    [Theory]
    [InlineData(3, 16)]
    [InlineData(4, 48)]
    public void NearestNeighborsDifferByOneBit(int k, int pairs)
    {
        Complex[] pts = Map(k, AllLabels(k));
        double nearest = double.PositiveInfinity;
        for (int a = 0; a < pts.Length; a++)
            for (int b = 0; b < pts.Length; b++)
                if (a != b)
                    nearest = Math.Min(nearest, Complex.Abs(pts[a] - pts[b]));
        int found = 0;
        for (int a = 0; a < pts.Length; a++)
            for (int b = 0; b < pts.Length; b++)
                if (a != b && Math.Abs(Complex.Abs(pts[a] - pts[b]) - nearest) < 1e-12)
                {
                    found++;
                    Assert.Equal(1, System.Numerics.BitOperations.PopCount((uint)(a ^ b)));
                }
        Assert.Equal(pairs, found);
    }

    [Theory]
    [InlineData(3)]
    [InlineData(4)]
    public void SmallNoiseDoesNotChangeADecision(int k)
    {
        byte[] bits = Waveforms.Prbs(11, 2047 * k);
        Complex[] s = Map(k, bits);
        double margin = k == 3 ? Math.Sin(Math.PI / 8) : 1 / Math.Sqrt(10);
        var rng = new Random(5);
        Complex[] noisy = [.. s.Select(x => x + 0.99 * margin / Math.Sqrt(2) * new Complex(2 * rng.NextDouble() - 1, 2 * rng.NextDouble() - 1))];
        Assert.Equal(bits, Demap(k, noisy));
    }

    [Fact]
    public void Ties()
    {
        double t = 2 / Math.Sqrt(10);
        Assert.Equal([0, 1, 0, 1, 0, 0, 1, 0], Modulation.Qam16DemapHard([0, new Complex(t, -t)]));
        Assert.Equal([0, 0, 0], Modulation.Psk8DemapHard([0]));
    }

    [Fact]
    public void BadArgumentsThrow()
    {
        Assert.ThrowsAny<ArgumentException>(() => Modulation.Psk8Map([0, 1]));
        Assert.ThrowsAny<ArgumentException>(() => Modulation.Psk8Map([0, 1, 2]));
        Assert.ThrowsAny<ArgumentException>(() => Modulation.Qam16Map([0, 1, 1]));
        Assert.ThrowsAny<ArgumentException>(() => Modulation.Qam16Map([0, 1, 1, 3]));
        Assert.ThrowsAny<ArgumentException>(() => Modulation.Psk8DemapHard([1, new Complex(0, double.NaN)]));
        Assert.ThrowsAny<ArgumentException>(() => Modulation.Qam16DemapHard([new Complex(double.NaN, 0)]));
    }
}
