using Xunit;

namespace SignalForge.Tests;

/// <summary>The rarefied richness (ADR 0552).</summary>
public class RarefiedRichnessTests
{
    [Fact]
    public void Ramp() =>
        Assert.Equal(26.0 / 15.0, Measurements.RarefiedRichness([1.0, 2.0, 3.0], 2), 14);

    [Fact]
    public void AllDrawn() =>
        Assert.Equal(3.0, Measurements.RarefiedRichness([3.0, 0.0, 1.0, 2.0], 6), 15);

    [Fact]
    public void RejectsSizeAboveTotal() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.RarefiedRichness([1.0, 2.0], 4));
}
