using System.Diagnostics;

namespace BlazePisonet.SoftTimer;

public sealed class TimerEngine : IDisposable
{
    private readonly object _gate = new();
    private readonly System.Threading.Timer _tick;
    private RuntimeState _state;
    private readonly Action<RuntimeState> _persistState;
    private bool _creditPersistenceFaulted;
    // Monotonic clock: wall-clock edits must not multiply or erase paid time.
    private long _lastTickStamp = Stopwatch.GetTimestamp();
    private long _lastPersistStamp;
    private double _fractionalSeconds;
    private bool _externalAuthority;
    private bool _paused;

    public event Action<long>? RemainingChanged;
    public event Action<bool>? ActiveChanged;
    public event Action<string>? Audit;

    public TimerEngine() : this(Storage.LoadState(), Storage.SaveState, true) { }

    // Same real timer engine under test: only storage I/O and ticker are
    // substituted, never the production financial logic.
    internal TimerEngine(RuntimeState initialState, Action<RuntimeState> persistState, bool startTicker)
    {
        _state = initialState ?? throw new ArgumentNullException(nameof(initialState));
        _persistState = persistState ?? throw new ArgumentNullException(nameof(persistState));
        _paused = _state.PendingMemberOperation is not null;
        int interval = startTicker ? 250 : Timeout.Infinite;
        _tick = new System.Threading.Timer(_ => Tick(), null, interval, interval);
    }

    public long RemainingSeconds
    {
        get { lock (_gate) return Math.Max(0, _state.RemainingSeconds); }
    }

    public bool IsActive => RemainingSeconds > 0;
    public bool IsPaused { get { lock (_gate) return _paused; } }
    public long SalesPulseCount { get { lock (_gate) return _state.SalesPulseCount; } }
    public bool CreditPersistenceFaulted { get { lock (_gate) return _creditPersistenceFaulted; } }

    public void SetExternalAuthority(bool external)
    {
        lock (_gate)
        {
            _externalAuthority = external;
            ResetTickClock();
        }
    }

    public void AddCoin(int secondsPerCoin, string source = "local")
    {
        if (secondsPerCoin <= 0) return;
        AddSeconds(secondsPerCoin, $"coin:{source}:{Guid.NewGuid():N}", true, $"Coin accepted from {source}");
    }

    // Purely stages a new state and invokes persistence BEFORE handing
    // ownership to the caller. A failed/ambiguous write never mutates
    // currently published paid time, sales totals, or deduplication IDs.
    internal static bool TryPersistCredit(RuntimeState original, long seconds,
        string eventId, bool countSale, Action<RuntimeState> persist,
        out RuntimeState committed)
    {
        committed = original;
        if (seconds <= 0 || string.IsNullOrWhiteSpace(eventId)) return false;
        if (original.AppliedEventIds.Contains(eventId)) return false;
        if (original.RemainingSeconds < 0 || original.SalesPulseCount < 0)
            throw new InvalidDataException("Negative financial state");
        var next = new RuntimeState
        {
            RemainingSeconds = checked(original.RemainingSeconds + seconds),
            SalesPulseCount = checked(original.SalesPulseCount + (countSale ? 1L : 0L)),
            TimerRunning = true,
            UpdatedUtc = DateTimeOffset.UtcNow,
            AppliedEventIds = new HashSet<string>(original.AppliedEventIds,
                StringComparer.OrdinalIgnoreCase),
            Members = original.Members,
            RemoteMembers = original.RemoteMembers,
            RemoteMemberRevision = original.RemoteMemberRevision,
            PendingMemberOperation = original.PendingMemberOperation
        };
        next.AppliedEventIds.Add(eventId);
        persist(next);
        committed = next;
        return true;
    }

