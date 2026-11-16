using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Autocorrelation (conventions: Pulse shaping, Autocorrelation; ADR 0148).</summary>
public class AutocorrelationTests
{
    private static Complex[] Samples()
    {
        var rng = new Random(148);
        return [.. Enumerable.Range(0, 40).Select(_ => new Complex(rng.NextDouble() - 0.5, rng.NextDouble() - 0.5))];
    }

    [Fact]
    public void MatchesADirectSum()
    {
        Complex[] x = Samples();
        Complex[] r = Dsp.Autocorrelation(x, scaling: CorrelationScaling.None);
        for (int k = 0; k < x.Length; k++)
        {
            Complex sum = 0;
            for (int i = 0; i + k < x.Length; i++)
                sum += x[i + k] * Complex.Conjugate(x[i]);
            Assert.True(Complex.Abs(sum - r[k]) < 1e-12);
        }
    }

    [Fact]
    public void ZeroLagIsTheEnergy()
    {
        Complex[] x = Samples();
        double energy = x.Sum(v => v.Real * v.Real + v.Imaginary * v.Imaginary);
        Assert.Equal(energy, Dsp.Autocorrelation(x, 0, CorrelationScaling.None)[0].Real, 1e-12);
    }

    [Fact]
    public void PeriodicSignalPeaksAtItsPeriod()
    {
        var rng = new Random(148);
        double[] cycle = [.. Enumerable.Range(0, 7).Select(_ => rng.NextDouble() - 0.5)];
        double[] x = [.. Enumerable.Range(0, 140).Select(n => cycle[n % 7])];
        double[] r = Dsp.Autocorrelation(x, 10, CorrelationScaling.Unbiased);
        int best = 1;
        for (int k = 2; k < r.Length; k++)
        {
            if (r[k] > r[best])
                best = k;
        }
        Assert.Equal(7, best);
    }
}
