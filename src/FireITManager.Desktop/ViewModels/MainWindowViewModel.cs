using FireITManager.Desktop.Models;
using FireITManager.Desktop.Services;
using System.Collections.ObjectModel;
using System.Windows;
using System.Windows.Media;

namespace FireITManager.Desktop.ViewModels;

internal sealed class MainWindowViewModel : ObservableObject, IAsyncDisposable
{
    private readonly IncidentServerClient _serverClient = new();
    private readonly IncidentRealtimeClient _realtimeClient = new();
    private readonly LocalCacheService _cacheService = new();
    private readonly OutputWorkflowService _outputWorkflow = new();

    private string _serverUrl = "http://localhost:5000";
    private string _userId = Environment.UserName;
    private string _userRole = "ITSS";
    private string _connectionStatus = "Disconnected";
    private string _lastSyncText = "No sync yet";
    private string _incidentNumber = "";
    private string _incidentName = "";
    private string _agency = "";
    private string _operationalPeriodStartUtcText = "";
    private string _operationalPeriodEndUtcText = "";
    private string _lastOutputPath = "";
    private string? _incidentId;
    private int _incidentVersion;
    private int _selectedWorkspaceIndex;
    private bool _isConnected;
    private bool _isBusy;

    public MainWindowViewModel()
    {
        _realtimeClient.StatusChanged += OnRealtimeStatusChanged;
        _realtimeClient.IncidentChanged += OnIncidentChanged;
        _realtimeClient.ClientConnectionChanged += OnClientConnectionChanged;
        _realtimeClient.ConnectionStatusReceived += OnConnectionStatusReceived;

        ConnectCommand = new AsyncRelayCommand(ConnectAsync, () => !IsBusy);
        RefreshCommand = new AsyncRelayCommand(RefreshAsync, () => !IsBusy);
        SaveIncidentCommand = new AsyncRelayCommand(SaveIncidentAsync, () => CanEdit && !IsBusy);
        LoadCacheCommand = new AsyncRelayCommand(LoadCacheAsync, () => !IsBusy);
        ExportBundleCommand = new AsyncRelayCommand(ExportBundleAsync, () => CanExport && !IsBusy);
        PrintSummaryCommand = new AsyncRelayCommand(PrintSummaryAsync, () => CanExport && !IsBusy);
        ValidateCommand = new RelayCommand(() => ValidateIncident(showSuccess: true));
        NewIncidentCommand = new RelayCommand(NewIncident, () => CanEdit);
        OpenOutputFolderCommand = new RelayCommand(_outputWorkflow.OpenOutputFolder);
        AboutCommand = new RelayCommand(ShowAbout);
        ExitCommand = new RelayCommand(() => Application.Current.MainWindow?.Close());
        SelectIncidentWorkspaceCommand = new RelayCommand(() => SelectedWorkspaceIndex = 0);
        SelectCampOpsWorkspaceCommand = new RelayCommand(() => SelectedWorkspaceIndex = 1);
        SelectInventoryWorkspaceCommand = new RelayCommand(() => SelectedWorkspaceIndex = 2);
        SelectNetworkWorkspaceCommand = new RelayCommand(() => SelectedWorkspaceIndex = 3);
        SelectOutputsWorkspaceCommand = new RelayCommand(() => SelectedWorkspaceIndex = 4);

        ActivityLog.Add("Desktop client ready.");
    }

    public IReadOnlyList<string> Roles { get; } =
    [
        "ITSS",
        "COML",
        "COMT",
        "Trainee",
        "Logistics",
        "Read-only Observer"
    ];

    public ObservableCollection<EntityListItem> Camps { get; } = [];
    public ObservableCollection<EntityListItem> Devices { get; } = [];
    public ObservableCollection<EntityListItem> Networks { get; } = [];
    public ObservableCollection<EntityListItem> Links { get; } = [];
    public ObservableCollection<EntityListItem> ChecklistRuns { get; } = [];
    public ObservableCollection<IncidentClientConnection> RealtimeConnections { get; } = [];
    public ObservableCollection<string> ValidationMessages { get; } = [];
    public ObservableCollection<string> ActivityLog { get; } = [];

