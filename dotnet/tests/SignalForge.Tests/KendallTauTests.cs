using Xunit;

namespace SignalForge.Tests;

/// <summary>Kendall's tau-b (ADR 0370).</summary>
public class KendallTauTests
{
    [Fact]
    public void OneSwap() =>
        Assert.Equal(2.0 / 3, Measurements.KendallTau([1.0, 2.0, 3.0, 4.0], [1.0, 3.0, 2.0, 4.0]), 1e-15);

    [Fact]
    public void Ties() =>
        Assert.Equal(0.8, Measurements.KendallTau([1.0, 2.0, 2.0, 3.0], [1.0, 1.0, 2.0, 3.0]), 1e-15);

    [Fact]
    public void RejectsAConstantRecord() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.KendallTau([1.0, 2.0], [3.0, 3.0]));
}
