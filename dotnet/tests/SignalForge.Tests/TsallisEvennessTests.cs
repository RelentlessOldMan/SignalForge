using Xunit;

namespace SignalForge.Tests;

/// <summary>Tsallis evenness (ADR 0569).</summary>
public class TsallisEvennessTests
{
    [Fact]
    public void Simpson() =>
        Assert.Equal(15.0 / 16.0, Measurements.TsallisEvenness([1.0, 1.0, 2.0], 2.0), 14);

    [Fact]
    public void ZeroOrderIsOne() =>
        Assert.Equal(1.0, Measurements.TsallisEvenness([0.0, 2.0, 5.0], 0.0), 14);

    [Fact]
    public void RejectsOneKind() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.TsallisEvenness([0.0, 4.0], 1.0));
}
