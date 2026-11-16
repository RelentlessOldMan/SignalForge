using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Noise power ratio (conventions: Spectra, Noise power ratio; ADR 0118).</summary>
public class NoisePowerRatioTests
{
    private const int N = 1024, Lo = 100, Hi = 300, NotchLo = 195, NotchHi = 205;
    private static readonly (double, double) Band = (Lo - 0.5, Hi + 0.5), Notch = (NotchLo - 0.5, NotchHi + 0.5);

    private static readonly double[] Drives = [1e-3, 1e-2];

    private static bool InNotch(int k) => k >= NotchLo && k <= NotchHi;

    /// <summary>Bins Lo..Hi except the notch, Newman phases (written out here), unit cosines; the
    /// samples and the two-sided line coefficients on bins −Hi..Hi.</summary>
    private static (double[] X, Complex[] C) NotchedMultitone()
    {
        int[] ks = [.. Enumerable.Range(Lo, Hi - Lo + 1).Where(k => !InNotch(k))];
        double[] phases = [.. Enumerable.Range(0, ks.Length).Select(i => Math.PI * i * i / ks.Length)];
        var c = new Complex[2 * Hi + 1];
        var x = new double[N];
        for (int i = 0; i < ks.Length; i++)
        {
            c[ks[i] + Hi] = Complex.FromPolarCoordinates(0.5, phases[i]);
            c[-ks[i] + Hi] = Complex.FromPolarCoordinates(0.5, -phases[i]);
            for (int n = 0; n < N; n++)
                x[n] += Math.Cos(2 * Math.PI * ks[i] * n / N + phases[i]);
        }
        return (x, c);
    }

    private static Complex[] Convolve(Complex[] a, Complex[] b)
    {
        var r = new Complex[a.Length + b.Length - 1];
        for (int i = 0; i < a.Length; i++)
            for (int j = 0; j < b.Length; j++)
                r[i + j] += a[i] * b[j];
        return r;
    }

    /// <summary>One-sided power per bin of y = x + a3 x³: the cube is the coefficients convolved
    /// three times (no FFT), folded mod N, then 2|c|² per bin above DC.</summary>
    private static double[] LinePowers(Complex[] c, double a3)
    {
        Complex[] c3 = Convolve(Convolve(c, c), c);
        var two = new Complex[N];
        for (int i = 0; i < c3.Length; i++)
            two[(((i - 3 * Hi) % N) + N) % N] += a3 * c3[i];
        for (int i = 0; i < c.Length; i++)
            two[(((i - Hi) % N) + N) % N] += c[i];
        double[] p = [.. two.Take(N / 2 + 1).Select(v => 2 * v.Magnitude * v.Magnitude)];
        p[0] /= 2;
        p[N / 2] /= 2;
        return p;
    }

    private static NoisePowerRatio Npr(double[] y)
    {
        SpectralDensity d = Spectral.WelchPsd(y, N, window: WindowType.Rectangular);
        return Spectral.NoisePowerRatio(d.Frequencies, d.Psd, Band, Notch, (0, N / 2.0));
    }

    [Theory]
    [InlineData(0.002)]
    [InlineData(-0.01)]
    public void ACubicFillsTheNotchAsItsExpansionSays(double a3)
    {
        var (x, c) = NotchedMultitone();
        NoisePowerRatio r = Npr([.. x.Select(v => v + a3 * v * v * v)]);
        double[] p = LinePowers(c, a3);
        double loaded = Enumerable.Range(Lo, Hi - Lo + 1).Where(k => !InNotch(k)).Average(k => p[k]);
        double inside = Enumerable.Range(NotchLo, NotchHi - NotchLo + 1).Average(k => p[k]);
        Assert.Equal(10 * Math.Log10(loaded / inside), r.NprDb, 1e-8);
        Assert.Equal(loaded, r.LoadedDensity, loaded * 1e-12);
    }

    [Fact]
    public void ALinearLoadLeavesTheNotchEmpty()
    {
        NoisePowerRatio r = Npr(NotchedMultitone().X);
        Assert.True(r.NprDb > 200); // rounding only
        Assert.Equal(0.5, r.LoadedDensity, 1e-12); // each cosine's 1/2 over 1 Hz
    }

    [Fact]
    public void NprFalls2DbPerDbOfDrive()
    {
        // third-order distortion: notch density goes as drive^6, the load as drive^2
        double[] x = NotchedMultitone().X;
        double[] got = [.. Drives.Select(a => Npr([.. x.Select(v => a * v + 0.01 * Math.Pow(a * v, 3))]).NprDb)];
        Assert.Equal(40, got[0] - got[1], 1e-2); // the load grows a little too
    }

    [Theory]
    [InlineData(0, 10, 10, 11)]
    [InlineData(0, 10, 5, 4)]
    [InlineData(0, 10, -1, 3)]
    [InlineData(0, 600, 5, 6)]
    [InlineData(double.NaN, 10, 5, 6)]
    public void BadEdges(double bLo, double bHi, double nLo, double nHi)
    {
        double[] f = [.. Enumerable.Range(0, 513).Select(k => (double)k)];
        double[] p = [.. f.Select(_ => 1.0)];
        Assert.ThrowsAny<ArgumentException>(() => Spectral.NoisePowerRatio(f, p, (bLo, bHi), (nLo, nHi)));
    }
}
