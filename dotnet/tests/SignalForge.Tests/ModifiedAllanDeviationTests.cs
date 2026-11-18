using Xunit;

namespace SignalForge.Tests;

/// <summary>Modified Allan deviation (ADR 0328).</summary>
public class ModifiedAllanDeviationTests
{
    [Fact]
    public void OneIsTheAllanDeviation()
    {
        double[] y = [0.3, -1.2, 2.0, 0.7, -0.4, 1.1, 0.0];
        Assert.Equal(Measurements.AllanDeviation(y, 1, [1]).Deviations[0],
            Measurements.ModifiedAllanDeviation(y, 1, [1]).Deviations[0], 1e-15);
    }

    [Fact]
    public void DriftGivesDTauOverRootTwo()
    {
        double[] y = new double[300];
        for (int i = 0; i < y.Length; i++)
            y[i] = 2e-8 * 0.5 * i;
        AllanDeviation a = Measurements.ModifiedAllanDeviation(y, 0.5, [3, 100]);
        for (int k = 0; k < 2; k++)
            Assert.Equal(2e-8 * a.Taus[k] / Math.Sqrt(2), a.Deviations[k], 1e-15);
    }

    [Fact]
    public void RejectsTooLargeAFactor() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ModifiedAllanDeviation([0.0, 1.0, 2.0, 3.0], 1, [2]));
}
