using Xunit;

namespace SignalForge.Tests;

/// <summary>The chi-square statistic of two binary records (ADR 0478).</summary>
public class BinaryChiSquareTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(3.6, Measurements.BinaryChiSquare([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 13);

    [Fact]
    public void RejectsAConstantRecord() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.BinaryChiSquare([1.0, 1.0], [1.0, 0.0]));
}
