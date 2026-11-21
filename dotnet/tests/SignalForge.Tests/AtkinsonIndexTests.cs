using Xunit;

namespace SignalForge.Tests;

/// <summary>The Atkinson index (ADR 0515).</summary>
public class AtkinsonIndexTests
{
    [Fact]
    public void Harmonic() =>
        Assert.Equal(0.25, Measurements.AtkinsonIndex([1.0, 3.0], 2.0), 15);

    [Fact]
    public void Geometric() =>
        Assert.Equal(1.0 / 7.0, Measurements.AtkinsonIndex([4.0, 1.0, 2.0], 1.0), 15);

    [Fact]
    public void RejectsANegativeEpsilon() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.AtkinsonIndex([1.0, 2.0], -0.1));
}
