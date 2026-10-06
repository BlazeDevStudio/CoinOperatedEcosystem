using System.Diagnostics;

namespace BlazePisonet.SoftTimer;

public sealed class AppController : IDisposable
{
    private readonly TimerEngine _timer;
    private readonly SerialHardware _serial;
    private readonly WindowsSecurity _security;
    private readonly BlazeTimerBridge _blazeTimer;
    private readonly BlazePwifiClient _blazePwifi;
    private CentralizedServer? _centralServer;
    private readonly System.Windows.Forms.Timer _maintenanceTimer;
    private readonly List<LockForm> _locks = new();
    private readonly HashSet<string> _activeScheduleShutdownWindows = new(StringComparer.OrdinalIgnoreCase);
    private MainForm? _mainForm;
    private ActiveTimerForm? _activeTimer;
    private bool _adminMaintenance;
    private bool _forcedScheduleLock;
    private bool _shutdownPrompted;
    private bool _warningPlayed;
    private DateTimeOffset _lastQueuePoll = DateTimeOffset.MinValue;

    public AppConfig Config { get; private set; }
    public TimerEngine Timer => _timer;
    public SerialHardware Serial => _serial;
    public BlazeTimerBridge BlazeTimer => _blazeTimer;
    public BlazePwifiClient BlazePwifi => _blazePwifi;
    public CentralizedServer? CentralServer => _centralServer;
    public string HardwareStatus { get; private set; } = "Not initialized";
    public string IntegrationStatus { get; private set; } = "Offline";

    public event Action? StatusChanged;

    public AppController(AppConfig config)
    {
        Config = config;
        _timer = new TimerEngine();
        _serial = new SerialHardware();
        _security = new WindowsSecurity(config);
        _blazeTimer = new BlazeTimerBridge(config);
        _blazePwifi = new BlazePwifiClient(config);
        _maintenanceTimer = new System.Windows.Forms.Timer { Interval = 1000 };
        _maintenanceTimer.Tick += async (_, _) => await MaintenanceTick();

        _timer.RemainingChanged += OnRemainingChanged;
        _timer.ActiveChanged += _ => EvaluateLockState();
        _timer.Audit += Storage.Log;
        _serial.ConnectionChanged += s => { HardwareStatus = s; StatusChanged?.Invoke(); };
        _serial.SignalChanged += () => { if (Config.TimerSource == TimerSourceMode.ExternalTimerBoard) UpdateExternalBoard(); };
        _serial.CoinPulseAccepted += async () => await HandleCoinPulse();
        _security.AdminSecretRequested += () => BeginInvokeUi(OpenAdminFromLock);
        _security.UnusualInputThresholdReached += () => BeginInvokeUi(() => ConfirmOrShutdown("Unusual keyboard or mouse activity detected."));
        _blazeTimer.RemainingReceived += s => _timer.SetAuthoritativeSeconds(s, "Blaze Pisonet Timer");
        _blazeTimer.StatusChanged += s => { HardwareStatus = s; StatusChanged?.Invoke(); };
        _blazePwifi.StatusChanged += s => { IntegrationStatus = s; StatusChanged?.Invoke(); };
        _blazePwifi.MembersReceived += snapshot =>
        {
            _timer.ApplyRemoteMembers(snapshot.Members, snapshot.Revision);
            StatusChanged?.Invoke();
        };
    }

    public void AttachMainForm(MainForm form) => _mainForm = form;

    public void Start()
    {
        _security.StartKeyboardHook();
        ConfigureRuntime();
        _maintenanceTimer.Start();
        EvaluateLockState();
    }

    public void ApplyConfig(AppConfig updated)
    {
        Config = updated;
        Storage.SaveConfig(Config);
        _security.UpdateConfig(Config);
        _blazeTimer.UpdateConfig(Config);
        _blazePwifi.UpdateConfig(Config);
        ConfigureRuntime();
        EvaluateLockState();
        StatusChanged?.Invoke();
    }

