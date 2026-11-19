using Xunit;

namespace SignalForge.Tests;

/// <summary>The log loss (ADR 0392).</summary>
public class LogLossTests
{
    [Fact]
    public void Hand() =>
        Assert.Equal(1.5 * Math.Log(2), Measurements.LogLoss([1.0, 0.0, 1.0, 0.0], [0.25, 0.75, 0.5, 0.5]), 1e-15);

    [Fact]
    public void RejectsACertainWrongForecast() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.LogLoss([1.0, 0.0], [0.5, 1.0]));
}
