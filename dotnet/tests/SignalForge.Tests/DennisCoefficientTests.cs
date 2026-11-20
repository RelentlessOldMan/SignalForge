using Xunit;

namespace SignalForge.Tests;

/// <summary>The Dennis coefficient (ADR 0437).</summary>
public class DennisCoefficientTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(3.0 / Math.Sqrt(10.0), Measurements.DennisCoefficient([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 14);

    [Fact]
    public void RejectsARecordWithNoOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.DennisCoefficient([1.0, 0.0], [0.0, 0.0]));
}