    private void ConfigureRuntime()
    {
        _blazeTimer.Stop();
        _blazePwifi.Stop();
        _serial.Disconnect();
        _centralServer?.Dispose();
        _centralServer = null;

        if (!Config.Enabled)
        {
            _timer.SetExternalAuthority(false);
            _security.SetLocked(false);
            HardwareStatus = "SoftTimer disabled";
            return;
        }

        if (Config.CoinTopology is CoinTopologyMode.CentralizedCoordinator or CoinTopologyMode.CentralizedStation)
        {
            _centralServer = new CentralizedServer(Config, _timer);
            _centralServer.QueueChanged += () => StatusChanged?.Invoke();
            _centralServer.Start();
        }

        switch (Config.TimerSource)
        {
            case TimerSourceMode.InternalPcTimer:
                _timer.SetExternalAuthority(false);
                if (Config.CoinTopology != CoinTopologyMode.CentralizedStation)
                {
                    _serial.Connect(Config);
                    HardwareStatus = _serial.IsConnected ? $"Serial connected · {_serial.ConnectedDevice?.Display}" : "Serial disconnected";
                }
                else HardwareStatus = "Centralized station · waiting for coordinator";
                break;

            case TimerSourceMode.ExternalTimerBoard:
                _timer.SetExternalAuthority(true);
                _serial.Connect(Config);
                UpdateExternalBoard();
                break;

            case TimerSourceMode.BlazePisonetTimer:
                _timer.SetExternalAuthority(true);
                HardwareStatus = "Connecting to Blaze Pisonet Timer…";
                _blazeTimer.Start();
                break;
        }

        if (Config.BlazePwifiEnabled) _blazePwifi.Start();
        if (Config.RunWatchdog) EnsureWatchdog();
    }

    private async Task HandleCoinPulse()
    {
        if (!Config.Enabled) return;
        if (Config.CoinTopology == CoinTopologyMode.CentralizedCoordinator)
        {
            if (_centralServer is not null)
            {
                var routed = await _centralServer.CreditCurrentAsync(Config.SecondsPerCoin);
                HardwareStatus = routed ? "Coin routed to active station" : "Coin received with no active station";
                StatusChanged?.Invoke();
            }
        }
        else if (Config.CoinTopology == CoinTopologyMode.StandardOneToOne && Config.TimerSource == TimerSourceMode.InternalPcTimer)
        {
            _timer.AddCoin(Config.SecondsPerCoin, _serial.ConnectedDevice?.PortName ?? "serial");
        }

        if (Config.BlazePwifiEnabled && Config.MirrorLocalCoinsToBlazePwifi)
            await _blazePwifi.ForwardCoinAsync(1);
    }

    private void UpdateExternalBoard()
    {
        if (!_serial.IsConnected)
        {
            _timer.SetAuthoritativeSeconds(0, "serial disconnected");
            return;
        }
        var raw = _serial.GetSignal(Config.TimerActiveSignal);
        var active = Config.TimerActiveHigh ? raw : !raw;
        _timer.SetAuthoritativeSeconds(active ? 1 : 0, "external timer board");
        HardwareStatus = active ? $"External timer active · {_serial.ConnectedDevice?.Display}" : $"External timer idle · {_serial.ConnectedDevice?.Display}";
        StatusChanged?.Invoke();
    }

    public async Task RequestCentralCoinAsync()
    {
        if (Config.CoinTopology != CoinTopologyMode.CentralizedStation) return;
        var ok = await PeerClient.RequestCoinAsync(Config);
        SetLockStatus(ok ? "Coin slot requested · waiting for READY" : "Coordinator unreachable", ok, !ok);
    }

    public async Task<IReadOnlyList<BlazeTimerDevice>> DiscoverBlazeTimersAsync() => await _blazeTimer.DiscoverAsync();

    public void EnterAdminMaintenance()
    {
        _adminMaintenance = true;
        HideLocks();
        HideActiveTimer();
        _security.SetLocked(false);
    }

    public void ExitAdminMaintenance()
    {
        _adminMaintenance = false;
        EvaluateLockState();
    }

    private void OpenAdminFromLock()
    {
        using var login = new AdminLoginForm(Config);
        if (login.ShowDialog() != DialogResult.OK || !login.Authenticated) return;
        EnterAdminMaintenance();
        if (_mainForm is not null)
        {
            _mainForm.Show();
            _mainForm.WindowState = FormWindowState.Normal;
            _mainForm.BringToFront();
            _mainForm.Activate();
        }
    }

    public bool AuthenticateAdmin(string password) => Passwords.VerifyAdminPassword(Config, password);

    public void SetAdminPassword(string password)
    {
        Passwords.SetAdminPassword(Config, password);
        Storage.SaveConfig(Config);
    }

