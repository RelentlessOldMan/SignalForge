using Xunit;

namespace SignalForge.Tests;

/// <summary>The Kullback–Leibler divergence (ADR 0407).</summary>
public class KlDivergenceTests
{
    [Fact]
    public void Half() =>
        Assert.Equal(Math.Log(2.0), Measurements.KlDivergence([1.0, 0.0], [1.0, 1.0]), 1e-15);

    [Fact]
    public void RejectsAZeroQUnderAPositiveP() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.KlDivergence([1.0, 1.0], [1.0, 0.0]));
}
