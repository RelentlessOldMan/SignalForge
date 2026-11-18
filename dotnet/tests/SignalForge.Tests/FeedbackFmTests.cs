using Xunit;

namespace SignalForge.Tests;

/// <summary>Feedback FM operator (ADR 0322).</summary>
public class FeedbackFmTests
{
    [Fact]
    public void NoFeedbackIsASine()
    {
        double[] y = Waveforms.FeedbackFm(8000, 8, 1000, 0);
        for (int n = 0; n < y.Length; n++)
            Assert.Equal(Math.Sin(2 * Math.PI * n / 8), y[n], 1e-15);
    }

    [Fact]
    public void TheSecondSampleFeedsTheFirstBack()
    {
        double[] y = Waveforms.FeedbackFm(8000, 2, 1000, 1, 1, 0.25);
        Assert.Equal(1.0, y[0]);
        Assert.Equal(Math.Sin((2 * Math.PI * 0.375) + 1), y[1], 1e-15);
    }

    [Fact]
    public void RejectsTooMuchFeedback() =>
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.FeedbackFm(8000, 4, 1000, 1.51));
}
