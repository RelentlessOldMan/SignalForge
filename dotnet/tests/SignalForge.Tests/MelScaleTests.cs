using Xunit;

namespace SignalForge.Tests;

/// <summary>Mel scale (conventions: Mel scale; ADR 0154).</summary>
public class MelScaleTests
{
    [Theory]
    [InlineData(MelScale.Htk)]
    [InlineData(MelScale.Slaney)]
    public void InverseOnAGridAndIncreasing(MelScale scale)
    {
        double previous = -1;
        for (int i = 0; i <= 400; i++)
        {
            double hz = 50.0 * i;
            double mel = Units.HzToMel(hz, scale);
            Assert.True(mel > previous);
            previous = mel;
            Assert.Equal(hz, Units.MelToHz(mel, scale), 1e-12 * hz + 1e-9);
        }
    }
}
