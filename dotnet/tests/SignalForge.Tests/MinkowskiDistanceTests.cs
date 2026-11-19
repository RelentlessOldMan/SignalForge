using Xunit;

namespace SignalForge.Tests;

/// <summary>The Minkowski distance (ADR 0419).</summary>
public class MinkowskiDistanceTests
{
    [Fact]
    public void Euclid() =>
        Assert.Equal(5.0, Measurements.MinkowskiDistance([0.0, 0.0], [3.0, 4.0], 2.0), 1e-15);

    [Fact]
    public void RejectsAnOrderBelowOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.MinkowskiDistance([1.0], [2.0], 0.5));
}
