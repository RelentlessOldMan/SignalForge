using Xunit;

namespace SignalForge.Tests;

/// <summary>The energy distance (ADR 0404).</summary>
public class EnergyDistanceTests
{
    [Fact]
    public void HandTwo() =>
        Assert.Equal(1.5, Measurements.EnergyDistance([0.0, 0.0], [0.0, 3.0]), 1e-15);

    [Fact]
    public void RejectsAnEmptySample() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.EnergyDistance([1.0], []));
}
