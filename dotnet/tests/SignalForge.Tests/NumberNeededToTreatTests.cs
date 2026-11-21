using Xunit;

namespace SignalForge.Tests;

/// <summary>The number needed to treat (ADR 0504).</summary>
public class NumberNeededToTreatTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(5.0 / 3.0, Measurements.NumberNeededToTreat([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsANumberNeededToTreatOfZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.NumberNeededToTreat([1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0]));
}
