using Xunit;

namespace SignalForge.Tests;

/// <summary>Transient shaper (ADR 0281).</summary>
public class TransientShaperTests
{
    [Fact]
    public void OnsetIsRaised()
    {
        // Step to 1: fast envelope 1/2, slow 1/4 at the first sample, so the gain is 2.
        double[] y = Dsp.TransientShaper([0.0, 1.0], 0.5, 0.75, 1.0);
        Assert.Equal([0.0, 2.0], y);
    }

    [Fact]
    public void RejectsNonFiniteAmount() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.TransientShaper([1.0], 0.5, 0.75, double.NaN));
}
