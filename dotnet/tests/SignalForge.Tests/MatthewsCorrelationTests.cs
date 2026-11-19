using Xunit;

namespace SignalForge.Tests;

/// <summary>The Matthews correlation coefficient (ADR 0385).</summary>
public class MatthewsCorrelationTests
{
    [Fact]
    public void OneMiss() =>
        Assert.Equal(1 / Math.Sqrt(3), Measurements.MatthewsCorrelation([1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]), 1e-15);

    [Fact]
    public void RejectsAMissingClass() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.MatthewsCorrelation([1.0, 0.0], [1.0, 1.0]));
}
