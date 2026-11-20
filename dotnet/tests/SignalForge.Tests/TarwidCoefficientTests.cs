using Xunit;

namespace SignalForge.Tests;

/// <summary>Tarwid's coefficient (ADR 0453).</summary>
public class TarwidCoefficientTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(3.0 / 13.0, Measurements.TarwidCoefficient([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsARecordWithNoOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.TarwidCoefficient([0.0, 0.0], [0.0, 1.0]));
}
