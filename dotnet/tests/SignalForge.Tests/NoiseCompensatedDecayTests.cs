using Xunit;

namespace SignalForge.Tests;

/// <summary>Noise-compensated decay (conventions: Noise-compensated decay; ADR 0183).</summary>
public class NoiseCompensatedDecayTests
{
    [Fact]
    public void WithoutNoiseItIsTheDecayOfTheTruncatedResponse()
    {
        double[] h = [1.0, 0.5, 0.25, 0.0, 0.0];
        double[] plain = Measurements.SchroederDecay(h.AsSpan(0, 3));
        double[] fixedDecay = Measurements.NoiseCompensatedDecay(h, 0.4);
        Assert.Equal(3, fixedDecay.Length);
        for (int k = 0; k < 3; k++)
            Assert.Equal(plain[k], fixedDecay[k], 1e-12);
    }
}
