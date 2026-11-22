using Xunit;

namespace SignalForge.Tests;

/// <summary>Hill evenness (ADR 0564).</summary>
public class HillEvennessTests
{
    [Fact]
    public void InverseSimpson() =>
        Assert.Equal(8.0 / 9.0, Measurements.HillEvenness([1.0, 1.0, 2.0], 2.0), 14);

    [Fact]
    public void ZeroOrderIsOne() =>
        Assert.Equal(1.0, Measurements.HillEvenness([0.0, 2.0, 5.0], 0.0));

    [Fact]
    public void RejectsNegativeOrder() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HillEvenness([1.0], -1.0));
}
