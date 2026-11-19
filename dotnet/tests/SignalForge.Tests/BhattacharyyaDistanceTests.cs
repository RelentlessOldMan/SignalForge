using Xunit;

namespace SignalForge.Tests;

/// <summary>The Bhattacharyya distance (ADR 0410).</summary>
public class BhattacharyyaDistanceTests
{
    [Fact]
    public void Quarter() =>
        Assert.Equal(Math.Log(2.0), Measurements.BhattacharyyaDistance([1.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0]), 1e-15);

    [Fact]
    public void RejectsDisjointSupport() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.BhattacharyyaDistance([1.0, 0.0], [0.0, 1.0]));
}
