using System.Numerics;

namespace SignalForge;

/// <summary>Symbol mapping, FSK and OFDM. Definitions in docs/conventions.md.</summary>
public static class Modulation
{
    private static readonly double InvSqrt2 = 1.0 / Math.Sqrt(2.0);

    /// <summary>Gray-coded QPSK: bit pair (b0, b1) to ((1−2·b0) + j·(1−2·b1)) / √2.</summary>
    public static Complex[] QpskMap(ReadOnlySpan<byte> bits)
    {
        if (bits.Length % 2 != 0)
            throw new ArgumentException("QPSK needs an even number of bits", nameof(bits));
        var symbols = new Complex[bits.Length / 2];
        for (int s = 0; s < symbols.Length; s++)
        {
            byte b0 = bits[2 * s], b1 = bits[2 * s + 1];
            if (b0 > 1 || b1 > 1)
                throw new ArgumentException("bits must be 0 or 1", nameof(bits));
            symbols[s] = new Complex((1.0 - 2.0 * b0) * InvSqrt2, (1.0 - 2.0 * b1) * InvSqrt2);
        }
        return symbols;
    }

    /// <summary>Hard-decision QPSK demapping: bit is 1 where I (or Q) is negative; exactly 0 gives 0.</summary>
    public static byte[] QpskDemapHard(ReadOnlySpan<Complex> symbols)
    {
        var bits = new byte[2 * symbols.Length];
        for (int s = 0; s < symbols.Length; s++)
        {
            bits[2 * s] = symbols[s].Real < 0 ? (byte)1 : (byte)0;
            bits[2 * s + 1] = symbols[s].Imaginary < 0 ? (byte)1 : (byte)0;
        }
        return bits;
    }

    private static readonly double InvSqrt10 = 1.0 / Math.Sqrt(10.0);
    private static readonly double Qam16Threshold = 2.0 / Math.Sqrt(10.0);
    private static readonly double InvSqrt42 = 1.0 / Math.Sqrt(42.0);
    private static readonly double Qam64T2 = 2.0 / Math.Sqrt(42.0);
    private static readonly double Qam64T4 = 4.0 / Math.Sqrt(42.0);
    private static readonly double Qam64T6 = 6.0 / Math.Sqrt(42.0);

    private static int Label(ReadOnlySpan<byte> bits, int start, int k)
    {
        int m = 0;
        for (int i = 0; i < k; i++)
        {
            byte b = bits[start + i];
            if (b > 1)
                throw new ArgumentException("bits must be 0 or 1", nameof(bits));
            m = 2 * m + b;
        }
        return m;
    }

    private static void NotNaN(ReadOnlySpan<Complex> symbols)
    {
        foreach (Complex s in symbols)
            if (double.IsNaN(s.Real) || double.IsNaN(s.Imaginary))
                throw new ArgumentException("symbols must not be NaN", nameof(symbols));
    }

    private static void CheckLength(ReadOnlySpan<byte> bits, int k, string name)
    {
        if (bits.Length % k != 0)
            throw new ArgumentException($"{name} needs a multiple of {k} bits", nameof(bits));
    }

    /// <summary>Gray-coded 8-PSK: label m (3 bits, MSB first) to e^{jπp/4} where p ⊕ (p &gt;&gt; 1) = m
    /// (conventions: Bits and symbols).</summary>
    /// <param name="bits">Bits, 0 or 1, a multiple of 3.</param>
    public static Complex[] Psk8Map(ReadOnlySpan<byte> bits)
    {
        CheckLength(bits, 3, "8-PSK");
        var symbols = new Complex[bits.Length / 3];
        for (int s = 0; s < symbols.Length; s++)
        {
            int m = Label(bits, 3 * s, 3);
            int p = m ^ (m >> 1) ^ (m >> 2);
            symbols[s] = Complex.FromPolarCoordinates(1, Math.PI / 4 * p);
        }
        return symbols;
    }

    /// <summary>Hard-decision 8-PSK: the nearest point's label; 0 decides 000.</summary>
    /// <param name="symbols">Received symbols, not NaN.</param>
    public static byte[] Psk8DemapHard(ReadOnlySpan<Complex> symbols)
    {
        NotNaN(symbols);
        var bits = new byte[3 * symbols.Length];
        for (int s = 0; s < symbols.Length; s++)
        {
            double sector = Math.Floor(Math.Atan2(symbols[s].Imaginary, symbols[s].Real) / (Math.PI / 4) + 0.5);
            int p = (((int)sector % 8) + 8) % 8;
            int m = p ^ (p >> 1);
            for (int i = 0; i < 3; i++)
                bits[3 * s + i] = (byte)((m >> (2 - i)) & 1);
        }
        return bits;
    }

