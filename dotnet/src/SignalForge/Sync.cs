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

/// <summary>What an equalizer gave (conventions: Synchronization, LMS equalizer).</summary>
/// <param name="Symbols">The output symbols, one per <c>samples_per_symbol</c> input samples.</param>
/// <param name="Errors">The reference minus the output at each symbol, before the update; 0 where
/// there is no reference.</param>
/// <param name="Taps">The taps after the last output.</param>
public sealed record Equalization(Complex[] Symbols, Complex[] Errors, Complex[] Taps);

/// <summary>What a decision-feedback equalizer gave (conventions: Synchronization,
/// Decision-feedback equalizer).</summary>
/// <param name="Symbols">The output symbols, one per <c>samples_per_symbol</c> input samples.</param>
/// <param name="Errors">The reference minus the output at each symbol, before the update; 0 where
/// there is no reference.</param>
/// <param name="Taps">The forward taps after the last output.</param>
/// <param name="FeedbackTaps">The feedback taps after the last output, on the references one,
/// two, … symbols back.</param>
public sealed record DfeEqualization(Complex[] Symbols, Complex[] Errors, Complex[] Taps, Complex[] FeedbackTaps);

/// <summary>Equalizer taps (conventions: Synchronization, Least-squares equalizer taps).</summary>
/// <param name="Taps">The forward taps.</param>
/// <param name="FeedbackTaps">The feedback taps, on the references one, two, … symbols back.</param>
public sealed record DfeTaps(Complex[] Taps, Complex[] FeedbackTaps);

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

    /// <summary>Decision-directed 64-QAM carrier loop (conventions: Synchronization, Tracking
    /// loops; ADR 0053).</summary>
    /// <param name="symbols">64-QAM symbols, all finite.</param>
    /// <param name="kp">Proportional gain, finite, not negative.</param>
    /// <param name="ki">Integral gain, finite, not negative.</param>
    /// <param name="phase">Phase removed from the first symbol, in radians, finite.</param>
    public static CarrierRecovery Qam64CarrierTracking(ReadOnlySpan<Complex> symbols, double kp, double ki, double phase = 0) =>
        CarrierLoop(symbols, kp, ki, phase, static (re, im) => (Qam64Level(re), Qam64Level(im)));

    /// <summary>Normalized LMS equalizer, fractionally spaced, trained on known symbols and then on
    /// its own decisions (conventions: Synchronization, LMS equalizer; ADR 0066).</summary>
    /// <param name="samples">The input, at least one sample, all finite.</param>
    /// <param name="training">Known symbols for the first outputs, finite, at most the output
    /// count.</param>
    /// <param name="numTaps">Number of taps, at least 1.</param>
    /// <param name="step">Normalized step size, in [0, 2].</param>
    /// <param name="samplesPerSymbol">Input samples per output symbol, at least 1.</param>
    /// <param name="center">The tap that starts at 1, in [0, numTaps); null for (numTaps − 1)/2.</param>
    /// <param name="decision">After training, adapt to the hard decision of this modulation
    /// ("qpsk", "psk8", "qam16", "qam64"); null holds the taps.</param>
    /// <param name="initialTaps">The taps to start from, <paramref name="numTaps"/> finite values;
    /// null for the unit impulse at <paramref name="center"/> (ADR 0072).</param>
    public static Equalization LmsEqualizer(ReadOnlySpan<Complex> samples, ReadOnlySpan<Complex> training, int numTaps,
        double step, int samplesPerSymbol = 1, int? center = null, string? decision = null, Complex[]? initialTaps = null)
    {
        DfeEqualization r = Equalize(samples, training, numTaps, 0, step, samplesPerSymbol, center, decision, initialTaps, null, null);
        return new Equalization(r.Symbols, r.Errors, r.Taps);
    }

    /// <summary>Exponentially weighted recursive-least-squares equalizer, fractionally spaced,
    /// trained on known symbols and then on its own decisions (conventions: Synchronization, RLS
    /// equalizer; ADR 0076). Converges in a few times <paramref name="numTaps"/> symbols however
    /// the channel is conditioned.</summary>
    /// <param name="samples">The input, at least one sample, all finite.</param>
    /// <param name="training">Known symbols for the first outputs, at most the output count.</param>
    /// <param name="numTaps">Number of taps, at least 1.</param>
    /// <param name="forgetting">The forgetting factor λ, in (0, 1]; 1 is growing-window least
    /// squares.</param>
    /// <param name="delta">δ, finite and above 0: the inverse correlation starts at I/δ.</param>
    /// <param name="samplesPerSymbol">Input samples per output symbol, at least 1.</param>
    /// <param name="center">The tap that starts at 1, in [0, numTaps); null for (numTaps − 1)/2.</param>
    /// <param name="decision">After training, adapt to the hard decision of this modulation
    /// ("qpsk", "psk8", "qam16", "qam64"); null holds the taps.</param>
    /// <param name="initialTaps">The taps to start from, <paramref name="numTaps"/> finite values;
    /// null for the unit impulse at <paramref name="center"/>.</param>
    public static Equalization RlsEqualizer(ReadOnlySpan<Complex> samples, ReadOnlySpan<Complex> training, int numTaps,
        double forgetting, double delta = 0.01, int samplesPerSymbol = 1, int? center = null, string? decision = null,
        Complex[]? initialTaps = null)
    {
        int c = CheckEqualizer(samples, training, numTaps, 0, samplesPerSymbol, center);
        if (!(forgetting > 0 && forgetting <= 1))
            throw new ArgumentOutOfRangeException(nameof(forgetting), forgetting, "must be in (0, 1]");
        if (!(double.IsFinite(delta) && delta > 0))
            throw new ArgumentOutOfRangeException(nameof(delta), delta, "must be finite and above 0");
        Func<Complex, Complex>? decide = Decider(decision);
        Complex[] w;
        if (initialTaps is null)
        {
            w = new Complex[numTaps];
            w[c] = 1;
        }
        else
        {
            w = StartTaps(initialTaps, numTaps, nameof(initialTaps));
        }
        var p = new Complex[numTaps, numTaps];
        for (int i = 0; i < numTaps; i++)
            p[i, i] = 1 / delta;
        int n = (samples.Length + samplesPerSymbol - 1) / samplesPerSymbol;
        var u = new Complex[numTaps];
        var q = new Complex[numTaps];
        var g = new Complex[numTaps];
        var r = new Complex[numTaps];
        var output = new Complex[n];
        var errors = new Complex[n];
        for (int k = 0; k < n; k++)
        {
            int b = k * samplesPerSymbol + c;
            Complex y = Complex.Zero;
            for (int i = 0; i < numTaps; i++)
            {
                u[i] = b - i >= 0 && b - i < samples.Length ? samples[b - i] : Complex.Zero;
                y += w[i] * u[i];
            }
            output[k] = y;
            Complex? d = k < training.Length ? training[k] : decide?.Invoke(y);
            if (d is not { } dk)
                continue;
            Complex e = dk - y;
            errors[k] = e;
            double power = 0;
            for (int i = 0; i < numTaps; i++)
                power += (u[i].Real * u[i].Real) + (u[i].Imaginary * u[i].Imaginary);
            if (!(power > 0))
                continue;
            Complex s = forgetting;
            for (int i = 0; i < numTaps; i++)
            {
                Complex qi = Complex.Zero;
                for (int j = 0; j < numTaps; j++)
                    qi += p[i, j] * Complex.Conjugate(u[j]);
                q[i] = qi;
            }
            for (int i = 0; i < numTaps; i++)
                s += u[i] * q[i];
            for (int i = 0; i < numTaps; i++)
            {
                g[i] = q[i] / s;
                w[i] += g[i] * e;
            }
            for (int j = 0; j < numTaps; j++)
            {
                Complex rj = Complex.Zero;
                for (int i = 0; i < numTaps; i++)
                    rj += u[i] * p[i, j];
                r[j] = rj;
            }
            for (int i = 0; i < numTaps; i++)
                for (int j = 0; j < numTaps; j++)
                    p[i, j] = (p[i, j] - (g[i] * r[j])) / forgetting;
        }
        return new Equalization(output, errors, w);
    }

    /// <summary>Blind constant-modulus equalizer, normalized, fractionally spaced; its output
    /// keeps the channel's phase (conventions: Synchronization, Constant-modulus equalizer; ADR
    /// 0074).</summary>
    /// <param name="samples">The input, at least one sample, all finite.</param>
    /// <param name="numTaps">Number of taps, at least 1.</param>
    /// <param name="step">Normalized step size, in [0, 2].</param>
    /// <param name="samplesPerSymbol">Input samples per output symbol, at least 1.</param>
    /// <param name="center">The tap that starts at 1, in [0, numTaps); null for (numTaps − 1)/2.</param>
    /// <param name="modulus">The modulus R the output is pulled to, finite and above 0:
    /// E|a|⁴ / E|a|² of the constellation.</param>
    /// <param name="initialTaps">The taps to start from, <paramref name="numTaps"/> finite values;
    /// null for the unit impulse at <paramref name="center"/>.</param>
    public static Equalization CmaEqualizer(ReadOnlySpan<Complex> samples, int numTaps, double step,
        int samplesPerSymbol = 1, int? center = null, double modulus = 1.0, Complex[]? initialTaps = null)
    {
        int c = CheckEqualizer(samples, [], numTaps, 0, samplesPerSymbol, center);
        if (!(step >= 0 && step <= 2))
            throw new ArgumentOutOfRangeException(nameof(step), step, "must be in [0, 2]");
        if (!(double.IsFinite(modulus) && modulus > 0))
            throw new ArgumentOutOfRangeException(nameof(modulus), modulus, "must be finite and above 0");
        Complex[] w;
        if (initialTaps is null)
        {
            w = new Complex[numTaps];
            w[c] = 1;
        }
        else
        {
            w = StartTaps(initialTaps, numTaps, nameof(initialTaps));
        }
        int n = (samples.Length + samplesPerSymbol - 1) / samplesPerSymbol;
        var u = new Complex[numTaps];
        var output = new Complex[n];
        var errors = new Complex[n];
        for (int k = 0; k < n; k++)
        {
            int b = k * samplesPerSymbol + c;
            Complex y = Complex.Zero;
            for (int i = 0; i < numTaps; i++)
            {
                u[i] = b - i >= 0 && b - i < samples.Length ? samples[b - i] : Complex.Zero;
                y += w[i] * u[i];
            }
            output[k] = y;
            Complex e = y * (modulus - ((y.Real * y.Real) + (y.Imaginary * y.Imaginary)));
            errors[k] = e;
            double p = 0;
            for (int i = 0; i < numTaps; i++)
                p += (u[i].Real * u[i].Real) + (u[i].Imaginary * u[i].Imaginary);
            if (p > 0)
            {
                double g = step / p;
                for (int i = 0; i < numTaps; i++)
                    w[i] += g * e * Complex.Conjugate(u[i]);
            }
        }
        return new Equalization(output, errors, w);
    }

    /// <summary>Decision-feedback equalizer: the LMS equalizer plus feedback taps on the past
    /// references, one normalized LMS update over both (conventions: Synchronization,
    /// Decision-feedback equalizer; ADR 0069).</summary>
    /// <param name="samples">The input, at least one sample, all finite.</param>
    /// <param name="training">Known symbols for the first outputs, finite, at most the output
    /// count.</param>
    /// <param name="numTaps">Number of forward taps, at least 1.</param>
    /// <param name="numFeedback">Number of feedback taps, not negative; with any, every output
    /// needs a reference (a <paramref name="decision"/>, or training for all of them).</param>
    /// <param name="step">Normalized step size, in [0, 2].</param>
    /// <param name="samplesPerSymbol">Input samples per output symbol, at least 1.</param>
    /// <param name="center">The forward tap that starts at 1, in [0, numTaps); null for
    /// (numTaps − 1)/2.</param>
    /// <param name="decision">After training, adapt to the hard decision of this modulation
    /// ("qpsk", "psk8", "qam16", "qam64"); null holds the taps.</param>
    /// <param name="initialTaps">The forward taps to start from, <paramref name="numTaps"/> finite
    /// values; null for the unit impulse at <paramref name="center"/> (ADR 0072).</param>
    /// <param name="initialFeedback">The feedback taps to start from, <paramref name="numFeedback"/>
    /// finite values; null for zeros.</param>
    /// <param name="phaseLoopGains">(kp, ki) of a second-order carrier loop on the forward part,
    /// finite, not negative; null for none (ADR 0073).</param>
    /// <param name="pilots">Known symbols at the pilot outputs, ⌊(N − T)/K⌋ finite values, with
    /// <paramref name="pilotInterval"/>; they are references there and correct the loop's cycle
    /// slips. Need <paramref name="phaseLoopGains"/> and <paramref name="decision"/>; null for none
    /// (ADR 0075).</param>
    /// <param name="pilotInterval">K, at least 1: output n ≥ T is a pilot when (n − T) mod K =
    /// K − 1; null for none, with <paramref name="pilots"/>.</param>
    /// <param name="slipWindow">Pilots summed per slip correction, at least 1.</param>
    public static DfeEqualization DfeEqualizer(ReadOnlySpan<Complex> samples, ReadOnlySpan<Complex> training, int numTaps,
        int numFeedback, double step, int samplesPerSymbol = 1, int? center = null, string? decision = null,
        Complex[]? initialTaps = null, Complex[]? initialFeedback = null, (double Kp, double Ki)? phaseLoopGains = null,
        Complex[]? pilots = null, int? pilotInterval = null, int slipWindow = 2) =>
        Equalize(samples, training, numTaps, numFeedback, step, samplesPerSymbol, center, decision, initialTaps, initialFeedback,
            phaseLoopGains, pilots, pilotInterval, slipWindow);

    /// <summary>The forward and feedback taps that minimize the squared error over the training,
    /// by Gaussian elimination on the normal equations (conventions: Synchronization, Least-squares
    /// equalizer taps; ADR 0072).</summary>
    /// <param name="samples">The input, at least one sample, all finite.</param>
    /// <param name="training">Known symbols for the first outputs, finite, at least
    /// <paramref name="numTaps"/> + <paramref name="numFeedback"/> and at most the output count.</param>
    /// <param name="numTaps">Number of forward taps, at least 1.</param>
    /// <param name="numFeedback">Number of feedback taps, not negative.</param>
    /// <param name="samplesPerSymbol">Input samples per output symbol, at least 1.</param>
    /// <param name="center">The forward tap on the output's own sample, in [0, numTaps); null for
    /// (numTaps − 1)/2.</param>
    /// <exception cref="ArgumentException">Also when the training does not determine the taps (a
    /// zero pivot).</exception>
    public static DfeTaps DfeLeastSquares(ReadOnlySpan<Complex> samples, ReadOnlySpan<Complex> training, int numTaps,
        int numFeedback, int samplesPerSymbol = 1, int? center = null)
    {
        int c = CheckEqualizer(samples, training, numTaps, numFeedback, samplesPerSymbol, center);
        int kAll = numTaps + numFeedback;
        if (training.Length < kAll)
            throw new ArgumentException("needs at least numTaps + numFeedback symbols", nameof(training));
        var g = new Complex[kAll][];
        for (int k = 0; k < kAll; k++)
            g[k] = new Complex[kAll];
        var h = new Complex[kAll];
        var v = new Complex[kAll];
        for (int n = 0; n < training.Length; n++)
        {
            int b = n * samplesPerSymbol + c;
            for (int i = 0; i < numTaps; i++)
                v[i] = b - i >= 0 && b - i < samples.Length ? samples[b - i] : Complex.Zero;
            for (int j = 1; j <= numFeedback; j++)
                v[numTaps + j - 1] = n - j >= 0 ? training[n - j] : Complex.Zero;
            for (int k = 0; k < kAll; k++)
            {
                Complex ck = Complex.Conjugate(v[k]);
                for (int l = 0; l < kAll; l++)
                    g[k][l] += ck * v[l];
                h[k] += ck * training[n];
            }
        }
        for (int k = 0; k < kAll; k++)
        {
            int r = k;
            double big = -1;
            for (int i = k; i < kAll; i++)
            {
                double mag = g[i][k].Real * g[i][k].Real + g[i][k].Imaginary * g[i][k].Imaginary;
                if (mag > big)
                {
                    r = i;
                    big = mag;
                }
            }
            if (big == 0)
                throw new ArgumentException("the training does not determine the taps", nameof(training));
            (g[k], g[r]) = (g[r], g[k]);
            (h[k], h[r]) = (h[r], h[k]);
            for (int i = k + 1; i < kAll; i++)
            {
                Complex f = g[i][k] / g[k][k];
                for (int l = k + 1; l < kAll; l++)
                    g[i][l] -= f * g[k][l];
                h[i] -= f * h[k];
            }
        }
        var th = new Complex[kAll];
        for (int k = kAll - 1; k >= 0; k--)
        {
            Complex acc = h[k];
            for (int l = k + 1; l < kAll; l++)
                acc -= g[k][l] * th[l];
            th[k] = acc / g[k][k];
        }
        return new DfeTaps(th[..numTaps], th[numTaps..]);
    }

    private static int CheckEqualizer(ReadOnlySpan<Complex> samples, ReadOnlySpan<Complex> training, int numTaps,
        int numFeedback, int samplesPerSymbol, int? center)
    {
        if (samples.IsEmpty)
            throw new ArgumentException("needs at least 1 sample", nameof(samples));
        foreach (Complex z in samples)
            if (!double.IsFinite(z.Real) || !double.IsFinite(z.Imaginary))
                throw new ArgumentException("must be finite", nameof(samples));
        foreach (Complex z in training)
            if (!double.IsFinite(z.Real) || !double.IsFinite(z.Imaginary))
                throw new ArgumentException("must be finite", nameof(training));
        ArgumentOutOfRangeException.ThrowIfLessThan(numTaps, 1);
        ArgumentOutOfRangeException.ThrowIfLessThan(samplesPerSymbol, 1);
        int c = center ?? (numTaps - 1) / 2;
        if (c < 0 || c >= numTaps)
            throw new ArgumentOutOfRangeException(nameof(center), center, "must be in [0, numTaps)");
        ArgumentOutOfRangeException.ThrowIfNegative(numFeedback);
        int n = (samples.Length + samplesPerSymbol - 1) / samplesPerSymbol;
        if (training.Length > n)
            throw new ArgumentException($"must be at most {n} symbols (the output count)", nameof(training));
        return c;
    }

    private static Complex[] StartTaps(Complex[] values, int size, string name)
    {
        if (values.Length != size)
            throw new ArgumentException($"must hold {size} values", name);
        foreach (Complex z in values)
            if (!double.IsFinite(z.Real) || !double.IsFinite(z.Imaginary))
                throw new ArgumentException("must be finite", name);
        return (Complex[])values.Clone();
    }

    private static Func<Complex, Complex>? Decider(string? decision) => decision switch
    {
        null => null,
        "qpsk" => static y => Modulation.QpskMap(Modulation.QpskDemapHard([y]))[0],
        "psk8" => static y => Modulation.Psk8Map(Modulation.Psk8DemapHard([y]))[0],
        "qam16" => static y => Modulation.Qam16Map(Modulation.Qam16DemapHard([y]))[0],
        "qam64" => static y => Modulation.Qam64Map(Modulation.Qam64DemapHard([y]))[0],
        _ => throw new ArgumentException("must be null, qpsk, psk8, qam16 or qam64", nameof(decision)),
    };

    private static DfeEqualization Equalize(ReadOnlySpan<Complex> samples, ReadOnlySpan<Complex> training, int numTaps,
        int numFeedback, double step, int samplesPerSymbol, int? center, string? decision, Complex[]? initialTaps,
        Complex[]? initialFeedback, (double Kp, double Ki)? loop, Complex[]? pilots = null, int? pilotInterval = null,
        int slipWindow = 2)
    {
        if (loop is { } lg && !(double.IsFinite(lg.Kp) && double.IsFinite(lg.Ki) && lg.Kp >= 0 && lg.Ki >= 0))
            throw new ArgumentOutOfRangeException(nameof(loop), lg, "phase loop gains must be finite and not negative");
        int c = CheckEqualizer(samples, training, numTaps, numFeedback, samplesPerSymbol, center);
        if (!(step >= 0 && step <= 2))
            throw new ArgumentOutOfRangeException(nameof(step), step, "must be in [0, 2]");
        Func<Complex, Complex>? decide = Decider(decision);
        int n = (samples.Length + samplesPerSymbol - 1) / samplesPerSymbol;
        if (numFeedback > 0 && decide is null && training.Length < n)
            throw new ArgumentException("with feedback taps, needs a decision or training for every output", nameof(decision));
        if ((pilots is null) != (pilotInterval is null))
            throw new ArgumentException("pilots and pilotInterval go together", nameof(pilots));
        if (slipWindow < 1)
            throw new ArgumentOutOfRangeException(nameof(slipWindow), slipWindow, "must be at least 1");
        int kp = 0;
        Complex[] known = [];
        if (pilots is not null && pilotInterval is { } interval)
        {
            if (interval < 1)
                throw new ArgumentOutOfRangeException(nameof(pilotInterval), interval, "must be at least 1");
            if (loop is null || decide is null)
                throw new ArgumentException("pilots need phaseLoopGains and decision", nameof(pilots));
            kp = interval;
            known = StartTaps(pilots, Math.Max(n - training.Length, 0) / kp, nameof(pilots));
        }
        double sigma = decision == "psk8" ? Math.PI / 4 : Math.PI / 2;
        Complex sp = Complex.Zero;
        int cp = 0;
        var fb = initialFeedback is null ? new Complex[numFeedback] : StartTaps(initialFeedback, numFeedback, nameof(initialFeedback));
        var past = new Complex[numFeedback]; // past[j - 1] is d_{k-j}
        Complex[] w;
        if (initialTaps is null)
        {
            w = new Complex[numTaps];
            w[c] = Complex.One;
        }
        else
        {
            w = StartTaps(initialTaps, numTaps, nameof(initialTaps));
        }
        var u = new Complex[numTaps];
        var output = new Complex[n];
        var errors = new Complex[n];
        double theta = 0, nu = 0;
        for (int k = 0; k < n; k++)
        {
            int b = k * samplesPerSymbol + c;
            Complex v = Complex.Zero;
            for (int i = 0; i < numTaps; i++)
            {
                u[i] = b - i >= 0 && b - i < samples.Length ? samples[b - i] : Complex.Zero;
                v += w[i] * u[i];
            }
            var rot = new Complex(Math.Cos(theta), -Math.Sin(theta));
            Complex y = loop is null ? v : v * rot;
            for (int j = 0; j < numFeedback; j++)
                y += fb[j] * past[j];
            output[k] = y;
            bool pilot = kp > 0 && k >= training.Length && (k - training.Length) % kp == kp - 1;
            Complex? d = k < training.Length ? training[k] : pilot ? known[(k - training.Length) / kp] : decide?.Invoke(y);
            if (d is not { } r)
                continue;
            Complex e = r - y;
            errors[k] = e;
            Complex f = Complex.Zero;
            for (int j = 0; j < numFeedback; j++)
                f += fb[j] * past[j];
            double p = 0;
            foreach (Complex x in u)
                p += x.Real * x.Real + x.Imaginary * x.Imaginary;
            foreach (Complex x in past)
                p += x.Real * x.Real + x.Imaginary * x.Imaginary;
            if (p > 0)
            {
                double g = step / p;
                Complex ef = loop is null ? e : e * Complex.Conjugate(rot);
                for (int i = 0; i < numTaps; i++)
                    w[i] += g * ef * Complex.Conjugate(u[i]);
                for (int j = 0; j < numFeedback; j++)
                    fb[j] += g * e * Complex.Conjugate(past[j]);
            }
            if (loop is { } gains)
            {
                Complex q = r - f;
                Complex cc = v * rot * Complex.Conjugate(q);
                double ph = v != Complex.Zero && q != Complex.Zero ? Math.Atan2(cc.Imaginary, cc.Real) : 0;
                nu += gains.Ki * ph;
                theta += gains.Kp * ph + nu;
            }
            if (pilot)
            {
                sp += y * Complex.Conjugate(r);
                if (++cp == slipWindow)
                {
                    theta += Math.Round(Math.Atan2(sp.Imaginary, sp.Real) / sigma) * sigma;
                    sp = Complex.Zero;
                    cp = 0;
                }
            }
            if (numFeedback > 0)
            {
                Array.Copy(past, 0, past, 1, numFeedback - 1);
                past[0] = r;
            }
        }
        return new DfeEqualization(output, errors, w, fb);
    }

    private static readonly double InvSqrt42 = 1.0 / Math.Sqrt(42.0);
    private static readonly double Qam64T2 = 2.0 / Math.Sqrt(42.0);
    private static readonly double Qam64T4 = 4.0 / Math.Sqrt(42.0);
    private static readonly double Qam64T6 = 6.0 / Math.Sqrt(42.0);

    private static double Qam64Level(double v)
    {
        double a = Math.Abs(v);
        double m = 4.0 + (a < Qam64T4 ? -1.0 : 1.0) * (a > Qam64T2 && a < Qam64T6 ? 1.0 : 3.0);
        return (v < 0 ? -m : m) * InvSqrt42;
    }

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

    /// <summary>Carrier frequency offset in Hz, in (−Rs/(2p), Rs/(2p)], from the peak of the
    /// spectrum of zᵖ (conventions: Synchronization; ADR 0049). Works for any constellation whose
    /// p-th power has a non-zero mean: QPSK and 16-QAM at 4, 8-PSK at 8.</summary>
    /// <param name="symbols">One complex value per symbol, at least two, all finite.</param>
    /// <param name="symbolRate">Symbol rate in Hz, positive and finite.</param>
    /// <param name="power">The power p, from 1 to 16.</param>
    public static double PowerFrequencyOffset(ReadOnlySpan<Complex> symbols, double symbolRate, int power)
    {
        Check.PositiveFinite(symbolRate, nameof(symbolRate));
        ArgumentOutOfRangeException.ThrowIfLessThan(power, 1);
        ArgumentOutOfRangeException.ThrowIfGreaterThan(power, 16);
        double scale = CheckFinite(symbols, 2, nameof(symbols));
        int n = symbols.Length;
        var w = new Complex[n];
        for (int k = 0; k < n; k++)
        {
            Complex z = symbols[k] * scale, v = z;
            for (int j = 1; j < power; j++)
                v *= z;
            w[k] = v;
        }
        int big = 1;
        while (big < 4 * n)
            big *= 2;
        var padded = new Complex[big];
        w.CopyTo(padded, 0);
        Complex[] spectrum = Spectral.Fft(padded);
        int i = 0;
        double best = 0;
        for (int b = 0; b < big; b++)
        {
            double p = spectrum[b].Real * spectrum[b].Real + spectrum[b].Imaginary * spectrum[b].Imaginary;
            if (p > best)
            {
                best = p;
                i = b;
            }
        }
        if (!(best > 0))
            return 0;
        if (i > big / 2)
            i -= big;
        double lo = (i - 1) / (double)big, hi = (i + 1) / (double)big;
        for (int step = 0; step < 60; step++)
        {
            double m = (lo + hi) / 2;
            if (Slope(w, m) > 0)
                lo = m;
            else
                hi = m;
        }
        double nu = (lo + hi) / 2;
        if (nu > 0.5)
            nu -= 1;
        else if (nu <= -0.5)
            nu += 1;
        return nu * symbolRate / power;
    }

    /// <summary>S.re·T.im − S.im·T.re with S = Σ w[k]·e^{−j2πνk}, T = Σ k·w[k]·e^{−j2πνk}: the sign
    /// of the periodogram's slope at ν.</summary>
    private static double Slope(Complex[] w, double nu)
    {
        Complex s = Complex.Zero, t = Complex.Zero;
        for (int k = 0; k < w.Length; k++)
        {
            double a = -2 * Math.PI * nu * k;
            Complex v = w[k] * new Complex(Math.Cos(a), Math.Sin(a));
            s += v;
            t += k * v;
        }
        return s.Real * t.Imaginary - s.Imaginary * t.Real;
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

    /// <summary>Carrier phase of 8-PSK symbols in radians, in (−π/8, π/8]; the true phase is this
    /// plus a multiple of π/4 (conventions: Synchronization; ADR 0051).</summary>
    /// <param name="symbols">One complex value per symbol, at least one, all finite.</param>
    public static double Psk8PhaseOffset(ReadOnlySpan<Complex> symbols)
    {
        double scale = CheckFinite(symbols, 1, nameof(symbols));
        Complex s = Complex.Zero;
        foreach (var z in symbols)
        {
            Complex z4 = Fourth(z * scale);
            s += z4 * z4;
        }
        return Arg(s) / 8;
    }

    /// <summary>8-PSK carrier phase of each block of <paramref name="blockSymbols"/> symbols,
    /// unwrapped in steps of π/4: the first is in (−π/8, π/8], each later one within π/8 of the one
    /// before. A last, shorter block is included.</summary>
    /// <param name="symbols">One complex value per symbol, at least one, all finite.</param>
    /// <param name="blockSymbols">Symbols per block, at least 1.</param>
    public static double[] Psk8BlockPhases(ReadOnlySpan<Complex> symbols, int blockSymbols)
    {
        ArgumentOutOfRangeException.ThrowIfLessThan(blockSymbols, 1);
        CheckFinite(symbols, 1, nameof(symbols));
        var phases = new double[(symbols.Length + blockSymbols - 1) / blockSymbols];
        for (int b = 0; b < phases.Length; b++)
        {
            int start = b * blockSymbols;
            double phi = Psk8PhaseOffset(symbols.Slice(start, Math.Min(blockSymbols, symbols.Length - start)));
            if (b > 0)
                phi += Math.PI / 4 * Math.Round((phases[b - 1] - phi) / (Math.PI / 4));
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
