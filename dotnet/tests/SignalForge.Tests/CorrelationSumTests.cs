using Xunit;

namespace SignalForge.Tests;

/// <summary>Correlation sum (ADR 0349).</summary>
public class CorrelationSumTests
{
    [Fact]
    public void ARampByHand()
    {
        // Distances 1, 2, 3, 1, 2, 1: C(1.5) = 3/6, C(2.5) = 5/6, the slope 1.
        var got = Measurements.CorrelationSum([0.0, 1.0, 2.0, 3.0], 1, [1.5, 2.5]);
        Assert.Equal(0.5, got.Values[0], 1e-15);
        Assert.Equal(5.0 / 6, got.Values[1], 1e-15);
        Assert.Equal(1.0, got.Dimension, 1e-14);
    }

    [Fact]
    public void ADistanceOnTheRadiusDoesNotCount() =>
        Assert.Equal(0.5, Measurements.CorrelationSum([0.0, 1.0, 2.0, 3.0], 1, [2.0, 3.0]).Values[0], 1e-15);

    [Fact]
    public void RejectsARadiusBelowEveryDistance() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.CorrelationSum([0.0, 1.0, 2.0], 1, [0.5, 2.0]));
}
