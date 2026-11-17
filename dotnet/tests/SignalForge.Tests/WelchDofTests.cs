using Xunit;

namespace SignalForge.Tests;

/// <summary>Welch equivalent degrees of freedom (conventions: Welch degrees of freedom; ADR 0200).</summary>
public class WelchDofTests
{
    [Fact]
    public void HannHalfOverlapTendsTo36Over19PerSegment()
    {
        const int k = 4000;
        Assert.Equal(36.0 / 19, Spectral.WelchDof(256, 128, k) / k, 1e-3);
    }
}
