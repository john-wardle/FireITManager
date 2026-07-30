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
    private readonly NetworkMapBuilder _networkMapBuilder = new();

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
    private string _mapSearchText = "";
    private string _mapStatusFilter = NetworkMapBuilder.AllStatusesFilter;
    private string _mapTypeFilter = NetworkMapBuilder.AllTypesFilter;
    private string _mapNetworkFilter = NetworkMapBuilder.AllNetworksFilter;
    private string _mapCampFilter = NetworkMapBuilder.AllCampsFilter;
    private string _mapDeviceTypeFilter = NetworkMapBuilder.AllDeviceTypesFilter;
    private string _mapSummaryText = "No map data loaded.";
    private string? _incidentId;
    private NetworkMapNode? _selectedMapNode;
    private NetworkMapLink? _selectedMapLink;
    private int _incidentVersion;
    private int _selectedWorkspaceIndex;
    private double _mapCanvasWidth = 820;
    private double _mapCanvasHeight = 520;
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
        SelectMapWorkspaceCommand = new RelayCommand(() => SelectedWorkspaceIndex = 3);
        SelectNetworkWorkspaceCommand = new RelayCommand(() => SelectedWorkspaceIndex = 4);
        SelectOutputsWorkspaceCommand = new RelayCommand(() => SelectedWorkspaceIndex = 5);
        SelectMapNodeCommand = new RelayCommand<NetworkMapNode>(node => SelectedMapNode = node);
        ClearMapFiltersCommand = new RelayCommand(ClearMapFilters);

        Replace(StatusLegend, _networkMapBuilder.BuildLegend());
        RefreshNetworkMap();

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
    public ObservableCollection<AuditEventItem> AuditEvents { get; } = [];
    public ObservableCollection<IncidentClientConnection> RealtimeConnections { get; } = [];
    public ObservableCollection<string> ValidationMessages { get; } = [];
    public ObservableCollection<string> ActivityLog { get; } = [];
    public ObservableCollection<NetworkMapNode> MapNodes { get; } = [];
    public ObservableCollection<NetworkMapLink> MapLinks { get; } = [];
    public ObservableCollection<StatusLegendItem> StatusLegend { get; } = [];
    public ObservableCollection<string> MapStatusFilters { get; } = [];
    public ObservableCollection<string> MapTypeFilters { get; } = [];
    public ObservableCollection<string> MapNetworkFilters { get; } = [];
    public ObservableCollection<string> MapCampFilters { get; } = [];
    public ObservableCollection<string> MapDeviceTypeFilters { get; } = [];
    public ObservableCollection<string> MapStatusHistory { get; } = [];

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
    public RelayCommand SelectMapWorkspaceCommand { get; }
    public RelayCommand SelectNetworkWorkspaceCommand { get; }
    public RelayCommand SelectOutputsWorkspaceCommand { get; }
    public RelayCommand<NetworkMapNode> SelectMapNodeCommand { get; }
    public RelayCommand ClearMapFiltersCommand { get; }

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

    public string MapSearchText
    {
        get => _mapSearchText;
        set
        {
            if (SetProperty(ref _mapSearchText, value))
            {
                RefreshNetworkMap();
            }
        }
    }

    public string MapStatusFilter
    {
        get => _mapStatusFilter;
        set
        {
            if (SetProperty(ref _mapStatusFilter, string.IsNullOrWhiteSpace(value) ? NetworkMapBuilder.AllStatusesFilter : value))
            {
                RefreshNetworkMap();
            }
        }
    }

    public string MapTypeFilter
    {
        get => _mapTypeFilter;
        set
        {
            if (SetProperty(ref _mapTypeFilter, string.IsNullOrWhiteSpace(value) ? NetworkMapBuilder.AllTypesFilter : value))
            {
                RefreshNetworkMap();
            }
        }
    }

    public string MapNetworkFilter
    {
        get => _mapNetworkFilter;
        set
        {
            if (SetProperty(ref _mapNetworkFilter, string.IsNullOrWhiteSpace(value) ? NetworkMapBuilder.AllNetworksFilter : value))
            {
                RefreshNetworkMap();
            }
        }
    }

    public string MapCampFilter
    {
        get => _mapCampFilter;
        set
        {
            if (SetProperty(ref _mapCampFilter, string.IsNullOrWhiteSpace(value) ? NetworkMapBuilder.AllCampsFilter : value))
            {
                RefreshNetworkMap();
            }
        }
    }

    public string MapDeviceTypeFilter
    {
        get => _mapDeviceTypeFilter;
        set
        {
            if (SetProperty(ref _mapDeviceTypeFilter, string.IsNullOrWhiteSpace(value) ? NetworkMapBuilder.AllDeviceTypesFilter : value))
            {
                RefreshNetworkMap();
            }
        }
    }

    public double MapCanvasWidth
    {
        get => _mapCanvasWidth;
        private set => SetProperty(ref _mapCanvasWidth, value);
    }

    public double MapCanvasHeight
    {
        get => _mapCanvasHeight;
        private set => SetProperty(ref _mapCanvasHeight, value);
    }

    public string MapSummaryText
    {
        get => _mapSummaryText;
        private set => SetProperty(ref _mapSummaryText, value);
    }

    public NetworkMapNode? SelectedMapNode
    {
        get => _selectedMapNode;
        set
        {
            if (SetProperty(ref _selectedMapNode, value))
            {
                if (value is not null && _selectedMapLink is not null)
                {
                    _selectedMapLink = null;
                    OnPropertyChanged(nameof(SelectedMapLink));
                }

                RefreshSelectedMapDetails();
            }
        }
    }

    public NetworkMapLink? SelectedMapLink
    {
        get => _selectedMapLink;
        set
        {
            if (SetProperty(ref _selectedMapLink, value))
            {
                if (value is not null && _selectedMapNode is not null)
                {
                    _selectedMapNode = null;
                    OnPropertyChanged(nameof(SelectedMapNode));
                }

                RefreshSelectedMapDetails();
            }
        }
    }

    public string SelectedMapDetailTitle =>
        SelectedMapLink?.Title ??
        SelectedMapNode?.Title ??
        "No map object selected";

    public string SelectedMapDetailText
    {
        get
        {
            if (SelectedMapLink is not null)
            {
                return BuildSelectedLinkDetail(SelectedMapLink);
            }

            if (SelectedMapNode is not null)
            {
                return BuildSelectedNodeDetail(SelectedMapNode);
            }

            return "Select a node on the map or a link in the link list.";
        }
    }

    public string SelectedMapHistoryTitle =>
        SelectedMapLink is not null ? "Selected Link History" : "Selected Object History";

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
            Replace(AuditEvents, cache.AuditEvents ?? []);
            RefreshNetworkMap();
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
        Replace(AuditEvents, await _serverClient.ListAuditEventsAsync());
        Replace(RealtimeConnections, await _serverClient.ListRealtimeConnectionsAsync());
        RefreshNetworkMap();
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
            CachedAtUtc: DateTimeOffset.UtcNow,
            AuditEvents: AuditEvents.ToList());
    }

    private void RefreshNetworkMap()
    {
        RefreshMapFilterOptions();

        var previousNodeId = SelectedMapNode?.Id;
        var previousLinkId = SelectedMapLink?.Id;
        var result = _networkMapBuilder.Build(
            Camps,
            Devices,
            Networks,
            Links,
            MapSearchText,
            MapStatusFilter,
            MapTypeFilter,
            MapNetworkFilter,
            MapCampFilter,
            MapDeviceTypeFilter);

        Replace(MapNodes, result.Nodes);
        Replace(MapLinks, result.Links);
        MapCanvasWidth = result.CanvasWidth;
        MapCanvasHeight = result.CanvasHeight;
        MapSummaryText = result.Summary;

        _selectedMapNode = previousNodeId is null
            ? null
            : MapNodes.FirstOrDefault(node => string.Equals(node.Id, previousNodeId, StringComparison.OrdinalIgnoreCase));
        _selectedMapLink = previousLinkId is null
            ? null
            : MapLinks.FirstOrDefault(link => string.Equals(link.Id, previousLinkId, StringComparison.OrdinalIgnoreCase));
        OnPropertyChanged(nameof(SelectedMapNode));
        OnPropertyChanged(nameof(SelectedMapLink));
        RefreshSelectedMapDetails();
    }

    private void RefreshMapFilterOptions()
    {
        Replace(MapStatusFilters, new[]
        {
            NetworkMapBuilder.AllStatusesFilter,
            "down",
            "degraded",
            "unknown",
            "maintenance",
            "disabled",
            "planned",
            "up"
        });
        Replace(MapTypeFilters, new[]
        {
            NetworkMapBuilder.AllTypesFilter,
            "Camp",
            "Building",
            "Device",
            "Link",
            "Network",
            "Service",
            "VLAN",
            "WAN",
            "Wireless"
        });
        Replace(MapNetworkFilters, new[] { NetworkMapBuilder.AllNetworksFilter }
            .Concat(Networks.Select(item => item.Title))
            .Where(value => !string.IsNullOrWhiteSpace(value))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .OrderBy(value => value, StringComparer.OrdinalIgnoreCase));
        Replace(MapCampFilters, new[] { NetworkMapBuilder.AllCampsFilter }
            .Concat(Camps.Select(item => item.Title))
            .Where(value => !string.IsNullOrWhiteSpace(value))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .OrderBy(value => value, StringComparer.OrdinalIgnoreCase));
        Replace(MapDeviceTypeFilters, new[] { NetworkMapBuilder.AllDeviceTypesFilter }
            .Concat(Devices.Select(item => item.DeviceType))
            .Where(value => !string.IsNullOrWhiteSpace(value))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .OrderBy(value => value, StringComparer.OrdinalIgnoreCase));

        EnsureFilterValue(MapStatusFilters, ref _mapStatusFilter, NetworkMapBuilder.AllStatusesFilter, nameof(MapStatusFilter));
        EnsureFilterValue(MapTypeFilters, ref _mapTypeFilter, NetworkMapBuilder.AllTypesFilter, nameof(MapTypeFilter));
        EnsureFilterValue(MapNetworkFilters, ref _mapNetworkFilter, NetworkMapBuilder.AllNetworksFilter, nameof(MapNetworkFilter));
        EnsureFilterValue(MapCampFilters, ref _mapCampFilter, NetworkMapBuilder.AllCampsFilter, nameof(MapCampFilter));
        EnsureFilterValue(MapDeviceTypeFilters, ref _mapDeviceTypeFilter, NetworkMapBuilder.AllDeviceTypesFilter, nameof(MapDeviceTypeFilter));
    }

    private void ClearMapFilters()
    {
        MapSearchText = "";
        MapStatusFilter = NetworkMapBuilder.AllStatusesFilter;
        MapTypeFilter = NetworkMapBuilder.AllTypesFilter;
        MapNetworkFilter = NetworkMapBuilder.AllNetworksFilter;
        MapCampFilter = NetworkMapBuilder.AllCampsFilter;
        MapDeviceTypeFilter = NetworkMapBuilder.AllDeviceTypesFilter;
    }

    private void RefreshSelectedMapDetails()
    {
        OnPropertyChanged(nameof(SelectedMapDetailTitle));
        OnPropertyChanged(nameof(SelectedMapDetailText));
        OnPropertyChanged(nameof(SelectedMapHistoryTitle));

        MapStatusHistory.Clear();
        if (SelectedMapLink is not null)
        {
            AddSelectedHistory(
                "link",
                SelectedMapLink.Id,
                $"{SelectedMapLink.StatusLabel} | {SelectedMapLink.LastSeenText}");
            return;
        }

        if (SelectedMapNode is not null)
        {
            AddSelectedHistory(
                ToAuditTargetType(SelectedMapNode),
                SelectedMapNode.Id,
                $"{SelectedMapNode.StatusLabel} | {SelectedMapNode.LastSeenText}");
        }
    }

    private void AddSelectedHistory(
        string targetType,
        string targetId,
        string currentStatus)
    {
        MapStatusHistory.Add($"Current: {currentStatus}");

        if (string.IsNullOrWhiteSpace(targetType) || string.IsNullOrWhiteSpace(targetId))
        {
            MapStatusHistory.Add("No audit target is available for this map object.");
            return;
        }

        var history = AuditEvents
            .Where(item =>
                string.Equals(item.TargetType, targetType, StringComparison.OrdinalIgnoreCase) &&
                string.Equals(item.TargetId, targetId, StringComparison.OrdinalIgnoreCase))
            .OrderByDescending(item => item.OccurredAtUtc)
            .Take(12)
            .ToList();

        if (history.Count == 0)
        {
            MapStatusHistory.Add("No audit events recorded for this object yet.");
            return;
        }

        foreach (var item in history)
        {
            MapStatusHistory.Add($"{item.OccurredAtUtc.LocalDateTime:g} | {item.Action} | {item.ActorId} | {item.Summary}");
        }
    }

    private string BuildSelectedNodeDetail(NetworkMapNode node)
    {
        var camp = FindTitle(Camps, node.CampId);
        var network = FindTitle(Networks, node.NetworkId);

        return JoinLines(
            $"Type: {node.ObjectType}",
            $"Status: {node.StatusLabel}",
            $"Priority: {node.StatusPriority}",
            $"Camp: {camp}",
            $"Network: {network}",
            $"Device type: {node.DeviceType}",
            node.LastSeenText,
            node.Detail);
    }

    private string BuildSelectedLinkDetail(NetworkMapLink link)
    {
        var camp = FindTitle(Camps, link.CampId);
        var network = FindTitle(Networks, link.NetworkId);

        return JoinLines(
            $"Type: {link.ObjectType}",
            $"Status: {link.StatusLabel}",
            $"Priority: {link.StatusPriority}",
            $"Direction: {link.SourceLabel} -> {link.TargetLabel}",
            $"Category: {link.LinkCategory}",
            $"Link type: {link.LinkType}",
            $"Camp: {camp}",
            $"Network: {network}",
            link.LastSeenText,
            link.Detail);
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
        RefreshNetworkMap();
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

    private void EnsureFilterValue(
        ObservableCollection<string> options,
        ref string field,
        string fallback,
        string propertyName)
    {
        var currentValue = field;
        if (options.Any(item => string.Equals(item, currentValue, StringComparison.OrdinalIgnoreCase)))
        {
            return;
        }

        field = fallback;
        OnPropertyChanged(propertyName);
    }

    private static string ToAuditTargetType(NetworkMapNode node) =>
        node.ObjectType switch
        {
            "Camp" => "camp",
            "Device" => "device",
            "Network" or "Service" or "VLAN" or "WAN" or "Wireless" => "network",
            _ => ""
        };

    private static string FindTitle(IEnumerable<EntityListItem> items, string? id) =>
        string.IsNullOrWhiteSpace(id)
            ? ""
            : items.FirstOrDefault(item => string.Equals(item.Id, id, StringComparison.OrdinalIgnoreCase))?.Title ?? "";

    private static string JoinLines(params string[] values) =>
        string.Join(Environment.NewLine, values.Where(value => !string.IsNullOrWhiteSpace(value)));

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
