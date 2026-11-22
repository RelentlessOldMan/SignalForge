using Xunit;

namespace SignalForge.Tests;

/// <summary>Morisita's overlap of two count records (ADR 0581).</summary>
public class MorisitaOverlapTests
{
    [Fact]
    public void Identical() =>
        Assert.Equal(1.125, Measurements.MorisitaOverlap([5.0, 5.0], [5.0, 5.0]));

    [Fact]
    public void Crossed() =>
        Assert.Equal(0.75, Measurements.MorisitaOverlap([3.0, 1.0], [1.0, 3.0]));

    [Fact]
    public void Disjoint() =>
        Assert.Equal(0.0, Measurements.MorisitaOverlap([2.0, 0.0], [0.0, 2.0]));

    [Fact]
    public void RejectsFraction() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.MorisitaOverlap([2.0, 0.5], [1.0, 2.0]));

    [Fact]
    public void RejectsAllOnes() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.MorisitaOverlap([1.0, 1.0], [1.0, 1.0]));
}
