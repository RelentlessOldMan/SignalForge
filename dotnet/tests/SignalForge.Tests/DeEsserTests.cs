using Xunit;

namespace SignalForge.Tests;

/// <summary>De-esser (ADR 0286).</summary>
public class DeEsserTests
{
    [Fact]
    public void IsDuckKeyedOnTheUnityBand()
    {
        double[] x = [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6];
        double[] bp = Dsp.Svf(x, 0.2, 3.0, 1.0, SvfOutput.Bandpass);
        double[] key = [.. bp.Select(v => 1 / 3.0 * v)];
        Assert.Equal(Dsp.Duck(x, key, -6.0, 3.0, 0.3, 0.9), Dsp.DeEsser(x, 0.2, 3.0, -6.0, 3.0, 0.3, 0.9, 1.0));
    }

    [Fact]
    public void RejectsZeroQ() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.DeEsser([1.0], 1.0, 0.0, 0.0, 2.0, 0.5, 0.5, 8.0));
}
