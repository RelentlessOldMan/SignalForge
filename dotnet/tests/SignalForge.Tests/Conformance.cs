using System.Globalization;
using System.Numerics;
using System.Reflection;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace SignalForge.Tests;

/// <summary>Loads and runs the shared vectors in vectors/cases. Format: vectors/README.md.</summary>
public static class Conformance
{
    private const double DefaultAbs = 1e-12, DefaultRel = 1e-12;

    public sealed record VectorCase(string File, string Id, JsonElement Json)
    {
        public override string ToString() => $"{File}:{Id}";
    }

    public static string VectorsDir()
    {
        for (var d = new DirectoryInfo(AppContext.BaseDirectory); d is not null; d = d.Parent)
        {
            string cand = Path.Combine(d.FullName, "vectors", "cases");
            if (Directory.Exists(cand))
                return cand;
        }
        throw new DirectoryNotFoundException("vectors/cases not found above " + AppContext.BaseDirectory);
    }

    public static IEnumerable<VectorCase> LoadCases(string? dir = null)
    {
        foreach (string path in Directory.GetFiles(dir ?? VectorsDir(), "*.json").Order(StringComparer.Ordinal))
        {
            using var doc = JsonDocument.Parse(File.ReadAllText(path));
            var root = doc.RootElement;
            if (root.GetProperty("schema").GetInt32() != 1)
                throw new InvalidDataException($"{Path.GetFileName(path)}: unsupported schema");
            foreach (var c in root.GetProperty("cases").EnumerateArray())
                yield return new VectorCase(Path.GetFileName(path), c.GetProperty("id").GetString()!, c.Clone());
        }
    }

    /// <summary>Runs one case; returns the failure messages (empty when it passes).</summary>
    public static List<string> Run(VectorCase c) => RunWithActual(c).Messages;

    /// <summary>Runs one case; returns the failure messages and the result in canonical form (null
    /// when the operation threw).</summary>
    public static (List<string> Messages, object? Actual) RunWithActual(VectorCase c)
    {
        object? actual = null;
        try
        {
            return (RunCase(c.Json, out actual), actual);
        }
        catch (InvalidDataException e)
        {
            return ([$"bad case: {e.Message}"], actual);
        }
    }

