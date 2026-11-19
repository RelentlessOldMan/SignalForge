using Xunit;

namespace SignalForge.Tests;

/// <summary>Pearson correlation (ADR 0371).</summary>
public class PearsonCorrelationTests
{
    [Fact]
    public void ByHand() =>
        Assert.Equal(0.8, Measurements.PearsonCorrelation([1.0, 2.0, 3.0, 4.0], [1.0, 3.0, 2.0, 4.0]), 1e-15);

    [Fact]
    public void Line() =>
        Assert.Equal(1.0, Measurements.PearsonCorrelation([1.0, 2.0, 3.0, 4.0], [3.0, 5.0, 7.0, 9.0]));

    [Fact]
    public void RejectsAConstantRecord() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.PearsonCorrelation([1.0, 2.0], [3.0, 3.0]));
}
