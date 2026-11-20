using Xunit;

namespace SignalForge.Tests;

/// <summary>Anderberg's D (ADR 0446).</summary>
public class AnderbergDTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(0.3, Measurements.AnderbergD([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsRecordsOfDifferentLengths() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.AnderbergD([0.0, 1.0], [0.0]));
}
