using Xunit;

namespace SignalForge.Tests;

/// <summary>The Braun-Blanquet coefficient (ADR 0440).</summary>
public class BraunBlanquetCoefficientTests
{
    [Fact]
    public void Thirds() =>
        Assert.Equal(1.0 / 3.0, Measurements.BraunBlanquetCoefficient([1, 1, 1, 0, 0, 0], [1, 0, 0, 1, 1, 0]), 15);

    [Fact]
    public void RejectsTwoRecordsOfZeros() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.BraunBlanquetCoefficient([0.0, 0.0], [0.0, 0.0]));
}
