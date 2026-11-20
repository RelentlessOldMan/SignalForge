using Xunit;

namespace SignalForge.Tests;

/// <summary>The Pearson-Heron II coefficient (ADR 0443).</summary>
public class PearsonHeronIITests
{
    [Fact]
    public void Fifth() =>
        Assert.Equal((1 + Math.Sqrt(5.0)) / 4, Measurements.PearsonHeronII([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 14);

    [Fact]
    public void RejectsATableWithBothProductsZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.PearsonHeronII([1.0, 1.0, 1.0], [1.0, 0.0, 1.0]));
}
