using Xunit;

namespace SignalForge.Tests;

/// <summary>Cross-spectral density (conventions: Cross-spectral density; ADR 0194).</summary>
public class CrossSpectralDensityTests
{
    [Fact]
    public void SameSignalIsTheWelchPsd()
    {
        var rng = new Random(41);
        var x = new double[1000];
        for (int n = 0; n < x.Length; n++)
            x[n] = rng.NextDouble() - 0.5;
        var p = Spectral.CrossSpectralDensity(x, x, 50, nperseg: 128, detrend: Detrend.Linear);
        var w = Spectral.WelchPsd(x, 50, nperseg: 128, detrend: Detrend.Linear);
        for (int k = 0; k < w.Psd.Length; k++)
        {
            Assert.Equal(w.Psd[k], p.Csd[k].Real, 1e-12);
            Assert.Equal(0, p.Csd[k].Imaginary, 1e-12);
        }
    }

    [Fact]
    public void ComplexSameSignalIsTheComplexWelchPsd()
    {
        var rng = new Random(44);
        var x = new System.Numerics.Complex[600];
        for (int n = 0; n < x.Length; n++)
            x[n] = new System.Numerics.Complex(rng.NextDouble() - 0.5, rng.NextDouble() - 0.5);
        var p = Spectral.CrossSpectralDensity(x, x, 10, nperseg: 64);
        var w = Spectral.WelchPsd(x, 10, nperseg: 64);
        for (int k = 0; k < w.Psd.Length; k++)
        {
            Assert.Equal(w.Psd[k], p.Csd[k].Real, 1e-12);
            Assert.Equal(w.Frequencies[k], p.Frequencies[k]);
        }
    }
}
