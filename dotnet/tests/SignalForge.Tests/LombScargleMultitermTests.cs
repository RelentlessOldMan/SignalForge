using Xunit;

namespace SignalForge.Tests;

/// <summary>Multiterm Lomb-Scargle against the generalized form, square waves and exact fits
/// (conventions: Spectra, Multiterm Lomb-Scargle; ADR 0103).</summary>
public class LombScargleMultitermTests
{
    private static readonly double[] T, Y, Sigma, F;

    static LombScargleMultitermTests()
    {
        var rng = new Random(103);
        T = [.. Enumerable.Range(0, 60).Select(_ => 30 * rng.NextDouble()).Order()];
        Y = [.. T.Select(_ => Gauss(rng))];
        Sigma = [.. T.Select(_ => 0.5 + 1.5 * rng.NextDouble())];
        F = [.. Enumerable.Range(0, 80).Select(k => 0.02 + k * (1.48 / 79))];
    }

    private static double Gauss(Random rng) =>
        Math.Sqrt(-2 * Math.Log(1 - rng.NextDouble())) * Math.Cos(2 * Math.PI * rng.NextDouble());

    [Theory]
    [InlineData(false, LombScargleNormalization.Standard)]
    [InlineData(true, LombScargleNormalization.Standard)]
    [InlineData(false, LombScargleNormalization.Power)]
    [InlineData(true, LombScargleNormalization.Power)]
    public void OneTermIsTheGeneralizedForm(bool weighted, LombScargleNormalization normalization)
    {
        double[]? sigma = weighted ? Sigma : null;
        double[] want = Spectral.GeneralizedLombScargle(T, Y, F, sigma, normalization);
        double[] got = Spectral.LombScargleMultiterm(T, Y, F, 1, sigma, normalization);
        for (int k = 0; k < F.Length; k++)
            Assert.True(Math.Abs(got[k] - want[k]) <= 1e-13 + 1e-10 * Math.Abs(want[k]), $"f {F[k]}");
    }

    [Theory]
    [InlineData(1, false)]
    [InlineData(2, false)]
    [InlineData(3, true)]
    [InlineData(4, true)]
    [InlineData(6, true)]
    public void SquareWaveByHand(int terms, bool all)
    {
        double[] t = [0, 1, 2, 3, 4, 5, 6, 7], y = [1, 1, 1, 1, -1, -1, -1, -1];
        double want = all ? 1 : (1 + Math.Sqrt(2) / 2) / 2;
        Assert.Equal(want, Spectral.LombScargleMultiterm(t, y, [0.125], terms)[0], 1e-14);
    }

    [Fact]
    public void MoreTermsExplainMore()
    {
        var previous = new double[F.Length];
        for (int terms = 1; terms <= 5; terms++)
        {
            double[] got = Spectral.LombScargleMultiterm(T, Y, F, terms, Sigma);
            for (int k = 0; k < F.Length; k++)
            {
                Assert.True(got[k] >= previous[k] - 1e-12 && got[k] >= 0 && got[k] <= 1 + 1e-12, $"terms {terms} f {F[k]}");
                previous[k] = got[k];
            }
        }
    }

    [Fact]
    public void HarmonicSignalFitsExactlyAtItsFrequency()
    {
        const double f0 = 0.23;
        double[] y = [.. T.Select(t => 1.5 + Math.Cos(2 * Math.PI * f0 * t) + 0.6 * Math.Sin(6 * Math.PI * f0 * t - 0.4))];
        double[] got = Spectral.LombScargleMultiterm(T, y, [f0, 1.3 * f0], 3);
        Assert.Equal(1.0, got[0], 1e-12);
        Assert.True(got[1] < 0.9);
        Assert.True(Spectral.LombScargleMultiterm(T, y, [f0], 2)[0] < 0.9);
    }

    [Fact]
    public void ShiftingEveryTimeChangesNothing()
    {
        double[] a = Spectral.LombScargleMultiterm(T, Y, F, 3, Sigma);
        double[] b = Spectral.LombScargleMultiterm([.. T.Select(t => t + 12.5)], Y, F, 3, Sigma);
        for (int k = 0; k < F.Length; k++)
            Assert.True(Math.Abs(a[k] - b[k]) <= 1e-11 + 1e-9 * Math.Abs(a[k]), $"f {F[k]}");
    }

    [Fact]
    public void PowerIsHalfTheWeightedDrop()
    {
        double[] std = Spectral.LombScargleMultiterm(T, Y, F, 2, Sigma);
        double[] power = Spectral.LombScargleMultiterm(T, Y, F, 2, Sigma, LombScargleNormalization.Power);
        double[] w = [.. Sigma.Select(s => 1 / (s * s))];
        double mean = w.Zip(Y, (a, b) => a * b).Sum() / w.Sum();
        double chi0 = w.Zip(Y, (a, b) => a * (b - mean) * (b - mean)).Sum();
        for (int k = 0; k < F.Length; k++)
            Assert.True(Math.Abs(power[k] - std[k] * chi0 / 2) <= 1e-12 * Math.Abs(power[k]) + 1e-14, $"f {F[k]}");
    }

    [Fact]
    public void BadArguments()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => Spectral.LombScargleMultiterm(T, Y, F, 0));
        Assert.Throws<ArgumentException>(() => Spectral.LombScargleMultiterm(T, [.. T.Select(_ => 1.0)], F, 2));
        Assert.Throws<ArgumentException>(() => Spectral.LombScargleMultiterm(T, Y, [0.0], 2));
        Assert.Throws<ArgumentException>(() => Spectral.LombScargleMultiterm(T, Y, [double.NaN], 2));
        Assert.Throws<ArgumentException>(() => Spectral.LombScargleMultiterm(T.AsSpan(0, 5), Y, F, 2));
        Assert.Throws<ArgumentException>(() => Spectral.LombScargleMultiterm(T, Y, F, 2, [.. Sigma.Select(s => -s)]));
        Assert.Throws<ArgumentException>(() => Spectral.LombScargleMultiterm(T, Y, F, 2, Sigma[..3]));
        Assert.Throws<ArgumentException>(() => Spectral.LombScargleMultiterm(T, Y, F, 2, null, (LombScargleNormalization)(-1)));
        Assert.Empty(Spectral.LombScargleMultiterm(T, Y, [], 2));
    }
}
