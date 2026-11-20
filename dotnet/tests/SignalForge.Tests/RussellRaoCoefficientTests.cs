using Xunit;

namespace SignalForge.Tests;

/// <summary>The Russell-Rao coefficient (ADR 0426).</summary>
public class RussellRaoCoefficientTests
{
    [Fact]
    public void SharedZerosDoNotCount() =>
        Assert.Equal(0.5, Measurements.RussellRaoCoefficient([1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0]));

    [Fact]
    public void Partial() =>
        Assert.Equal(0.4, Measurements.RussellRaoCoefficient([1.0, 1.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0, 1.0]), 15);
}
