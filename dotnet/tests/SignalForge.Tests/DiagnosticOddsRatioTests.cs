using Xunit;

namespace SignalForge.Tests;

/// <summary>The diagnostic odds ratio (ADR 0390).</summary>
public class DiagnosticOddsRatioTests
{
    [Fact]
    public void Thirds() =>
        Assert.Equal(2.0 / 9, Measurements.DiagnosticOddsRatio([1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0]), 1e-15);

    [Fact]
    public void RejectsNoFalseNegative() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.DiagnosticOddsRatio([1.0, 0.0, 0.0], [1.0, 1.0, 0.0]));
}
