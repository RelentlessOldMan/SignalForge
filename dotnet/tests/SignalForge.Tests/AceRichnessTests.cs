using Xunit;

namespace SignalForge.Tests;

/// <summary>The ACE richness (ADR 0551).</summary>
public class AceRichnessTests
{
    [Fact]
    public void Mixed() =>
        Assert.Equal(509.0 / 75.0, Measurements.AceRichness([1.0, 1.0, 2.0, 3.0, 20.0]), 13);

    [Fact]
    public void AbundantOnly() =>
        Assert.Equal(2.0, Measurements.AceRichness([20.0, 15.0]), 15);

    [Fact]
    public void RejectsAllSingletons() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.AceRichness([30.0, 1.0]));
}
