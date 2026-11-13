using System.Numerics;

namespace SignalForge;

/// <summary>What a timing loop took (conventions: Synchronization, Tracking loops).</summary>
/// <param name="Symbols">The symbols, one per loop step.</param>
/// <param name="Positions">Where each symbol was taken, in samples.</param>
/// <param name="Errors">The timing detector's output at each symbol, 0 for the first.</param>
public sealed record TimingRecovery(Complex[] Symbols, double[] Positions, double[] Errors);

/// <summary>What a carrier loop gave (conventions: Synchronization, Tracking loops).</summary>
/// <param name="Symbols">The corrected symbols.</param>
/// <param name="Phases">The phase removed from each symbol, in radians, not wrapped.</param>
/// <param name="Errors">The phase detector's output at each symbol.</param>
public sealed record CarrierRecovery(Complex[] Symbols, double[] Phases, double[] Errors);

/// <summary>Synchronization: block estimators of symbol timing, QPSK carrier frequency and phase,
/// and tracking loops. Definitions in docs/conventions.md (Synchronization).</summary>
public static class Sync
{
    /// <summary>(kp, ki) of a second-order loop with noise bandwidth <paramref name="loopBandwidth"/>
    /// per update (conventions: Synchronization, Tracking loops).</summary>
    /// <param name="loopBandwidth">One-sided noise bandwidth per update, in (0, 0.5).</param>
    /// <param name="damping">Damping factor, positive and finite.</param>
    /// <param name="detectorGain">Slope of the detector at lock, positive and finite.</param>
    public static (double Kp, double Ki) PiLoopGains(double loopBandwidth, double damping, double detectorGain)
    {
        if (!(loopBandwidth > 0 && loopBandwidth < 0.5))
            throw new ArgumentOutOfRangeException(nameof(loopBandwidth), loopBandwidth, "must be in (0, 0.5)");
        Check.PositiveFinite(damping, nameof(damping));
        Check.PositiveFinite(detectorGain, nameof(detectorGain));
        double z = damping, kd = detectorGain;
        double theta = loopBandwidth / (z + 1 / (4 * z));
        double d = 1 + 2 * z * theta + theta * theta;
        return (4 * z * theta / d / kd, 4 * theta * theta / d / kd);
    }

    /// <summary>Gardner timing recovery: a PI loop on the step between symbols, reading between
    /// samples by the fractional-delay kernel (conventions: Synchronization, Tracking loops).</summary>
    /// <param name="samples">Matched-filter output, all finite.</param>
    /// <param name="samplesPerSymbol">Nominal samples per symbol, at least 2.</param>
    /// <param name="kp">Proportional gain, finite, not negative.</param>
    /// <param name="ki">Integral gain, finite, not negative.</param>
    /// <param name="start">Position of the first symbol in samples, finite, not negative.</param>
    /// <param name="halfWidth">Half the interpolator's length, at least 1.</param>
    public static TimingRecovery GardnerTiming(ReadOnlySpan<Complex> samples, int samplesPerSymbol, double kp, double ki, double start = 0, int halfWidth = 8)
    {
        ArgumentOutOfRangeException.ThrowIfLessThan(samplesPerSymbol, 2);
        foreach (Complex y in samples)
            if (!double.IsFinite(y.Real) || !double.IsFinite(y.Imaginary))
                throw new ArgumentException("must be finite", nameof(samples));
        NotNegativeFinite(kp, nameof(kp));
        NotNegativeFinite(ki, nameof(ki));
        NotNegativeFinite(start, nameof(start));
        ArgumentOutOfRangeException.ThrowIfLessThan(halfWidth, 1);
        var symbols = new List<Complex>();
        var positions = new List<double>();
        var errors = new List<double>();
        double tau = start, v = 0, sps = samplesPerSymbol;
        while (tau <= samples.Length - 1)
        {
            Complex z = Channel.Interpolate(samples, tau, halfWidth);
            double e = 0;
            if (symbols.Count > 0)
            {
                Complex mid = Channel.Interpolate(samples, (positions[^1] + tau) / 2, halfWidth);
                Complex delta = z - symbols[^1];
                e = mid.Real * delta.Real + mid.Imaginary * delta.Imaginary;
            }
            symbols.Add(z);
            positions.Add(tau);
            errors.Add(e);
            v += ki * e;
            double step = Math.Min(Math.Max(sps - kp * e - v, sps / 2), 3 * sps / 2);
            tau += step;
        }
        return new TimingRecovery([.. symbols], [.. positions], [.. errors]);
    }

