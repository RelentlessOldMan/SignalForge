using Xunit;

namespace SignalForge.Tests;

/// <summary>The replacement part of the Ruzicka dissimilarity (ADR 0586).</summary>
public class RuzickaReplacementTests
{
    [Fact]
    public void Nested() =>
        Assert.Equal(0.0, Measurements.RuzickaReplacement([1.0, 0.0, 0.0], [1.0, 1.0, 1.0]));

    [Fact]
    public void Huge() =>
        Assert.Equal(2.0 / 3.0, Measurements.RuzickaReplacement([1.5e308, 1.5e308, 0.0], [1.5e308, 0.0, 1.5e308]), 15);

    [Fact]
    public void Disjoint() =>
        Assert.Equal(1.0, Measurements.RuzickaReplacement([1.0, 0.0], [0.0, 1.0]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.RuzickaReplacement([0.0, 0.0], [1.0, 2.0]));
}
