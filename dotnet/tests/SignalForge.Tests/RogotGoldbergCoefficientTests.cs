using Xunit;

namespace SignalForge.Tests;

/// <summary>The Rogot-Goldberg coefficient (ADR 0467).</summary>
public class RogotGoldbergCoefficientTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(0.8, Measurements.RogotGoldbergCoefficient([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsRecordsBothAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.RogotGoldbergCoefficient([0.0, 0.0], [0.0, 0.0]));
}