    /// <summary>Decision-directed QPSK carrier loop: a PI loop on the phase, one update per symbol
    /// (conventions: Synchronization, Tracking loops).</summary>
    /// <param name="symbols">QPSK symbols, all finite.</param>
    /// <param name="kp">Proportional gain, finite, not negative.</param>
    /// <param name="ki">Integral gain, finite, not negative.</param>
    /// <param name="phase">Phase removed from the first symbol, in radians, finite.</param>
    public static CarrierRecovery QpskCarrierTracking(ReadOnlySpan<Complex> symbols, double kp, double ki, double phase = 0) =>
        CarrierLoop(symbols, kp, ki, phase, static (re, im) => (re >= 0 ? 1 : -1, im >= 0 ? 1 : -1));

    /// <summary>Decision-directed 8-PSK carrier loop (conventions: Synchronization, Tracking
    /// loops).</summary>
    /// <param name="symbols">8-PSK symbols, all finite.</param>
    /// <param name="kp">Proportional gain, finite, not negative.</param>
    /// <param name="ki">Integral gain, finite, not negative.</param>
    /// <param name="phase">Phase removed from the first symbol, in radians, finite.</param>
    public static CarrierRecovery Psk8CarrierTracking(ReadOnlySpan<Complex> symbols, double kp, double ki, double phase = 0) =>
        CarrierLoop(symbols, kp, ki, phase, static (re, im) =>
            Psk8Points[(int)(((long)Math.Floor(Math.Atan2(im, re) / (Math.PI / 4) + 0.5) % 8 + 8) % 8)]);

    /// <summary>Decision-directed 16-QAM carrier loop (conventions: Synchronization, Tracking
    /// loops).</summary>
    /// <param name="symbols">16-QAM symbols, all finite.</param>
    /// <param name="kp">Proportional gain, finite, not negative.</param>
    /// <param name="ki">Integral gain, finite, not negative.</param>
    /// <param name="phase">Phase removed from the first symbol, in radians, finite.</param>
    public static CarrierRecovery Qam16CarrierTracking(ReadOnlySpan<Complex> symbols, double kp, double ki, double phase = 0) =>
        CarrierLoop(symbols, kp, ki, phase, static (re, im) => (Qam16Level(re), Qam16Level(im)));

    private static readonly double C8 = 1 / Math.Sqrt(2);
    private static readonly (double, double)[] Psk8Points =
        [(1, 0), (C8, C8), (0, 1), (-C8, C8), (-1, 0), (-C8, -C8), (0, -1), (C8, -C8)];
    private static readonly double InvSqrt10 = 1.0 / Math.Sqrt(10.0);
    private static readonly double Qam16Threshold = 2.0 / Math.Sqrt(10.0);

    private static double Qam16Level(double v)
    {
        double m = Math.Abs(v) < Qam16Threshold ? 1 : 3;
        return (v >= 0 ? m : -m) * InvSqrt10;
    }

    private static CarrierRecovery CarrierLoop(ReadOnlySpan<Complex> symbols, double kp, double ki, double phase,
        Func<double, double, (double Re, double Im)> decide)
    {
        foreach (Complex z in symbols)
            if (!double.IsFinite(z.Real) || !double.IsFinite(z.Imaginary))
                throw new ArgumentException("must be finite", nameof(symbols));
        NotNegativeFinite(kp, nameof(kp));
        NotNegativeFinite(ki, nameof(ki));
        if (!double.IsFinite(phase))
            throw new ArgumentOutOfRangeException(nameof(phase), phase, "must be finite");
        var output = new Complex[symbols.Length];
        var phases = new double[symbols.Length];
        var errors = new double[symbols.Length];
        double phi = phase, v = 0;
        for (int k = 0; k < symbols.Length; k++)
        {
            Complex z = symbols[k];
            double c = Math.Cos(phi), s = Math.Sin(phi);
            double re = z.Real * c + z.Imaginary * s;
            double im = z.Imaginary * c - z.Real * s;
            var (dre, dim) = decide(re, im);
            double e = dre * im - dim * re;
            output[k] = new Complex(re, im);
            phases[k] = phi;
            errors[k] = e;
            v += ki * e;
            phi = phi + kp * e + v;
        }
        return new CarrierRecovery(output, phases, errors);
    }

    private static void NotNegativeFinite(double x, string name)
    {
        if (!(x >= 0 && double.IsFinite(x)))
            throw new ArgumentOutOfRangeException(name, x, "must be finite and not negative");
    }

