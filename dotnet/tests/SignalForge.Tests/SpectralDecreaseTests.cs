using Xunit;

namespace SignalForge.Tests;

/// <summary>Spectral decrease (conventions: Spectra, Spectral decrease; ADR 0130).</summary>
public class SpectralDecreaseTests
{
    private static readonly double[] Ten = [.. Enumerable.Range(0, 10).Select(k => (double)k)];
    private static readonly double[] P = [3, 1, 3, 2, 5, 0.5, 0, 4, 1, 0.2];

    [Fact]
    public void ScalingThePsdChangesNothing()
    {
        double want = Spectral.SpectralDecrease(Ten, P);
        Assert.Equal(want, Spectral.SpectralDecrease(Ten, [.. P.Select(v => 1e-4 * v)]), 1e-12 * Math.Abs(want));
    }

    [Fact]
    public void StretchingTheAxisChangesNothing()
    {
        double want = Spectral.SpectralDecrease(Ten, P);
        Assert.Equal(want, Spectral.SpectralDecrease([.. Ten.Select(f => 1000 + 37.5 * f)], P), 1e-12 * Math.Abs(want));
    }

    [Fact]
    public void UncutBinsMatchTheLibraryForm()
    {
        double num = 0, den = 0;
        for (int k = 1; k < P.Length; k++)
        {
            num += (P[k] - P[0]) / k;
            den += P[k];
        }
        double want = num / den;
        Assert.Equal(want, Spectral.SpectralDecrease(Ten, P), 1e-12 * Math.Abs(want));
    }
}
