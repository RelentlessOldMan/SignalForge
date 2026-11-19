using Xunit;

namespace SignalForge.Tests;

/// <summary>The two-sample Cramér–von Mises statistic (ADR 0405).</summary>
public class CramerVonMisesTests
{
    [Fact]
    public void Hand() =>
        Assert.Equal(0.1, Measurements.CramerVonMises([1.0, 2.0, 3.0], [2.0, 4.0]), 1e-15);

    [Fact]
    public void RejectsAnEmptySample() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.CramerVonMises([1.0], []));
}
