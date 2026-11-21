using Xunit;

namespace SignalForge.Tests;

/// <summary>The Herfindahl index (ADR 0523).</summary>
public class HerfindahlIndexTests
{
    [Fact]
    public void Ramp() =>
        Assert.Equal(0.3, Measurements.HerfindahlIndex([4.0, 1.0, 3.0, 2.0]), 15);

    [Fact]
    public void Halves() =>
        Assert.Equal(11.0 / 32.0, Measurements.HerfindahlIndex([0.5, 0.25, 0.25, 1.0]), 15);

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HerfindahlIndex([0.0, 0.0]));
}
