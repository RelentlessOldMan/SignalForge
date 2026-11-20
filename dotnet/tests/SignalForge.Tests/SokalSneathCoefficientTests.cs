using Xunit;

namespace SignalForge.Tests;

/// <summary>The Sokal-Sneath coefficient (ADR 0427).</summary>
public class SokalSneathCoefficientTests
{
    [Fact]
    public void Subset() =>
        Assert.Equal(0.2, Measurements.SokalSneathCoefficient([1.0, 1.0, 1.0, 0.0], [0.0, 1.0, 0.0, 0.0]), 15);

    [Fact]
    public void RejectsRecordsWithNoOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.SokalSneathCoefficient([0.0, 0.0], [0.0, 0.0]));
}
