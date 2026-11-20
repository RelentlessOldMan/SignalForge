using Xunit;

namespace SignalForge.Tests;

/// <summary>The variance dissimilarity (ADR 0475).</summary>
public class VarianceDissimilarityTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(0.05, Measurements.VarianceDissimilarity([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsUnequalLengths() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.VarianceDissimilarity([0.0, 1.0], [1.0]));
}
