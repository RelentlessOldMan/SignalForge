using Xunit;

namespace SignalForge.Tests;

/// <summary>The mutual information of two binary records (ADR 0464).</summary>
public class BinaryMutualInformationTests
{
    [Fact]
    public void Identical() =>
        Assert.Equal(Math.Log(2), Measurements.BinaryMutualInformation([1, 0, 1, 0], [1, 0, 1, 0]), 15);

    [Fact]
    public void RejectsRecordsOfDifferentLengths() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.BinaryMutualInformation([1.0, 0.0], [1.0]));
}
