using Xunit;

namespace SignalForge.Tests;

/// <summary>The Gilbert-Wells coefficient (ADR 0463).</summary>
public class GilbertWellsCoefficientTests
{
    [Fact]
    public void Independent() =>
        Assert.Equal(0.0, Measurements.GilbertWellsCoefficient([1, 1, 0, 0], [1, 0, 1, 0]), 15);

    [Fact]
    public void RejectsRecordsThatShareNoOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.GilbertWellsCoefficient([1.0, 0.0], [0.0, 1.0]));
}
