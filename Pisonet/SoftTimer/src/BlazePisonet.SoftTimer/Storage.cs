using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace BlazePisonet.SoftTimer;

public sealed class RuntimeState
{
    public long RemainingSeconds { get; set; }
    public bool TimerRunning { get; set; }
    public DateTimeOffset UpdatedUtc { get; set; } = DateTimeOffset.UtcNow;
    public long SalesPulseCount { get; set; }
    public HashSet<string> AppliedEventIds { get; set; } = new(StringComparer.OrdinalIgnoreCase);
    public Dictionary<string, MemberAccount> Members { get; set; } = new(StringComparer.OrdinalIgnoreCase);
    public Dictionary<string, MemberAccount> RemoteMembers { get; set; } = new(StringComparer.OrdinalIgnoreCase);
    public long RemoteMemberRevision { get; set; }
    public PendingMemberOperation? PendingMemberOperation { get; set; }
}

public sealed class PendingMemberOperation
{
    public string Action { get; set; } = string.Empty;
    public string Username { get; set; } = string.Empty;
    public string MemberToken { get; set; } = string.Empty;
    public string EventId { get; set; } = string.Empty;
    public long Seconds { get; set; }
    public long MemberRevision { get; set; }
    public DateTimeOffset CreatedUtc { get; set; } = DateTimeOffset.UtcNow;
}

public sealed class MemberAccount
{
    public string Username { get; set; } = string.Empty;
    public string Label { get; set; } = string.Empty;
    public bool Enabled { get; set; } = true;
    public string PasswordScheme { get; set; } = "pbkdf2-sha256";
    public string PasswordSalt { get; set; } = string.Empty;
    public string PasswordHash { get; set; } = string.Empty;
    public int PasswordRounds { get; set; } = 120000;
    public long BankedSeconds { get; set; }
    public long Revision { get; set; }
    public bool RemoteManaged { get; set; }
    public DateTimeOffset UpdatedUtc { get; set; } = DateTimeOffset.UtcNow;
}

public static class Storage
{
    public static readonly JsonSerializerOptions JsonOptions = new()
    {
        WriteIndented = true,
        PropertyNameCaseInsensitive = true
    };