    public void EvaluateLockState()
    {
        if (!Config.Enabled || _adminMaintenance)
        {
            HideLocks();
            HideActiveTimer();
            _security.SetLocked(false);
            return;
        }
        var shouldLock = !_timer.IsActive || _forcedScheduleLock;
        if (shouldLock)
        {
            HideActiveTimer();
            ShowLocks();
            _security.SetLocked(true);
        }
        else
        {
            HideLocks();
            ShowActiveTimer();
            _security.SetLocked(false);
        }
    }

    private void ShowLocks()
    {
        if (_locks.Count > 0)
        {
            foreach (var f in _locks) { if (!f.Visible) f.Show(); f.UpdateRemaining(_timer.RemainingSeconds); }
            return;
        }
        var screens = Screen.AllScreens;
        for (var i = 0; i < screens.Length; i++)
        {
            var form = new LockForm(Config, screens[i], i == 0);
            form.RequestCoin += async () => await RequestCentralCoinAsync();
            form.MemberLogin += () => _ = OpenMemberLoginAsync();
            form.AdminSequenceArmRequested += () => _security.ArmAdminSecret(TimeSpan.FromSeconds(Math.Max(5, Config.AdminSecretWindowSeconds)));
            form.UpdateRemaining(_timer.RemainingSeconds);
            _locks.Add(form);
            form.Show();
        }
    }

    private void HideLocks()
    {
        foreach (var f in _locks.ToArray())
        {
            try { f.AllowClose = true; f.Close(); f.Dispose(); } catch { }
        }
        _locks.Clear();
    }

    private void ShowActiveTimer()
    {
        if (!Config.ShowActiveTimerOverlay || Config.TimerSource == TimerSourceMode.ExternalTimerBoard)
        {
            HideActiveTimer();
            return;
        }

        if (_activeTimer is null || _activeTimer.IsDisposed)
        {
            _activeTimer = new ActiveTimerForm(Config);
            _activeTimer.BankRequested += () => _ = OpenMemberBankFromOverlayAsync();
            _activeTimer.UpdateRemaining(_timer.RemainingSeconds);
            _activeTimer.Show();
        }
        else
        {
            _activeTimer.UpdateRemaining(_timer.RemainingSeconds);
            if (!_activeTimer.Visible) _activeTimer.Show();
        }
    }

    private void HideActiveTimer()
    {
        if (_activeTimer is null) return;
        try { _activeTimer.Close(); _activeTimer.Dispose(); } catch { }
        _activeTimer = null;
    }

    private async Task OpenMemberBankFromOverlayAsync()
    {
        if (!Config.AllowMemberBankFromOverlay || !_timer.IsActive) return;
        using var bank = new MemberBankForm();
        if (bank.ShowDialog() != DialogResult.OK) return;

        if (!Config.BlazePwifiMemberAuthorityEnabled)
        {
            if (_timer.BankCurrentTime(bank.Username, bank.Password))
            {
                SetLockStatus("Time banked to member account", true);
                EvaluateLockState();
            }
            else
            {
                MessageBox.Show(
                    "Could not bank the remaining time. Check the member username/password.",
                    "BlazePisonet SoftTimer",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Warning);
            }
            return;
        }

        var member = await GetRemoteMemberAsync(bank.Username);
        if (member is null)
        {
            MessageBox.Show(
                "This member is not available in the BlazePwifi member list. Manage members from BlazePwifi Admin.",
                "BlazePisonet SoftTimer",
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning);
            return;
        }

        var seconds = _timer.RemainingSeconds;
        if (seconds <= 0) return;

        _timer.Pause(true);
        try
        {
            var result = await _blazePwifi.BankMemberAsync(member, bank.Password, seconds);
            if (result is null)
            {
                MessageBox.Show(
                    "BlazePwifi did not confirm the member bank operation. The running time was kept on this PC.",
                    "BlazePisonet SoftTimer",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Warning);
                return;
            }

            _timer.Reset($"banked to BlazePwifi member {member.Username}");
            SetLockStatus($"Time banked to {member.Username}", true);
            await _blazePwifi.SyncMembersAsync();
            EvaluateLockState();
        }
        finally
        {
            _timer.Pause(false);
        }
    }

    public void PlayWarningPreview() => WarningSound.Play(Config);

