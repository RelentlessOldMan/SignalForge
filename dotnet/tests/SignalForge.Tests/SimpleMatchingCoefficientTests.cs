using Xunit;

namespace SignalForge.Tests;

/// <summary>The simple matching coefficient (ADR 0424).</summary>
public class SimpleMatchingCoefficientTests
{
    [Fact]
    public void SharedAbsencesCount() =>
        Assert.Equal(1.0, Measurements.SimpleMatchingCoefficient([0.0, 0.0, 0.0], [0.0, 0.0, 0.0]));

    [Fact]
    public void Partial() =>
        Assert.Equal(0.6, Measurements.SimpleMatchingCoefficient([1.0, 1.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0, 1.0]), 15);
}
