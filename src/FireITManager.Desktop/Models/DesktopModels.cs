using System.Text.Json.Serialization;
using System.Windows.Media;

namespace FireITManager.Desktop.Models;

internal sealed record IncidentSummary(
    string Id,
    string IncidentNumber,
    string Name,
    string Agency,
    DateTimeOffset? OperationalPeriodStartUtc,
    DateTimeOffset? OperationalPeriodEndUtc,
    DateTimeOffset CreatedAtUtc,
    DateTimeOffset UpdatedAtUtc,
    int Version);

internal sealed record IncidentSummaryRequest(
    string? Id,
    string IncidentNumber,
    string Name,
    string Agency,
    DateTimeOffset? OperationalPeriodStartUtc,
    DateTimeOffset? OperationalPeriodEndUtc,
    int? ExpectedVersion);

internal sealed record EntityListItem(
    string Id,
    string Title,
    string Status,
    int Version,
    string Detail,
    DateTimeOffset? UpdatedAtUtc,
    string Kind = "",
    string? IncidentId = null,
    string? CampId = null,
    string? NetworkId = null,
    string? LocationId = null,
    string? SourceDeviceId = null,
    string? DestinationDeviceId = null,
    string? SourceLocationId = null,
    string? DestinationLocationId = null,
    string SourceRef = "",
    string DestinationRef = "",
    string LinkCategory = "",
    string LinkType = "",
    string NetworkType = "",
    string DeviceType = "",
    string CampType = "",
    string Label = "",
    string Length = "",
    string Path = "",
    string Notes = "",
    string SearchText = "",
    bool ManualOverride = false);

internal sealed record AuditEventItem(
    string Id,
    string IncidentId,
    string ActorType,
    string ActorId,
    string Action,
    string TargetType,
    string TargetId,
    DateTimeOffset OccurredAtUtc,
    string Summary);

internal sealed record StatusLegendItem(
    string Status,
    string Label,
    Brush Brush,
    int Priority,
    string Meaning);

internal sealed record NetworkMapNode(
    string Id,
    string Title,
    string ObjectType,
    string Status,
    int StatusPriority,
    Brush StatusBrush,
    double X,
    double Y,
    double Width,
    double Height,
    string Detail,
    DateTimeOffset? LastSeenAtUtc,
    bool ManualOverride,
    string? CampId,
    string? NetworkId,
    string DeviceType,
    string SearchText)
{
    public string StatusLabel => ManualOverride ? $"{Status} manual" : Status;

    public string LastSeenText => LastSeenAtUtc is null
        ? "No status timestamp"
        : $"Last seen {LastSeenAtUtc.Value.LocalDateTime:g}";

    public string ManualOverrideText => ManualOverride ? "Manual override" : "";
}

internal sealed record NetworkMapLink(
    string Id,
    string Title,
    string ObjectType,
    string Status,
    int StatusPriority,
    Brush StatusBrush,
    double SourceX,
    double SourceY,
    double TargetX,
    double TargetY,
    double LabelX,
    double LabelY,
    string SourceNodeId,
    string TargetNodeId,
    string SourceLabel,
    string TargetLabel,
    string LinkCategory,
    string LinkType,
    string Detail,
    DateTimeOffset? LastSeenAtUtc,
    bool ManualOverride,
    string? CampId,
    string? NetworkId,
    string SearchText)
{
    public string StatusLabel => ManualOverride ? $"{Status} manual" : Status;

    public string LastSeenText => LastSeenAtUtc is null
        ? "No status timestamp"
        : $"Last seen {LastSeenAtUtc.Value.LocalDateTime:g}";

    public string TypeLabel => string.Join(" / ", new[] { LinkCategory, LinkType }
        .Where(value => !string.IsNullOrWhiteSpace(value)));

    public string DirectionLabel => string.IsNullOrWhiteSpace(TypeLabel)
        ? $"{SourceLabel} -> {TargetLabel}"
        : $"{SourceLabel} -> {TargetLabel} | {TypeLabel}";
}

internal sealed record IncidentClientConnection(
    string ConnectionId,
    string UserId,
    string ClientName,
    string ClientKind,
    string RemoteAddress,
    DateTimeOffset ConnectedAtUtc,
    DateTimeOffset LastSeenAtUtc);

internal sealed record IncidentChangeEvent(
    long Sequence,
    string EventId,
    string ChangeType,
    string EntityType,
    string EntityId,
    string? IncidentId,
    int? Version,
    string ActorId,
    string Summary,
    DateTimeOffset OccurredAtUtc);

internal sealed record ClientConnectionChange(
    string ConnectionId,
    string ChangeType,
    DateTimeOffset ChangedAtUtc);

internal sealed record ConflictMessage(
    string Message,
    int CurrentVersion);

internal sealed record HealthResponse(
    string Status,
    string Service,
    string DatabaseStatus,
    IReadOnlyList<string> AppliedMigrations,
    DateTimeOffset CheckedAtUtc);

internal sealed record DesktopCache(
    string ServerUrl,
    string UserId,
    string UserRole,
    IncidentSummary? Incident,
    IReadOnlyList<EntityListItem> Camps,
    IReadOnlyList<EntityListItem> Devices,
    IReadOnlyList<EntityListItem> Networks,
    IReadOnlyList<EntityListItem> Links,
    IReadOnlyList<EntityListItem> ChecklistRuns,
    DateTimeOffset CachedAtUtc,
    IReadOnlyList<AuditEventItem>? AuditEvents = null);
