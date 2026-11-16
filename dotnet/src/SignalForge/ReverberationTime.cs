using System.Numerics;

namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Schroeder backward-integrated energy decay <c>10·log10(E[n]/E[0])</c>,
    /// <c>E[n] = Σ_{k≥n} |h[k]|²</c> (conventions: Reverberation time; ADR 0171).</summary>
    /// <param name="impulseResponse">Complex response, finite, not empty, not all zero.</param>
    /// <returns>The decay in dB, one value per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] SchroederDecay(ReadOnlySpan<Complex> impulseResponse)
    {
        var p = new double[impulseResponse.Length];
        for (int n = 0; n < p.Length; n++)
        {
            Complex v = impulseResponse[n];
            if (!(double.IsFinite(v.Real) && double.IsFinite(v.Imaginary)))
                throw new ArgumentException("impulseResponse must be finite", nameof(impulseResponse));
            p[n] = v.Real * v.Real + v.Imaginary * v.Imaginary;
        }
        return Decay(p, nameof(impulseResponse));
    }

    /// <summary>The Schroeder backward-integrated energy decay <c>10·log10(E[n]/E[0])</c>,
    /// <c>E[n] = Σ_{k≥n} h[k]²</c> (conventions: Reverberation time; ADR 0171).</summary>
    /// <param name="impulseResponse">Real response, finite, not empty, not all zero.</param>
    /// <returns>The decay in dB, one value per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] SchroederDecay(ReadOnlySpan<double> impulseResponse)
    {
        var p = new double[impulseResponse.Length];
        for (int n = 0; n < p.Length; n++)
        {
            if (!double.IsFinite(impulseResponse[n]))
                throw new ArgumentException("impulseResponse must be finite", nameof(impulseResponse));
            p[n] = impulseResponse[n] * impulseResponse[n];
        }
        return Decay(p, nameof(impulseResponse));
    }

    /// <summary>The reverberation time <c>−60/m</c> from the least-squares slope <c>m</c> (dB/s)
    /// of the Schroeder decay between <paramref name="startDb"/> and <paramref name="stopDb"/>
    /// (conventions: Reverberation time; ADR 0171).</summary>
    /// <param name="impulseResponse">Complex response, finite, not empty, not all zero.</param>
    /// <param name="sampleRate">Sample rate in Hz, finite and positive.</param>
    /// <param name="startDb">The upper level of the fit, at most 0.</param>
    /// <param name="stopDb">The lower level of the fit, below <paramref name="startDb"/>.</param>
    /// <returns>The reverberation time in seconds.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double ReverberationTime(ReadOnlySpan<Complex> impulseResponse, double sampleRate,
        double startDb = -5, double stopDb = -25) =>
        FitDecay(SchroederDecay(impulseResponse), sampleRate, startDb, stopDb);

    /// <summary>The reverberation time <c>−60/m</c> from the least-squares slope <c>m</c> (dB/s)
    /// of the Schroeder decay between <paramref name="startDb"/> and <paramref name="stopDb"/>
    /// (conventions: Reverberation time; ADR 0171).</summary>
    /// <param name="impulseResponse">Real response, finite, not empty, not all zero.</param>
    /// <param name="sampleRate">Sample rate in Hz, finite and positive.</param>
    /// <param name="startDb">The upper level of the fit, at most 0.</param>
    /// <param name="stopDb">The lower level of the fit, below <paramref name="startDb"/>.</param>
    /// <returns>The reverberation time in seconds.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double ReverberationTime(ReadOnlySpan<double> impulseResponse, double sampleRate,
        double startDb = -5, double stopDb = -25) =>
        FitDecay(SchroederDecay(impulseResponse), sampleRate, startDb, stopDb);

    /// <summary>The early decay time: <see cref="ReverberationTime(ReadOnlySpan{Complex}, double, double, double)"/>
    /// fitted from 0 to −10 dB (conventions: Early decay time; ADR 0181).</summary>
    /// <param name="impulseResponse">Complex response, finite, not empty, not all zero.</param>
    /// <param name="sampleRate">Sample rate in Hz, finite and positive.</param>
    /// <returns>The early decay time in seconds.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double EarlyDecayTime(ReadOnlySpan<Complex> impulseResponse, double sampleRate) =>
        ReverberationTime(impulseResponse, sampleRate, 0, -10);

    /// <summary>The early decay time: <see cref="ReverberationTime(ReadOnlySpan{double}, double, double, double)"/>
    /// fitted from 0 to −10 dB (conventions: Early decay time; ADR 0181).</summary>
    /// <param name="impulseResponse">Real response, finite, not empty, not all zero.</param>
    /// <param name="sampleRate">Sample rate in Hz, finite and positive.</param>
    /// <returns>The early decay time in seconds.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double EarlyDecayTime(ReadOnlySpan<double> impulseResponse, double sampleRate) =>
        ReverberationTime(impulseResponse, sampleRate, 0, -10);

    /// <summary>The decay curvature <c>100·(T30/T20 − 1)</c> in percent (conventions: Decay
    /// curvature; ADR 0182).</summary>
    /// <param name="impulseResponse">Complex response, finite, not empty, not all zero.</param>
    /// <param name="sampleRate">Sample rate in Hz, finite and positive.</param>
    /// <returns>The curvature in percent, signed.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double DecayCurvature(ReadOnlySpan<Complex> impulseResponse, double sampleRate) =>
        Curvature(SchroederDecay(impulseResponse), sampleRate);

    /// <summary>The decay curvature <c>100·(T30/T20 − 1)</c> in percent (conventions: Decay
    /// curvature; ADR 0182).</summary>
    /// <param name="impulseResponse">Real response, finite, not empty, not all zero.</param>
    /// <param name="sampleRate">Sample rate in Hz, finite and positive.</param>
    /// <returns>The curvature in percent, signed.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double DecayCurvature(ReadOnlySpan<double> impulseResponse, double sampleRate) =>
        Curvature(SchroederDecay(impulseResponse), sampleRate);

    /// <summary>The decay time <c>−60/m</c> from the least-squares slope <c>m</c> (dB/s) of a
    /// supplied dB decay curve between <paramref name="startDb"/> and <paramref name="stopDb"/>
    /// (conventions: Decay time from a curve; ADR 0184).</summary>
    /// <param name="decay">The decay in dB, one value per sample; <c>−∞</c> allowed, NaN and
    /// <c>+∞</c> not; not empty.</param>
    /// <param name="sampleRate">Sample rate in Hz, finite and positive.</param>
    /// <param name="startDb">The upper level of the fit, at most 0.</param>
    /// <param name="stopDb">The lower level of the fit, below <paramref name="startDb"/>.</param>
    /// <returns>The decay time in seconds.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double DecayTime(ReadOnlySpan<double> decay, double sampleRate, double startDb = -5, double stopDb = -25)
    {
        if (decay.IsEmpty)
            throw new ArgumentException("decay must not be empty", nameof(decay));
        foreach (double v in decay)
        {
            if (double.IsNaN(v) || double.IsPositiveInfinity(v))
                throw new ArgumentException("decay must not hold NaN or +inf", nameof(decay));
        }
        return FitDecay(decay.ToArray(), sampleRate, startDb, stopDb);
    }

    private static double Curvature(double[] d, double sampleRate)
    {
        double t20 = FitDecay(d, sampleRate, -5, -25);
        double t30 = FitDecay(d, sampleRate, -5, -35);
        return 100 * (t30 / t20 - 1);
    }

    private static double[] Decay(double[] p, string paramName)
    {
        if (p.Length == 0)
            throw new ArgumentException("impulseResponse must not be empty", paramName);
        var energy = new double[p.Length];
        double sum = 0;
        for (int n = p.Length - 1; n >= 0; n--)
            energy[n] = sum += p[n];
        if (!(energy[0] > 0))
            throw new ArgumentException("impulseResponse must not be all zero", paramName);
        var d = new double[p.Length];
        for (int n = 0; n < p.Length; n++)
            d[n] = 10 * Math.Log10(energy[n] / energy[0]);
        return d;
    }

    private static double FitDecay(double[] d, double sampleRate, double startDb, double stopDb)
    {
        if (!(double.IsFinite(sampleRate) && sampleRate > 0))
            throw new ArgumentOutOfRangeException(nameof(sampleRate), sampleRate, "must be finite and positive");
        if (!(double.IsFinite(startDb) && double.IsFinite(stopDb) && stopDb < startDb && startDb <= 0))
            throw new ArgumentException("need stopDb < startDb <= 0, both finite", nameof(stopDb));
        int n1 = Array.FindIndex(d, v => v <= startDb), n2 = Array.FindIndex(d, v => v <= stopDb);
        if (n2 < 0)
            throw new ArgumentException("the decay never reaches stopDb", nameof(stopDb));
        if (n2 - n1 < 2)
            throw new ArgumentException("fewer than two samples lie between startDb and stopDb", nameof(stopDb));
        int count = n2 - n1;
        double meanN = 0, meanY = 0;
        for (int n = n1; n < n2; n++)
        {
            meanN += n;
            meanY += d[n];
        }
        meanN /= count;
        meanY /= count;
        double sxy = 0, sxx = 0;
        for (int n = n1; n < n2; n++)
        {
            sxy += (n - meanN) * (d[n] - meanY);
            sxx += (n - meanN) * (n - meanN);
        }
        double slope = sxy / sxx * sampleRate;
        if (!(slope < 0))
            throw new ArgumentException("the decay slope must be negative", nameof(stopDb));
        return -60.0 / slope;
    }
}
