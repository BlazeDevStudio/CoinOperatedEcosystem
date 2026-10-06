using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace BlazePisonet.SoftTimer;

public sealed record BlazePwifiMemberSnapshot(long Revision, IReadOnlyList<MemberAccount> Members);

public sealed record BlazePwifiMemberMutationResult(
    string EventId,
    long ResultSeconds,
    long BankedSeconds,
    long Revision);

public sealed class BlazePwifiClient : IDisposable
{
    private readonly HttpClient _http = new() { Timeout = TimeSpan.FromSeconds(4) };
    private readonly System.Threading.Timer _timer;
    private AppConfig _config;
    private string _targetNonce = string.Empty;
    private bool _insertWindow;
    private int _busy;
    private DateTimeOffset _lastMemberSync = DateTimeOffset.MinValue;

    public event Action<string>? StatusChanged;
    public event Action<BlazePwifiMemberSnapshot>? MembersReceived;
    public bool InsertWindow => _insertWindow;
    public string TargetNonce => _targetNonce;

    public BlazePwifiClient(AppConfig config)
    {
        _config = config;
        _timer = new System.Threading.Timer(async _ => await Poll(), null, Timeout.Infinite, Timeout.Infinite);
    }

    public void UpdateConfig(AppConfig config) => _config = config;

    public void Start()
    {
        if (!_config.BlazePwifiEnabled) return;
        _timer.Change(0, 2500);
    }

    public void Stop() => _timer.Change(Timeout.Infinite, Timeout.Infinite);

    private async Task Poll()
    {
        if (!_config.BlazePwifiEnabled || string.IsNullOrWhiteSpace(_config.BlazePwifiVendoKey)) return;
        if (Interlocked.Exchange(ref _busy, 1) != 0) return;
        try
        {
            var json = await Call("poll", 0, string.Empty);
            if (json is null)
            {
                StatusChanged?.Invoke("BlazePwifi offline");
                return;
            }
            using var doc = JsonDocument.Parse(json);
            var root = doc.RootElement;
            _insertWindow = root.TryGetProperty("insert", out var ins) && (ins.ValueKind == JsonValueKind.True || (ins.ValueKind == JsonValueKind.Number && ins.GetInt32() == 1));
            _targetNonce = root.TryGetProperty("target_nonce", out var tn) ? tn.GetString() ?? string.Empty : string.Empty;
            StatusChanged?.Invoke(_insertWindow ? "BlazePwifi connected · coin window active" : "BlazePwifi connected");
        }
        catch (Exception ex) { StatusChanged?.Invoke("BlazePwifi error: " + ex.Message); }
        finally { Interlocked.Exchange(ref _busy, 0); }
    }

    public async Task<bool> ForwardCoinAsync(int pulses = 1)
    {
        if (!_config.BlazePwifiEnabled || !_config.MirrorLocalCoinsToBlazePwifi || !_insertWindow || string.IsNullOrWhiteSpace(_targetNonce)) return false;
        try
        {
            var json = await Call("coin", Math.Clamp(pulses, 1, 20), _targetNonce);
            if (json is null) return false;
            using var doc = JsonDocument.Parse(json);
            return doc.RootElement.TryGetProperty("ok", out var ok) && ok.GetBoolean();
        }
        catch { return false; }
    }

    public async Task<bool> PingAsync()
    {
        var json = await Call("ping", 0, string.Empty);
        return json is not null;
    }

    private async Task<string?> Call(string action, int pulses, string target)
    {
        var result = await CallDetailed(action, pulses, target);
        return result?.Json;
    }

    private async Task<CallResult?> CallDetailed(string action, int pulses, string target)
    {
        if (string.IsNullOrWhiteSpace(_config.BlazePwifiVendoUrl)
            || string.IsNullOrWhiteSpace(_config.BlazePwifiVendoKey))
            return null;

        var id = Storage.NormalizeId(_config.BlazePwifiControllerId);
        var nonce = Convert.ToHexString(RandomNumberGenerator.GetBytes(8)).ToLowerInvariant();
        var sig = Signature(_config.BlazePwifiVendoKey, action, id, nonce, pulses, target);
        var form = new Dictionary<string, string>
        {
            ["action"] = action,
            ["id"] = id,
            ["nonce"] = nonce,
            ["pulses"] = pulses.ToString(),
            ["target"] = target,
            ["sig"] = sig
        };
        using var resp = await _http.PostAsync(_config.BlazePwifiVendoUrl, new FormUrlEncodedContent(form));
        var text = await resp.Content.ReadAsStringAsync();
        if (!resp.IsSuccessStatusCode)
        {
            Storage.Log($"BlazePwifi {action} failed {(int)resp.StatusCode}: {text}");
            return null;
        }
        return new CallResult(text, nonce);
    }

    public static string Signature(string secret, string action, string id, string nonce, int pulses, string target)
    {
        var raw = $"{secret}|{action}|{id}|{nonce}|{pulses}|{target}|{secret}";
        return HexSha256(raw);
    }

    private static string HexSha256(string value) =>
        Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(value))).ToLowerInvariant();

    private static bool FixedHexEquals(string left, string right)
    {
        if (left.Length != right.Length || left.Length == 0) return false;
        return CryptographicOperations.FixedTimeEquals(
            Encoding.ASCII.GetBytes(left.ToLowerInvariant()),
            Encoding.ASCII.GetBytes(right.ToLowerInvariant()));
    }

    public void Dispose()
    {
        _timer.Dispose();
        _http.Dispose();
    }

    private sealed record CallResult(string Json, string Nonce);
}