    /// <summary>Gray-coded 16-QAM: I from (b0, b1), Q from (b2, b3), each (1 − 2·first)·(3 − 2·second),
    /// over √10 (conventions: Bits and symbols).</summary>
    /// <param name="bits">Bits, 0 or 1, a multiple of 4.</param>
    public static Complex[] Qam16Map(ReadOnlySpan<byte> bits)
    {
        CheckLength(bits, 4, "16-QAM");
        var symbols = new Complex[bits.Length / 4];
        for (int s = 0; s < symbols.Length; s++)
        {
            int m = Label(bits, 4 * s, 4);
            double i = (1 - 2 * ((m >> 3) & 1)) * (3 - 2 * ((m >> 2) & 1));
            double q = (1 - 2 * ((m >> 1) & 1)) * (3 - 2 * (m & 1));
            symbols[s] = new Complex(i * InvSqrt10, q * InvSqrt10);
        }
        return symbols;
    }

    /// <summary>Hard-decision 16-QAM: per component v, first bit v &lt; 0, second |v| &lt; 2/√10.</summary>
    /// <param name="symbols">Received symbols, not NaN.</param>
    public static byte[] Qam16DemapHard(ReadOnlySpan<Complex> symbols)
    {
        NotNaN(symbols);
        var bits = new byte[4 * symbols.Length];
        for (int s = 0; s < symbols.Length; s++)
        {
            double i = symbols[s].Real, q = symbols[s].Imaginary;
            bits[4 * s] = i < 0 ? (byte)1 : (byte)0;
            bits[4 * s + 1] = Math.Abs(i) < Qam16Threshold ? (byte)1 : (byte)0;
            bits[4 * s + 2] = q < 0 ? (byte)1 : (byte)0;
            bits[4 * s + 3] = Math.Abs(q) < Qam16Threshold ? (byte)1 : (byte)0;
        }
        return bits;
    }

    /// <summary>Gray-coded 64-QAM: I from (b0, b1, b2), Q from (b3, b4, b5), each
    /// (1 − 2·a)·(4 + (1 − 2·b)·(3 − 2·c)), over √42 (conventions: Bits and symbols; ADR 0052).</summary>
    /// <param name="bits">Bits, 0 or 1, a multiple of 6.</param>
    public static Complex[] Qam64Map(ReadOnlySpan<byte> bits)
    {
        CheckLength(bits, 6, "64-QAM");
        var symbols = new Complex[bits.Length / 6];
        for (int s = 0; s < symbols.Length; s++)
        {
            int m = Label(bits, 6 * s, 6);
            symbols[s] = new Complex(Pam8(m >> 3) * InvSqrt42, Pam8(m & 7) * InvSqrt42);
        }
        return symbols;
    }

    private static double Pam8(int g) =>
        (1 - 2 * ((g >> 2) & 1)) * (4 + (1 - 2 * ((g >> 1) & 1)) * (3 - 2 * (g & 1)));

    /// <summary>Hard-decision 64-QAM: per component v with a = |v|, bits v &lt; 0, a &lt; 4/√42 and
    /// 2/√42 &lt; a &lt; 6/√42.</summary>
    /// <param name="symbols">Received symbols, not NaN.</param>
    public static byte[] Qam64DemapHard(ReadOnlySpan<Complex> symbols)
    {
        NotNaN(symbols);
        var bits = new byte[6 * symbols.Length];
        for (int s = 0; s < symbols.Length; s++)
        {
            for (int j = 0; j < 2; j++)
            {
                double v = j == 0 ? symbols[s].Real : symbols[s].Imaginary, a = Math.Abs(v);
                bits[6 * s + 3 * j] = v < 0 ? (byte)1 : (byte)0;
                bits[6 * s + 3 * j + 1] = a < Qam64T4 ? (byte)1 : (byte)0;
                bits[6 * s + 3 * j + 2] = a > Qam64T2 && a < Qam64T6 ? (byte)1 : (byte)0;
            }
        }
        return bits;
    }

