using Xunit;

namespace SignalForge.Tests;

/// <summary>The Rogers-Tanimoto coefficient (ADR 0425).</summary>
public class RogersTanimotoCoefficientTests
{
    [Fact]
    public void Identical() =>
        Assert.Equal(1.0, Measurements.RogersTanimotoCoefficient([1.0, 0.0, 1.0], [1.0, 0.0, 1.0]));

    [Fact]
    public void Partial() =>
        Assert.Equal(3.0 / 7.0, Measurements.RogersTanimotoCoefficient([1.0, 1.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0, 1.0]), 15);
}