    public static string RootDirectory => Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData),
        "BlazeSystems", "BlazePisonetSoftTimer");

    public static string ConfigPath => Path.Combine(RootDirectory, "config.json");
    public static string StatePath => Path.Combine(RootDirectory, "state.json");
    public static string LogPath => Path.Combine(RootDirectory, "softtimer.log");
    public static string MaintenancePath => Path.Combine(RootDirectory, "maintenance.until");

    public static AppConfig LoadConfig()
    {
        Directory.CreateDirectory(RootDirectory);
        return LoadConfigFromPath(ConfigPath);
    }

    // The production loader and disposable-file regression harness share this
    // exact path. Only a truly absent configuration may be initialized.
    internal static AppConfig LoadConfigFromPath(string path)
    {
        if (!File.Exists(path))
        {
            // A lost configuration with an existing paid session is not a
            // first installation. Regenerating its key/identity could orphan
            // member reconciliation or authorize a reset of operator policy.
            var paidState = Path.Combine(
                Path.GetDirectoryName(path) ?? throw new InvalidDataException(
                    "Configuration path has no parent directory."), "state.json");
            if (File.Exists(paidState) || File.Exists(paidState + ".bak") ||
                File.Exists(paidState + ".tmp"))
                throw new InvalidDataException(
                    "SoftTimer configuration is missing while paid-state evidence exists. " +
                    "Preserve paid state and configuration before supervised recovery.");

            // A missing primary alongside an older snapshot or interrupted
            // write is recovery work, never permission to reset operator auth.
            if (File.Exists(path + ".bak") || File.Exists(path + ".tmp"))
                throw new InvalidDataException(
                    "SoftTimer configuration is missing but recovery evidence exists. " +
                    "Preserve config.json/.bak/.tmp and reconcile under operator supervision.");

            var initial = new AppConfig
            {
                CentralSharedKey = Convert.ToHexString(RandomNumberGenerator.GetBytes(24)).ToLowerInvariant(),
                BlazePwifiControllerId = "softtimer-" + NormalizeId(Environment.MachineName)
            };
            SaveConfigToPath(path, initial);
            return initial;
        }

        // A parseable primary does not make an interrupted configuration
        // update safe: an uncommitted new key or password may be in .tmp.
        if (File.Exists(path + ".tmp"))
            throw new InvalidDataException(
                "SoftTimer configuration has an unresolved pending write. " +
                "Preserve config.json/.bak/.tmp for supervised recovery.");

        AppConfig config;
        try
        {
            var json = File.ReadAllText(path);
            using (var document = JsonDocument.Parse(json))
            {
                if (document.RootElement.ValueKind != JsonValueKind.Object)
                    throw new InvalidDataException(
                        "Existing SoftTimer configuration must be a JSON object.");

                // Missing security fields otherwise deserialize to defaults,
                // and MainForm may enter unrestricted admin maintenance.
                // Reject ambiguous case-insensitive duplicates too: JsonOptions
                // would otherwise silently choose one of the conflicting values.
                var fields = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
                foreach (var property in document.RootElement.EnumerateObject())
                {
                    if (!fields.Add(property.Name))
                        throw new InvalidDataException(
                            "Existing SoftTimer configuration has duplicate fields.");
                }
                foreach (var required in new[]
                {
                    "Enabled", "AdminPasswordHash", "AdminPasswordSalt",
                    "AdminPasswordIterations", "CentralSharedKey",
                    "BlazePwifiControllerId"
                })
                {
                    if (!fields.Contains(required))
                        throw new InvalidDataException(
                            "Existing SoftTimer configuration is missing required field: " +
                            required);
                }
            }

            config = JsonSerializer.Deserialize<AppConfig>(json, JsonOptions)
                ?? throw new InvalidDataException("Existing SoftTimer configuration is null.");
        }
        catch (JsonException ex)
        {
            throw new InvalidDataException(
                "Existing SoftTimer configuration is unreadable. Preserve original files; " +
                "do not silently reset administrator or integration settings.", ex);
        }

        var hasSalt = !string.IsNullOrWhiteSpace(config.AdminPasswordSalt);
        var hasHash = !string.IsNullOrWhiteSpace(config.AdminPasswordHash);
        if (config.AdminPasswordIterations <= 0 || hasSalt != hasHash ||
            (config.Enabled && !config.HasAdminPassword))
            throw new InvalidDataException(
                "Existing SoftTimer configuration has invalid administrator credentials. " +
                "Preserve it for supervised recovery.");

        // Identity/key generation is permitted only on genuine first install.
        // A damaged installed configuration must never silently rotate its
        // coordinator secret or device binding and resume in a new identity.
        if (string.IsNullOrWhiteSpace(config.CentralSharedKey) ||
            string.IsNullOrWhiteSpace(config.BlazePwifiControllerId))
            throw new InvalidDataException(
                "Existing SoftTimer configuration has no stable controller identity or " +
                "coordinator key. Preserve it for supervised migration/recovery.");

        config.Version = "0.4.0";
        EnsureSchedules(config);
        return config;
    }

    public static void SaveConfig(AppConfig config) =>
        SaveConfigToPath(ConfigPath, config);

    internal static void SaveConfigToPath(string path, AppConfig config)
    {
        ArgumentNullException.ThrowIfNull(config);
        EnsureSchedules(config);
        AtomicWrite(path, JsonSerializer.Serialize(config, JsonOptions));
    }

    private static void EnsureSchedules(AppConfig config)
    {
        config.NotificationSchedules ??= new List<NotificationSchedule>();
        while (config.NotificationSchedules.Count < 3)
            config.NotificationSchedules.Add(new NotificationSchedule { Name = $"Schedule {config.NotificationSchedules.Count + 1}" });
        if (config.NotificationSchedules.Count > 3)
            config.NotificationSchedules = config.NotificationSchedules.Take(3).ToList();

        for (var i = 0; i < config.NotificationSchedules.Count; i++)
        {
            var schedule = config.NotificationSchedules[i];
            if (string.IsNullOrWhiteSpace(schedule.Name)) schedule.Name = $"Schedule {i + 1}";
            schedule.Days ??= Enum.GetValues<DayOfWeek>().ToHashSet();
        }
    }

    public static RuntimeState LoadState()
    {
        Directory.CreateDirectory(RootDirectory);
        try
        {
            return LoadStateFromPath(StatePath, DateTimeOffset.UtcNow);
        }
        catch (Exception ex)
        {
            // Never substitute an empty state for unreadable paid time or coin dedupe history.
            // Preserve state.json, state.json.bak and state.json.tmp for manual recovery.
            Log("CRITICAL paid session state unreadable; admission disabled: " + ex);
            throw new InvalidDataException(
                "Paid session state could not be verified. SoftTimer will not reset it automatically. " +
                "Preserve state.json/.bak/.tmp and recover under operator supervision.", ex);
        }
    }

    // This is the same decoder called by production startup. A test-only path
    // allows deterministic fault injection without touching a customer's ProgramData.
    internal static RuntimeState LoadStateFromPath(string path, DateTimeOffset now)
    {
        if (!File.Exists(path))
        {
            if (File.Exists(path + ".bak") || File.Exists(path + ".tmp"))
                throw new InvalidDataException(
                    "Paid state is missing but a backup or pending transaction exists.");
            return new RuntimeState(); // actual first installation only
        }

        // A leftover .tmp may contain a credit or deduplication update not
        // represented in the primary. Even a parseable primary is ambiguous.
        // Preserve both files for supervised recovery; never guess which wins.
        if (File.Exists(path + ".tmp"))
            throw new InvalidDataException("Paid state has an unresolved pending write.");

        var json = File.ReadAllText(path);
        using (var doc = JsonDocument.Parse(json))
        {
            if (doc.RootElement.ValueKind != JsonValueKind.Object)
                throw new InvalidDataException("Paid state must be a JSON object.");
            // JSON deserialization otherwise fills omitted financial fields
            // with empty defaults, silently losing deduplication/member data.
            var required = new[] { "RemainingSeconds", "TimerRunning",
                "UpdatedUtc", "SalesPulseCount", "AppliedEventIds", "Members",
                "RemoteMembers", "RemoteMemberRevision", "PendingMemberOperation" };
            foreach (var key in required)
            {
                if (!doc.RootElement.EnumerateObject().Any(p =>
                        string.Equals(p.Name, key, StringComparison.OrdinalIgnoreCase)))
                    throw new InvalidDataException("Paid state missing required field: " + key);
            }
        }

        var state = JsonSerializer.Deserialize<RuntimeState>(json, JsonOptions)
            ?? throw new InvalidDataException("Paid state JSON is null.");
        ValidateFinancialState(state);
        // Preserve case-insensitive event and member identity after JSON
        // round-trip. Ambiguous mixed-case member duplicates must fail closed.
        state.AppliedEventIds = state.AppliedEventIds.ToHashSet(StringComparer.OrdinalIgnoreCase);
        state.Members = state.Members.ToDictionary(
            entry => entry.Key, entry => entry.Value, StringComparer.OrdinalIgnoreCase);
        state.RemoteMembers = state.RemoteMembers.ToDictionary(
            entry => entry.Key, entry => entry.Value, StringComparer.OrdinalIgnoreCase);
        if (state.UpdatedUtc == default || state.UpdatedUtc > now.AddMinutes(2))
            throw new InvalidDataException("Paid state clock is invalid or in the future.");

        if (state.TimerRunning && state.RemainingSeconds > 0 &&
            state.PendingMemberOperation is null)
        {
            var elapsed = Math.Max(0, (long)(now - state.UpdatedUtc).TotalSeconds);
            state.RemainingSeconds = Math.Max(0, state.RemainingSeconds - elapsed);
            state.TimerRunning = state.RemainingSeconds > 0;
            state.UpdatedUtc = now;
        }
        else if (state.PendingMemberOperation is not null)
        {
            state.UpdatedUtc = now;
        }
        return state;
    }

    // Shared startup/write guard: never deserialize or persist member balances
    // that could be mistaken for usable prepaid credit on later operations.
    private static void ValidateFinancialState(RuntimeState state)
    {
        if (state.RemainingSeconds < 0 || state.SalesPulseCount < 0 ||
            state.RemoteMemberRevision < 0 || state.AppliedEventIds is null ||
            state.Members is null || state.RemoteMembers is null ||
            state.AppliedEventIds.Any(string.IsNullOrWhiteSpace))
            throw new InvalidDataException("Paid state has invalid accounting fields.");

        ValidateMemberAccounting(state.Members, "local");
        ValidateMemberAccounting(state.RemoteMembers, "remote");
    }

    private static void ValidateMemberAccounting(
        Dictionary<string, MemberAccount> accounts, string scope)
    {
        foreach (var (key, member) in accounts)
        {
            if (string.IsNullOrWhiteSpace(key) || member is null ||
                member.BankedSeconds < 0 || member.Revision < 0)
                throw new InvalidDataException(
                    "Paid state has invalid " + scope + " member accounting fields.");
        }
    }

    public static void SaveState(RuntimeState state) =>
        SaveStateToPath(StatePath, state, DateTimeOffset.UtcNow);

    // Production uses this exact writer; tests provide only a disposable
    // destination and clock. Do not mutate caller-owned state on failure.
    internal static void SaveStateToPath(string path, RuntimeState state, DateTimeOffset now)
    {
        ArgumentNullException.ThrowIfNull(state);
        ValidateFinancialState(state);

        // Never silently truncate historical event identities. Removing an
        // old ID permits a replay of already-paid coin/member events. A
        // future bounded ledger requires an explicit durable tombstone design,
        // not an arbitrary HashSet length threshold.
        var snapshot = new RuntimeState
        {
            RemainingSeconds = state.RemainingSeconds,
            TimerRunning = state.TimerRunning,
            UpdatedUtc = now,
            SalesPulseCount = state.SalesPulseCount,
            AppliedEventIds = new HashSet<string>(
                state.AppliedEventIds, StringComparer.OrdinalIgnoreCase),
            Members = new Dictionary<string, MemberAccount>(
                state.Members, StringComparer.OrdinalIgnoreCase),
            RemoteMembers = new Dictionary<string, MemberAccount>(
                state.RemoteMembers, StringComparer.OrdinalIgnoreCase),
            RemoteMemberRevision = state.RemoteMemberRevision,
            PendingMemberOperation = state.PendingMemberOperation
        };
        AtomicWrite(path, JsonSerializer.Serialize(snapshot, JsonOptions));
    }

    public static void AtomicWrite(string path, string content)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        var temp = path + ".tmp";
        var backup = path + ".bak";

        // A leftover temporary file may represent a credit that reached disk
        // before an interrupted replace. Never destroy that evidence.
        if (File.Exists(temp))
            throw new InvalidDataException("Unresolved paid-state write: " + temp);

        // CreateNew (rather than truncating an existing .tmp) also prevents
        // accidental concurrent writers from discarding a pending journal.
        using (var fs = new FileStream(temp, FileMode.CreateNew, FileAccess.Write,
                   FileShare.None, 4096, FileOptions.WriteThrough))
        {
            var bytes = new UTF8Encoding(false).GetBytes(content);
            fs.Write(bytes);
            fs.Flush(flushToDisk: true);
        }

        if (File.Exists(path))
        {
            // If replace fails, leave the previous committed state and
            // temporary file intact. A copy+overwrite fallback is not atomic.
            File.Replace(temp, path, backup, ignoreMetadataErrors: true);
        }
        else
        {
            File.Move(temp, path);
        }
    }

    public static void Log(string line)
    {
        try
        {
            Directory.CreateDirectory(RootDirectory);
            File.AppendAllText(LogPath, $"{DateTimeOffset.Now:yyyy-MM-dd HH:mm:ss zzz}  {line}{Environment.NewLine}");
        }
        catch { }
    }

    public static string NormalizeId(string value)
    {
        var sb = new StringBuilder();
        foreach (var c in value)
            if (char.IsLetterOrDigit(c) || c is '.' or '_' or '-') sb.Append(char.ToLowerInvariant(c));
        return sb.Length == 0 ? "pc" : sb.ToString()[..Math.Min(40, sb.Length)];
    }
}

