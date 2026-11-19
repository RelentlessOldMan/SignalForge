using Xunit;

namespace SignalForge.Tests;

/// <summary>The triangular discrimination (ADR 0416).</summary>
public class TriangularDiscriminationTests
{
    [Fact]
    public void Half() =>
        Assert.Equal(2.0 / 3.0, Measurements.TriangularDiscrimination([1.0, 0.0], [1.0, 1.0]), 1e-15);

    [Fact]
    public void RejectsUnequalLengths() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.TriangularDiscrimination([1.0], [1.0, 1.0]));
}
