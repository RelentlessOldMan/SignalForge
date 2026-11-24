using Xunit;

namespace SignalForge.Tests;

/// <summary>Magurran's beta of two presence records (ADR 0592).</summary>
public class MagurranBetaTests
{
    [Fact]
    public void Nested() =>
        Assert.Equal(8.0 / 3.0, Measurements.MagurranBeta([1.0, 0.0, 0.0], [1.0, 1.0, 1.0]), 14);

    [Fact]
    public void Uneven() =>
        Assert.Equal(35.0 / 6.0, Measurements.MagurranBeta([1.0, 1.0, 0.0, 1.0, 1.0, 1.0], [1.0, 0.0, 1.0, 0.0, 0.0, 0.0]), 14);

    [Fact]
    public void Disjoint() =>
        Assert.Equal(2.0, Measurements.MagurranBeta([1.0, 0.0], [0.0, 1.0]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.MagurranBeta([0.0, 0.0], [1.0, 2.0]));
}
