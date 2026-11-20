using Xunit;

namespace SignalForge.Tests;

/// <summary>The Hamann coefficient (ADR 0432).</summary>
public class HamannCoefficientTests
{
    [Fact]
    public void Uneven() =>
        Assert.Equal(0.2, Measurements.HamannCoefficient([1.0, 1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0, 1.0]), 15);

    [Fact]
    public void RejectsAnEmptyRecord() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HamannCoefficient([], []));
}
