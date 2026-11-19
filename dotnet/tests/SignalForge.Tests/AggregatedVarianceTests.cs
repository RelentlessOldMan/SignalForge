using Xunit;

namespace SignalForge.Tests;

/// <summary>Aggregated variance (ADR 0355).</summary>
public class AggregatedVarianceTests
{
    [Fact]
    public void OddBlocksByHand()
    {
        // ±1 alternating, 18 samples: variances 1, 1/9, 1/81 at s = 1, 3, 9; slope −2.
        var x = new double[18];
        for (int i = 0; i < x.Length; i++)
            x[i] = i % 2 == 0 ? 1 : -1;
        var got = Measurements.AggregatedVariance(x, [1, 3, 9]);
        Assert.Equal(1.0 / 9, got.Values[1], 1e-15);
        Assert.Equal(1.0 / 81, got.Values[2], 1e-15);
        Assert.Equal(0.0, got.Hurst, 1e-14);
    }

    [Fact]
    public void RejectsBlockMeansThatDoNotVary() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.AggregatedVariance([1.0, -1.0, 1.0, -1.0], [1, 2]));
}
