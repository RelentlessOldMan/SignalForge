using Xunit;

namespace SignalForge.Tests;

/// <summary>Line spectral frequencies (conventions: Line spectral frequencies; ADR 0208).</summary>
public class LineSpectralFrequenciesTests
{
    [Fact]
    public void BurgFitsGiveInterlacedFrequencies()
    {
        var rng = new Random(59);
        var x = new double[400];
        for (int i = 0; i < x.Length; i++)
            x[i] = rng.NextDouble() - 0.5;
        var w = Dsp.LineSpectralFrequencies(Dsp.Burg(x, 10).Coefficients);
        Assert.Equal(10, w.Length);
        for (int i = 1; i < w.Length; i++)
            Assert.True(w[i] > w[i - 1]);
        Assert.True(w[0] > 0 && w[^1] < Math.PI);
    }
}
