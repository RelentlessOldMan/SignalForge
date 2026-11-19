using Xunit;

namespace SignalForge.Tests;

/// <summary>The Pearson chi-square divergence (ADR 0412).</summary>
public class ChiSquareDivergenceTests
{
    [Fact]
    public void Reverse() =>
        Assert.Equal(1.0 / 3.0, Measurements.ChiSquareDivergence([1.0, 1.0], [3.0, 1.0]), 1e-15);

    [Fact]
    public void RejectsAZeroQUnderAPositiveP() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ChiSquareDivergence([1.0, 1.0], [1.0, 0.0]));
}