public static class Passwords
{
    public static void SetAdminPassword(AppConfig config, string password)
    {
        var salt = RandomNumberGenerator.GetBytes(24);
        var hash = Rfc2898DeriveBytes.Pbkdf2(password, salt, config.AdminPasswordIterations, HashAlgorithmName.SHA256, 32);
        config.AdminPasswordSalt = Convert.ToBase64String(salt);
        config.AdminPasswordHash = Convert.ToBase64String(hash);
    }

    public static bool VerifyAdminPassword(AppConfig config, string password)
    {
        if (!config.HasAdminPassword) return false;
        try
        {
            var salt = Convert.FromBase64String(config.AdminPasswordSalt);
            var expected = Convert.FromBase64String(config.AdminPasswordHash);
            var actual = Rfc2898DeriveBytes.Pbkdf2(password, salt, config.AdminPasswordIterations, HashAlgorithmName.SHA256, expected.Length);
            return CryptographicOperations.FixedTimeEquals(actual, expected);
        }
        catch { return false; }
    }

    public static (string Salt, string Hash) HashMemberPassword(string password, int iterations = 120000)
    {
        var salt = RandomNumberGenerator.GetBytes(20);
        var hash = Rfc2898DeriveBytes.Pbkdf2(password, salt, iterations, HashAlgorithmName.SHA256, 32);
        return (Convert.ToBase64String(salt), Convert.ToBase64String(hash));
    }

