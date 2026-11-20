using Xunit;

namespace SignalForge.Tests;

/// <summary>The Baroni-Urbani-Buser coefficient (ADR 0433).</summary>
public class BaroniUrbaniBuserCoefficientTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(0.8, Measurements.BaroniUrbaniBuserCoefficient([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsRecordsWithNoOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.BaroniUrbaniBuserCoefficient([0.0, 0.0], [0.0, 0.0]));
}
