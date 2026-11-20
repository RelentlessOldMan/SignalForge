using Xunit;

namespace SignalForge.Tests;

/// <summary>The Doolittle coefficient (ADR 0466).</summary>
public class DoolittleCoefficientTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(0.36, Measurements.DoolittleCoefficient([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsAConstantRecord() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.DoolittleCoefficient([1.0, 0.0], [0.0, 0.0]));
}
