using Xunit;

namespace SignalForge.Tests;

/// <summary>Michael's coefficient (ADR 0442).</summary>
public class MichaelCoefficientTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(15.0 / 17.0, Measurements.MichaelCoefficient([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void IsDefinedForConstantRecords() =>
        Assert.Equal(0.0, Measurements.MichaelCoefficient([0.0, 0.0], [0.0, 0.0]));
}
