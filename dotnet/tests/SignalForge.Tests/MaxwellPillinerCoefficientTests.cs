using Xunit;

namespace SignalForge.Tests;

/// <summary>The Maxwell-Pilliner coefficient (ADR 0458).</summary>
public class MaxwellPillinerCoefficientTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(0.6, Measurements.MaxwellPillinerCoefficient([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsTwoConstantRecords() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.MaxwellPillinerCoefficient([1.0, 1.0], [0.0, 0.0]));
}
