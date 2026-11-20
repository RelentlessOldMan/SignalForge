using Xunit;

namespace SignalForge.Tests;

/// <summary>Cole's coefficient (ADR 0445).</summary>
public class ColeCoefficientTests
{
    [Fact]
    public void Negative() =>
        Assert.Equal(-1.0 / 3.0, Measurements.ColeCoefficient([1, 1, 1, 0, 0, 0], [1, 0, 0, 1, 1, 0]), 15);

    [Fact]
    public void RejectsAConstantRecord() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ColeCoefficient([0.0, 1.0], [0.0, 0.0]));
}
