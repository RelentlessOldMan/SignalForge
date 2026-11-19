using Xunit;

namespace SignalForge.Tests;

/// <summary>Distribution entropy (ADR 0348).</summary>
public class DistributionEntropyTests
{
    [Fact]
    public void ThreePointsByHand()
    {
        // Distances 1, 2, 1 over [1, 2] in four bins: bins 0, 3, 0.
        double expected = -((2.0 / 3 * Math.Log(2.0 / 3)) + (1.0 / 3 * Math.Log(1.0 / 3))) / Math.Log(4);
        Assert.Equal(expected, Measurements.DistributionEntropy([0.0, 1.0, 2.0], 1, 4), 1e-15);
    }

    [Fact]
    public void AConstantIsZero() =>
        Assert.Equal(0.0, Measurements.DistributionEntropy([3.0, 3.0, 3.0, 3.0], 2));

    [Fact]
    public void RejectsTooShort() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.DistributionEntropy([0.0, 1.0], 2));
}
