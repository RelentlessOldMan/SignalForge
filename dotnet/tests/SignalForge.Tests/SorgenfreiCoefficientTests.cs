using Xunit;

namespace SignalForge.Tests;

/// <summary>The Sorgenfrei coefficient (ADR 0434).</summary>
public class SorgenfreiCoefficientTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(0.5, Measurements.SorgenfreiCoefficient([1.0, 1.0, 1.0, 1.0, 0.0], [1.0, 1.0, 0.0, 0.0, 0.0]), 15);

    [Fact]
    public void RejectsARecordWithNoOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.SorgenfreiCoefficient([1.0, 0.0], [0.0, 0.0]));
}
