using Xunit;

namespace SignalForge.Tests;

/// <summary>Whittaker's beta of two records (ADR 0575).</summary>
public class WhittakerBetaTests
{
    [Fact]
    public void Nested() =>
        Assert.Equal(0.5, Measurements.WhittakerBeta([1.0, 0.0, 0.0], [1.0, 1.0, 1.0]));

    [Fact]
    public void Disjoint() =>
        Assert.Equal(1.0, Measurements.WhittakerBeta([1.0, 0.0], [0.0, 1.0]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.WhittakerBeta([0.0, 0.0], [1.0, 2.0]));
}
