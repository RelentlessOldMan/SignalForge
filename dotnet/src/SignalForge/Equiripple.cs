namespace SignalForge;

public static partial class Dsp
{
    /// <summary>Parks–McClellan (Remez exchange) symmetric FIR taps: the minimax weighted error
    /// over the bands with a constant desired gain in each, on the grid the conventions define
    /// (conventions: FIR filters, Equiripple design; ADR 0024).</summary>
    /// <param name="numTaps">Number of taps, 1 to 1001; odd is type I, even type II.</param>
    /// <param name="bands">Band edges in Hz as pairs [b0, b1, b2, b3, …], strictly increasing,
    /// from 0 or above to sampleRate/2 or below.</param>
    /// <param name="desired">Desired gain in each band, finite.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    /// <param name="weights">Positive weight for each band; all 1 if null.</param>
    /// <param name="gridDensity">Grid points per extremum, 1 to 64.</param>
    /// <exception cref="ArgumentException">Bad arguments, or a design whose ripple is beyond
    /// double precision (it does not converge).</exception>
    public static double[] FirEquiripple(int numTaps, IReadOnlyList<double> bands, IReadOnlyList<double> desired,
        double sampleRate, IReadOnlyList<double>? weights = null, int gridDensity = 16)
    {
        ArgumentNullException.ThrowIfNull(bands);
        ArgumentNullException.ThrowIfNull(desired);
        var (_, _, dd, _, _) = EquirippleGrid(numTaps, bands, desired, sampleRate, weights, gridDensity);
        int n = numTaps;
        if (dd.All(v => v == 0) || (n % 2 == 1 && dd.All(v => v == dd[0])))
        {
            var exact = new double[n];
            exact[(n - 1) / 2] = dd[0];
            return exact;
        }
        return Remez(n, bands, desired, sampleRate, weights, gridDensity)?.Taps
            ?? throw new ArgumentException("the equiripple design is beyond double precision: its ripple is too small, or its gaps between bands too wide, for double taps to reach", nameof(numTaps));
    }

    // The first extremal set (conventions: Equiripple design, reference scaling) from the smaller
    // design's final set (its frequencies), or by grid index without one.
    private static int[] ScaledStart(int l, double[] nu, int[] band, double[]? prior)
    {
        int g = nu.Length;
        var ext = new int[l + 1];
        if (prior is null)
        {
            for (int i = 0; i <= l; i++)
                ext[i] = (int)((long)i * (g - 1) / l);
            return ext;
        }
        var s = new double[g];
        for (int k = 1; k < g; k++)
            s[k] = s[k - 1] + (band[k] == band[k - 1] ? nu[k] - nu[k - 1] : 0);
        int lp = prior.Length - 1;
        var sp = new double[lp + 1];
        for (int i = 0; i <= lp; i++)
            sp[i] = Interp(prior[i], nu, s);
        var pos = new double[lp + 1];
        for (int i = 0; i <= lp; i++)
            pos[i] = i;
        for (int i = 0; i <= l; i++)
        {
            double t = Interp((double)i * lp / l, pos, sp);
            int k = 0;
            while (k < g && s[k] < t)
                k++;
            ext[i] = i > 0 ? Math.Max(k, ext[i - 1] + 1) : k;
        }
        for (int i = 0; i <= l; i++)
            ext[i] = Math.Min(ext[i], g - 1 - (l - i));
        return ext;
    }

    // Linear interpolation of (xp, fp) at x, xp increasing, held constant outside (as NumPy's interp).
    private static double Interp(double x, double[] xp, double[] fp)
    {
        if (x <= xp[0])
            return fp[0];
        if (x >= xp[^1])
            return fp[^1];
        int j = Array.BinarySearch(xp, x);
        if (j >= 0)
            return fp[j];
        j = ~j - 1;
        return (fp[j + 1] - fp[j]) / (xp[j + 1] - xp[j]) * (x - xp[j]) + fp[j];
    }

