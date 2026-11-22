using Xunit;

namespace SignalForge.Tests;

/// <summary>The Patil-Taillie diversity (ADR 0565).</summary>
public class PatilTaillieDiversityTests
{
    [Fact]
    public void Simpson() =>
        Assert.Equal(5.0 / 8.0, Measurements.PatilTaillieDiversity([1.0, 1.0, 2.0], 1.0), 14);

    [Fact]
    public void Shannon() =>
        Assert.Equal(Math.Log(2.0), Measurements.PatilTaillieDiversity([1.0, 1.0], 0.0), 14);

    [Fact]
    public void RejectsLowBeta() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.PatilTaillieDiversity([1.0], -1.5));
}
