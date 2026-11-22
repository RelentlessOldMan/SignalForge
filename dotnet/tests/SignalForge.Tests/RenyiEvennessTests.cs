using Xunit;

namespace SignalForge.Tests;

/// <summary>Renyi evenness (ADR 0567).</summary>
public class RenyiEvennessTests
{
    [Fact]
    public void InverseSimpson() =>
        Assert.Equal(Math.Log(8.0 / 3.0) / Math.Log(3.0), Measurements.RenyiEvenness([1.0, 1.0, 2.0], 2.0), 14);

    [Fact]
    public void ZeroOrderIsOne() =>
        Assert.Equal(1.0, Measurements.RenyiEvenness([0.0, 2.0, 5.0], 0.0));

    [Fact]
    public void RejectsOneKind() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.RenyiEvenness([0.0, 4.0], 1.0));
}
