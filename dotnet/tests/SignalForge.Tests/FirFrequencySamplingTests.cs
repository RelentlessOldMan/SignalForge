using Xunit;

namespace SignalForge.Tests;

/// <summary>Frequency-sampling FIR design (conventions: FIR filters, Frequency-sampling design; ADR 0084).</summary>
public sealed class FirFrequencySamplingTests
{
    private static double Amplitude(double[] h, double nu) =>
        h.Select((v, n) => v * Math.Cos(2 * Math.PI * nu * (n - ((h.Length - 1) / 2.0)))).Sum();

    private static double Interp(double nu, double[] f, double[] g)
    {
        int i = 0;
        while (i < f.Length - 2 && f[i + 1] < nu)
            i++;
        return g[i] + ((g[i + 1] - g[i]) * (nu - f[i]) / (f[i + 1] - f[i]));
    }

    [Fact]
    public void HitsTheSamplesWhenTheGridMatchesTheLength()
    {
        double[] f = [0, 0.1, 0.3, 0.5], g = [0.5, 1.5, 0.2, 0.0];
        double[] h = Dsp.FirFrequencySampling(24, f, g, 1.0, WindowType.Rectangular, numPoints: 13);
        for (int k = 0; k < 13; k++)
            Assert.True(Math.Abs(Amplitude(h, k / 24.0) - Interp(k / 24.0, f, g)) < 1e-13);
    }

    [Fact]
    public void TapsAreExactlySymmetric()
    {
        foreach (int n in new[] { 31, 32, 255 })
        {
            double[] h = Dsp.FirFrequencySampling(n, [0, 0.13, 0.21, 0.5], [1, 0.7, 0, 0], 1.0, WindowType.Hann);
            Assert.Equal(h, h.Reverse());
        }
    }

    [Fact]
    public void LongDesignApproachesTheTarget()
    {
        double[] h = Dsp.FirFrequencySampling(201, [0, 0.1, 0.15, 0.5], [1, 1, 0, 0], 1.0, WindowType.Kaiser, 8.0);
        for (int i = 0; i < 50; i++)
        {
            Assert.True(Math.Abs(Amplitude(h, 0.08 * i / 49) - 1) < 1e-3);
            Assert.True(Math.Abs(Amplitude(h, 0.17 + (0.33 * i / 49))) < 1e-3);
        }
    }

    [Fact]
    public void LinearInTheGains()
    {
        double[] f = [0, 0.2, 0.3, 0.5], g1 = [1, 1, 0, 0], g2 = [0.2, -0.5, 1, 3];
        double[] both = Dsp.FirFrequencySampling(17, f, [.. g1.Zip(g2, (a, b) => (2.5 * a) + b)], 1.0);
        double[] h1 = Dsp.FirFrequencySampling(17, f, g1, 1.0), h2 = Dsp.FirFrequencySampling(17, f, g2, 1.0);
        for (int i = 0; i < 17; i++)
            Assert.True(Math.Abs(both[i] - ((2.5 * h1[i]) + h2[i])) < 1e-14);
    }

    [Fact]
    public void Rejects()
    {
        double[] f = [0, 0.2, 0.3, 0.5], g = [1, 1, 0, 0];
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirFrequencySampling(0, f, g, 1.0));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirFrequencySampling(11, [0, 0.2, 0.2, 0.5], g, 1.0));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirFrequencySampling(11, [0, 0.2, 0.3, 0.4], g, 1.0));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirFrequencySampling(11, f, [1, 1, 0], 1.0));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirFrequencySampling(10, f, [0, 0, 1, 1], 1.0));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirFrequencySampling(11, f, g, 1.0, numPoints: 5));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirFrequencySampling(11, f, g, 1.0, numPoints: 1));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirFrequencySampling(11, f, g, 1.0, beta: 3.0));
    }

    // A(ν) with H = −j·e^(−j2πνc)·A: A = Σ h[n]·sin(2πνt), t = n − c.
    private static double AntiAmplitude(double[] h, double nu) =>
        h.Select((v, n) => v * Math.Sin(2 * Math.PI * nu * (n - ((h.Length - 1) / 2.0)))).Sum();

    [Fact]
    public void HilbertTurnsCosIntoSin()
    {
        double[] h = Dsp.FirFrequencySampling(101, [0, 0.05, 0.45, 0.5], [0, 1, 1, 0], 1.0, WindowType.Kaiser, 8.0,
            kind: FirKind.Hilbert);
        double[] x = [.. Enumerable.Range(0, 400).Select(n => Math.Cos(2 * Math.PI * 0.2 * n))];
        double[] y = Dsp.Convolve(x, h);
        for (int n = 100; n < 400; n++)
            Assert.True(Math.Abs(y[n] - Math.Sin(2 * Math.PI * 0.2 * (n - 50))) < 1e-3);
    }

    [Fact]
    public void DifferentiatorFollowsTheSlope()
    {
        foreach (int n in new[] { 61, 60 })
        {
            double[] h = Dsp.FirFrequencySampling(n, [0, 0.4, 0.5], [1, 1, 0], 1.0, WindowType.Kaiser, 8.0,
                kind: FirKind.Differentiator);
            for (int i = 0; i < 30; i++)
            {
                double nu = 0.01 + (0.29 * i / 29);
                Assert.True(Math.Abs(AntiAmplitude(h, nu) + (2 * Math.PI * nu)) < 2e-3);
            }
        }
    }

    [Fact]
    public void AntisymmetricTapsAreExact()
    {
        foreach (int n in new[] { 31, 32 })
        {
            double[] h = Dsp.FirFrequencySampling(n, [0, 0.1, 0.5], [0, 1, 0], 1.0, kind: FirKind.Hilbert);
            Assert.Equal(h, h.Reverse().Select(v => -v));
            if (n % 2 == 1)
                Assert.Equal(0.0, h[n / 2]);
        }
    }

    [Fact]
    public void RejectsUnmeetableAntisymmetricTargets()
    {
        double[] f = [0, 0.2, 0.5];
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirFrequencySampling(11, f, [0, 1, 0], 1.0, kind: (FirKind)7));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirFrequencySampling(1, f, [0, 1, 0], 1.0, kind: FirKind.Hilbert));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirFrequencySampling(12, f, [1, 1, 1], 1.0, kind: FirKind.Hilbert));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirFrequencySampling(11, f, [0, 1, 1], 1.0, kind: FirKind.Hilbert));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirFrequencySampling(11, f, [1, 1, 1], 1.0, kind: FirKind.Differentiator));
    }
}