    public bool AddSeconds(long seconds, string eventId, bool countSale, string audit)
    {
        if (seconds <= 0 || string.IsNullOrWhiteSpace(eventId)) return false;
        bool wasActive;
        long remaining;
        lock (_gate)
        {
            if (_creditPersistenceFaulted)
                throw new InvalidOperationException(
                    "Coin credit is suspended after an uncertain paid-state save. Operator recovery required.");
            wasActive = _state.RemainingSeconds > 0;
            RuntimeState committed;
            try
            {
                if (!TryPersistCredit(_state, seconds, eventId, countSale,
                        _persistState, out committed)) return false;
            }
            catch (Exception ex)
            {
                // Even when File.Replace reports an error after a partial
                // operation, we must not retry and credit the same coin.
                _creditPersistenceFaulted = true;
                throw new IOException(
                    "Coin credit write is uncertain; credits are suspended pending operator reconciliation.", ex);
            }
            _state = committed;
            ResetTickClock();
            remaining = committed.RemainingSeconds;
        }
        Audit?.Invoke(audit + $"; +{seconds}s; remaining={remaining}s");
        RemainingChanged?.Invoke(remaining);
        if (!wasActive && remaining > 0) ActiveChanged?.Invoke(true);
        return true;
    }

    public void SetAuthoritativeSeconds(long seconds, string source)
    {
        seconds = Math.Max(0, seconds);
        bool oldActive = false;
        bool changed = false;
        bool failed = false;
        Exception? failure = null;
        lock (_gate)
        {
            _externalAuthority = true;
            if (_creditPersistenceFaulted) return;
            oldActive = _state.RemainingSeconds > 0;
            changed = _state.RemainingSeconds != seconds;
            if (!changed)
            {
                ResetTickClock();
                return;
            }

            // External timer updates can change customer lock state. Never
            // publish a due checkpoint before the disk write is confirmed.
            var next = ClonePaidState(_state);
            next.RemainingSeconds = seconds;
            next.TimerRunning = seconds > 0;
            next.UpdatedUtc = DateTimeOffset.UtcNow;
            var stamp = Stopwatch.GetTimestamp();
            if (ElapsedSince(stamp, _lastPersistStamp) >= 2)
            {
                try
                {
                    _persistState(next);
                    _lastPersistStamp = stamp;
                }
                catch (Exception ex)
                {
                    _creditPersistenceFaulted = true;
                    failure = ex;
                    failed = true;
                }
            }

            if (!failed)
            {
                _state = next;
                ResetTickClock();
            }
        }
        if (failed)
        {
            Audit?.Invoke("CRITICAL external timer persistence fault; access locked: " +
                failure?.GetType().Name);
            return;
        }
        RemainingChanged?.Invoke(seconds);
        if (oldActive != (seconds > 0)) ActiveChanged?.Invoke(seconds > 0);
    }

    public void Reset(string reason = "admin reset")
    {
        bool oldActive;
        lock (_gate)
        {
            if (_creditPersistenceFaulted)
                throw new InvalidOperationException("Paid-state recovery required.");
            var next = ClonePaidState(_state);
            oldActive = next.RemainingSeconds > 0;
            next.RemainingSeconds = 0;
            next.TimerRunning = false;
            next.UpdatedUtc = DateTimeOffset.UtcNow;
            CommitFinancialStateLocked(next);
            ResetTickClock();
        }
        Audit?.Invoke($"Timer reset: {reason}");
        RemainingChanged?.Invoke(0);
        if (oldActive) ActiveChanged?.Invoke(false);
    }

    public void Pause(bool paused)
    {
        lock (_gate)
        {
            _paused = paused;
            ResetTickClock();
        }
        Audit?.Invoke(paused ? "Timer paused" : "Timer resumed");
    }

