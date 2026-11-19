using Xunit;

namespace SignalForge.Tests;

/// <summary>The first Wasserstein distance (ADR 0403).</summary>
public class WassersteinDistanceTests
{
    [Fact]
    public void Unequal() =>
        Assert.Equal(1.0, Measurements.WassersteinDistance([0.0, 2.0], [1.0]), 1e-15);

    [Fact]
    public void RejectsAnEmptySample() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.WassersteinDistance([], [1.0]));
}
