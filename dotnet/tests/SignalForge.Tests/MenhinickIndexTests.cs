using Xunit;

namespace SignalForge.Tests;

/// <summary>Menhinick's index (ADR 0541).</summary>
public class MenhinickIndexTests
{
    [Fact]
    public void OneZero() =>
        Assert.Equal(3.0 / Math.Sqrt(6.0), Measurements.MenhinickIndex([0.0, 2.0, 2.0, 2.0]), 14);

    [Fact]
    public void Ones() =>
        Assert.Equal(3.0, Measurements.MenhinickIndex([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]), 14);

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.MenhinickIndex([0.0, 0.0]));
}