    // Clone *all* paid state before financial member mutations. A staged
    // change must not leak through MemberAccount references before disk commit.
    private static RuntimeState ClonePaidState(RuntimeState original) => new()
    {
        RemainingSeconds = original.RemainingSeconds,
        TimerRunning = original.TimerRunning,
        UpdatedUtc = original.UpdatedUtc,
        SalesPulseCount = original.SalesPulseCount,
        AppliedEventIds = new HashSet<string>(original.AppliedEventIds,
            StringComparer.OrdinalIgnoreCase),
        Members = original.Members.ToDictionary(x => x.Key, x => CloneMember(x.Value),
            StringComparer.OrdinalIgnoreCase),
        RemoteMembers = original.RemoteMembers.ToDictionary(x => x.Key, x => CloneMember(x.Value),
            StringComparer.OrdinalIgnoreCase),
        RemoteMemberRevision = original.RemoteMemberRevision,
        PendingMemberOperation = original.PendingMemberOperation is { } p
            ? new PendingMemberOperation
            {
                Action = p.Action, Username = p.Username, MemberToken = p.MemberToken,
                EventId = p.EventId, Seconds = p.Seconds,
                MemberRevision = p.MemberRevision, CreatedUtc = p.CreatedUtc
            }
            : null
    };

    // Caller holds _gate. Publish only after durable write is acknowledged;
    // any uncertain persistence failure latches the same lockout as a coin.
    private void CommitFinancialStateLocked(RuntimeState staged)
    {
        if (_creditPersistenceFaulted)
            throw new InvalidOperationException(
                "Paid-state persistence is uncertain; operator recovery required.");
        try { _persistState(staged); }
        catch (Exception ex)
        {
            _creditPersistenceFaulted = true;
            throw new IOException(
                "Paid-state write result is uncertain; session and credits suspended.", ex);
        }
        _state = staged;
    }

    public bool CreateOrUpdateMember(string username, string password)
    {
        username = username.Trim();
        if (username.Length < 2 || username.Length > 32 || password.Length < 4) return false;
        var hp = Passwords.HashMemberPassword(password);
        lock (_gate)
        {
            if (_creditPersistenceFaulted)
                throw new InvalidOperationException("Paid-state recovery required.");
            var next = ClonePaidState(_state);
            next.Members[username] = new MemberAccount
            {
                Username = username,
                Enabled = true,
                PasswordScheme = "pbkdf2-sha256",
                PasswordRounds = 120000,
                PasswordSalt = hp.Salt,
                PasswordHash = hp.Hash,
                BankedSeconds = next.Members.TryGetValue(username, out var old)
                    ? old.BankedSeconds : 0,
                UpdatedUtc = DateTimeOffset.UtcNow
            };
            CommitFinancialStateLocked(next);
        }
        Audit?.Invoke($"Member account created/updated: {username}");
        return true;
    }

    public bool BankCurrentTime(string username, string password)
    {
        bool wasActive;
        lock (_gate)
        {
            if (_creditPersistenceFaulted)
                throw new InvalidOperationException("Paid-state recovery required.");
            if (!_state.Members.TryGetValue(username, out var original) ||
                !Passwords.VerifyMemberPassword(original, password)) return false;
            var next = ClonePaidState(_state);
            var member = next.Members[username];
            wasActive = next.RemainingSeconds > 0;
            member.BankedSeconds = checked(member.BankedSeconds + Math.Max(0, next.RemainingSeconds));
            member.UpdatedUtc = DateTimeOffset.UtcNow;
            next.RemainingSeconds = 0;
            next.TimerRunning = false;
            next.UpdatedUtc = DateTimeOffset.UtcNow;
            CommitFinancialStateLocked(next);
            ResetTickClock();
        }
        RemainingChanged?.Invoke(0);
        if (wasActive) ActiveChanged?.Invoke(false);
        Audit?.Invoke($"Time banked to member: {username}");
        return true;
    }