    public AsyncRelayCommand ConnectCommand { get; }
    public AsyncRelayCommand RefreshCommand { get; }
    public AsyncRelayCommand SaveIncidentCommand { get; }
    public AsyncRelayCommand LoadCacheCommand { get; }
    public AsyncRelayCommand ExportBundleCommand { get; }
    public AsyncRelayCommand PrintSummaryCommand { get; }
    public RelayCommand ValidateCommand { get; }
    public RelayCommand NewIncidentCommand { get; }
    public RelayCommand OpenOutputFolderCommand { get; }
    public RelayCommand AboutCommand { get; }
    public RelayCommand ExitCommand { get; }
    public RelayCommand SelectIncidentWorkspaceCommand { get; }
    public RelayCommand SelectCampOpsWorkspaceCommand { get; }
    public RelayCommand SelectInventoryWorkspaceCommand { get; }
    public RelayCommand SelectNetworkWorkspaceCommand { get; }
    public RelayCommand SelectOutputsWorkspaceCommand { get; }

    public string ServerUrl
    {
        get => _serverUrl;
        set => SetProperty(ref _serverUrl, value);
    }

    public string UserId
    {
        get => _userId;
        set => SetProperty(ref _userId, value);
    }

    public string UserRole
    {
        get => _userRole;
        set
        {
            if (SetProperty(ref _userRole, value))
            {
                OnPropertyChanged(nameof(CanEdit));
                OnPropertyChanged(nameof(CanExport));
                InvalidateCommands();
            }
        }
    }

    public string ConnectionStatus
    {
        get => _connectionStatus;
        private set => SetProperty(ref _connectionStatus, value);
    }

    public Brush ConnectionBrush =>
        IsConnected ? Brushes.ForestGreen : Brushes.Firebrick;

    public string LastSyncText
    {
        get => _lastSyncText;
        private set => SetProperty(ref _lastSyncText, value);
    }

    public string IncidentNumber
    {
        get => _incidentNumber;
        set
        {
            if (SetProperty(ref _incidentNumber, value))
            {
                OnPropertyChanged(nameof(CanExport));
                InvalidateCommands();
            }
        }
    }

    public string IncidentName
    {
        get => _incidentName;
        set
        {
            if (SetProperty(ref _incidentName, value))
            {
                OnPropertyChanged(nameof(CanExport));
                InvalidateCommands();
            }
        }
    }

    public string Agency
    {
        get => _agency;
        set
        {
            if (SetProperty(ref _agency, value))
            {
                OnPropertyChanged(nameof(CanExport));
                InvalidateCommands();
            }
        }
    }

    public string OperationalPeriodStartUtcText
    {
        get => _operationalPeriodStartUtcText;
        set => SetProperty(ref _operationalPeriodStartUtcText, value);
    }

    public string OperationalPeriodEndUtcText
    {
        get => _operationalPeriodEndUtcText;
        set => SetProperty(ref _operationalPeriodEndUtcText, value);
    }

    public string IncidentVersionText =>
        _incidentVersion > 0 ? $"Version {_incidentVersion}" : "New incident";

    public string LastOutputPath
    {
        get => _lastOutputPath;
        private set => SetProperty(ref _lastOutputPath, value);
    }

    public int SelectedWorkspaceIndex
    {
        get => _selectedWorkspaceIndex;
        set => SetProperty(ref _selectedWorkspaceIndex, value);
    }

    public bool IsConnected
    {
        get => _isConnected;
        private set
        {
            if (SetProperty(ref _isConnected, value))
            {
                OnPropertyChanged(nameof(ConnectionBrush));
                OnPropertyChanged(nameof(CanExport));
                InvalidateCommands();
            }
        }
    }

    public bool IsBusy
    {
        get => _isBusy;
        private set
        {
            if (SetProperty(ref _isBusy, value))
            {
                InvalidateCommands();
            }
        }
    }

    public bool CanEdit => !string.Equals(UserRole, "Read-only Observer", StringComparison.OrdinalIgnoreCase);

    public bool CanExport =>
        _incidentId is not null ||
        HasIncidentDraft() ||
        Camps.Count > 0 ||
        Devices.Count > 0 ||
        Networks.Count > 0 ||
        Links.Count > 0;

