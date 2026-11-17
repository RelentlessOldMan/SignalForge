using Xunit;

namespace SignalForge.Tests;

/// <summary>Bandwidth expansion (ADR 0219).</summary>
public class BandwidthExpansionTests
{
    [Fact]
    public void ScalesTheReflectionOfAnOrderOneFilter()
    {
        double[] a = Dsp.BandwidthExpansion([1, -0.8], 0.5);
        Assert.Equal(-0.4, Dsp.LpcToReflection(a)[0], 1e-15);
    }
}
