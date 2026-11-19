using Xunit;

namespace SignalForge.Tests;

/// <summary>Mann–Kendall trend test (ADR 0364).</summary>
public class MannKendallTests
{
    [Fact]
    public void RisingByHand()
    {
        var got = Measurements.MannKendall([1.0, 2.0, 3.0, 4.0]);
        Assert.Equal(6, got.S);
        Assert.Equal(5 / Math.Sqrt(26.0 / 3), got.Z, 1e-15);
    }

    [Fact]
    public void TiesByHand()
    {
        var got = Measurements.MannKendall([1.0, 1.0, 2.0, 0.0]);
        Assert.Equal(-1, got.S);
        Assert.Equal(0.0, got.Z);
    }

    [Fact]
    public void RejectsAConstantRecord() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.MannKendall([1.0, 1.0]));
}
