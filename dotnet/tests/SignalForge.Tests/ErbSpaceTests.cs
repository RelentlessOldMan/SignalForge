using Xunit;

namespace SignalForge.Tests;

/// <summary>ERB-spaced frequencies (conventions: ERB-spaced frequencies; ADR 0162).</summary>
public class ErbSpaceTests
{
    [Fact]
    public void AscendingWithExactEndpointsAndEqualErbSteps()
    {
        double[] f = Units.ErbSpace(80, 7600, 40);
        Assert.Equal(80.0, f[0]);
        Assert.Equal(7600.0, f[^1]);
        double step = (Units.HzToErbRate(7600) - Units.HzToErbRate(80)) / 39;
        for (int i = 1; i < f.Length; i++)
            Assert.Equal(step, Units.HzToErbRate(f[i]) - Units.HzToErbRate(f[i - 1]), 1e-10);
    }
}