    public async Task ConnectAsync()
    {
        await RunBusyAsync(async () =>
        {
            _serverClient.Configure(ServerUrl);
            var health = await _serverClient.GetHealthAsync();
            IsConnected = true;
            ConnectionStatus = $"{health.Service} / {health.DatabaseStatus}";
            AddActivity($"Connected to {IncidentServerClient.NormalizeServerUrl(ServerUrl)}.");

            await RefreshCoreAsync();
            await _realtimeClient.ConnectAsync(
                ServerUrl,
                UserId,
                Environment.MachineName,
                "desktop");
        });
    }

    public async Task RefreshAsync()
    {
        await RunBusyAsync(async () =>
        {
            _serverClient.Configure(ServerUrl);
            await RefreshCoreAsync();
            AddActivity("Refreshed from server.");
        });
    }

    public async Task SaveIncidentAsync()
    {
        if (!ValidateIncident(showSuccess: false))
        {
            return;
        }

        await RunBusyAsync(async () =>
        {
            var request = new IncidentSummaryRequest(
                Id: _incidentId,
                IncidentNumber: IncidentNumber.Trim(),
                Name: IncidentName.Trim(),
                Agency: Agency.Trim(),
                OperationalPeriodStartUtc: ParseOptionalUtc(OperationalPeriodStartUtcText),
                OperationalPeriodEndUtc: ParseOptionalUtc(OperationalPeriodEndUtcText),
                ExpectedVersion: _incidentVersion > 0 ? _incidentVersion : null);

            try
            {
                _serverClient.Configure(ServerUrl);
                var saved = _incidentId is null
                    ? await _serverClient.CreateIncidentSummaryAsync(request, UserId)
                    : await _serverClient.UpdateIncidentSummaryAsync(request, UserId);

                ApplyIncident(saved);
                IsConnected = true;
                ConnectionStatus = "Incident saved.";
                await SaveCacheCoreAsync();
                AddActivity($"Saved incident summary version {saved.Version}.");
            }
            catch (IncidentConflictException ex)
            {
                ValidationMessages.Clear();
                ValidationMessages.Add($"{ex.Message} Current version: {ex.CurrentVersion ?? 0}.");
                AddActivity("Save blocked by stale incident version.");
                await RefreshCoreAsync();
            }
            catch (Exception ex)
            {
                await SaveCacheCoreAsync();
                IsConnected = false;
                ConnectionStatus = "Offline cache saved.";
                ValidationMessages.Clear();
                ValidationMessages.Add(ex.Message);
                AddActivity("Saved local cache after server write failed.");
            }
        });
    }

    public async Task LoadCacheAsync()
    {
        await RunBusyAsync(async () =>
        {
            var cache = await _cacheService.LoadAsync();
            if (cache is null)
            {
                AddActivity("No desktop cache found.");
                return;
            }

            ServerUrl = cache.ServerUrl;
            UserId = cache.UserId;
            UserRole = cache.UserRole;
            ApplyIncident(cache.Incident);
            Replace(Camps, cache.Camps);
            Replace(Devices, cache.Devices);
            Replace(Networks, cache.Networks);
            Replace(Links, cache.Links);
            Replace(ChecklistRuns, cache.ChecklistRuns);
            LastSyncText = $"Loaded cache {cache.CachedAtUtc:g}";
            AddActivity($"Loaded local cache from {_cacheService.CachePath}.");
        });
    }

    public async Task ExportBundleAsync()
    {
        await RunBusyAsync(async () =>
        {
            var path = await _outputWorkflow.ExportIncidentBundleAsync(BuildCache());
            LastOutputPath = path;
            AddActivity($"Exported incident bundle: {path}");
        });
    }

    public async Task PrintSummaryAsync()
    {
        await RunBusyAsync(async () =>
        {
            var path = await _outputWorkflow.CreatePrintSummaryAsync(BuildCache());
            LastOutputPath = path;
            AddActivity($"Created print summary: {path}");
        });
    }

    public async ValueTask DisposeAsync()
    {
        await _realtimeClient.DisposeAsync();
    }

    private async Task RefreshCoreAsync()
    {
        var incident = await _serverClient.GetIncidentSummaryAsync();
        ApplyIncident(incident);
        Replace(Camps, await _serverClient.ListCampsAsync());
        Replace(Devices, await _serverClient.ListDevicesAsync());
        Replace(Networks, await _serverClient.ListNetworksAsync());
        Replace(Links, await _serverClient.ListLinksAsync());
        Replace(ChecklistRuns, await _serverClient.ListChecklistRunsAsync());
        Replace(RealtimeConnections, await _serverClient.ListRealtimeConnectionsAsync());
        LastSyncText = $"Synced {DateTimeOffset.Now:g}";
        OnPropertyChanged(nameof(CanExport));
        InvalidateCommands();
        await SaveCacheCoreAsync();
    }

