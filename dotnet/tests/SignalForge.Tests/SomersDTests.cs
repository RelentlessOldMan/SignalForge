using Xunit;

namespace SignalForge.Tests;

/// <summary>Somers' D (ADR 0378).</summary>
public class SomersDTests
{
    [Fact]
    public void TiesInThePredictorLeaveTheDenominator() =>
        Assert.Equal(-0.2, Measurements.SomersD([1.0, 1.0, 2.0, 3.0], [1.0, 2.0, 2.0, 1.0]), 1e-15);

    [Fact]
    public void RejectsAConstantPredictor() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.SomersD([1.0, 1.0, 1.0], [1.0, 2.0, 3.0]));
}
