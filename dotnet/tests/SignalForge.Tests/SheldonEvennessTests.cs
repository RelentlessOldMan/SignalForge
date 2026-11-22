using Xunit;

namespace SignalForge.Tests;

/// <summary>Sheldon's evenness (ADR 0538).</summary>
public class SheldonEvennessTests
{
    [Fact]
    public void OneZero() =>
        Assert.Equal(0.8, Measurements.SheldonEvenness([0.0, 2.0, 2.0, 2.0, 2.0]), 13);

    [Fact]
    public void OneHoldsAll() =>
        Assert.Equal(0.25, Measurements.SheldonEvenness([0.0, 0.0, 0.0, 4.0]), 15);

    [Fact]
    public void RejectsEmpty() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.SheldonEvenness([]));
}
