using Xunit;

namespace SignalForge.Tests;

/// <summary>SVD entropy (ADR 0342).</summary>
public class SvdEntropyTests
{
    [Fact]
    public void OrthogonalRowsGiveOne() =>
        Assert.Equal(1.0, Measurements.SvdEntropy([1.0, 0.0, -1.0, 0.0, 1.0], 2), 1e-15);

    [Fact]
    public void AConstantHasRankOne() =>
        Assert.Equal(0.0, Measurements.SvdEntropy([2.0, 2.0, 2.0, 2.0, 2.0, 2.0], 3), 1e-12);

    [Fact]
    public void ARampByHand()
    {
        // A^T A = [[14, 20], [20, 29]]: λ = (43 ± √1825)/2.
        double big = Math.Sqrt((43 + Math.Sqrt(1825)) / 2), small = Math.Sqrt((43 - Math.Sqrt(1825)) / 2);
        double p = big / (big + small), q = small / (big + small);
        double expected = -(p * Math.Log(p) + q * Math.Log(q)) / Math.Log(2);
        Assert.Equal(expected, Measurements.SvdEntropy([1.0, 2.0, 3.0, 4.0], 2), 1e-12);
    }

    [Fact]
    public void RejectsTooShort() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.SvdEntropy([1.0, 2.0, 3.0, 4.0], 3));
}