    private async Task SaveCacheCoreAsync()
    {
        await _cacheService.SaveAsync(BuildCache());
    }

    private DesktopCache BuildCache()
    {
        var incident = !HasIncidentDraft()
            ? null
            : new IncidentSummary(
                Id: _incidentId ?? "local-draft",
                IncidentNumber: IncidentNumber.Trim(),
                Name: IncidentName.Trim(),
                Agency: Agency.Trim(),
                OperationalPeriodStartUtc: ParseOptionalUtc(OperationalPeriodStartUtcText),
                OperationalPeriodEndUtc: ParseOptionalUtc(OperationalPeriodEndUtcText),
                CreatedAtUtc: DateTimeOffset.UtcNow,
                UpdatedAtUtc: DateTimeOffset.UtcNow,
                Version: _incidentVersion);

        return new DesktopCache(
            ServerUrl: ServerUrl,
            UserId: UserId,
            UserRole: UserRole,
            Incident: incident,
            Camps: Camps.ToList(),
            Devices: Devices.ToList(),
            Networks: Networks.ToList(),
            Links: Links.ToList(),
            ChecklistRuns: ChecklistRuns.ToList(),
            CachedAtUtc: DateTimeOffset.UtcNow);
    }

    private bool ValidateIncident(bool showSuccess)
    {
        ValidationMessages.Clear();

        if (string.IsNullOrWhiteSpace(IncidentNumber))
        {
            ValidationMessages.Add("Incident number is required.");
        }

        if (string.IsNullOrWhiteSpace(IncidentName))
        {
            ValidationMessages.Add("Incident name is required.");
        }

        if (string.IsNullOrWhiteSpace(Agency))
        {
            ValidationMessages.Add("Agency is required.");
        }

        if (!string.IsNullOrWhiteSpace(OperationalPeriodStartUtcText) &&
            ParseOptionalUtc(OperationalPeriodStartUtcText) is null)
        {
            ValidationMessages.Add("Operational start UTC is not a valid date/time.");
        }

        if (!string.IsNullOrWhiteSpace(OperationalPeriodEndUtcText) &&
            ParseOptionalUtc(OperationalPeriodEndUtcText) is null)
        {
            ValidationMessages.Add("Operational end UTC is not a valid date/time.");
        }

        if (ValidationMessages.Count == 0 && showSuccess)
        {
            ValidationMessages.Add("Validation passed.");
        }

        return ValidationMessages.Count == 0 ||
            (ValidationMessages.Count == 1 && ValidationMessages[0] == "Validation passed.");
    }

    private void NewIncident()
    {
        _incidentId = null;
        _incidentVersion = 0;
        IncidentNumber = "";
        IncidentName = "";
        Agency = "";
        OperationalPeriodStartUtcText = "";
        OperationalPeriodEndUtcText = "";
        ValidationMessages.Clear();
        OnPropertyChanged(nameof(IncidentVersionText));
        OnPropertyChanged(nameof(CanExport));
        InvalidateCommands();
        AddActivity("Started a new incident summary.");
    }

    private void ApplyIncident(IncidentSummary? incident)
    {
        if (incident is null)
        {
            _incidentId = null;
            _incidentVersion = 0;
            IncidentNumber = "";
            IncidentName = "";
            Agency = "";
            OperationalPeriodStartUtcText = "";
            OperationalPeriodEndUtcText = "";
            OnPropertyChanged(nameof(IncidentVersionText));
            return;
        }

        _incidentId = incident.Id;
        _incidentVersion = incident.Version;
        IncidentNumber = incident.IncidentNumber;
        IncidentName = incident.Name;
        Agency = incident.Agency;
        OperationalPeriodStartUtcText = FormatOptionalUtc(incident.OperationalPeriodStartUtc);
        OperationalPeriodEndUtcText = FormatOptionalUtc(incident.OperationalPeriodEndUtc);
        OnPropertyChanged(nameof(IncidentVersionText));
    }

