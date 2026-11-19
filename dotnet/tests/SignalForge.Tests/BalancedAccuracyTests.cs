using Xunit;

namespace SignalForge.Tests;

/// <summary>The balanced accuracy (ADR 0396).</summary>
public class BalancedAccuracyTests
{
    [Fact]
    public void Hand() =>
        Assert.Equal(17.0 / 24, Measurements.BalancedAccuracy([1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0]), 1e-15);

    [Fact]
    public void RejectsATruthWithoutAOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.BalancedAccuracy([0.0, 0.0], [1.0, 0.0]));
}