    public static bool VerifyMemberPassword(MemberAccount member, string password, int iterations = 120000)
    {
        if (!member.Enabled) return false;
        try
        {
            if (member.PasswordScheme.Equals("sha256i", StringComparison.OrdinalIgnoreCase))
            {
                var value = DeriveSha256iVerifier(password, member.PasswordSalt, member.PasswordRounds);
                var got = Encoding.ASCII.GetBytes(value);
                var expected = Encoding.ASCII.GetBytes(member.PasswordHash.ToLowerInvariant());
                return got.Length == expected.Length && CryptographicOperations.FixedTimeEquals(got, expected);
            }

            var salt = Convert.FromBase64String(member.PasswordSalt);
            var expectedPbkdf = Convert.FromBase64String(member.PasswordHash);
            var roundsPbkdf = member.PasswordRounds > 0 ? member.PasswordRounds : iterations;
            var actual = Rfc2898DeriveBytes.Pbkdf2(password, salt, roundsPbkdf, HashAlgorithmName.SHA256, expectedPbkdf.Length);
            return CryptographicOperations.FixedTimeEquals(actual, expectedPbkdf);
        }
        catch { return false; }
    }

    public static string DeriveSha256iVerifier(string password, string salt, int rounds)
    {
        rounds = Math.Clamp(rounds, 1, 20000);
        var value = HexSha256($"{salt}|{password}|{salt}");
        for (var i = 1; i < rounds; i++)
            value = HexSha256($"{value}|{password}|{salt}");
        return value;
    }

    private static string HexSha256(string value) =>
        Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(value))).ToLowerInvariant();
}
