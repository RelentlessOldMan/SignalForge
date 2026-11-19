using Xunit;

namespace SignalForge.Tests;

/// <summary>Spearman rank correlation (ADR 0369).</summary>
public class SpearmanCorrelationTests
{
    [Fact]
    public void ByHand()
    {
        // Centred ranks give a product sum of 4 over sums of squares of 5.
        Assert.Equal(0.8, Measurements.SpearmanCorrelation([1.0, 2.0, 3.0, 4.0], [1.0, 3.0, 2.0, 4.0]), 1e-15);
    }

    [Fact]
    public void Ties() =>
        Assert.Equal(5.0 / 6, Measurements.SpearmanCorrelation([1.0, 2.0, 2.0, 3.0], [1.0, 1.0, 2.0, 3.0]), 1e-15);

    [Fact]
    public void RejectsAConstantRecord() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.SpearmanCorrelation([1.0, 2.0], [3.0, 3.0]));
}