    /// <summary>Runs every case and writes the report that <c>python -m signalforge.conformance
    /// --report</c> writes: implementation, passed, failed, and per case file, id, passed, messages
    /// and the actual result (no file when <paramref name="path"/> is null). Returns the number of
    /// failures.</summary>
    public static int WriteReport(string? path, string? dir = null, TextWriter? log = null)
    {
        var cases = new JsonArray();
        int passed = 0, failed = 0;
        foreach (var c in LoadCases(dir))
        {
            var (msgs, actual) = RunWithActual(c);
            if (msgs.Count == 0)
                passed++;
            else
            {
                failed++;
                log?.WriteLine($"FAIL {c.File} {c.Id}: {string.Join("; ", msgs)}");
            }
            cases.Add(new JsonObject
            {
                ["file"] = c.File,
                ["id"] = c.Id,
                ["passed"] = msgs.Count == 0,
                ["messages"] = new JsonArray([.. msgs.Select(m => (JsonNode?)JsonValue.Create(m))]),
                ["actual"] = Encode(actual),
            });
        }
        log?.WriteLine($"{passed}/{passed + failed} cases passed");
        if (path is null)
            return failed;
        var report = new JsonObject { ["implementation"] = "dotnet", ["passed"] = passed, ["failed"] = failed, ["cases"] = cases };
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(path))!);
        File.WriteAllText(path, report.ToJsonString(new JsonSerializerOptions { WriteIndented = true }));
        return failed;
    }

    /// <summary>Canonical result to the JSON vector form: non-finite numbers as "inf", "-inf",
    /// "nan"; complex values as {"re", "im"}.</summary>
    public static JsonNode? Encode(object? v) => v switch
    {
        null => null,
        double d => double.IsFinite(d) ? JsonValue.Create(d) : JsonValue.Create(double.IsNaN(d) ? "nan" : d > 0 ? "inf" : "-inf"),
        bool b => JsonValue.Create(b),
        string s => JsonValue.Create(s),
        Complex z => new JsonObject { ["re"] = Encode(z.Real), ["im"] = Encode(z.Imaginary) },
        Complex[] zs => new JsonObject
        {
            ["re"] = new JsonArray([.. zs.Select(z => Encode(z.Real))]),
            ["im"] = new JsonArray([.. zs.Select(z => Encode(z.Imaginary))]),
        },
        double[] ds => new JsonArray([.. ds.Select(d => Encode(d))]),
        double[][] rows => new JsonArray([.. rows.Select(r => Encode(r))]),
        Dictionary<string, object?> m => new JsonObject(m.Select(kv => KeyValuePair.Create(kv.Key, Encode(kv.Value)))),
        _ => throw new InvalidOperationException($"cannot encode {v.GetType()}"),
    };

    private static List<string> RunCase(JsonElement json, out object? canonical)
    {
        canonical = null;
        string op = json.GetProperty("op").GetString()!;
        var args = new Dictionary<string, object?>();
        var fractional = new HashSet<string>(); // numbers written with a point or exponent
        if (json.TryGetProperty("args", out var a))
            foreach (var p in a.EnumerateObject())
            {
                args[p.Name] = Decode(p.Value);
                if (p.Value.ValueKind == JsonValueKind.Number && p.Value.GetRawText().IndexOfAny(['.', 'e', 'E']) >= 0)
                    fractional.Add(p.Name);
            }
        double abs = DefaultAbs, rel = DefaultRel;
        if (json.TryGetProperty("tol", out var tol))
        {
            if (tol.TryGetProperty("abs", out var t)) abs = t.GetDouble();
            if (tol.TryGetProperty("rel", out t)) rel = t.GetDouble();
        }
        bool wantError = json.TryGetProperty("error", out var err);

        object? actual;
        try
        {
            actual = Invoke(op, new Args(args, fractional));
            canonical = Canonical(actual);
        }
        catch (LibraryArgumentException e)
        {
            return wantError && err.GetString() == "invalid_argument"
                ? []
                : [$"threw {e.InnerException!.GetType().Name}: {e.InnerException.Message}"];
        }
        if (wantError)
            return [$"expected error {err.GetString()}"];
        var msgs = new List<string>();
        if (!json.TryGetProperty("expected", out var expected))
            throw new InvalidDataException("no expected value or error");
        Compare(canonical, Decode(expected), abs, rel, "", msgs);
        return msgs;
    }

    /// <summary>An ArgumentException thrown by the library itself (not by argument decoding).</summary>
    private sealed class LibraryArgumentException(ArgumentException inner) : Exception(inner.Message, inner);

    /// <summary>A case's arguments. Every argument must be read exactly once, so a misspelled one fails.
    /// An integer argument must be written as a JSON integer: Python rejects 2.0 where it wants an
    /// int, and the C# API cannot be given one, so such a case could only pass in one language.</summary>
    private sealed class Args(Dictionary<string, object?> a, HashSet<string>? fractional = null)
    {
        private readonly HashSet<string> _unused = [.. a.Keys];

        public bool Has(string k) => a.ContainsKey(k);

        public object? Get(string k)
        {
            if (!a.TryGetValue(k, out var v))
                throw new InvalidDataException($"missing argument {k}");
            _unused.Remove(k);
            return v;
        }

        public double D(string k) => Get(k) as double? ?? throw new InvalidDataException($"{k} must be a number");

        public double Opt(string k, double dflt) => Has(k) ? D(k) : dflt;

        public double? OptD(string k) => Has(k) ? D(k) : null;

        public int I(string k)
        {
            double v = D(k);
            if (fractional?.Contains(k) == true)
                throw new InvalidDataException($"{k} must be written as a JSON integer, got {v}");
            return v == Math.Floor(v) && v is >= int.MinValue and <= int.MaxValue
                ? (int)v
                : throw new InvalidDataException($"{k} must be an integer, got {v}");
        }

        public int? OptInt(string k) => Has(k) ? I(k) : null;

        public bool Flag(string k, bool dflt = false) =>
            !Has(k) ? dflt : Get(k) as bool? ?? throw new InvalidDataException($"{k} must be true or false");

        public void CheckAllUsed()
        {
            if (_unused.Count > 0)
                throw new InvalidDataException($"unknown argument(s): {string.Join(", ", _unused)}");
        }
    }

    private static object? Invoke(string op, Args a)
    {
        Func<object?> call = op switch
        {
            "lin_to_db" => Bind(a.D("ratio"), Units.LinToDb),
            "db_to_lin" => Bind(a.D("db"), Units.DbToLin),
            "amp_to_db" => Bind(a.D("ratio"), Units.AmpToDb),
            "db_to_amp" => Bind(a.D("db"), Units.DbToAmp),
            "w_to_dbm" => Bind(a.D("watts"), Units.WToDbm),
            "dbm_to_w" => Bind(a.D("dbm"), Units.DbmToW),
            "vrms_to_dbm" => Bind((a.D("vrms"), a.Opt("impedance", Units.DefaultImpedance)), t => Units.VrmsToDbm(t.Item1, t.Item2)),
            "dbm_to_vrms" => Bind((a.D("dbm"), a.Opt("impedance", Units.DefaultImpedance)), t => Units.DbmToVrms(t.Item1, t.Item2)),
            "tone" => Tone(a),
            "prbs" => Prbs(a),
            "multitone" => Multitone(a),
            "newman_phases" => Bind(a.I("count"), Waveforms.NewmanPhases),
            "chirp" => Chirp(a),
            "pulse_train" => Bind((a.I("num_samples"), a.I("period"), a.I("width"), a.Opt("amplitude", 1), a.Has("delay") ? a.I("delay") : 0),
                t => Waveforms.PulseTrain(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "power_stats" => a.Get("samples") is Complex[] cs
                ? () => Measurements.PowerStats(cs)
                : Bind(Reals(a.Get("samples")), x => Measurements.PowerStats(x)),
            "tone_metrics" => ToneMetricsOp(a),
            "sfdr" => SfdrOp(a),
            "qpsk_map" => Bind(Bits(a.Get("bits")), b => Modulation.QpskMap(b)),
            "qpsk_demap_hard" => Bind(Complexes(a.Get("symbols")), s => Modulation.QpskDemapHard(s)),
            "qpsk_demap_llr" => Bind((Complexes(a.Get("symbols")), a.D("noise_variance")), t => Modulation.QpskDemapLlr(t.Item1, t.Item2)),
            "psk8_map" => Bind(Bits(a.Get("bits")), b => Modulation.Psk8Map(b)),
            "psk8_demap_hard" => Bind(Complexes(a.Get("symbols")), s => Modulation.Psk8DemapHard(s)),
            "psk8_demap_llr" => Bind((Complexes(a.Get("symbols")), a.D("noise_variance")), t => Modulation.Psk8DemapLlr(t.Item1, t.Item2)),
            "qam16_map" => Bind(Bits(a.Get("bits")), b => Modulation.Qam16Map(b)),
            "qam16_demap_hard" => Bind(Complexes(a.Get("symbols")), s => Modulation.Qam16DemapHard(s)),
            "qam16_demap_llr" => Bind((Complexes(a.Get("symbols")), a.D("noise_variance")), t => Modulation.Qam16DemapLlr(t.Item1, t.Item2)),
            "bit_errors" => Bind((Bits(a.Get("reference")), Bits(a.Get("received"))), t => Metrics.BitErrors(t.Item1, t.Item2)),
            "fft" => a.Get("samples") is Complex[] fc
                ? () => Spectral.Fft(fc)
                : Bind(Reals(a.Get("samples")), x => Spectral.Fft(x)),
            "ifft" => Bind(Complexes(a.Get("spectrum")), x => Spectral.Ifft(x)),
            "fft_frequencies" => Bind((a.I("n"), a.D("sample_rate"), a.Flag("shifted")),
                t => Spectral.FftFrequencies(t.Item1, t.Item2, t.Item3)),
            "window" => Bind((WindowName(a.Get("name")), a.I("n"), a.Flag("symmetric"), a.OptD("beta")),
                t => Spectral.Window(t.Item1, t.Item2, t.Item3, t.Item4)),
            "window_stats" => Bind(Reals(a.Get("w")), w => Spectral.WindowStats(w)),
            "welch_psd" => Welch(a),
            "spectrogram" => SpectrogramOp(a),
            "occupied_bandwidth" => Bind((Reals(a.Get("frequencies")), Reals(a.Get("psd")), a.Opt("fraction", 0.99), Span(a)),
                t => Spectral.OccupiedBandwidth(t.Item1, t.Item2, t.Item3, t.Item4)),
            "channel_power" => Bind((Reals(a.Get("frequencies")), Reals(a.Get("psd")), a.D("low"), a.D("high"), Span(a)),
                t => Spectral.ChannelPower(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "acpr" => Bind((Reals(a.Get("frequencies")), Reals(a.Get("psd")), a.D("center"), a.D("bandwidth"), Reals(a.Get("offsets")), a.OptD("adjacent_bandwidth"), Span(a)),
                t => Spectral.Acpr(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5, t.Item6, t.Item7)),
            "convolve" => Convolve(a),
            "upsample" => a.Get("x") is Complex[] ux
                ? Bind((ux, a.I("factor")), t => Dsp.Upsample(t.Item1, t.Item2))
                : Bind((Reals(a.Get("x")), a.I("factor")), t => Dsp.Upsample(t.Item1, t.Item2)),
            "rrc_taps" => Bind((a.D("beta"), a.I("samples_per_symbol"), a.I("span_symbols")),
                t => Dsp.RrcTaps(t.Item1, t.Item2, t.Item3)),
            "pulse_shape" => a.Get("symbols") is Complex[] ps
                ? Bind((ps, Reals(a.Get("taps")), a.I("samples_per_symbol")), t => Dsp.PulseShape(t.Item1, t.Item2, t.Item3))
                : Bind((Reals(a.Get("symbols")), Reals(a.Get("taps")), a.I("samples_per_symbol")),
                    t => Dsp.PulseShape(t.Item1, t.Item2, t.Item3)),
            "fir_lowpass" => Bind((a.I("num_taps"), a.D("cutoff"), a.D("sample_rate"), FirWindow(a), a.OptD("beta")),
                t => Dsp.FirLowpass(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "fir_highpass" => Bind((a.I("num_taps"), a.D("cutoff"), a.D("sample_rate"), FirWindow(a), a.OptD("beta")),
                t => Dsp.FirHighpass(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "fir_bandpass" => Bind((a.I("num_taps"), a.D("low"), a.D("high"), a.D("sample_rate"), FirWindow(a), a.OptD("beta")),
                t => Dsp.FirBandpass(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5, t.Item6)),
            "fir_equiripple" => Bind((a.I("num_taps"), Reals(a.Get("bands")), Reals(a.Get("desired")), a.D("sample_rate"),
                    a.Has("weights") ? Reals(a.Get("weights")) : null, a.OptInt("grid_density") ?? 16,
                    a.Has("kind") ? EquirippleKindName(a.Get("kind")) : EquirippleKind.Filter),
                t => Dsp.FirEquiripple(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5, t.Item6, t.Item7)),
            "fir_least_squares" => Bind((a.I("num_taps"), Reals(a.Get("bands")), Reals(a.Get("desired")), a.D("sample_rate"),
                    a.Has("weights") ? Reals(a.Get("weights")) : null),
                t => Dsp.FirLeastSquares(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "kaiser_parameters" => Bind((a.D("attenuation_db"), a.D("transition_width"), a.D("sample_rate")),
                t => Dsp.KaiserParameters(t.Item1, t.Item2, t.Item3)),
            "fir_response" => Bind((Reals(a.Get("taps")), Reals(a.Get("frequencies")), a.D("sample_rate")),
                t => Dsp.FirResponse(t.Item1, t.Item2, t.Item3)),
            "fir_group_delay" => Bind((Reals(a.Get("taps")), Reals(a.Get("frequencies")), a.D("sample_rate")),
                t => Dsp.FirGroupDelay(t.Item1, t.Item2, t.Item3)),
            "fir_filter" => ChunkedOp(a, Reals(a.Get("taps")), t => new FirFilter(t), (f, x) => f.Process(x), (f, z) => f.Process(z)),
            "iir_filter" => ChunkedOp(a, Rows(a.Get("sos")), c => new IirFilter(c), (f, x) => f.Process(x), (f, z) => f.Process(z)),
            "resampler" => ChunkedOp(a, (a.I("up"), a.I("down"), a.Has("taps") ? Reals(a.Get("taps")) : null),
                c => new Resampler(c.Item1, c.Item2, c.Item3), (f, x) => f.Process(x), (f, z) => f.Process(z)),
            "butterworth_lowpass" => Bind((a.I("order"), a.D("cutoff"), a.D("sample_rate")), t => Dsp.ButterworthLowpass(t.Item1, t.Item2, t.Item3)),
            "butterworth_highpass" => Bind((a.I("order"), a.D("cutoff"), a.D("sample_rate")), t => Dsp.ButterworthHighpass(t.Item1, t.Item2, t.Item3)),
            "chebyshev1_lowpass" => Bind((a.I("order"), a.D("ripple_db"), a.D("cutoff"), a.D("sample_rate")), t => Dsp.Chebyshev1Lowpass(t.Item1, t.Item2, t.Item3, t.Item4)),
            "chebyshev1_highpass" => Bind((a.I("order"), a.D("ripple_db"), a.D("cutoff"), a.D("sample_rate")), t => Dsp.Chebyshev1Highpass(t.Item1, t.Item2, t.Item3, t.Item4)),
            "chebyshev2_lowpass" => Bind((a.I("order"), a.D("attenuation_db"), a.D("cutoff"), a.D("sample_rate")), t => Dsp.Chebyshev2Lowpass(t.Item1, t.Item2, t.Item3, t.Item4)),
            "chebyshev2_highpass" => Bind((a.I("order"), a.D("attenuation_db"), a.D("cutoff"), a.D("sample_rate")), t => Dsp.Chebyshev2Highpass(t.Item1, t.Item2, t.Item3, t.Item4)),
            "bessel_lowpass" => Bind((a.I("order"), a.D("cutoff"), a.D("sample_rate")), t => Dsp.BesselLowpass(t.Item1, t.Item2, t.Item3)),
            "bessel_highpass" => Bind((a.I("order"), a.D("cutoff"), a.D("sample_rate")), t => Dsp.BesselHighpass(t.Item1, t.Item2, t.Item3)),
            "allpass_first_order" => Bind((a.D("cutoff"), a.D("sample_rate")), t => Dsp.AllpassFirstOrder(t.Item1, t.Item2)),
            "allpass_second_order" => Bind((a.D("center"), a.D("bandwidth"), a.D("sample_rate")), t => Dsp.AllpassSecondOrder(t.Item1, t.Item2, t.Item3)),
            "bessel_bandpass" => Bind((a.I("order"), a.D("low"), a.D("high"), a.D("sample_rate")), t => Dsp.BesselBandpass(t.Item1, t.Item2, t.Item3, t.Item4)),
            "bessel_bandstop" => Bind((a.I("order"), a.D("low"), a.D("high"), a.D("sample_rate")), t => Dsp.BesselBandstop(t.Item1, t.Item2, t.Item3, t.Item4)),
            "elliptic_lowpass" => Bind((a.I("order"), a.D("ripple_db"), a.D("attenuation_db"), a.D("cutoff"), a.D("sample_rate")), t => Dsp.EllipticLowpass(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "elliptic_highpass" => Bind((a.I("order"), a.D("ripple_db"), a.D("attenuation_db"), a.D("cutoff"), a.D("sample_rate")), t => Dsp.EllipticHighpass(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "butterworth_bandpass" => Bind((a.I("order"), a.D("low"), a.D("high"), a.D("sample_rate")), t => Dsp.ButterworthBandpass(t.Item1, t.Item2, t.Item3, t.Item4)),
            "butterworth_bandstop" => Bind((a.I("order"), a.D("low"), a.D("high"), a.D("sample_rate")), t => Dsp.ButterworthBandstop(t.Item1, t.Item2, t.Item3, t.Item4)),
            "elliptic_bandpass" => Bind((a.I("order"), a.D("ripple_db"), a.D("attenuation_db"), a.D("low"), a.D("high"), a.D("sample_rate")), t => Dsp.EllipticBandpass(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5, t.Item6)),
            "elliptic_bandstop" => Bind((a.I("order"), a.D("ripple_db"), a.D("attenuation_db"), a.D("low"), a.D("high"), a.D("sample_rate")), t => Dsp.EllipticBandstop(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5, t.Item6)),
            "chebyshev1_bandpass" => Bind((a.I("order"), a.D("ripple_db"), a.D("low"), a.D("high"), a.D("sample_rate")), t => Dsp.Chebyshev1Bandpass(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "chebyshev1_bandstop" => Bind((a.I("order"), a.D("ripple_db"), a.D("low"), a.D("high"), a.D("sample_rate")), t => Dsp.Chebyshev1Bandstop(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "chebyshev2_bandpass" => Bind((a.I("order"), a.D("attenuation_db"), a.D("low"), a.D("high"), a.D("sample_rate")), t => Dsp.Chebyshev2Bandpass(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "chebyshev2_bandstop" => Bind((a.I("order"), a.D("attenuation_db"), a.D("low"), a.D("high"), a.D("sample_rate")), t => Dsp.Chebyshev2Bandstop(t.Item1, t.Item2, t.Item3, t.Item4, t.Item5)),
            "zero_phase_filter" => a.Get("samples") is Complex[] zs
                ? Bind((Rows(a.Get("sos")), zs, a.OptInt("pad")), t => Dsp.ZeroPhaseFilter(t.Item1, t.Item2, t.Item3))
                : Bind((Rows(a.Get("sos")), Reals(a.Get("samples")), a.OptInt("pad")), t => Dsp.ZeroPhaseFilter(t.Item1, t.Item2, t.Item3)),
            "sos_group_delay" => Bind((Rows(a.Get("sos")), Reals(a.Get("frequencies")), a.D("sample_rate")), t => Dsp.SosGroupDelay(t.Item1, t.Item2, t.Item3)),
            "sos_response" => Bind((Rows(a.Get("sos")), Reals(a.Get("frequencies")), a.D("sample_rate")), t => Dsp.SosResponse(t.Item1, t.Item2, t.Item3)),
            "encode_samples" => a.Get("x") is Complex[] z
                ? Bind((z, Str(a, "datatype")), t => Convert.ToHexStringLower(SignalFiles.EncodeSamples(t.Item1, t.Item2)))
                : Bind((Reals(a.Get("x")), Str(a, "datatype")), t => Convert.ToHexStringLower(SignalFiles.EncodeSamples(t.Item1, t.Item2))),
            "decode_samples" => DecodeSamplesOp(Convert.FromHexString(Str(a, "data")), Str(a, "datatype")),
            "read_sigmf" => ReadSigmfOp(Str(a, "file")),
            "resample" => ResampleOp(a, a.I("up"), a.I("down")),
            "interpolate" => ResampleOp(a, a.I("factor"), 1),
            "decimate" => ResampleOp(a, 1, a.I("factor")),
            "resample_taps" => Bind((a.I("up"), a.I("down")), t => Dsp.ResampleTaps(t.Item1, t.Item2)),
            "frequency_offset" => Bind((Complexes(a.Get("samples")), a.D("offset_hz"), a.D("sample_rate"), a.Opt("phase", 0)),
                t => Channel.FrequencyOffset(t.Item1, t.Item2, t.Item3, t.Item4)),
            "iq_imbalance" => Bind((Complexes(a.Get("samples")), a.D("gain_db"), a.D("phase")), t => Channel.IqImbalance(t.Item1, t.Item2, t.Item3)),
            "iq_image_rejection_db" => Bind((a.D("gain_db"), a.D("phase")), t => Channel.IqImageRejectionDb(t.Item1, t.Item2)),
            "phase_noise" => Bind((Complexes(a.Get("samples")), a.D("linewidth_hz"), a.D("sample_rate"), a.I("seed")), t => Channel.PhaseNoise(t.Item1, t.Item2, t.Item3, t.Item4)),
            "multipath" => Bind((Complexes(a.Get("samples")), Ints(a.Get("delays")), Complexes(a.Get("gains"))), t => Channel.Multipath(t.Item1, t.Item2, t.Item3)),
            "dc_offset" => Bind((Complexes(a.Get("samples")), ComplexScalar(a.Get("offset"))), t => Channel.DcOffset(t.Item1, t.Item2)),
            "evm" => Bind((Complexes(a.Get("measured")), Complexes(a.Get("reference"))), t => Metrics.Evm(t.Item1, t.Item2)),
            "qpsk_ber_theory" => Bind(a.D("eb_n0_db"), Metrics.QpskBerTheory),
            "qam16_ber_theory" => Bind(a.D("eb_n0_db"), Metrics.Qam16BerTheory),
            "qam16_ser_theory" => Bind(a.D("eb_n0_db"), Metrics.Qam16SerTheory),
            "psk8_ber_theory" => Bind(a.D("eb_n0_db"), Metrics.Psk8BerTheory),
            "psk8_ser_theory" => Bind(a.D("eb_n0_db"), Metrics.Psk8SerTheory),
            "timing_offset" => Bind((Complexes(a.Get("samples")), a.I("samples_per_symbol")), t => Sync.TimingOffset(t.Item1, t.Item2)),
            "qpsk_frequency_offset" => Bind((Complexes(a.Get("symbols")), a.D("symbol_rate")), t => Sync.QpskFrequencyOffset(t.Item1, t.Item2)),
            "qpsk_phase_offset" => Bind(Complexes(a.Get("symbols")), s => Sync.QpskPhaseOffset(s)),
            "qpsk_block_phases" => Bind((Complexes(a.Get("symbols")), a.I("block_symbols")), t => Sync.QpskBlockPhases(t.Item1, t.Item2)),
            "qpsk_link" => Bind(LinkConfig(a), Link.QpskLink),
            _ => throw new InvalidDataException($"unknown op {op}"),
        };
        a.CheckAllUsed();
        try
        {
            return call();
        }
        catch (ArgumentException e)
        {
            throw new LibraryArgumentException(e);
        }
    }

    private static Func<object?> Bind<T, TResult>(T args, Func<T, TResult> f) => () => f(args);

    private static QpskLinkConfig LinkConfig(Args a)
    {
        var d = new QpskLinkConfig { NumSymbols = a.I("num_symbols") };
        return d with
        {
            EbN0Db = a.OptD("eb_n0_db"),
            SymbolRate = a.Opt("symbol_rate", d.SymbolRate),
            SamplesPerSymbol = a.OptInt("samples_per_symbol") ?? d.SamplesPerSymbol,
            Rolloff = a.Opt("rolloff", d.Rolloff),
            SpanSymbols = a.OptInt("span_symbols") ?? d.SpanSymbols,
            DelaySamples = a.OptInt("delay_samples") ?? d.DelaySamples,
            FrequencyOffsetHz = a.Opt("frequency_offset_hz", d.FrequencyOffsetHz),
            Phase = a.Opt("phase", d.Phase),
            PreambleSymbols = a.OptInt("preamble_symbols") ?? d.PreambleSymbols,
            PhaseBlockSymbols = a.OptInt("phase_block_symbols") ?? d.PhaseBlockSymbols,
            PrbsOrder = a.OptInt("prbs_order") ?? d.PrbsOrder,
            Seed = a.OptInt("seed") ?? d.Seed,
        };
    }

    private static Func<object?> Tone(Args a)
    {
        var (fs, n, f, amp, ph) = (a.D("sample_rate"), a.I("num_samples"), a.D("frequency"), a.Opt("amplitude", 1), a.Opt("phase", 0));
        return a.Flag("complex", dflt: true)
            ? () => Waveforms.Tone(fs, n, f, amp, ph)
            : () => Waveforms.RealTone(fs, n, f, amp, ph);
    }

    private static Func<object?> Multitone(Args a)
    {
        var (fs, n, f) = (a.D("sample_rate"), a.I("num_samples"), Reals(a.Get("frequencies")));
        double[]? amps = a.Has("amplitudes") ? Reals(a.Get("amplitudes")) : null;
        double[]? phases = a.Has("phases") ? Reals(a.Get("phases")) : null;
        return a.Flag("complex", dflt: true)
            ? () => Waveforms.Multitone(fs, n, f, amps, phases)
            : () => Waveforms.RealMultitone(fs, n, f, amps, phases);
    }

    private static Func<object?> Chirp(Args a)
    {
        var (fs, n, f0, f1, amp, ph) = (a.D("sample_rate"), a.I("num_samples"), a.D("start"), a.D("stop"), a.Opt("amplitude", 1), a.Opt("phase", 0));
        return a.Flag("complex", dflt: true)
            ? () => Waveforms.Chirp(fs, n, f0, f1, amp, ph)
            : () => Waveforms.RealChirp(fs, n, f0, f1, amp, ph);
    }

    private static Func<object?> Prbs(Args a)
    {
        var (order, n, invert) = (a.I("order"), a.I("num_bits"), a.Flag("invert"));
        uint? seed = a.Has("seed") ? (a.I("seed") is var v and >= 0 ? (uint)v : throw new InvalidDataException("seed < 0")) : null;
        return () => Waveforms.Prbs(order, n, seed, invert);
    }

    private static Func<object?> Welch(Args a)
    {
        object? samples = a.Get("samples");
        var (fs, nperseg, noverlap) = (a.D("sample_rate"), a.OptInt("nperseg"), a.OptInt("noverlap"));
        var window = a.Has("window") ? WindowName(a.Get("window")) : WindowType.Hann;
        double? beta = a.OptD("beta");
        var detrend = DetrendName(a);
        int? nfft = a.OptInt("nfft");
        var average = a.Has("average") ? Str(a, "average") switch
        {
            "mean" => WelchAverage.Mean,
            "median" => WelchAverage.Median,
            _ => (WelchAverage)(-1), // the library rejects it, as Python does
        } : WelchAverage.Mean;
        if (samples is Complex[] cs)
        {
            // C# has no one-sided option for complex samples (Python raises for one_sided=True).
            if (a.Flag("one_sided"))
                throw new InvalidDataException("one_sided=true with complex samples has no C# form");
            return () => Spectral.WelchPsd(cs, fs, nperseg, noverlap, window, beta, detrend, average, nfft);
        }
        double[] x = Reals(samples);
        bool oneSided = a.Flag("one_sided", dflt: true);
        return () => Spectral.WelchPsd(x, fs, nperseg, noverlap, window, oneSided, beta, detrend, average, nfft);
    }

    private static Detrend DetrendName(Args a) => a.Has("detrend") ? Str(a, "detrend") switch
    {
        "none" => Detrend.None,
        "constant" => Detrend.Constant,
        "linear" => Detrend.Linear,
        _ => (Detrend)(-1), // the library rejects it, as Python does
    } : Detrend.None;

    private static Func<object?> ToneMetricsOp(Args a)
    {
        object? samples = a.Get("samples");
        double fs = a.D("sample_rate");
        var window = a.Has("window") ? WindowName(a.Get("window")) : WindowType.BlackmanHarris;
        var (beta, width, fundamental) = (a.OptD("beta"), a.OptInt("width"), a.OptD("fundamental"));
        int harmonics = a.Has("num_harmonics") ? a.I("num_harmonics") : 5;
        if (samples is Complex[] cs)
            return () => Measurements.ToneMetrics(cs, fs, window, beta, width, harmonics, fundamental);
        double[] x = Reals(samples);
        return () => Measurements.ToneMetrics(x, fs, window, beta, width, harmonics, fundamental);
    }

    private static Func<object?> SfdrOp(Args a)
    {
        object? samples = a.Get("samples");
        double fs = a.D("sample_rate");
        var window = a.Has("window") ? WindowName(a.Get("window")) : WindowType.BlackmanHarris;
        var (beta, width, fundamental) = (a.OptD("beta"), a.OptInt("width"), a.OptD("fundamental"));
        int spurs = a.Has("num_spurs") ? a.I("num_spurs") : 1;
        if (samples is Complex[] cs)
            return () => Measurements.Sfdr(cs, fs, window, beta, width, fundamental, spurs);
        double[] x = Reals(samples);
        return () => Measurements.Sfdr(x, fs, window, beta, width, fundamental, spurs);
    }

    private static Func<object?> SpectrogramOp(Args a)
    {
        object? samples = a.Get("samples");
        var (fs, nperseg, noverlap) = (a.D("sample_rate"), a.I("nperseg"), a.OptInt("noverlap"));
        var window = a.Has("window") ? WindowName(a.Get("window")) : WindowType.Hann;
        double? beta = a.OptD("beta");
        var detrend = DetrendName(a);
        int? nfft = a.OptInt("nfft");
        if (samples is Complex[] cs)
        {
            if (a.Flag("one_sided"))
                throw new InvalidDataException("one_sided=true with complex samples has no C# form");
            return () => Spectral.Spectrogram(cs, fs, nperseg, noverlap, window, beta, detrend, nfft);
        }
        double[] x = Reals(samples);
        bool oneSided = a.Flag("one_sided", dflt: true);
        return () => Spectral.Spectrogram(x, fs, nperseg, noverlap, window, oneSided, beta, detrend, nfft);
    }

    /// <summary>Real only when both inputs are real, as in NumPy.</summary>
    private static Func<object?> Convolve(Args a)
    {
        object? x = a.Get("x"), h = a.Get("h");
        if (x is Complex[] || h is Complex[])
        {
            Complex[] cx = Complexes(x);
            return h is Complex[] ch ? () => Dsp.Convolve(cx, ch) : Bind(Reals(h), rh => Dsp.Convolve(cx, rh));
        }
        return Bind((Reals(x), Reals(h)), t => Dsp.Convolve(t.Item1, t.Item2));
    }

    private static string Str(Args a, string k) => a.Get(k) as string ?? throw new InvalidDataException($"{k} must be a string");

    private static Func<object?> DecodeSamplesOp(byte[] data, string datatype) => datatype.StartsWith('c')
        ? () => SignalFiles.DecodeSamples<Complex>(data, datatype)
        : () => SignalFiles.DecodeSamples<double>(data, datatype);

    /// <summary>A recording in vectors/files, read as the kind its datatype names (the runner
    /// peeks; a file it can't peek at is read as real, and the library must reject it).</summary>
    private static Func<object?> ReadSigmfOp(string name)
    {
        if (Path.GetFileName(name) != name)
            throw new InvalidDataException("file must be a bare file name in vectors/files");
        string path = Path.Combine(VectorsDir(), "..", "files", name);
        bool isComplex = false;
        try
        {
            using var doc = JsonDocument.Parse(File.ReadAllBytes(path + ".sigmf-meta"));
            isComplex = doc.RootElement.GetProperty("global").GetProperty("core:datatype").GetString()?.StartsWith('c') == true;
        }
        catch (Exception e) when (e is JsonException or KeyNotFoundException or InvalidOperationException)
        {
        }
        return isComplex
            ? () => SignalRecord(SignalFiles.ReadSigmf<Complex>(path))
            : () => SignalRecord(SignalFiles.ReadSigmf<double>(path));
    }

    private static Dictionary<string, object?> SignalRecord<T>(Signal<T> s) where T : struct => new()
    {
        ["samples"] = s.Samples.ToArray(),
        ["sample_rate"] = s.SampleRate,
        ["center_frequency"] = s.CenterFrequency,
        ["time_origin"] = s.TimeOrigin,
        ["units"] = s.Units,
        ["impedance"] = s.Impedance,
        ["metadata"] = s.Metadata.ToDictionary(kv => kv.Key, kv => kv.Value),
    };

    private static Func<object?> ResampleOp(Args a, int up, int down)
    {
        object? x = a.Get("x");
        double[]? taps = a.Has("taps") ? Reals(a.Get("taps")) : null;
        return x is Complex[] z
            ? () => Dsp.Resample(z, up, down, taps)
            : Bind(Reals(x), r => Dsp.Resample(r, up, down, taps));
    }

    private static WindowType FirWindow(Args a) => a.Has("window") ? WindowName(a.Get("window")) : WindowType.Hamming;

    /// <summary>A 2-D vector argument as rows.</summary>
    private static double[][] Rows(object? v) =>
        v switch
        {
            double[][] rows => rows,
            Array { Length: 0 } => [],
            _ => throw new InvalidDataException("expected an array of rows"),
        };

    /// <summary>Runs the samples through one streaming filter, made from the coefficients when the
    /// case runs, in chunks of the given lengths.</summary>
    private static Func<object?> ChunkedOp<TCoefficients, TFilter>(Args a, TCoefficients coefficients, Func<TCoefficients, TFilter> make,
        Func<TFilter, double[], double[]> real, Func<TFilter, Complex[], Complex[]> complex)
    {
        object? samples = a.Get("samples");
        int[] sizes = [.. Reals(a.Get("chunks")).Select(c => c >= 0 && c == Math.Floor(c) && c <= int.MaxValue
            ? (int)c : throw new InvalidDataException("chunks must be non-negative whole numbers"))];
        int total = samples is Complex[] zc ? zc.Length : Reals(samples).Length;
        if (sizes.Sum() != total)
            throw new InvalidDataException("chunks must add up to the number of samples");
        return () =>
        {
            TFilter f = make(coefficients);
            int at = 0;
            if (samples is Complex[] z)
            {
                var yz = new List<Complex>();
                foreach (int c in sizes)
                {
                    yz.AddRange(complex(f, z[at..(at + c)]));
                    at += c;
                }
                return yz.ToArray();
            }
            double[] x = Reals(samples);
            var y = new List<double>();
            foreach (int c in sizes)
            {
                y.AddRange(real(f, x[at..(at + c)]));
                at += c;
            }
            return y.ToArray();
        };
    }

    private static (double Low, double High)? Span(Args a)
    {
        if (!a.Has("span"))
            return null;
        double[] s = Reals(a.Get("span"));
        return s.Length == 2 ? (s[0], s[1]) : throw new InvalidDataException("span must have two values");
    }

    /// <summary>Vector window names: exactly the Python names. An unknown name is a library error in
    /// Python, so it maps to an undefined enum value that the library must reject.</summary>
    private static WindowType WindowName(object? v) => (v as string) switch
    {
        "rectangular" => WindowType.Rectangular,
        "hann" => WindowType.Hann,
        "hamming" => WindowType.Hamming,
        "blackman" => WindowType.Blackman,
        "blackman_harris" => WindowType.BlackmanHarris,
        "flattop" => WindowType.Flattop,
        "kaiser" => WindowType.Kaiser,
        string => (WindowType)(-1),
        _ => throw new InvalidDataException("window name must be a string"),
    };

    /// <summary>Vector equiripple kinds: the Python names; an unknown one maps to an undefined
    /// value the library must reject.</summary>
    private static EquirippleKind EquirippleKindName(object? v) => (v as string) switch
    {
        "filter" => EquirippleKind.Filter,
        "hilbert" => EquirippleKind.Hilbert,
        "differentiator" => EquirippleKind.Differentiator,
        string => (EquirippleKind)(-1),
        _ => throw new InvalidDataException("kind must be a string"),
    };

    private static double[] Reals(object? v) => v as double[] ?? throw new InvalidDataException("expected a real array");

    private static int[] Ints(object? v) => Reals(v).Select(x =>
        x >= int.MinValue && x <= int.MaxValue && x == Math.Floor(x)
            ? (int)x
            : throw new InvalidDataException($"not representable as an int: {x}")).ToArray();

    private static Complex ComplexScalar(object? v) => v switch
    {
        Complex c => c,
        double d => new Complex(d, 0),
        _ => throw new InvalidDataException("expected a number"),
    };

    private static Complex[] Complexes(object? v) =>
        v as Complex[] ?? Reals(v).Select(x => new Complex(x, 0)).ToArray();

    /// <summary>Bits as bytes. A value that is not 0 or 1 has no byte form the library could reject
    /// for being a non-bit (e.g. 0.5), so it is a bad case, except whole numbers 2…255, which the
    /// library must reject.</summary>
    private static byte[] Bits(object? v) => Reals(v).Select(x =>
        x is >= 0 and <= byte.MaxValue && x == Math.Floor(x)
            ? (byte)x
            : throw new InvalidDataException($"not representable as a byte: {x}")).ToArray();

    /// <summary>JSON vector value to: double, bool, string, double[], Complex, Complex[], or a record dictionary.</summary>
    public static object? Decode(JsonElement v)
    {
        switch (v.ValueKind)
        {
            case JsonValueKind.Null:
                return null;
            case JsonValueKind.Number:
                return v.GetDouble();
            case JsonValueKind.True:
                return true;
            case JsonValueKind.False:
                return false;
            case JsonValueKind.String:
                return v.GetString() switch
                {
                    "inf" => double.PositiveInfinity,
                    "-inf" => double.NegativeInfinity,
                    "nan" => double.NaN,
                    var s => s,
                };
            case JsonValueKind.Array:
                if (v.GetArrayLength() > 0 && v[0].ValueKind == JsonValueKind.Array)
                    return v.EnumerateArray().Select(e => (double[])Decode(e)!).ToArray(); // rows of a 2-D result
                return v.EnumerateArray().Select(e => (double)Decode(e)!).ToArray();
            case JsonValueKind.Object:
                var props = v.EnumerateObject().ToList();
                if (props.Count == 2 && v.TryGetProperty("re", out var re) && v.TryGetProperty("im", out var im))
                {
                    if (re.ValueKind == JsonValueKind.Array)
                    {
                        var r = (double[])Decode(re)!;
                        var i = (double[])Decode(im)!;
                        if (r.Length != i.Length)
                            throw new InvalidDataException("re and im have different lengths");
                        return r.Zip(i, (x, y) => new Complex(x, y)).ToArray();
                    }
                    return new Complex((double)Decode(re)!, (double)Decode(im)!);
                }
                return props.ToDictionary(p => p.Name, p => Decode(p.Value));
            default:
                return null;
        }
    }

    /// <summary>Result to the decoded-vector shape: numbers as double, arrays as double[]/Complex[], records as snake_case dictionaries.</summary>
    public static object? Canonical(object? v) => v switch
    {
        null => null,
        double or Complex or Complex[] or double[] or double[][] or bool or string => v,
        long l => (double)l,
        Dictionary<string, object?> m => m.ToDictionary(kv => kv.Key, kv => Canonical(kv.Value)),
        int i => (double)i,
        byte[] b => b.Select(x => (double)x).ToArray(),
        System.Runtime.CompilerServices.ITuple t => Enumerable.Range(0, t.Length).Select(i => Convert.ToDouble(t[i], CultureInfo.InvariantCulture)).ToArray(),
        _ when v.GetType().Assembly == typeof(Units).Assembly =>
            v.GetType().GetProperties(BindingFlags.Public | BindingFlags.Instance)
                .ToDictionary(p => SnakeCase(p.Name), p => Canonical(p.GetValue(v))),
        _ => throw new InvalidOperationException($"no canonical form for {v.GetType()}"),
    };

    public static string SnakeCase(string name)
    {
        var sb = new StringBuilder();
        for (int i = 0; i < name.Length; i++)
        {
            if (char.IsUpper(name[i]) && i > 0)
                sb.Append('_');
            sb.Append(char.ToLowerInvariant(name[i]));
        }
        return sb.ToString();
    }

    private static void Compare(object? actual, object? expected, double abs, double rel, string path, List<string> msgs)
    {
        string where = path.Length == 0 ? "value" : path;
        switch (expected)
        {
            case null:
                if (actual is not null) msgs.Add($"{where}: expected null, got {actual.GetType().Name}");
                return;
            case Dictionary<string, object?> rec:
                if (actual is not Dictionary<string, object?> act)
                {
                    msgs.Add($"{where}: expected a record, got {actual?.GetType().Name ?? "null"}");
                    return;
                }
                foreach (var (k, e) in rec)
                {
                    string p = path.Length == 0 ? k : $"{path}.{k}";
                    if (act.TryGetValue(k, out var x)) Compare(x, e, abs, rel, p, msgs);
                    else msgs.Add($"{p}: missing");
                }
                return;
            case double[] ed when actual is double[] ad:
                if (ad.Length != ed.Length)
                    msgs.Add($"{where}: length {ad.Length} != expected {ed.Length}");
                else if (Enumerable.Range(0, ed.Length).Where(i => !Close(ad[i], ed[i], abs, rel)).ToList() is [int i0, ..] bad)
                    msgs.Add($"{where}[{i0}]: {ad[i0]:R} != expected {ed[i0]:R} ({bad.Count} differ)");
                return;
            case double[][] er when actual is double[][] ar:
                if (ar.Length != er.Length)
                    msgs.Add($"{where}: {ar.Length} rows != expected {er.Length}");
                else
                    for (int r = 0; r < er.Length; r++)
                        Compare(ar[r], er[r], abs, rel, $"{where}[{r}]", msgs);
                return;
            case Complex[] ec when actual is Complex[] ac:
                CompareArrays(ac, ec, abs, rel, where, msgs);
                return;
            case string es:
                if (actual as string != es) msgs.Add($"{where}: {actual ?? "null"} != expected {es}");
                return;
            case bool eb when actual is bool ab:
                if (ab != eb) msgs.Add($"{where}: {ab} != expected {eb}");
                return;
            case double ed when actual is double ad:
                if (!Close(ad, ed, abs, rel)) msgs.Add($"{where}: {ad:R} != expected {ed:R}");
                return;
            case Complex ec when actual is Complex ac:
                if (!Close(ac, ec, abs, rel)) msgs.Add($"{where}: {ac} != expected {ec}");
                return;
            default:
                msgs.Add($"{where}: type {actual?.GetType().Name ?? "null"} does not match expected {expected?.GetType().Name ?? "null"}");
                return;
        }
    }

    private static void CompareArrays(Complex[] a, Complex[] e, double abs, double rel, string where, List<string> msgs)
    {
        if (a.Length != e.Length)
        {
            msgs.Add($"{where}: length {a.Length} != expected {e.Length}");
            return;
        }
        var bad = Enumerable.Range(0, e.Length).Where(i => !Close(a[i], e[i], abs, rel)).ToList();
        if (bad.Count > 0)
            msgs.Add($"{where}[{bad[0]}]: {a[bad[0]]} != expected {e[bad[0]]} ({bad.Count} differ)");
    }

    private static bool Close(double a, double e, double abs, double rel)
    {
        if (double.IsNaN(e)) return double.IsNaN(a);
        if (double.IsInfinity(e)) return a == e;
        return Math.Abs(a - e) <= abs + rel * Math.Abs(e);
    }

    private static bool Close(Complex a, Complex e, double abs, double rel) =>
        double.IsFinite(e.Real) && double.IsFinite(e.Imaginary)
            ? Complex.Abs(a - e) <= abs + rel * Complex.Abs(e)
            : Close(a.Real, e.Real, abs, rel) && Close(a.Imaginary, e.Imaginary, abs, rel); // part by part, so inf matches inf
}
