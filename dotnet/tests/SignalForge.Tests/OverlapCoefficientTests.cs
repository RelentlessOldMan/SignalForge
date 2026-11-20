using Xunit;

namespace SignalForge.Tests;

/// <summary>The overlap coefficient (ADR 0422).</summary>
public class OverlapCoefficientTests
{
    [Fact]
    public void Subset() =>
        Assert.Equal(1.0, Measurements.OverlapCoefficient([1.0, 1.0, 1.0, 0.0], [0.0, 1.0, 0.0, 0.0]));

    [Fact]
    public void RejectsARecordWithNoOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.OverlapCoefficient([1.0, 0.0], [0.0, 0.0]));
}
