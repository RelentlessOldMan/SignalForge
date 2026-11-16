using Xunit;

namespace SignalForge.Tests;

/// <summary>Real cepstrum (conventions: Real cepstrum; ADR 0151).</summary>
public class RealCepstrumTests
{
    private const int Period = 40;

    [Fact]
    public void PulseTrainPeaksAtItsPeriod()
    {
        // 401 samples: not a whole number of periods, so no bin of the spectrum is 0.
        var x = new double[401];
        for (int n = 0; n < x.Length; n++)
            x[n] = (n % Period) switch { 0 => 1, 1 => 0.6, 2 => 0.2, _ => 0 };
        double[] c = Spectral.RealCepstrum(x);
        int best = 20;
        for (int m = 21; m < 200; m++)
        {
            if (c[m] > c[best])
                best = m;
        }
        Assert.Equal(Period, best);
    }

    [Fact]
    public void ResultIsEven()
    {
        var rng = new Random(7);
        double[] x = [.. Enumerable.Range(0, 33).Select(_ => rng.NextDouble() - 0.5)];
        double[] c = Spectral.RealCepstrum(x, 64);
        Assert.Equal(64, c.Length);
        for (int m = 1; m < 64; m++)
            Assert.Equal(c[m], c[64 - m], 1e-12);
    }
}
