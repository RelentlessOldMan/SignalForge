using Xunit;

namespace SignalForge.Tests;

/// <summary>Kendall's W (ADR 0379).</summary>
public class KendallWTests
{
    [Fact]
    public void Ties() =>
        Assert.Equal(37.0 / 38, Measurements.KendallW([[1.0, 2.0, 3.0, 4.0], [1.0, 1.0, 2.0, 3.0]]), 1e-15);

    [Fact]
    public void RejectsRaggedRows() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.KendallW([[1.0, 2.0, 3.0], [1.0, 2.0]]));

    [Fact]
    public void RejectsEveryRowConstant() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.KendallW([[1.0, 1.0, 1.0], [2.0, 2.0, 2.0]]));
}
