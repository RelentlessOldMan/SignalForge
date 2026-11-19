using Xunit;

namespace SignalForge.Tests;

/// <summary>von Neumann ratio (ADR 0362).</summary>
public class VonNeumannRatioTests
{
    [Fact]
    public void ByHand()
    {
        Assert.Equal(3.0, Measurements.VonNeumannRatio([1.0, -1.0, 1.0, -1.0]), 1e-15);
        Assert.Equal(6.0 / 55, Measurements.VonNeumannRatio([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]), 1e-15);
    }

    [Fact]
    public void RejectsOneSample() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.VonNeumannRatio([1.0]));
}