    public bool RestoreMemberTime(string username, string password)
    {
        long restored;
        long remaining;
        bool wasActive;
        lock (_gate)
        {
            if (_creditPersistenceFaulted)
                throw new InvalidOperationException("Paid-state recovery required.");
            if (!_state.Members.TryGetValue(username, out var original) ||
                !Passwords.VerifyMemberPassword(original, password)) return false;
            restored = original.BankedSeconds;
            if (restored <= 0) return true;
            var next = ClonePaidState(_state);
            wasActive = next.RemainingSeconds > 0;
            next.RemainingSeconds = checked(next.RemainingSeconds + restored);
            next.TimerRunning = true;
            var member = next.Members[username];
            member.BankedSeconds = 0;
            member.UpdatedUtc = DateTimeOffset.UtcNow;
            next.UpdatedUtc = DateTimeOffset.UtcNow;
            CommitFinancialStateLocked(next);
            ResetTickClock();
            remaining = next.RemainingSeconds;
        }
        RemainingChanged?.Invoke(remaining);
        if (!wasActive) ActiveChanged?.Invoke(true);
        Audit?.Invoke($"Member time restored: {username}; {restored}s");
        return true;
    }

    public bool TransferMemberTime(string fromUser, string fromPassword, string toUser, long seconds)
    {
        if (seconds <= 0) return false;
        lock (_gate)
        {
            if (_creditPersistenceFaulted)
                throw new InvalidOperationException("Paid-state recovery required.");
            if (!_state.Members.TryGetValue(fromUser, out var from) ||
                !_state.Members.TryGetValue(toUser, out var to)) return false;
            if (!Passwords.VerifyMemberPassword(from, fromPassword) ||
                from.BankedSeconds < seconds) return false;
            // No-op for transfers to the same case-insensitive member identity.
            if (ReferenceEquals(from, to)) return true;
            var next = ClonePaidState(_state);
            var debited = next.Members[fromUser];
            var credited = next.Members[toUser];
            debited.BankedSeconds = checked(debited.BankedSeconds - seconds);
            credited.BankedSeconds = checked(credited.BankedSeconds + seconds);
            debited.UpdatedUtc = credited.UpdatedUtc = DateTimeOffset.UtcNow;
            CommitFinancialStateLocked(next);
        }
        Audit?.Invoke($"Member transfer: {fromUser} -> {toUser}; {seconds}s");
        return true;
    }

    public IReadOnlyList<MemberAccount> MembersSnapshot()
    {
        lock (_gate)
            return _state.Members.Values.Select(CloneMember).OrderBy(m => m.Username).ToList();
    }

    public long RemoteMemberRevision
    {
        get { lock (_gate) return _state.RemoteMemberRevision; }
    }

    public PendingMemberOperation? PendingMemberOperation
    {
        get
        {
            lock (_gate)
            {
                var p = _state.PendingMemberOperation;
                if (p is null) return null;
                return new PendingMemberOperation
                {
                    Action = p.Action,
                    Username = p.Username,
                    MemberToken = p.MemberToken,
                    EventId = p.EventId,
                    Seconds = p.Seconds,
                    MemberRevision = p.MemberRevision,
                    CreatedUtc = p.CreatedUtc
                };
            }
        }
    }

    public void SetPendingMemberOperation(PendingMemberOperation pending)
    {
        ArgumentNullException.ThrowIfNull(pending);
        if (string.IsNullOrWhiteSpace(pending.EventId))
            throw new ArgumentException("Pending member transaction must have an event ID", nameof(pending));
        lock (_gate)
        {
            if (_creditPersistenceFaulted)
                throw new InvalidOperationException("Paid-state recovery required.");
            if (_state.PendingMemberOperation is { } existing &&
                !existing.EventId.Equals(pending.EventId, StringComparison.OrdinalIgnoreCase))
                throw new InvalidOperationException("Resolve existing pending member transaction first.");
            var next = ClonePaidState(_state);
            next.PendingMemberOperation = new PendingMemberOperation
            {
                Action = pending.Action, Username = pending.Username,
                MemberToken = pending.MemberToken, EventId = pending.EventId,
                Seconds = pending.Seconds, MemberRevision = pending.MemberRevision,
                CreatedUtc = pending.CreatedUtc
            };
            CommitFinancialStateLocked(next);
        }
        Audit?.Invoke($"Pending BlazePwifi member operation recorded: {pending.Action}:{pending.Username}:{pending.EventId}");
    }

