using Xunit;

namespace SignalForge.Tests;

/// <summary>AR model PSD (ADR 0223).</summary>
public class ArPsdTests
{
    [Fact]
    public void MatchesBurgPsdOfTheSameModel()
    {
        var rng = new Random(5);
        double[] x = [.. Enumerable.Range(0, 300).Select(_ => rng.NextDouble() - 0.5)];
        var fit = Dsp.Burg(x, 4);
        var burg = Spectral.BurgPsd(x, 8.0, 4, nfft: 64);
        var model = Spectral.ArPsd(fit.Coefficients, fit.Error, 8.0, 64);
        for (int k = 0; k < burg.Psd.Length; k++)
            Assert.Equal(burg.Psd[k], model.Psd[k], burg.Psd[k] * 1e-12);
    }
}
