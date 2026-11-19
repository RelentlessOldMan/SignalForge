using Xunit;

namespace SignalForge.Tests;

/// <summary>Pettitt change-point test (ADR 0366).</summary>
public class PettittTests
{
    [Fact]
    public void StepByHand()
    {
        // U = 2, 4, 2: K = 4 at index 1; p = 2 exp(−96/80).
        var got = Measurements.Pettitt([0.0, 0.0, 1.0, 1.0]);
        Assert.Equal(4, got.Statistic);
        Assert.Equal(1, got.Index);
        Assert.Equal(2 * Math.Exp(-1.2), got.PValue, 1e-15);
    }

    [Fact]
    public void AConstantRecordHasPOne() =>
        Assert.Equal(1.0, Measurements.Pettitt([3.0, 3.0, 3.0]).PValue);

    [Fact]
    public void RejectsOneSample() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.Pettitt([1.0]));
}
