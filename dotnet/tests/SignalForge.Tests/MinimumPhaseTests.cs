using Xunit;

namespace SignalForge.Tests;

/// <summary>Minimum phase from the cepstrum (conventions: Minimum phase; ADR 0153).</summary>
public class MinimumPhaseTests
{
    // Zeros 0.5, −2, ±1.6j, 0.7 ± 0.3j: radii 0.5 to 2, none near the unit circle.
    private static readonly double[] X = [1.0, 0.1, 0.04, 2.526, -7.0312, 5.8112, -1.4848];

    [Fact]
    public void MagnitudeIsKept()
    {
        double[] y = Spectral.MinimumPhase(X, 1024);
        var padded = new double[1024];
        X.CopyTo(padded, 0);
        var a = Spectral.Fft(y);
        var b = Spectral.Fft(padded);
        for (int k = 0; k < 1024; k++)
            Assert.Equal(b[k].Magnitude, a[k].Magnitude, 1e-10);
    }

    [Fact]
    public void PartialEnergiesAreAtLeastTheInputs()
    {
        double[] y = Spectral.MinimumPhase(X, 1024);
        double ey = 0, ex = 0;
        for (int n = 0; n < X.Length; n++)
        {
            ey += y[n] * y[n];
            ex += X[n] * X[n];
            Assert.True(ey >= ex - 1e-10, $"n = {n}");
        }
        for (int n = X.Length; n < y.Length; n++)
            Assert.True(Math.Abs(y[n]) < 1e-10);
    }
}
