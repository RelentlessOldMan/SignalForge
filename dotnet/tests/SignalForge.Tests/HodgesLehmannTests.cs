using Xunit;

namespace SignalForge.Tests;

/// <summary>The Hodges–Lehmann shift estimate (ADR 0406).</summary>
public class HodgesLehmannTests
{
    [Fact]
    public void Negative() =>
        Assert.Equal(-2.75, Measurements.HodgesLehmann([0.0, 0.5], [2.0, 3.0, 3.5]), 1e-15);

    [Fact]
    public void RejectsAnEmptySample() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HodgesLehmann([1.0], []));
}
