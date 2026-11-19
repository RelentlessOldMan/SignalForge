using Xunit;

namespace SignalForge.Tests;

/// <summary>Chatterjee's xi (ADR 0376).</summary>
public class ChatterjeeXiTests
{
    [Fact]
    public void MonotoneFive() =>
        Assert.Equal(0.5, Measurements.ChatterjeeXi([1.0, 2.0, 3.0, 4.0, 5.0], [1.0, 2.0, 3.0, 4.0, 5.0]));

    [Fact]
    public void TiesInXKeepRecordOrder() =>
        Assert.Equal(-0.2, Measurements.ChatterjeeXi([1.0, 0.0, 1.0, 0.0], [0.0, 1.0, 3.0, 2.0]), 1e-15);

    [Fact]
    public void RejectsAConstantY() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ChatterjeeXi([1.0, 2.0, 3.0], [1.0, 1.0, 1.0]));
}
