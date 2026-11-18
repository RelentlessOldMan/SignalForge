using Xunit;

namespace SignalForge.Tests;

/// <summary>Lempel-Ziv complexity (ADR 0336).</summary>
public class LempelZivComplexityTests
{
    [Fact]
    public void LempelAndZivsExample() =>
        Assert.Equal(6, Measurements.LempelZivComplexity([0, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1]));

    [Fact]
    public void TwoBits()
    {
        Assert.Equal(2, Measurements.LempelZivComplexity([0, 1]));
        Assert.Equal(2, Measurements.LempelZivComplexity([1, 1]));
    }

    [Fact]
    public void RejectsEmpty() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.LempelZivComplexity([]));
}