    private static byte[] LabelBits(int k)
    {
        var bits = new byte[k << k];
        for (int m = 0; m < 1 << k; m++)
            for (int i = 0; i < k; i++)
                bits[m * k + i] = (byte)((m >> (k - 1 - i)) & 1);
        return bits;
    }

    private static readonly Complex[] QpskPoints = QpskMap(LabelBits(2));
    private static readonly Complex[] Psk8Points = Psk8Map(LabelBits(3));
    private static readonly Complex[] Qam16Points = Qam16Map(LabelBits(4));
    private static readonly Complex[] Qam64Points = Qam64Map(LabelBits(6));

    /// <summary>Max-log LLRs of QPSK, positive for bit 0 (conventions: Bits and symbols, Soft
    /// demapping).</summary>
    /// <param name="symbols">Received symbols, finite.</param>
    /// <param name="noiseVariance">N0 = E|n|² of the complex noise, positive and finite.</param>
    public static double[] QpskDemapLlr(ReadOnlySpan<Complex> symbols, double noiseVariance) =>
        DemapLlr(symbols, noiseVariance, QpskPoints, 2);

    /// <summary>Max-log LLRs of 8-PSK, positive for bit 0 (conventions: Bits and symbols, Soft
    /// demapping).</summary>
    /// <param name="symbols">Received symbols, finite.</param>
    /// <param name="noiseVariance">N0 = E|n|² of the complex noise, positive and finite.</param>
    public static double[] Psk8DemapLlr(ReadOnlySpan<Complex> symbols, double noiseVariance) =>
        DemapLlr(symbols, noiseVariance, Psk8Points, 3);

    /// <summary>Max-log LLRs of 16-QAM, positive for bit 0 (conventions: Bits and symbols, Soft
    /// demapping).</summary>
    /// <param name="symbols">Received symbols, finite.</param>
    /// <param name="noiseVariance">N0 = E|n|² of the complex noise, positive and finite.</param>
    public static double[] Qam16DemapLlr(ReadOnlySpan<Complex> symbols, double noiseVariance) =>
        DemapLlr(symbols, noiseVariance, Qam16Points, 4);

    /// <summary>Max-log LLRs of 64-QAM, six per symbol, positive for bit 0 (conventions: Soft
    /// demapping).</summary>
    /// <param name="symbols">Received symbols, all finite.</param>
    /// <param name="noiseVariance">N0 = E|n|², positive and finite.</param>
    public static double[] Qam64DemapLlr(ReadOnlySpan<Complex> symbols, double noiseVariance) =>
        DemapLlr(symbols, noiseVariance, Qam64Points, 6);

    private static double[] DemapLlr(ReadOnlySpan<Complex> symbols, double noiseVariance, Complex[] points, int k)
    {
        if (!(noiseVariance > 0 && double.IsFinite(noiseVariance)))
            throw new ArgumentOutOfRangeException(nameof(noiseVariance), noiseVariance, "must be positive and finite");
        foreach (Complex s in symbols)
            if (!double.IsFinite(s.Real) || !double.IsFinite(s.Imaginary))
                throw new ArgumentException("symbols must be finite", nameof(symbols));
        var llr = new double[k * symbols.Length];
        Span<double> min0 = stackalloc double[k], min1 = stackalloc double[k];
        for (int n = 0; n < symbols.Length; n++)
        {
            min0.Fill(double.PositiveInfinity);
            min1.Fill(double.PositiveInfinity);
            for (int m = 0; m < points.Length; m++)
            {
                double dr = symbols[n].Real - points[m].Real, di = symbols[n].Imaginary - points[m].Imaginary;
                double d2 = dr * dr + di * di;
                for (int i = 0; i < k; i++)
                {
                    Span<double> mins = ((m >> (k - 1 - i)) & 1) == 1 ? min1 : min0;
                    if (d2 < mins[i])
                        mins[i] = d2;
                }
            }
            for (int i = 0; i < k; i++)
                llr[n * k + i] = (min1[i] - min0[i]) / noiseVariance;
        }
        return llr;
    }

    private static int FskBits(int order, int samplesPerSymbol, double modulationIndex)
    {
        int k = order switch
        {
            2 => 1,
            4 => 2,
            8 => 3,
            16 => 4,
            _ => throw new ArgumentException("order must be 2, 4, 8 or 16", nameof(order)),
        };
        if (samplesPerSymbol < 1)
            throw new ArgumentException("samplesPerSymbol must be at least 1", nameof(samplesPerSymbol));
        Check.PositiveFinite(modulationIndex, nameof(modulationIndex));
        return k;
    }

