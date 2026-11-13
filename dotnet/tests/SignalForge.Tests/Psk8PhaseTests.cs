using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Psk8PhaseOffset and Psk8BlockPhases (conventions: Synchronization; ADR 0051).</summary>
public class Psk8PhaseTests
{
    private static Complex[] Symbols(int n, int seed = 3)
    {
        var rng = new Random(seed);
        byte[] bits = [.. Enumerable.Range(0, 3 * n).Select(_ => (byte)rng.Next(2))];
        return Modulation.Psk8Map(bits);
    }

    private static Complex[] Rotate(Complex[] z, Func<int, double> phase) =>
        [.. z.Select((v, k) => v * Complex.FromPolarCoordinates(1, phase(k)))];

    [Theory]
    [InlineData(-0.39)]
    [InlineData(-0.1)]
    [InlineData(0.0)]
    [InlineData(0.2)]
    [InlineData(0.39)]
    public void PhaseInsideRangeIsExact(double phi) =>
        Assert.Equal(phi, Sync.Psk8PhaseOffset(Rotate(Symbols(50), _ => phi)), 1e-12);

    [Fact]
    public void PhaseIsModuloPiOver4()
    {
        Complex[] z = Symbols(50);
        for (int m = -4; m <= 4; m++)
            Assert.Equal(0.1, Sync.Psk8PhaseOffset(Rotate(z, _ => 0.1 + m * Math.PI / 4)), 1e-12);
    }

    [Fact]
    public void ScaleDoesNotMatter()
    {
        Complex[] z = Rotate(Symbols(20), _ => 0.25);
        foreach (double s in new[] { 1e-200, 1e-3, 1e150 })
            Assert.Equal(0.25, Sync.Psk8PhaseOffset([.. z.Select(v => v * s)]), 1e-12);
    }

    [Fact]
    public void BlockPhasesFollowARampPastPiOver8()
    {
        const int n = 400, b = 20;
        const double w = 0.004; // 0.08 rad per block, under π/8
        double[] ph = Sync.Psk8BlockPhases(Rotate(Symbols(n), k => 0.3 + w * k), b);
        for (int i = 0; i < ph.Length; i++)
            Assert.Equal(0.3 + w * (i * b + Math.Min(i * b + b, n) - 1) / 2.0, ph[i], 1e-9);
        Assert.True(ph[^1] > 1.5);
    }

    [Fact]
    public void ShortLastBlock() => Assert.Equal(3, Sync.Psk8BlockPhases(Symbols(45), 20).Length);

    [Fact]
    public void Rejects()
    {
        Assert.ThrowsAny<ArgumentException>(() => Sync.Psk8BlockPhases(Symbols(10), 0));
        Assert.ThrowsAny<ArgumentException>(() => Sync.Psk8PhaseOffset([]));
        Assert.ThrowsAny<ArgumentException>(() => Sync.Psk8PhaseOffset([Complex.One, new Complex(double.NaN, 0)]));
        Assert.ThrowsAny<ArgumentException>(() => Sync.Psk8BlockPhases([], 2));
    }
}
