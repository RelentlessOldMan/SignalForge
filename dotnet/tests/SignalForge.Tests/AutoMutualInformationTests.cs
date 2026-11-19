using Xunit;

namespace SignalForge.Tests;

/// <summary>Auto mutual information (ADR 0352).</summary>
public class AutoMutualInformationTests
{
    [Fact]
    public void AlternatingTwoLevelsByHand()
    {
        double[] x = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0];
        double[] got = Measurements.AutoMutualInformation(x, [0, 1, 7], 2);
        Assert.Equal(Math.Log(2), got[0], 1e-15);
        // Seven pairs at lag 1, each fixing the other level: the entropy of (4/7, 3/7).
        Assert.Equal(-((4.0 / 7 * Math.Log(4.0 / 7)) + (3.0 / 7 * Math.Log(3.0 / 7))), got[1], 1e-15);
        Assert.Equal(0.0, got[2]);
    }

    [Fact]
    public void EveryJointBinOnceIsIndependent() =>
        Assert.Equal(0.0, Measurements.AutoMutualInformation([0.0, 0.0, 1.0, 1.0, 0.0], [1], 2)[0], 1e-15);

    [Fact]
    public void RejectsAConstant() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.AutoMutualInformation([2.0, 2.0, 2.0], [1]));
}