    // The exchange (conventions: Equiripple design): the taps and the final set's frequencies, or
    // null if the design is beyond double precision.
    private static (double[] Taps, double[] Nu)? Remez(int n, IReadOnlyList<double> bands, IReadOnlyList<double> desired,
        double sampleRate, IReadOnlyList<double>? weights, int gridDensity)
    {
        var (l, nu, dd, ww, band) = EquirippleGrid(n, bands, desired, sampleRate, weights, gridDensity);
        bool odd = n % 2 == 1;
        int g = nu.Length;
        double[] dp = new double[g], wp = new double[g], x = new double[g];
        double slack = 0;
        for (int i = 0; i < g; i++)
        {
            double q = odd ? 1 : Math.Cos(Math.PI * nu[i]);
            dp[i] = dd[i] / q;
            wp[i] = ww[i] * q;
            x[i] = Math.Cos(2 * Math.PI * nu[i]);
            slack = Math.Max(slack, Math.Abs(ww[i] * dd[i]));
        }
        slack *= 1e-12;
        double[]? prior = l > 16 ? Remez(n - 2 * (l - (l + 1) / 2), bands, desired, sampleRate, weights, gridDensity)?.Nu : null;
        int[] ext = ScaledStart(l, nu, band, prior);
        double[] gamma = new double[l + 1], logs = new double[l + 1], values = new double[l + 1];
        double[] bary = new double[l], e = new double[g];
        for (int iteration = 0; iteration < 250; iteration++)
        {
            double minLog = double.PositiveInfinity;
            for (int i = 0; i <= l; i++)
            {
                double s = 0, sign = 1;
                for (int j = 0; j <= l; j++)
                {
                    if (j == i)
                        continue;
                    double d = x[ext[i]] - x[ext[j]];
                    s += Math.Log(Math.Abs(d));
                    sign *= Math.Sign(d);
                }
                logs[i] = s;
                gamma[i] = sign;
                minLog = Math.Min(minLog, s);
            }
            double num = 0, den = 0;
            for (int i = 0; i <= l; i++)
            {
                gamma[i] *= Math.Exp(minLog - logs[i]);
                num += gamma[i] * dp[ext[i]];
                den += gamma[i] * Alt(i) / wp[ext[i]];
            }
            double delta = num / den;
            for (int i = 0; i <= l; i++)
                values[i] = dp[ext[i]] - Alt(i) * delta / wp[ext[i]];
            for (int i = 0; i < l; i++)
                bary[i] = gamma[i] * (x[ext[i]] - x[ext[l]]);
            double top = 0;
            for (int k = 0; k < g; k++)
            {
                e[k] = wp[k] * (dp[k] - Barycentric(x[k], x, ext, bary, values));
                top = Math.Max(top, Math.Abs(e[k]));
            }
            for (int i = 0; i <= l; i++)
                e[ext[i]] = Alt(i) * delta; // exact at the set; the last point is not a node
            var next = Extrema(e, band, l + 1, ext, delta >= 0 ? 1 : -1);
            if (next.Count < l + 1)
                break;
            if (next.SequenceEqual(ext) || top <= Math.Abs(delta) * (1 + 1e-9) + slack)
            {
                double[] c = Coefficients(l, nu, dp, wp, ext);
                double worst = 0;
                for (int k = 0; k < g; k++)
                    worst = Math.Max(worst, Math.Abs(wp[k] * (dp[k] - Clenshaw(c, x[k]))));
                if (worst > Math.Abs(delta) * (1 + 1e-3) + 100 * slack)
                    break;
                return (EquirippleTaps(n, c), [.. ext.Select(i => nu[i])]);
            }
            next.CopyTo(ext);
        }
        return null;
    }

    private static double Alt(int i) => i % 2 == 0 ? 1 : -1;

    /// <summary>P at x by barycentric interpolation through the first L extremal points.</summary>
    private static double Barycentric(double xk, double[] x, int[] ext, double[] bary, double[] values)
    {
        double num = 0, den = 0;
        for (int j = 0; j < bary.Length; j++)
        {
            double t = xk - x[ext[j]];
            if (t == 0)
                return values[j];
            double r = bary[j] / t;
            num += r * values[j];
            den += r;
        }
        return num / den;
    }

