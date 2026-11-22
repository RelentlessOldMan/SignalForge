using Xunit;

namespace SignalForge.Tests;

/// <summary>Alatalo's evenness (ADR 0537).</summary>
public class AlataloEvennessTests
{
    [Fact]
    public void Two() =>
        Assert.Equal(0.6 / ((4.0 / Math.Pow(3.0, 0.75)) - 1.0),
            Measurements.AlataloEvenness([3.0, 1.0]), 12);

    [Fact]
    public void EqualWithAZero() =>
        Assert.Equal(1.0, Measurements.AlataloEvenness([0.0, 2.0, 2.0]), 13);

    [Fact]
    public void RejectsOnePositive() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.AlataloEvenness([0.0, 3.0]));
}