    /// <summary>Continuous-phase M-FSK, natural binary labels, tone levels 2m − (M − 1) at a·h/2 cycles
    /// per symbol (conventions: Bits and symbols, FSK; ADR 0054).</summary>
    /// <param name="bits">Bits, 0 or 1, a multiple of log2(order).</param>
    /// <param name="order">2, 4, 8 or 16.</param>
    /// <param name="samplesPerSymbol">Samples per symbol, at least 1.</param>
    /// <param name="modulationIndex">Tone spacing in symbol rates, positive and finite.</param>
    public static Complex[] FskModulate(ReadOnlySpan<byte> bits, int order, int samplesPerSymbol, double modulationIndex)
    {
        int k = FskBits(order, samplesPerSymbol, modulationIndex);
        CheckLength(bits, k, $"{order}-FSK");
        int sps = samplesPerSymbol;
        var samples = new Complex[bits.Length / k * sps];
        long start = 0;
        for (int i = 0; i < bits.Length / k; i++)
        {
            long a = 2L * Label(bits, k * i, k) - (order - 1);
            for (int n = 0; n < sps; n++)
            {
                double phi = Math.PI * modulationIndex * (start + a * n / (double)sps);
                samples[i * sps + n] = new Complex(Math.Cos(phi), Math.Sin(phi));
            }
            start += a;
        }
        return samples;
    }

    /// <summary>Square-law M-FSK detection, one block of samplesPerSymbol per symbol; the label with the
    /// most energy wins, ties to the smallest (conventions: Bits and symbols, FSK; ADR 0054).</summary>
    /// <param name="samples">Samples, finite, a multiple of samplesPerSymbol.</param>
    /// <param name="order">2, 4, 8 or 16.</param>
    /// <param name="samplesPerSymbol">Samples per symbol, at least 1.</param>
    /// <param name="modulationIndex">Tone spacing in symbol rates, positive and finite.</param>
    public static byte[] FskDemodNoncoherent(ReadOnlySpan<Complex> samples, int order, int samplesPerSymbol, double modulationIndex)
    {
        int k = FskBits(order, samplesPerSymbol, modulationIndex);
        int sps = samplesPerSymbol;
        if (samples.Length % sps != 0)
            throw new ArgumentException("samples must be a multiple of samplesPerSymbol", nameof(samples));
        foreach (Complex x in samples)
            if (!double.IsFinite(x.Real) || !double.IsFinite(x.Imaginary))
                throw new ArgumentException("samples must be finite", nameof(samples));
        var cosRef = new double[order * sps];
        var sinRef = new double[order * sps];
        for (int m = 0; m < order; m++)
        {
            long a = 2L * m - (order - 1);
            for (int n = 0; n < sps; n++)
            {
                double psi = Math.PI * modulationIndex * (a * n / (double)sps);
                cosRef[m * sps + n] = Math.Cos(psi);
                sinRef[m * sps + n] = Math.Sin(psi);
            }
        }
        int symbols = samples.Length / sps;
        var bits = new byte[symbols * k];
        for (int i = 0; i < symbols; i++)
        {
            int best = 0;
            double bestEnergy = double.NegativeInfinity;
            for (int m = 0; m < order; m++)
            {
                double re = 0, im = 0;
                for (int n = 0; n < sps; n++)
                {
                    Complex x = samples[i * sps + n];
                    double c = cosRef[m * sps + n], s = sinRef[m * sps + n];
                    re += x.Real * c + x.Imaginary * s;
                    im += x.Imaginary * c - x.Real * s;
                }
                double energy = re * re + im * im;
                if (energy > bestEnergy)
                {
                    best = m;
                    bestEnergy = energy;
                }
            }
            for (int b = 0; b < k; b++)
                bits[i * k + b] = (byte)((best >> (k - 1 - b)) & 1);
        }
        return bits;
    }

