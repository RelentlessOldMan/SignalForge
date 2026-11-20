using Xunit;

namespace SignalForge.Tests;

/// <summary>The Johnson coefficient (ADR 0470).</summary>
public class JohnsonCoefficientTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(1.6, Measurements.JohnsonCoefficient([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsARecordWithNoOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.JohnsonCoefficient([0.0, 0.0], [1.0, 0.0]));
}
