using Xunit;

namespace SignalForge.Tests;

/// <summary>The McConnaughey coefficient (ADR 0436).</summary>
public class McConnaugheyCoefficientTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(0.5, Measurements.McConnaugheyCoefficient([1.0, 1.0, 1.0, 1.0, 0.0], [1.0, 1.0, 0.0, 0.0, 0.0]), 15);

    [Fact]
    public void RejectsARecordWithNoOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.McConnaugheyCoefficient([1.0, 0.0], [0.0, 0.0]));
}
