using Xunit;

namespace SignalForge.Tests;

/// <summary>Scott's pi (ADR 0384).</summary>
public class ScottPiTests
{
    [Fact]
    public void UnsharedCategory() =>
        Assert.Equal(3.0 / 19, Measurements.ScottPi([0.0, 0.0, 1.0, 2.0], [0.0, 1.0, 1.0, 1.0]), 1e-15);

    [Fact]
    public void RejectsOneSharedLabel() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ScottPi([1.0, 1.0], [1.0, 1.0]));
}
