using Xunit;

namespace SignalForge.Tests;

/// <summary>Allan deviation (ADR 0327).</summary>
public class AllanDeviationTests
{
    [Fact]
    public void AlternatingSamplesByHand()
    {
        AllanDeviation a = Measurements.AllanDeviation([1.0, -1.0, 1.0, -1.0], 2, [1, 2]);
        Assert.Equal([2.0, 4.0], a.Taus);
        Assert.Equal(Math.Sqrt(2), a.Deviations[0], 1e-15);
        Assert.Equal(0.0, a.Deviations[1]);
    }

    [Fact]
    public void DriftGivesDTauOverRootTwo()
    {
        double[] y = new double[300];
        for (int i = 0; i < y.Length; i++)
            y[i] = 2e-8 * 0.5 * i;
        AllanDeviation a = Measurements.AllanDeviation(y, 0.5, [3, 150]);
        for (int k = 0; k < 2; k++)
            Assert.Equal(2e-8 * a.Taus[k] / Math.Sqrt(2), a.Deviations[k], 1e-15);
    }

    [Fact]
    public void RejectsAFactorAboveHalf() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.AllanDeviation([0.0, 1.0, 2.0], 1, [2]));
}