    public void ClearPendingMemberOperation(string eventId)
    {
        lock (_gate)
        {
            if (_creditPersistenceFaulted)
                throw new InvalidOperationException("Paid-state recovery required.");
            if (_state.PendingMemberOperation is null
                || !_state.PendingMemberOperation.EventId.Equals(eventId, StringComparison.OrdinalIgnoreCase))
                return;
            var next = ClonePaidState(_state);
            next.PendingMemberOperation = null;
            CommitFinancialStateLocked(next);
        }
        Audit?.Invoke($"Pending BlazePwifi member operation cleared: {eventId}");
    }

    public IReadOnlyList<MemberAccount> RemoteMembersSnapshot()
    {
        lock (_gate)
            return _state.RemoteMembers.Values.Select(CloneMember).OrderBy(m => m.Username).ToList();
    }

    public void ApplyRemoteMembers(IEnumerable<MemberAccount> members, long revision)
    {
        ArgumentNullException.ThrowIfNull(members);
        int count;
        lock (_gate)
        {
            if (_creditPersistenceFaulted)
                throw new InvalidOperationException("Paid-state recovery required.");
            if (revision < _state.RemoteMemberRevision) return;
            var updated = new Dictionary<string, MemberAccount>(StringComparer.OrdinalIgnoreCase);
            foreach (var member in members)
            {
                if (string.IsNullOrWhiteSpace(member.Username)) continue;
                // Do not modify caller-owned server snapshot objects.
                var copy = CloneMember(member);
                copy.RemoteManaged = true;
                if (!updated.TryAdd(copy.Username, copy))
                    throw new InvalidDataException("Duplicate remote member identity: " + copy.Username);
            }
            count = updated.Count;
            var next = ClonePaidState(_state);
            next.RemoteMembers = updated;
            next.RemoteMemberRevision = revision;
            CommitFinancialStateLocked(next);
        }
        Audit?.Invoke($"BlazePwifi member snapshot applied; revision={revision}; members={count}");
    }

    public MemberAccount? RemoteMember(string username)
    {
        lock (_gate)
            return _state.RemoteMembers.TryGetValue(username.Trim(), out var member) ? CloneMember(member) : null;
    }

    public bool VerifyRemoteMember(string username, string password)
    {
        lock (_gate)
            return _state.RemoteMembers.TryGetValue(username.Trim(), out var member)
                && member.Enabled
                && Passwords.VerifyMemberPassword(member, password);
    }

    private static MemberAccount CloneMember(MemberAccount m) => new()
    {
        Username = m.Username,
        Label = m.Label,
        Enabled = m.Enabled,
        PasswordScheme = m.PasswordScheme,
        PasswordSalt = m.PasswordSalt,
        PasswordHash = m.PasswordHash,
        PasswordRounds = m.PasswordRounds,
        BankedSeconds = m.BankedSeconds,
        Revision = m.Revision,
        RemoteManaged = m.RemoteManaged,
        UpdatedUtc = m.UpdatedUtc
    };

    // Deterministic, unit-testable portion of the billable elapsed-time logic.
    internal static long DebitWholeSeconds(ref double carry, double elapsed)
    {
        if (double.IsNaN(elapsed) || double.IsInfinity(elapsed) || elapsed <= 0)
            return 0;
        carry += elapsed;
        long whole = (long)Math.Floor(carry);
        carry -= whole;
        return whole;
    }

