using System.Text.Json.Serialization;

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
    DateTimeOffset? UpdatedAtUtc);

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
    DateTimeOffset CachedAtUtc);
