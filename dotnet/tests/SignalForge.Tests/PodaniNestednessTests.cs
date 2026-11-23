using Xunit;

namespace SignalForge.Tests;

/// <summary>Podani's nestedness of two presence records (ADR 0588).</summary>
public class PodaniNestednessTests
{
    [Fact]
    public void Nested() =>
        Assert.Equal(1.0, Measurements.PodaniNestedness([1.0, 0.0, 0.0], [1.0, 1.0, 1.0]));

    [Fact]
    public void Uneven() =>
        Assert.Equal(2.0 / 3.0, Measurements.PodaniNestedness([1.0, 1.0, 0.0, 1.0, 1.0, 1.0], [1.0, 0.0, 1.0, 0.0, 0.0, 0.0]), 15);

    [Fact]
    public void Disjoint() =>
        Assert.Equal(0.0, Measurements.PodaniNestedness([1.0, 0.0], [0.0, 1.0]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.PodaniNestedness([0.0, 0.0], [1.0, 2.0]));
}
