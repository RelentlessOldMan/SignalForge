using Xunit;

namespace SignalForge.Tests;

/// <summary>Eyraud's coefficient (ADR 0450).</summary>
public class EyraudCoefficientTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(2.4, Measurements.EyraudCoefficient([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 14);

    [Fact]
    public void RejectsAConstantRecord() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.EyraudCoefficient([0.0, 1.0], [1.0, 1.0]));
}
