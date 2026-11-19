using Xunit;

namespace SignalForge.Tests;

/// <summary>The Hellinger distance (ADR 0409).</summary>
public class HellingerDistanceTests
{
    [Fact]
    public void Quarter() =>
        Assert.Equal(Math.Sqrt(0.5), Measurements.HellingerDistance([1.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0]), 1e-15);

    [Fact]
    public void RejectsANegativeWeight() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HellingerDistance([1.0, -1.0], [1.0, 1.0]));
}
