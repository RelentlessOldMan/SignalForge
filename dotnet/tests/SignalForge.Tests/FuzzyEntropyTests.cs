using Xunit;

namespace SignalForge.Tests;

/// <summary>Fuzzy entropy (ADR 0339).</summary>
public class FuzzyEntropyTests
{
    [Fact]
    public void ALineIsZero()
    {
        double[] x = new double[15];
        for (int i = 0; i < x.Length; i++)
            x[i] = 0.5 * i;
        Assert.Equal(0.0, Measurements.FuzzyEntropy(x, 2, 0.3), 1e-15);
    }

    [Fact]
    public void ThreeSamplesByHand()
    {
        // m = 1, x = 0, 1, 3: two templates. Length 1 minus its mean is 0 for both: φ1 = 1.
        // Length 2: (−0.5, 0.5) and (−1, 1), d = 0.5: φ2 = exp(−0.25/r).
        double r = 0.5;
        Assert.Equal(0.25 / r, Measurements.FuzzyEntropy([0.0, 1.0, 3.0], 1, r), 1e-15);
    }

    [Fact]
    public void RejectsAPowerBelowOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.FuzzyEntropy([0.0, 1.0, 2.0, 3.0], 1, 0.5, 0.5));
}
