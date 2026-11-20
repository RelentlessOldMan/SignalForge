using Xunit;

namespace SignalForge.Tests;

/// <summary>Gower's coefficient (ADR 0469).</summary>
public class GowerCoefficientTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(0.32, Measurements.GowerCoefficient([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsAConstantRecord() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.GowerCoefficient([1.0, 1.0], [1.0, 0.0]));
}
