using Xunit;

namespace SignalForge.Tests;

/// <summary>Spectral irregularity (conventions: Spectra, Spectral irregularity; ADR 0132).</summary>
public class SpectralIrregularityTests
{
    private static readonly double[] Ten = [.. Enumerable.Range(0, 10).Select(k => (double)k)];
    private static readonly double[] P = [3, 1, 3, 2, 5, 0.5, 0, 4, 1, 0.2];

    [Fact]
    public void ScalingThePsdChangesNothing()
    {
        double want = Spectral.SpectralIrregularity(Ten, P);
        Assert.Equal(want, Spectral.SpectralIrregularity(Ten, [.. P.Select(v => 1e-4 * v)]), 1e-12 * want);
    }

    [Fact]
    public void StretchingTheAxisChangesNothing()
    {
        double want = Spectral.SpectralIrregularity(Ten, P);
        Assert.Equal(want, Spectral.SpectralIrregularity([.. Ten.Select(f => 1000 + 37.5 * f)], P), 1e-12 * want);
    }

    [Fact]
    public void ReversingThePsdChangesNothing()
    {
        double want = Spectral.SpectralIrregularity(Ten, P, (0.25, 8.0));
        double got = Spectral.SpectralIrregularity(Ten, [.. P.Reverse()], (1.0, 8.75));
        Assert.Equal(want, got, 1e-12 * want);
    }

    [Fact]
    public void UncutBinsMatchJensensForm()
    {
        double num = 0, den = 0;
        for (int k = 0; k < P.Length; k++)
        {
            den += P[k] * P[k];
            if (k + 1 < P.Length)
                num += (P[k + 1] - P[k]) * (P[k + 1] - P[k]);
        }
        Assert.Equal(num / den, Spectral.SpectralIrregularity(Ten, P), 1e-12 * num / den);
    }
}
