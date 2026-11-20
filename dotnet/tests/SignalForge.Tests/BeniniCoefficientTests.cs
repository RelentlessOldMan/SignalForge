using Xunit;

namespace SignalForge.Tests;

/// <summary>The Benini coefficient (ADR 0465).</summary>
public class BeniniCoefficientTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(0.6, Measurements.BeniniCoefficient([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsARecordWithNoOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.BeniniCoefficient([1.0, 0.0], [0.0, 0.0]));
}