    /// <summary>The new extremal set from the error on the grid (conventions: Equiripple design): the
    /// old set's points always count, with alternating signs starting at <paramref name="s"/>.</summary>
    private static List<int> Extrema(double[] e, int[] band, int want, int[] ext, int s)
    {
        int g = e.Length;
        var sgn = new int[g];
        var found = new bool[g];
        for (int k = 0; k < g; k++)
            sgn[k] = Math.Sign(e[k]);
        for (int i = 0; i < ext.Length; i++)
        {
            // E = ±δ at the old set, so the new set always alternates L + 1 times.
            sgn[ext[i]] = i % 2 == 0 ? s : -s;
            found[ext[i]] = true;
        }
        var cand = new List<int>();
        for (int k = 0; k < g; k++)
        {
            bool hasLeft = k > 0 && band[k - 1] == band[k], hasRight = k + 1 < g && band[k + 1] == band[k];
            bool up = e[k] > 0 && (!hasLeft || e[k] >= e[k - 1]) && (!hasRight || e[k] >= e[k + 1]);
            bool down = e[k] < 0 && (!hasLeft || e[k] <= e[k - 1]) && (!hasRight || e[k] <= e[k + 1]);
            if (up || down || found[k])
                cand.Add(k);
        }
        cand = Merge(cand, e, sgn);
        while (cand.Count > want)
        {
            if (cand.Count == want + 1)
            {
                cand.RemoveAt(Math.Abs(e[cand[0]]) <= Math.Abs(e[cand[^1]]) ? 0 : cand.Count - 1);
            }
            else
            {
                int smallest = 0;
                for (int i = 1; i < cand.Count; i++)
                {
                    if (Math.Abs(e[cand[i]]) < Math.Abs(e[cand[smallest]]))
                        smallest = i;
                }
                cand.RemoveAt(smallest);
                cand = Merge(cand, e, sgn);
            }
        }
        return cand;
    }

    /// <summary>Runs of the same sign keep their largest |E|, the first of equals.</summary>
    private static List<int> Merge(List<int> cand, double[] e, int[] sgn)
    {
        var merged = new List<int>(cand.Count);
        foreach (int k in cand)
        {
            if (merged.Count > 0 && sgn[k] == sgn[merged[^1]])
            {
                if (Math.Abs(e[k]) > Math.Abs(e[merged[^1]]))
                    merged[^1] = k;
            }
            else
            {
                merged.Add(k);
            }
        }
        return merged;
    }

    /// <summary>Σ c_k·cos(2πkν) at x = cos(2πν), by Clenshaw's recurrence.</summary>
    private static double Clenshaw(double[] c, double x)
    {
        double b1 = 0, b2 = 0;
        for (int k = c.Length - 1; k >= 1; k--)
            (b1, b2) = (2 * x * b1 - b2 + c[k], b1);
        return x * b1 - b2 + c[0];
    }

    /// <summary>Cosine coefficients by a direct solve at the final set (conventions: Equiripple
    /// design, Taps).</summary>
    private static double[] Coefficients(int l, double[] nu, double[] dp, double[] wp, int[] ext)
    {
        var a = new double[l + 1, l + 1];
        var rhs = new double[l + 1];
        for (int i = 0; i <= l; i++)
        {
            for (int k = 0; k < l; k++)
                a[i, k] = Math.Cos(2 * Math.PI * nu[ext[i]] * k);
            a[i, l] = Alt(i) / wp[ext[i]];
            rhs[i] = dp[ext[i]];
        }
        return Solve(a, rhs)[..l];
    }

    /// <summary>Taps from the cosine coefficients (conventions: Equiripple design, Taps).</summary>
    private static double[] EquirippleTaps(int n, double[] c)
    {
        int l = c.Length;
        var h = new double[n];
        if (n % 2 == 1)
        {
            int mid = (n - 1) / 2;
            h[mid] = c[0];
            for (int k = 1; k < l; k++)
                h[mid - k] = h[mid + k] = c[k] / 2;
            return h;
        }
        var beta = new double[l];
        beta[0] = c[0] + (l > 1 ? c[1] / 2 : 0);
        for (int k = 1; k < l - 1; k++)
            beta[k] = (c[k] + c[k + 1]) / 2;
        if (l > 1)
            beta[l - 1] = c[l - 1] / 2;
        for (int k = 1; k <= l; k++)
            h[n / 2 - 1 + k] = h[n / 2 - k] = beta[k - 1] / 2;
        return h;
    }

