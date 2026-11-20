using Xunit;

namespace SignalForge.Tests;

/// <summary>Fossum's coefficient (ADR 0449).</summary>
public class FossumCoefficientTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(4.9, Measurements.FossumCoefficient([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 14);

    [Fact]
    public void RejectsARecordWithNoOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.FossumCoefficient([0.0, 1.0], [0.0, 0.0]));
}
