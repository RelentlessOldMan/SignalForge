namespace SignalForge;

public static partial class Dsp
{
    /// <summary>Symmetric or antisymmetric FIR taps minimizing the weighted integral squared error over
    /// the bands, the desired gain linear across each band from its two edge values (conventions: FIR
    /// filters, Least-squares design; ADR 0029, ADR 0086).</summary>
    /// <param name="numTaps">Number of taps, 1 to 1001 (2 to 1001 for the antisymmetric kinds).</param>
    /// <param name="bands">Band edges in Hz as pairs, strictly increasing, from ≥ 0 to ≤ sampleRate/2.</param>
    /// <param name="desired">Two gains per band: at its lower and its upper edge.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    /// <param name="weights">One positive weight per band; null for all 1.</param>
    /// <param name="kind">Symmetric filter, or antisymmetric Hilbert (amplitude the gain) or
    /// differentiator (amplitude −2πν·gain), as for <see cref="FirEquiripple"/>, with the plain weight.</param>
    public static double[] FirLeastSquares(int numTaps, IReadOnlyList<double> bands, IReadOnlyList<double> desired,
        double sampleRate, IReadOnlyList<double>? weights = null, FirKind kind = FirKind.Filter)
    {
        ArgumentNullException.ThrowIfNull(bands);
        ArgumentNullException.ThrowIfNull(desired);
        if (!Enum.IsDefined(kind))
            throw new ArgumentOutOfRangeException(nameof(kind), kind, "unknown kind");
        int minTaps = kind == FirKind.Filter ? 1 : 2;
        if (numTaps < minTaps || numTaps > 1001)
            throw new ArgumentOutOfRangeException(nameof(numTaps), numTaps, $"must be in [{minTaps}, 1001]");
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
        if (kind != FirKind.Filter)
            return LeastSquaresAntisymmetric(n, bands, desired, fs, weights, kind == FirKind.Differentiator);
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

    /// <summary>The sine-basis normal equations of the antisymmetric kinds (conventions).</summary>
    private static double[] LeastSquaresAntisymmetric(int n, IReadOnlyList<double> bands, IReadOnlyList<double> desired,
        double fs, IReadOnlyList<double>? weights, bool differentiator)
    {
        int l = n / 2;
        double T(int k) => k + (n % 2 == 1 ? 1.0 : 0.5);
        var g = new double[l, l];
        var p = new double[l];
        for (int j = 0; j < bands.Count / 2; j++)
        {
            double lo = bands[2 * j] / fs, hi = bands[2 * j + 1] / fs, w = weights?[j] ?? 1.0;
            double slope = (desired[2 * j + 1] - desired[2 * j]) / (hi - lo);
            double level = desired[2 * j] - slope * lo;
            for (int k = 0; k < l; k++)
            {
                for (int m = 0; m < l; m++)
                    g[k, m] += w * (CosIntegral(T(k) - T(m), lo, hi) - CosIntegral(T(k) + T(m), lo, hi)) / 2;
                p[k] += differentiator
                    ? w * -2 * Math.PI * (level * SinMoment(1, T(k), lo, hi) + slope * SinMoment(2, T(k), lo, hi))
                    : w * (level * SinMoment(0, T(k), lo, hi) + slope * SinMoment(1, T(k), lo, hi));
            }
        }
        double[] a = Solve(g, p);
        var h = new double[n];
        for (int k = 0; k < l; k++)
        {
            h[n / 2 + n % 2 + k] = a[k] / 2; // the taps after the centre; an odd N's centre stays 0
            h[n / 2 - 1 - k] = -a[k] / 2;
        }
        return h;
    }

    /// <summary>M_i(u): the integral of νⁱ·sin(2πuν) over [lo, hi], u ≠ 0 (conventions).</summary>
    private static double SinMoment(int i, double u, double lo, double hi)
    {
        double k = 2 * Math.PI * u;
        double F(double v)
        {
            double c = Math.Cos(k * v), s = Math.Sin(k * v);
            return i switch
            {
                0 => -c / k,
                1 => (-v * c / k) + (s / (k * k)),
                _ => (-v * v * c / k) + (2 * v * s / (k * k)) + (2 * c / (k * k * k)),
            };
        }
        return F(hi) - F(lo);
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
