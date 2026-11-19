using Xunit;

namespace SignalForge.Tests;

/// <summary>Standard normal homogeneity test (ADR 0368).</summary>
public class SnhtTests
{
    [Fact]
    public void StepByHand()
    {
        // z = −1, −1, 1, 1: T_2 = 4.
        var got = Measurements.Snht([0.0, 0.0, 2.0, 2.0]);
        Assert.Equal(4.0, got.Statistic, 1e-15);
        Assert.Equal(1, got.Index);
    }

    [Fact]
    public void OneOutlier()
    {
        var got = Measurements.Snht([0.0, 0.0, 0.0, 4.0]);
        Assert.Equal(4.0, got.Statistic, 1e-15);
        Assert.Equal(2, got.Index);
    }

    [Fact]
    public void RejectsAConstantRecord() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.Snht([1.0, 1.0]));
}
