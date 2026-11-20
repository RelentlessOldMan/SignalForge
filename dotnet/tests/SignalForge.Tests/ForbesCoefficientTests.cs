using Xunit;

namespace SignalForge.Tests;

/// <summary>The Forbes coefficient (ADR 0435).</summary>
public class ForbesCoefficientTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(1.25, Measurements.ForbesCoefficient([1.0, 1.0, 1.0, 1.0, 0.0], [1.0, 1.0, 0.0, 0.0, 0.0]), 15);

    [Fact]
    public void RejectsARecordWithNoOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ForbesCoefficient([1.0, 0.0], [0.0, 0.0]));
}
