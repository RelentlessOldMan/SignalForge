using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>64-QAM map, demap and theory (conventions: Bits and symbols, EVM and BER; ADR 0052).</summary>
public class Qam64Tests
{
    private static readonly byte[] All =
        [.. Enumerable.Range(0, 64).SelectMany(m => Enumerable.Range(0, 6).Select(i => (byte)((m >> (5 - i)) & 1)))];

    private static double Normal(Random rng) =>
        Math.Sqrt(-2 * Math.Log(1 - rng.NextDouble())) * Math.Cos(2 * Math.PI * rng.NextDouble());

    [Fact]
    public void UnitEnergyAndRoundTrip()
    {
        Complex[] z = Modulation.Qam64Map(All);
        Assert.Equal(1.0, z.Average(v => v.Real * v.Real + v.Imaginary * v.Imaginary), 1e-15);
        Assert.Equal(All, Modulation.Qam64DemapHard(z));
    }

    [Fact]
    public void GrayNeighboursDifferInOneBit()
    {
        Complex[] z = Modulation.Qam64Map(All);
        double d = 2 / Math.Sqrt(42);
        for (int a = 0; a < 64; a++)
        {
            for (int b = 0; b < 64; b++)
            {
                if (Math.Abs((z[a] - z[b]).Magnitude - d) < 1e-12)
                    Assert.Equal(1, Enumerable.Range(0, 6).Count(i => All[6 * a + i] != All[6 * b + i]));
            }
        }
    }

    [Fact]
    public void LlrSignIsTheHardDecision()
    {
        var rng = new Random(4);
        Complex[] y = [.. Enumerable.Range(0, 500).Select(_ => 1.3 * new Complex(Normal(rng), Normal(rng)))];
        double[] llr = Modulation.Qam64DemapLlr(y, 0.1);
        Assert.Equal(Modulation.Qam64DemapHard(y), llr.Select(l => l < 0 ? (byte)1 : (byte)0).ToArray());
    }

    [Fact]
    public void BerAndSerMatchMonteCarlo()
    {
        var rng = new Random(7);
        const double eb = 12;
        const int n = 100_000;
        byte[] bits = [.. Enumerable.Range(0, 6 * n).Select(_ => (byte)rng.Next(2))];
        Complex[] z = Modulation.Qam64Map(bits);
        double sigma = Math.Sqrt(Math.Pow(10, -(eb + 10 * Math.Log10(6)) / 10) / 2);
        Complex[] y = [.. z.Select(v => v + new Complex(sigma * Normal(rng), sigma * Normal(rng)))];
        byte[] got = Modulation.Qam64DemapHard(y);
        double ber = Enumerable.Range(0, 6 * n).Count(i => got[i] != bits[i]) / (6.0 * n);
        double ser = Enumerable.Range(0, n).Count(s => Enumerable.Range(0, 6).Any(i => got[6 * s + i] != bits[6 * s + i])) / (double)n;
        Assert.Equal(1.0, ber / Metrics.Qam64BerTheory(eb), 0.05);
        Assert.Equal(1.0, ser / Metrics.Qam64SerTheory(eb), 0.05);
    }

    [Fact]
    public void TheoryLimits()
    {
        Assert.Equal(0.5, Metrics.Qam64BerTheory(double.NegativeInfinity));
        Assert.Equal(63.0 / 64, Metrics.Qam64SerTheory(double.NegativeInfinity));
        Assert.Equal(0.0, Metrics.Qam64BerTheory(double.PositiveInfinity));
        Assert.ThrowsAny<ArgumentException>(() => Metrics.Qam64BerTheory(double.NaN));
    }

    [Fact]
    public void Rejects()
    {
        Assert.ThrowsAny<ArgumentException>(() => Modulation.Qam64Map([0, 1, 1]));
        Assert.ThrowsAny<ArgumentException>(() => Modulation.Qam64Map([0, 1, 1, 0, 2, 0]));
        Assert.ThrowsAny<ArgumentException>(() => Modulation.Qam64DemapHard([Complex.One, new Complex(double.NaN, 0)]));
    }
}