    internal static int VerifyTimerMath()
    {
        double carry = 0;
        for (int i = 0; i < 14400; i++)
        {
            long billed = DebitWholeSeconds(ref carry, 0.25); // 60 min at 250-ms cadence
            if (billed != (i % 4 == 3 ? 1L : 0L)) return 1;
        }
        if (Math.Abs(carry) > 0.000001) return 2;
        carry = 0;
        if (DebitWholeSeconds(ref carry, 0.375) != 0) return 3;
        if (DebitWholeSeconds(ref carry, 0.125) != 0) return 4;
        if (DebitWholeSeconds(ref carry, 0.625) != 1) return 5;
        if (Math.Abs(carry - 0.125) > 0.000001) return 6;
        if (DebitWholeSeconds(ref carry, -100) != 0) return 7;
        if (DebitWholeSeconds(ref carry, double.NaN) != 0) return 8;
        return 0;
    }

    private static double ElapsedSince(long now, long previous)
    {
        if (previous == 0) return double.PositiveInfinity;
        return Math.Max(0, (now - previous) / (double)Stopwatch.Frequency);
    }

    private void ResetTickClock()
    {
        _lastTickStamp = Stopwatch.GetTimestamp();
        _fractionalSeconds = 0;
    }

    private void Tick()
    {
        bool changed = false;
        bool becameInactive = false;
        bool storageFaulted = false;
        Exception? storageFailure = null;
        long remaining = 0;
        lock (_gate)
        {
            long stamp = Stopwatch.GetTimestamp();
            double elapsed = ElapsedSince(stamp, _lastTickStamp);
            _lastTickStamp = stamp;
            if (_creditPersistenceFaulted)
            {
                _fractionalSeconds = 0;
                return;
            }
            if (_externalAuthority || _paused || _state.RemainingSeconds <= 0)
            {
                _fractionalSeconds = 0;
                return;
            }

            long toDebit = DebitWholeSeconds(ref _fractionalSeconds, elapsed);
            if (toDebit <= 0) return;
            long old = _state.RemainingSeconds;
            remaining = Math.Max(0, old - toDebit);
            changed = remaining != old;
            if (!changed) return;
            becameInactive = old > 0 && remaining == 0;
            bool persistNow = ElapsedSince(stamp, _lastPersistStamp) >= 5 || becameInactive;

            if (persistNow)
            {
                // Never mutate the live state before a durable scheduled save.
                // A failed timer callback must not throw on the ThreadPool or
                // leave a partially published credit/session state behind.
                var staged = ClonePaidState(_state);
                staged.RemainingSeconds = remaining;
                staged.TimerRunning = remaining > 0;
                staged.UpdatedUtc = DateTimeOffset.UtcNow;
                try
                {
                    _persistState(staged);
                    _state = staged;
                    _lastPersistStamp = stamp;
                }
                catch (Exception ex)
                {
                    _creditPersistenceFaulted = true;
                    storageFailure = ex;
                    storageFaulted = true;
                    changed = false;
                    becameInactive = false;
                }
            }
            else
            {
                // Normal interim debit stays in memory until the bounded
                // periodic checkpoint. The next durable checkpoint is staged.
                _state.RemainingSeconds = remaining;
                _state.TimerRunning = remaining > 0;
                _state.UpdatedUtc = DateTimeOffset.UtcNow;
            }
        }
        if (storageFaulted)
        {
            Audit?.Invoke("CRITICAL countdown persistence fault; paid session suspended: " +
                storageFailure?.GetType().Name);
            // AppController maintenance observes CreditPersistenceFaulted and
            // applies customer lock; do not announce uncommitted time changes.
            return;
        }
        if (changed) RemainingChanged?.Invoke(remaining);
        if (becameInactive) ActiveChanged?.Invoke(false);
    }

    public void Dispose()
    {
        _tick.Dispose();
        lock (_gate)
        {
            // A failed credit must retain any .tmp / previous state for manual
            // reconciliation instead of performing another uncertain write.
            if (!_creditPersistenceFaulted) _persistState(_state);
        }
    }
}