    private async Task RunBusyAsync(Func<Task> work)
    {
        try
        {
            IsBusy = true;
            await work();
        }
        catch (Exception ex)
        {
            IsConnected = false;
            ConnectionStatus = "Disconnected";
            ValidationMessages.Clear();
            ValidationMessages.Add(ex.Message);
            AddActivity(ex.Message);
        }
        finally
        {
            IsBusy = false;
        }
    }

    private void OnRealtimeStatusChanged(object? sender, string status)
    {
        OnUiThread(() =>
        {
            ConnectionStatus = status;
            IsConnected =
                status.Contains("connected", StringComparison.OrdinalIgnoreCase) &&
                !status.Contains("disconnected", StringComparison.OrdinalIgnoreCase) &&
                !status.Contains("reconnecting", StringComparison.OrdinalIgnoreCase);
            AddActivity(status);
        });
    }

    private void OnIncidentChanged(object? sender, IncidentChangeEvent change)
    {
        OnUiThread(() =>
        {
            AddActivity($"{change.OccurredAtUtc:t} {change.Summary}");
            _ = RefreshAsync();
        });
    }

    private void OnClientConnectionChanged(object? sender, ClientConnectionChange change)
    {
        OnUiThread(() =>
        {
            AddActivity($"Client {change.ChangeType}: {change.ConnectionId}");
            _ = RefreshConnectionsAsync();
        });
    }

    private void OnConnectionStatusReceived(object? sender, IncidentClientConnection connection)
    {
        OnUiThread(() =>
        {
            UpsertConnection(connection);
            IsConnected = true;
            ConnectionStatus = $"Live as {connection.UserId}";
        });
    }

    private async Task RefreshConnectionsAsync()
    {
        try
        {
            Replace(RealtimeConnections, await _serverClient.ListRealtimeConnectionsAsync());
        }
        catch
        {
            // The status bar already reflects connection loss through the SignalR event.
        }
    }

    private void UpsertConnection(IncidentClientConnection connection)
    {
        var existing = RealtimeConnections.FirstOrDefault(item => item.ConnectionId == connection.ConnectionId);
        if (existing is not null)
        {
            RealtimeConnections.Remove(existing);
        }

        RealtimeConnections.Add(connection);
    }

    private void AddActivity(string message)
    {
        ActivityLog.Insert(0, $"{DateTimeOffset.Now:t} {message}");
        while (ActivityLog.Count > 80)
        {
            ActivityLog.RemoveAt(ActivityLog.Count - 1);
        }
    }

    private void InvalidateCommands()
    {
        ConnectCommand.RaiseCanExecuteChanged();
        RefreshCommand.RaiseCanExecuteChanged();
        SaveIncidentCommand.RaiseCanExecuteChanged();
        LoadCacheCommand.RaiseCanExecuteChanged();
        ExportBundleCommand.RaiseCanExecuteChanged();
        PrintSummaryCommand.RaiseCanExecuteChanged();
        NewIncidentCommand.RaiseCanExecuteChanged();
    }

    private void ShowAbout()
    {
        MessageBox.Show(
            "FireIT Manager desktop client",
            "About FireIT Manager",
            MessageBoxButton.OK,
            MessageBoxImage.Information);
    }

    private static DateTimeOffset? ParseOptionalUtc(string value)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            return null;
        }

        return DateTimeOffset.TryParse(value, out var parsed)
            ? parsed.ToUniversalTime()
            : null;
    }

    private static string FormatOptionalUtc(DateTimeOffset? value) =>
        value?.ToUniversalTime().ToString("O") ?? "";

    private bool HasIncidentDraft() =>
        !string.IsNullOrWhiteSpace(IncidentNumber) ||
        !string.IsNullOrWhiteSpace(IncidentName) ||
        !string.IsNullOrWhiteSpace(Agency) ||
        !string.IsNullOrWhiteSpace(OperationalPeriodStartUtcText) ||
        !string.IsNullOrWhiteSpace(OperationalPeriodEndUtcText);

    private static void Replace<T>(
        ObservableCollection<T> target,
        IEnumerable<T> source)
    {
        target.Clear();
        foreach (var item in source)
        {
            target.Add(item);
        }
    }

    private static void OnUiThread(Action action)
    {
        var dispatcher = Application.Current?.Dispatcher;
        if (dispatcher is not null && !dispatcher.CheckAccess())
        {
            dispatcher.Invoke(action);
            return;
        }

        action();
    }
}
