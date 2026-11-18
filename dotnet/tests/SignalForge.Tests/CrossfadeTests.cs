using Xunit;

namespace SignalForge.Tests;

/// <summary>Crossfade (ADR 0263).</summary>
public class CrossfadeTests
{
    [Fact]
    public void LinearOverlap()
    {
        double[] y = Dsp.Crossfade([1.0, 1.0, 1.0, 1.0], [0.0, 0.0, 0.0, 0.0], 3);
        double[] want = [1.0, 0.75, 0.5, 0.25, 0.0];
        Assert.Equal(want, y);
    }

    [Fact]
    public void RejectsOverlapLongerThanAnInput() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Crossfade([1.0, 2.0], [3.0], 2));
}