    /// <summary>Gaussian elimination with partial pivoting; overwrites its arguments.</summary>
    private static double[] Solve(double[,] a, double[] b)
    {
        int n = b.Length;
        for (int col = 0; col < n; col++)
        {
            int p = col;
            for (int r = col + 1; r < n; r++)
            {
                if (Math.Abs(a[r, col]) > Math.Abs(a[p, col]))
                    p = r;
            }
            if (p != col)
            {
                for (int k = 0; k < n; k++)
                    (a[col, k], a[p, k]) = (a[p, k], a[col, k]);
                (b[col], b[p]) = (b[p], b[col]);
            }
            for (int r = col + 1; r < n; r++)
            {
                double f = a[r, col] / a[col, col];
                if (f == 0)
                    continue;
                for (int k = col; k < n; k++)
                    a[r, k] -= f * a[col, k];
                b[r] -= f * b[col];
            }
        }
        var x = new double[n];
        for (int r = n - 1; r >= 0; r--)
        {
            double s = b[r];
            for (int k = r + 1; k < n; k++)
                s -= a[r, k] * x[k];
            x[r] = s / a[r, r];
        }
        return x;
    }

    private static (int L, double[] Nu, double[] D, double[] W, int[] Band) EquirippleGrid(int numTaps,
        IReadOnlyList<double> bands, IReadOnlyList<double> desired, double sampleRate,
        IReadOnlyList<double>? weights, int gridDensity)
    {
        if (numTaps < 1 || numTaps > 1001)
            throw new ArgumentOutOfRangeException(nameof(numTaps), numTaps, "must be in [1, 1001]");
        if (gridDensity < 1 || gridDensity > 64)
            throw new ArgumentOutOfRangeException(nameof(gridDensity), gridDensity, "must be in [1, 64]");
        double fs = Check.PositiveFinite(sampleRate, nameof(sampleRate));
        if (bands.Count < 2 || bands.Count % 2 != 0 || bands.Any(v => !double.IsFinite(v)))
            throw new ArgumentException("bands must be finite edge pairs", nameof(bands));
        if (bands[0] < 0 || bands[^1] > fs / 2 || Enumerable.Range(1, bands.Count - 1).Any(i => bands[i] <= bands[i - 1]))
            throw new ArgumentException("band edges must increase strictly from >= 0 to <= sampleRate/2", nameof(bands));
        int nb = bands.Count / 2;
        if (desired.Count != nb || desired.Any(v => !double.IsFinite(v)))
            throw new ArgumentException("desired must have one finite value per band", nameof(desired));
        if (weights is not null && (weights.Count != nb || weights.Any(v => !double.IsFinite(v) || v <= 0)))
            throw new ArgumentException("weights must have one positive finite value per band", nameof(weights));
        bool odd = numTaps % 2 == 1;
        if (!odd && bands[^1] == fs / 2 && desired[^1] != 0)
            throw new ArgumentException("an even numTaps has zero gain at sampleRate/2: desired must be 0 there", nameof(desired));
        int l = odd ? (numTaps + 1) / 2 : numTaps / 2;
        double step = 0.5 / (gridDensity * l);
        List<double> nu = [], dd = [], ww = [];
        List<int> bi = [];
        for (int j = 0; j < nb; j++)
        {
            double lo = bands[2 * j] / fs, hi = bands[2 * j + 1] / fs;
            int m = (int)Math.Ceiling((hi - lo) / step);
            for (int i = 0; i <= m; i++)
            {
                double v = i == m ? hi : lo + (hi - lo) * i / m;
                if (!odd && v == 0.5)
                    continue;
                nu.Add(v);
                dd.Add(desired[j]);
                ww.Add(weights?[j] ?? 1.0);
                bi.Add(j);
            }
        }
        if (nu.Count < l + 1)
            throw new ArgumentException("the bands are too narrow for numTaps: too few grid points", nameof(bands));
        return (l, [.. nu], [.. dd], [.. ww], [.. bi]);
    }
}
