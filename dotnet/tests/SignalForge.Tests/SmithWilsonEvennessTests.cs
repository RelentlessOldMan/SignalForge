using Xunit;

namespace SignalForge.Tests;

/// <summary>The Smith-Wilson evenness (ADR 0534).</summary>
public class SmithWilsonEvennessTests
{
    [Fact]
    public void VarianceOne() =>
        Assert.Equal(0.5, Measurements.SmithWilsonEvenness([1.0, Math.Exp(2.0)]), 14);

    [Fact]
    public void Equal() =>
        Assert.Equal(1.0, Measurements.SmithWilsonEvenness([2.0, 2.0, 2.0, 2.0]), 15);

    [Fact]
    public void RejectsAZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.SmithWilsonEvenness([1.0, 0.0]));
}
