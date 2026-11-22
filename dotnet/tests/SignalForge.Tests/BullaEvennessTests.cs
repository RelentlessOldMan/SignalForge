using Xunit;

namespace SignalForge.Tests;

/// <summary>Bulla's evenness (ADR 0535).</summary>
public class BullaEvennessTests
{
    [Fact]
    public void Halves() =>
        Assert.Equal(2.0 / 3.0, Measurements.BullaEvenness([0.5, 0.25, 0.25, 1.0]), 15);

    [Fact]
    public void Three() =>
        Assert.Equal(0.375, Measurements.BullaEvenness([3.0, 0.0, 1.0]), 15);

    [Fact]
    public void RejectsOneValue() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.BullaEvenness([5.0]));
}
