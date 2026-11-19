using Xunit;

namespace SignalForge.Tests;

/// <summary>The Vargha–Delaney A (ADR 0401).</summary>
public class VarghaDelaneyATests
{
    [Fact]
    public void HandTwo() =>
        Assert.Equal(0.625, Measurements.VarghaDelaneyA([2.0, 4.0, 6.0, 8.0], [1.0, 5.0, 6.0]), 1e-15);

    [Fact]
    public void RejectsAnEmptySample() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.VarghaDelaneyA([1.0], []));
}
