using Xunit;

namespace SignalForge.Tests;

/// <summary>Hadamard deviation (ADR 0329).</summary>
public class HadamardDeviationTests
{
    [Fact]
    public void AlternatingSamplesByHand()
    {
        AllanDeviation h = Measurements.HadamardDeviation([1.0, -1.0, 1.0, -1.0, 1.0, -1.0], 0.5, [1, 2]);
        Assert.Equal([0.5, 1.0], h.Taus);
        Assert.Equal(Math.Sqrt(16.0 / 6), h.Deviations[0], 1e-15);
        Assert.Equal(0.0, h.Deviations[1]);
    }

    [Fact]
    public void DriftCancels()
    {
        double[] y = new double[90];
        for (int i = 0; i < y.Length; i++)
            y[i] = 0.25 + (i / 1024.0);
        Assert.All(Measurements.HadamardDeviation(y, 1, [1, 7, 30]).Deviations, d => Assert.Equal(0.0, d, 1e-15));
    }

    [Fact]
    public void RejectsTooLargeAFactor() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HadamardDeviation([0.0, 1.0, 2.0, 3.0, 4.0], 1, [2]));
}
