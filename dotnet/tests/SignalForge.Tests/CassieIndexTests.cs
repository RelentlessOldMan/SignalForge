using Xunit;

namespace SignalForge.Tests;

/// <summary>Cassie's index (ADR 0614).</summary>
public class CassieIndexTests
{
    [Fact]
    public void Mixed() =>
        Assert.Equal(-0.25, Measurements.CassieIndex([1.0, 2.0, 3.0]), 14);

    [Fact]
    public void Uneven() =>
        Assert.Equal(85.0 / 128.0, Measurements.CassieIndex([4.0, 0.0, 1.0, 0.0, 3.0]), 14);

    [Fact]
    public void Singles() =>
        Assert.Equal(-2.0 / 3.0, Measurements.CassieIndex([1.0, 1.0, 0.0, 0.0]), 14);

    [Fact]
    public void RejectsOneUnit() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.CassieIndex([5.0]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.CassieIndex([0.0, 0.0]));
}
