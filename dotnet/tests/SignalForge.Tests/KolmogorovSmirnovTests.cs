using Xunit;

namespace SignalForge.Tests;

/// <summary>The two-sample Kolmogorov–Smirnov statistic (ADR 0402).</summary>
public class KolmogorovSmirnovTests
{
    [Fact]
    public void Spread() =>
        Assert.Equal(1.0 / 3.0, Measurements.KolmogorovSmirnov([0.0, 0.0, 0.0, 0.0], [-1.0, 0.0, 1.0]), 1e-15);

    [Fact]
    public void RejectsAnEmptySample() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.KolmogorovSmirnov([], [1.0]));
}
