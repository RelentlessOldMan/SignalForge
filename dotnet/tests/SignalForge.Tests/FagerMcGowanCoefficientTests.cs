using Xunit;

namespace SignalForge.Tests;

/// <summary>The Fager-McGowan coefficient (ADR 0438).</summary>
public class FagerMcGowanCoefficientTests
{
    [Fact]
    public void Singles() =>
        Assert.Equal(-0.5, Measurements.FagerMcGowanCoefficient([1.0, 0.0], [0.0, 1.0]), 15);

    [Fact]
    public void RejectsARecordWithNoOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.FagerMcGowanCoefficient([1.0, 0.0], [0.0, 0.0]));
}