    /// <summary>Oerder–Meyr symbol timing estimate in samples, in [0, sps): the phase of the
    /// symbol-rate line in |y|².</summary>
    /// <param name="samples">Matched-filter output, at least one sample, all finite.</param>
    /// <param name="samplesPerSymbol">Samples per symbol, at least 2.</param>
    public static double TimingOffset(ReadOnlySpan<Complex> samples, int samplesPerSymbol)
    {
        ArgumentOutOfRangeException.ThrowIfLessThan(samplesPerSymbol, 2);
        double scale = CheckFinite(samples, 1, nameof(samples));
        Complex s = Complex.Zero;
        for (int n = 0; n < samples.Length; n++)
        {
            Complex y = samples[n] * scale;
            double p = y.Real * y.Real + y.Imaginary * y.Imaginary;
            s += p * Complex.FromPolarCoordinates(1, -2 * Math.PI * (n % samplesPerSymbol) / samplesPerSymbol);
        }
        double tau = -samplesPerSymbol * Arg(s) / (2 * Math.PI);
        if (tau < 0)
            tau += samplesPerSymbol;
        return tau >= samplesPerSymbol ? 0 : tau;
    }

    /// <summary>Carrier frequency offset of QPSK symbols in Hz, in (−Rs/8, Rs/8], from the mean phase
    /// step of z⁴.</summary>
    /// <param name="symbols">One complex value per symbol, at least two, all finite.</param>
    /// <param name="symbolRate">Symbol rate in Hz, positive and finite.</param>
    public static double QpskFrequencyOffset(ReadOnlySpan<Complex> symbols, double symbolRate)
    {
        Check.PositiveFinite(symbolRate, nameof(symbolRate));
        double scale = CheckFinite(symbols, 2, nameof(symbols));
        Complex s = Complex.Zero, prev = Fourth(symbols[0] * scale);
        for (int k = 1; k < symbols.Length; k++)
        {
            Complex w = Fourth(symbols[k] * scale);
            s += w * Complex.Conjugate(prev);
            prev = w;
        }
        return Arg(s) * symbolRate / (8 * Math.PI);
    }

    /// <summary>Carrier phase of QPSK symbols in radians, in (−π/4, π/4]; the true phase is this
    /// plus a multiple of π/2.</summary>
    /// <param name="symbols">One complex value per symbol, at least one, all finite.</param>
    public static double QpskPhaseOffset(ReadOnlySpan<Complex> symbols)
    {
        double scale = CheckFinite(symbols, 1, nameof(symbols));
        Complex s = Complex.Zero;
        foreach (var z in symbols)
            s += Fourth(z * scale);
        return Arg(-s) / 4;
    }

    /// <summary>QPSK carrier phase of each block of <paramref name="blockSymbols"/> symbols,
    /// unwrapped in steps of π/2: the first is in (−π/4, π/4], each later one within π/4 of the one
    /// before. A last, shorter block is included.</summary>
    /// <param name="symbols">One complex value per symbol, at least one, all finite.</param>
    /// <param name="blockSymbols">Symbols per block, at least 1.</param>
    public static double[] QpskBlockPhases(ReadOnlySpan<Complex> symbols, int blockSymbols)
    {
        ArgumentOutOfRangeException.ThrowIfLessThan(blockSymbols, 1);
        CheckFinite(symbols, 1, nameof(symbols));
        var phases = new double[(symbols.Length + blockSymbols - 1) / blockSymbols];
        for (int b = 0; b < phases.Length; b++)
        {
            int start = b * blockSymbols;
            double phi = QpskPhaseOffset(symbols.Slice(start, Math.Min(blockSymbols, symbols.Length - start)));
            if (b > 0)
                phi += Math.PI / 2 * Math.Round((phases[b - 1] - phi) / (Math.PI / 2));
            phases[b] = phi;
        }
        return phases;
    }

    private static Complex Fourth(Complex z)
    {
        Complex z2 = z * z;
        return z2 * z2;
    }

    /// <summary>Phase in (−π, π]; 0 for an exact zero.</summary>
    private static double Arg(Complex s)
    {
        if (s == Complex.Zero)
            return 0;
        double a = Math.Atan2(s.Imaginary, s.Real);
        return a == -Math.PI ? Math.PI : a;
    }

    /// <summary>Checks the length and that every value is finite; returns the power of two that
    /// brings the largest component into [0.5, 1). The estimates do not depend on scale, and the
    /// exact scaling keeps |z|⁴ from overflowing or underflowing.</summary>
    private static double CheckFinite(ReadOnlySpan<Complex> x, int minimum, string name)
    {
        if (x.Length < minimum)
            throw new ArgumentException($"needs at least {minimum} value(s)", name);
        double m = 0;
        foreach (var z in x)
        {
            if (!double.IsFinite(z.Real) || !double.IsFinite(z.Imaginary))
                throw new ArgumentException("values must be finite", name);
            m = Math.Max(m, Math.Max(Math.Abs(z.Real), Math.Abs(z.Imaginary)));
        }
        return m > 0 ? Math.ScaleB(1.0, -(Math.ILogB(m) + 1)) : 1.0;
    }
}
