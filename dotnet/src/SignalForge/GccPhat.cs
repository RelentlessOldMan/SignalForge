using System.Numerics;

namespace SignalForge;

/// <summary>GCC-PHAT delay of <c>x</c> relative to <c>y</c> (conventions: GCC-PHAT delay;
/// ADR 0191).</summary>
/// <param name="Delay">The delay in seconds, <c>(lag + δ)/fs</c>; positive when <c>x</c> is
/// later.</param>
/// <param name="Lag">The integer lag of the peak.</param>
/// <param name="Peak">The PHAT correlation at that lag.</param>
public sealed record GccPhat(double Delay, int Lag, double Peak);

public static partial class Measurements
{
    /// <summary>The delay of <c>x</c> relative to <c>y</c> from the phase-transform weighted
    /// cross-correlation (conventions: GCC-PHAT delay; ADR 0191).</summary>
    /// <param name="x">Real samples, finite, not empty, not all zero.</param>
    /// <param name="y">Real samples, finite, not empty, not all zero.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <param name="maxDelay">The largest delay searched in seconds, finite and at least 0; all
    /// lags when null.</param>
    /// <returns>The delay, the integer lag and the peak.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static GccPhat GccPhat(ReadOnlySpan<double> x, ReadOnlySpan<double> y, double sampleRate, double? maxDelay = null)
    {
        SignalForge.Check.PositiveFinite(sampleRate, nameof(sampleRate));
        CheckPhatInput(x, nameof(x));
        CheckPhatInput(y, nameof(y));
        int n = x.Length, m = y.Length;
        int lo = -(m - 1), hi = n - 1;
        if (maxDelay is double md)
        {
            if (!double.IsFinite(md) || md < 0)
                throw new ArgumentException("max_delay must be finite and at least 0", nameof(maxDelay));
            double kd = Math.Floor(md * sampleRate);
            int k = kd >= int.MaxValue ? int.MaxValue : (int)kd;
            lo = Math.Max(lo, -k);
            hi = Math.Min(hi, k);
        }
        int size = n + m - 1;
        var xs = new Complex[size];
        var ys = new Complex[size];
        for (int i = 0; i < n; i++)
            xs[i] = x[i];
        for (int i = 0; i < m; i++)
            ys[i] = y[i];
        Complex[] xf = Spectral.Fft(xs), yf = Spectral.Fft(ys);
        var w = new Complex[size];
        for (int i = 0; i < size; i++)
        {
            Complex g = xf[i] * Complex.Conjugate(yf[i]);
            double mag = g.Magnitude;
            w[i] = mag > 0 ? g / mag : Complex.Zero;
        }
        Complex[] r = Spectral.Ifft(w);
        double At(int lag) => r[((lag % size) + size) % size].Real;
        int best = lo;
        for (int k = lo + 1; k <= hi; k++)
        {
            if (At(k) > At(best))
                best = k;
        }
        double frac = 0;
        if (lo < best && best < hi)
        {
            double a = At(best - 1), b = At(best), c = At(best + 1);
            double curve = a - 2 * b + c;
            if (curve < 0)
                frac = (a - c) / (2 * curve);
        }
        return new GccPhat((best + frac) / sampleRate, best, At(best));
    }

    private static void CheckPhatInput(ReadOnlySpan<double> v, string paramName)
    {
        if (v.IsEmpty)
            throw new ArgumentException("the samples must not be empty", paramName);
        bool any = false;
        foreach (double s in v)
        {
            if (!double.IsFinite(s))
                throw new ArgumentException("the samples must be finite", paramName);
            any |= s != 0;
        }
        if (!any)
            throw new ArgumentException("the samples must not be all zero", paramName);
    }
}
