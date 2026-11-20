using Xunit;

namespace SignalForge.Tests;

/// <summary>The Kulczynski coefficient (ADR 0428).</summary>
public class KulczynskiCoefficientTests
{
    [Fact]
    public void Subset() =>
        Assert.Equal(2.0 / 3.0, Measurements.KulczynskiCoefficient([1.0, 1.0, 1.0, 0.0], [0.0, 1.0, 0.0, 0.0]), 15);

    [Fact]
    public void RejectsARecordWithNoOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.KulczynskiCoefficient([1.0, 0.0], [0.0, 0.0]));
}
