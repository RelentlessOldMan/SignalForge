using Xunit;

namespace SignalForge.Tests;

/// <summary>The ROC AUC (ADR 0393).</summary>
public class RocAucTests
{
    [Fact]
    public void SomeTies() =>
        Assert.Equal(0.75, Measurements.RocAuc([1.0, 0.0, 1.0, 0.0, 1.0], [3.0, 3.0, 1.0, 0.0, 5.0]), 1e-15);

    [Fact]
    public void RejectsAMissingClass() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.RocAuc([1.0, 1.0], [0.2, 0.4]));
}
