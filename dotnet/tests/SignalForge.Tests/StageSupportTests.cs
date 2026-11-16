using Xunit;

namespace SignalForge.Tests;

/// <summary>Stage support (conventions: Stage support; ADR 0179).</summary>
public class StageSupportTests
{
    [Fact]
    public void AReflectionAtMinusTwentyDecibelsGivesMinusTwenty()
    {
        var ir = new double[48000];
        ir[0] = 1;
        ir[2400] = 0.1;
        Assert.Equal(-20, Measurements.StageSupport(ir, 48000), 1e-12);
        Assert.Equal(double.NegativeInfinity, Measurements.StageSupport(ir, 48000, late: true));
    }
}
