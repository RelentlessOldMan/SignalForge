using Xunit;

namespace SignalForge.Tests;

/// <summary>ICC(3,1) (ADR 0381).</summary>
public class IccConsistencyTests
{
    [Fact]
    public void Opposed() =>
        Assert.Equal(-1.0, Measurements.IccConsistency([[1.0, 2.0, 3.0], [3.0, 2.0, 1.0]]), 1e-14);

    [Fact]
    public void RejectsRaggedRows() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.IccConsistency([[1.0, 2.0, 3.0], [1.0, 2.0]]));
}
