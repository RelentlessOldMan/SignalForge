using Xunit;

namespace SignalForge.Tests;

/// <summary>The relative risk reduction (ADR 0505).</summary>
public class RelativeRiskReductionTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(-3.0, Measurements.RelativeRiskReduction([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsNoFalseNegative() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.RelativeRiskReduction([1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0]));
}