    private void OnRemainingChanged(long seconds)
    {
        BeginInvokeUi(() =>
        {
            foreach (var f in _locks) f.UpdateRemaining(seconds);
            _activeTimer?.UpdateRemaining(seconds);

            if (seconds == 0 || seconds > Math.Max(1, Config.WarningSeconds))
                _warningPlayed = false;
            else if (!_warningPlayed
                && Config.WarningSoundEnabled
                && Config.TimerSource != TimerSourceMode.ExternalTimerBoard
                && Config.WarningSeconds > 0)
            {
                _warningPlayed = true;
                WarningSound.Play(Config);
                _activeTimer?.SetStatus($"LOW TIME · {BlazeTheme.FormatTime(seconds)}", false, true);
                Storage.Log($"Low-time warning triggered at {seconds}s remaining.");
            }

            StatusChanged?.Invoke();
            if (seconds == 0 && Config.AutoShutdownAtZero && Config.TimerSource == TimerSourceMode.InternalPcTimer)
                ConfirmOrShutdown("Paid time has ended.");
        });
    }

    private async Task OpenMemberLoginAsync()
    {
        using var login = new MemberLoginForm();
        if (login.ShowDialog() != DialogResult.OK) return;

        if (!Config.BlazePwifiMemberAuthorityEnabled)
        {
            if (!_timer.RestoreMemberTime(login.Username, login.Password))
            {
                SetLockStatus("Invalid member account or no banked time", false, true);
                return;
            }
            SetLockStatus("Member time restored", true);
            return;
        }

        var member = await GetRemoteMemberAsync(login.Username);
        if (member is null || !member.Enabled)
        {
            SetLockStatus("Member unavailable in BlazePwifi", false, true);
            return;
        }

        var result = await _blazePwifi.RestoreMemberAsync(member, login.Password);
        if (result is null)
        {
            SetLockStatus("BlazePwifi member login failed or server is offline", false, true);
            return;
        }

        if (result.ResultSeconds <= 0)
        {
            SetLockStatus("Member authenticated · no banked time", false, true);
            await _blazePwifi.SyncMembersAsync();
            return;
        }

        _timer.AddSeconds(
            result.ResultSeconds,
            $"blazepwifi-member:{result.EventId}",
            false,
            $"BlazePwifi member time restored: {member.Username}");

        await _blazePwifi.SyncMembersAsync();
        SetLockStatus($"Member time restored · {member.Username}", true);
    }

    private async Task<MemberAccount?> GetRemoteMemberAsync(string username)
    {
        var member = _timer.RemoteMember(username);
        if (member is not null) return member;

        await _blazePwifi.SyncMembersAsync();
        return _timer.RemoteMember(username);
    }

    public async Task<bool> BankTimeToMemberAsync(string user, string pass)
    {
        if (!Config.BlazePwifiMemberAuthorityEnabled)
            return _timer.BankCurrentTime(user, pass);

        var member = await GetRemoteMemberAsync(user);
        if (member is null || !_timer.IsActive) return false;

        var seconds = _timer.RemainingSeconds;
        _timer.Pause(true);
        try
        {
            var result = await _blazePwifi.BankMemberAsync(member, pass, seconds);
            if (result is null) return false;
            _timer.Reset($"banked to BlazePwifi member {member.Username}");
            await _blazePwifi.SyncMembersAsync();
            return true;
        }
        finally
        {
            _timer.Pause(false);
        }
    }

    private async Task MaintenanceTick()
    {
        if (!Config.Enabled) return;
        if (Config.TimerSource is TimerSourceMode.InternalPcTimer or TimerSourceMode.ExternalTimerBoard && Config.CoinTopology != CoinTopologyMode.CentralizedStation)
        {
            if (!_serial.IsConnected) _serial.TryReconnect(Config);
            if (Config.TimerSource == TimerSourceMode.ExternalTimerBoard) UpdateExternalBoard();
        }

        EvaluateSchedules();
        if (Config.IdleShutdownEnabled && WindowsSecurity.GetIdleTime() >= TimeSpan.FromMinutes(Math.Max(1, Config.IdleShutdownMinutes)))
            ConfirmOrShutdown("No active user detected.");

        if (Config.CoinTopology == CoinTopologyMode.CentralizedStation && DateTimeOffset.UtcNow - _lastQueuePoll > TimeSpan.FromSeconds(2))
        {
            _lastQueuePoll = DateTimeOffset.UtcNow;
            var state = await PeerClient.GetQueueStateAsync(Config);
            if (state is not null)
            {
                if (state.Position == 0) SetLockStatus("COIN SLOT READY · INSERT COIN", true);
                else if (state.Position > 0) SetLockStatus($"Waiting for coin slot · queue position {state.Position}", false, true);
            }
        }
    }