    /// <summary>OFDM blocks: symbols on the listed subcarriers, unitary inverse DFT of <paramref name="nfft"/>,
    /// cyclic prefix of <paramref name="cpLen"/> (conventions: Bits and symbols, OFDM; ADR 0060).</summary>
    /// <param name="symbols">Finite symbols, a whole number of blocks of the used subcarriers.</param>
    /// <param name="nfft">DFT size, at least 1.</param>
    /// <param name="cpLen">Cyclic prefix length, 0 to <paramref name="nfft"/>.</param>
    /// <param name="subcarriers">Distinct signed subcarrier indices, −⌊N/2⌋ to N − 1 − ⌊N/2⌋, filled in this
    /// order; null for all of them, ascending.</param>
    /// <returns>The blocks in order, nfft + cpLen samples each.</returns>
    public static Complex[] OfdmModulate(ReadOnlySpan<Complex> symbols, int nfft, int cpLen, int[]? subcarriers = null)
    {
        int[] bins = OfdmBins(nfft, cpLen, subcarriers);
        int u = bins.Length, w = nfft + cpLen;
        if (symbols.Length % u != 0)
            throw new ArgumentException("symbols must fill a whole number of blocks", nameof(symbols));
        CheckFinite(symbols, nameof(symbols));
        double scale = Math.Sqrt(nfft);
        var output = new Complex[symbols.Length / u * w];
        var spectrum = new Complex[nfft];
        for (int b = 0; b < symbols.Length / u; b++)
        {
            Array.Clear(spectrum);
            for (int i = 0; i < u; i++)
                spectrum[bins[i]] = symbols[b * u + i];
            Complex[] x = Spectral.Ifft(spectrum);
            for (int n = 0; n < w; n++)
                output[b * w + n] = x[(n + nfft - cpLen) % nfft] * scale;
        }
        return output;
    }

    /// <summary>Drop each block's cyclic prefix, take the unitary DFT of <paramref name="nfft"/>, and read the
    /// listed subcarriers in order (conventions: Bits and symbols, OFDM; ADR 0060).</summary>
    /// <param name="samples">Finite samples, a whole number of blocks of nfft + cpLen.</param>
    /// <param name="nfft">DFT size, at least 1.</param>
    /// <param name="cpLen">Cyclic prefix length, 0 to <paramref name="nfft"/>.</param>
    /// <param name="subcarriers">Distinct signed subcarrier indices, as for <see cref="OfdmModulate"/>; null for
    /// all of them, ascending.</param>
    /// <returns>The symbols on the listed subcarriers, block after block.</returns>
    public static Complex[] OfdmDemodulate(ReadOnlySpan<Complex> samples, int nfft, int cpLen, int[]? subcarriers = null)
    {
        int[] bins = OfdmBins(nfft, cpLen, subcarriers);
        int u = bins.Length, w = nfft + cpLen;
        if (samples.Length % w != 0)
            throw new ArgumentException("samples must be a whole number of blocks of nfft + cpLen", nameof(samples));
        CheckFinite(samples, nameof(samples));
        double scale = 1 / Math.Sqrt(nfft);
        var output = new Complex[samples.Length / w * u];
        for (int b = 0; b < samples.Length / w; b++)
        {
            Complex[] y = Spectral.Fft(samples.Slice(b * w + cpLen, nfft));
            for (int i = 0; i < u; i++)
                output[b * u + i] = y[bins[i]] * scale;
        }
        return output;
    }

    /// <summary>The DFT bins of the subcarriers, after checking the OFDM arguments.</summary>
    private static int[] OfdmBins(int nfft, int cpLen, int[]? subcarriers)
    {
        if (nfft < 1)
            throw new ArgumentOutOfRangeException(nameof(nfft), "nfft must be at least 1");
        if (cpLen < 0 || cpLen > nfft)
            throw new ArgumentOutOfRangeException(nameof(cpLen), "cpLen must be 0 to nfft");
        int low = -(nfft / 2);
        if (subcarriers is null)
            return [.. Enumerable.Range(low, nfft).Select(k => ((k % nfft) + nfft) % nfft)];
        if (subcarriers.Length == 0)
            throw new ArgumentException("subcarriers must not be empty", nameof(subcarriers));
        if (subcarriers.Any(k => k < low || k > low + nfft - 1))
            throw new ArgumentException($"subcarriers must lie in {low} ... {low + nfft - 1}", nameof(subcarriers));
        if (subcarriers.Distinct().Count() != subcarriers.Length)
            throw new ArgumentException("subcarriers must be distinct", nameof(subcarriers));
        return [.. subcarriers.Select(k => ((k % nfft) + nfft) % nfft)];
    }

    private static void CheckFinite(ReadOnlySpan<Complex> x, string paramName)
    {
        foreach (Complex z in x)
            if (!double.IsFinite(z.Real) || !double.IsFinite(z.Imaginary))
                throw new ArgumentException($"{paramName} must be finite", paramName);
    }
}
