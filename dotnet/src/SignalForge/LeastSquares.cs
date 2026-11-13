namespace SignalForge;

public static partial class Dsp
{
    /// <summary>Symmetric FIR taps minimizing the weighted integral squared error over the bands,
    /// the desired gain linear across each band from its two edge values (conventions: FIR
    /// filters, Least-squares design; ADR 0029).</summary>
    /// <param name="numTaps">Number of taps, 1 to 1001; odd is type I, even type II.</param>
    /// <param name="bands">Band edges in Hz as pairs, strictly increasing, from ≥ 0 to ≤ sampleRate/2.</param>
    /// <param name="desired">Two gains per band: at its lower and its upper edge.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    /// <param name="weights">One positive weight per band; null for all 1.</param>
    public static double[] FirLeastSquares(int numTaps, IReadOnlyList<double> bands, IReadOnlyList<double> desired,
        double sampleRate, IReadOnlyList<double>? weights = null)
    {
        ArgumentNullException.ThrowIfNull(bands);
        ArgumentNullException.ThrowIfNull(desired);
        if (numTaps < 1 || numTaps > 1001)
            throw new ArgumentOutOfRangeException(nameof(numTaps), numTaps, "must be in [1, 1001]");
        double fs = Check.PositiveFinite(sampleRate, nameof(sampleRate));
        if (bands.Count < 2 || bands.Count % 2 != 0 || bands.Any(v => !double.IsFinite(v)))
            throw new ArgumentException("bands must be finite edge pairs", nameof(bands));
        if (bands[0] < 0 || bands[^1] > fs / 2 || Enumerable.Range(1, bands.Count - 1).Any(i => bands[i] <= bands[i - 1]))
            throw new ArgumentException("band edges must increase strictly from >= 0 to <= sampleRate/2", nameof(bands));
        int nb = bands.Count / 2;
        if (desired.Count != 2 * nb || desired.Any(v => !double.IsFinite(v)))
            throw new ArgumentException("desired must have two finite values per band (its edge gains)", nameof(desired));
        if (weights is not null && (weights.Count != nb || weights.Any(v => !double.IsFinite(v) || v <= 0)))
            throw new ArgumentException("weights must have one positive finite value per band", nameof(weights));

        int n = numTaps;
        bool odd = n % 2 == 1;
        int l = odd ? (n + 1) / 2 : n / 2;
        double T(int k) => k + (odd ? 0.0 : 0.5);
        var g = new double[l, l];
        var p = new double[l];
        for (int j = 0; j < nb; j++)
        {
            double lo = bands[2 * j] / fs, hi = bands[2 * j + 1] / fs, w = weights?[j] ?? 1.0;
            double slope = (desired[2 * j + 1] - desired[2 * j]) / (hi - lo);
            for (int k = 0; k < l; k++)
            {
                for (int m = 0; m < l; m++)
                    g[k, m] += w * (CosIntegral(T(k) - T(m), lo, hi) + CosIntegral(T(k) + T(m), lo, hi)) / 2;
                p[k] += w * ((desired[2 * j] - slope * lo) * CosIntegral(T(k), lo, hi) + slope * NuCosIntegral(T(k), lo, hi));
            }
        }
        double[] a = Solve(g, p);
        var h = new double[n];
        if (odd)
        {
            int c = (n - 1) / 2;
            h[c] = a[0];
            for (int k = 1; k < l; k++)
                h[c + k] = h[c - k] = a[k] / 2;
        }
        else
        {
            for (int k = 0; k < l; k++)
                h[n / 2 + k] = h[n / 2 - 1 - k] = a[k] / 2;
        }
        return h;
    }

    /// <summary>C(u): the integral of cos(2πuν) over [lo, hi] (conventions).</summary>
    private static double CosIntegral(double u, double lo, double hi)
    {
        if (u == 0)
            return hi - lo;
        double k = 2 * Math.PI * u;
        return (Math.Sin(k * hi) - Math.Sin(k * lo)) / k;
    }

    /// <summary>S(u): the integral of ν·cos(2πuν) over [lo, hi] (conventions).</summary>
    private static double NuCosIntegral(double u, double lo, double hi)
    {
        if (u == 0)
            return (hi * hi - lo * lo) / 2;
        double k = 2 * Math.PI * u;
        double F(double v) => v * Math.Sin(k * v) / k + Math.Cos(k * v) / (k * k);
        return F(hi) - F(lo);
    }
}