    private void EvaluateSchedules()
    {
        var now = DateTime.Now;
        var t = now.TimeOfDay;
        var forced = false;
        var liveShutdownWindows = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        for (var i = 0; i < Config.NotificationSchedules.Count; i++)
        {
            var s = Config.NotificationSchedules[i];
            if (!s.Enabled) continue;

            var overnight = s.Start > s.End;
            var inWindow = overnight ? t >= s.Start || t < s.End : t >= s.Start && t < s.End;
            if (!inWindow) continue;

            var anchorDate = overnight && t < s.End ? now.Date.AddDays(-1) : now.Date;
            if (!s.Days.Contains(anchorDate.DayOfWeek)) continue;

            if (s.LockDuringWindow) forced = true;
            if (!string.IsNullOrWhiteSpace(s.Message)) SetLockStatus(s.Message, false, true);

            if (s.ShutdownDuringWindow)
            {
                var key = $"{i}:{anchorDate:yyyyMMdd}:{s.Start:c}:{s.End:c}";
                liveShutdownWindows.Add(key);
                if (_activeScheduleShutdownWindows.Add(key))
                    ConfirmOrShutdown(string.IsNullOrWhiteSpace(s.Message) ? "Scheduled closing time." : s.Message, true);
            }
        }

        _activeScheduleShutdownWindows.RemoveWhere(k => !liveShutdownWindows.Contains(k));

        if (forced != _forcedScheduleLock)
        {
            _forcedScheduleLock = forced;
            EvaluateLockState();
        }
    }

    private void ConfirmOrShutdown(string reason, bool forcePolicy = false)
    {
        if (_shutdownPrompted || !forcePolicy && !Config.AutoShutdownAtZero && !Config.IdleShutdownEnabled && !Config.UnusualInputShutdownEnabled) return;
        _shutdownPrompted = true;
        Storage.Log("Shutdown policy triggered: " + reason);
        var grace = Math.Max(15, Config.ShutdownGraceSeconds);
        try
        {
            Process.Start(new ProcessStartInfo("shutdown.exe", $"/s /f /t {grace}")
            {
                UseShellExecute = false,
                CreateNoWindow = true
            });
        }
        catch (Exception ex)
        {
            Storage.Log("Could not schedule Windows shutdown: " + ex.Message);
            _shutdownPrompted = false;
            return;
        }

        var result = MessageBox.Show(
            reason + $"\n\nWindows will shut down in {grace} seconds. Press Cancel to abort the shutdown.",
            "BlazePisonet SoftTimer",
            MessageBoxButtons.OKCancel,
            MessageBoxIcon.Warning,
            MessageBoxDefaultButton.Button2,
            MessageBoxOptions.ServiceNotification);

        if (result == DialogResult.Cancel)
        {
            try
            {
                Process.Start(new ProcessStartInfo("shutdown.exe", "/a")
                {
                    UseShellExecute = false,
                    CreateNoWindow = true
                });
                Storage.Log("Scheduled shutdown cancelled by user/admin.");
            }
            catch (Exception ex) { Storage.Log("Could not abort scheduled shutdown: " + ex.Message); }
        }
        _shutdownPrompted = false;
    }

    private void SetLockStatus(string text, bool good = false, bool warn = false)
    {
        BeginInvokeUi(() =>
        {
            foreach (var f in _locks) f.SetStatus(text, good, warn);
            _activeTimer?.SetStatus(text, good, warn);
        });
    }

    private void BeginInvokeUi(Action action)
    {
        if (_mainForm is not null && _mainForm.IsHandleCreated)
        {
            if (_mainForm.InvokeRequired) _mainForm.BeginInvoke(action); else action();
        }
        else action();
    }

    private void EnsureWatchdog()
    {
        try
        {
            if (Process.GetProcessesByName("BlazePisonet.SoftTimer.Watchdog").Length > 0) return;
            var exe = Path.Combine(AppContext.BaseDirectory, "BlazePisonet.SoftTimer.Watchdog.exe");
            if (File.Exists(exe)) Process.Start(new ProcessStartInfo(exe) { UseShellExecute = true, WorkingDirectory = AppContext.BaseDirectory });
        }
        catch (Exception ex) { Storage.Log("Could not start watchdog: " + ex.Message); }
    }

    public void Dispose()
    {
        _maintenanceTimer.Stop();
        HideLocks();
        HideActiveTimer();
        WarningSound.Stop();
        _centralServer?.Dispose();
        _blazePwifi.Dispose();
        _blazeTimer.Dispose();
        _serial.Dispose();
        _security.Dispose();
        _timer.Dispose();
    }
}
