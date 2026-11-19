using Xunit;

namespace SignalForge.Tests;

/// <summary>Runs test (ADR 0361).</summary>
public class RunsTestTests
{
    [Fact]
    public void ByHand()
    {
        // + + − − + −: four runs, the mean of four for n1 = n2 = 3.
        var got = Measurements.RunsTest([1.0, 2.0, -1.0, -2.0, 3.0, -3.0]);
        Assert.Equal(4, got.Runs);
        Assert.Equal(0.0, got.Z);
    }

    [Fact]
    public void SamplesAtTheMeanAreDropped()
    {
        // + − + −: four runs; n = 4, μ = 3, σ² = 2/3.
        var got = Measurements.RunsTest([0.0, 1.0, -1.0, 0.0, 1.0, -1.0, 0.0]);
        Assert.Equal(4, got.Runs);
        Assert.Equal(1 / Math.Sqrt(2.0 / 3), got.Z, 1e-15);
    }

    [Fact]
    public void RejectsAConstantRecord() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.RunsTest([1.0, 1.0, 1.0]));
}
