using Xunit;

namespace SignalForge.Tests;

/// <summary>The Ochiai coefficient (ADR 0429).</summary>
public class OchiaiCoefficientTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(1.0 / Math.Sqrt(2.0), Measurements.OchiaiCoefficient([1.0, 1.0, 1.0, 1.0, 0.0], [1.0, 1.0, 0.0, 0.0, 0.0]), 15);

    [Fact]
    public void RejectsARecordWithNoOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.OchiaiCoefficient([1.0, 0.0], [0.0, 0.0]));
}
