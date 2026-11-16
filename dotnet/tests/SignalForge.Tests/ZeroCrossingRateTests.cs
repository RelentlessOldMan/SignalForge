using Xunit;

namespace SignalForge.Tests;

/// <summary>Zero-crossing rate (conventions: Zero-crossing rate; ADR 0146).</summary>
public class ZeroCrossingRateTests
{
    private static double[] Sine(int cycles, int n) =>
        [.. Enumerable.Range(0, n).Select(i => Math.Sin(2 * Math.PI * cycles * i / n + 0.3))];

    [Fact]
    public void SineCrossesTwicePerCycle()
    {
        const int n = 1000;
        Assert.Equal(14.0 / (n - 1), Measurements.ZeroCrossingRate(Sine(7, n)), 1e-15);
    }

    [Fact]
    public void PositiveScalingLeavesItUnchanged()
    {
        var rng = new Random(146);
        double[] x = [.. Enumerable.Range(0, 500).Select(_ => rng.NextDouble() - 0.5)];
        Assert.Equal(Measurements.ZeroCrossingRate(x), Measurements.ZeroCrossingRate([.. x.Select(v => 3.5 * v)]));
    }
}
