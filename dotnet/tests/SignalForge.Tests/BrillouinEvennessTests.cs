using Xunit;

namespace SignalForge.Tests;

/// <summary>The Brillouin evenness (ADR 0547).</summary>
public class BrillouinEvennessTests
{
    [Fact]
    public void Ramp() =>
        Assert.Equal(Math.Log(60.0) / Math.Log(90.0), Measurements.BrillouinEvenness([1.0, 2.0, 3.0]), 14);

    [Fact]
    public void AsEvenAsPossible() =>
        Assert.Equal(1.0, Measurements.BrillouinEvenness([0.0, 2.0, 1.0]), 14);

    [Fact]
    public void RejectsOnePositive() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.BrillouinEvenness([0.0, 5.0]));
}
