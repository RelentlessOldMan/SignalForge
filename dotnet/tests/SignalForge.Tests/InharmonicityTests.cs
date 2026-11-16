using Xunit;

namespace SignalForge.Tests;

/// <summary>Inharmonicity (conventions: Spectra, Inharmonicity; ADR 0140).</summary>
public class InharmonicityTests
{
    private static readonly double[] Tones = [100, 203, 298.5, 404];
    private static readonly double[] Heights = [5, 3, 2, 1];
    private static readonly int[] Orders = [1, 2, 3, 4];
    private static readonly double[] Stiffness = [0, 1e-4, 1e-3, 1e-2];

    [Fact]
    public void ScalingFrequenciesAndFundamentalLeavesItUnchanged()
    {
        double a = Spectral.Inharmonicity(Tones, Heights, 100, Orders);
        double b = Spectral.Inharmonicity([.. Tones.Select(v => 3.5 * v)], Heights, 350, Orders);
        Assert.Equal(a, b, 1e-12 * a);
    }

    [Fact]
    public void ScalingHeightsLeavesItUnchanged()
    {
        double a = Spectral.Inharmonicity(Tones, Heights, 100, Orders);
        double b = Spectral.Inharmonicity(Tones, [.. Heights.Select(h => 7 * h)], 100, Orders);
        Assert.Equal(a, b, 1e-12 * a);
    }

    [Fact]
    public void StiffStringGrowsWithStiffness()
    {
        int[] m = [.. Enumerable.Range(1, 8)];
        double[] values = [.. Stiffness.Select(b => Spectral.Inharmonicity(
            [.. m.Select(k => 110.0 * k * Math.Sqrt(1 + b * k * k))], [.. m.Select(k => 1.0 / k)], 110, m))];
        Assert.Equal(0.0, values[0]);
        for (int i = 1; i < values.Length; i++)
            Assert.True(values[i] > values[i - 1]);
    }
}
