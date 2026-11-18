using Xunit;

namespace SignalForge.Tests;

/// <summary>Downward expander (ADR 0258).</summary>
public class ExpandTests
{
    [Fact]
    public void InstantSquareBelowZeroDb()
    {
        double[] y = Dsp.Expand([2.0, 1.0, 0.5, -0.25], 0.0, 2.0, 0.0, 0.0);
        double[] want = [2.0, 1.0, 0.25, -0.0625];
        for (int n = 0; n < want.Length; n++)
            Assert.Equal(want[n], y[n], 1e-12);
    }

    [Fact]
    public void RejectsAttackOfOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Expand([1.0], -10.0, 2.0, 1.0, 0.5));
}
