using Microsoft.AspNetCore.SignalR;
using System.Collections.Concurrent;

namespace FireITManager.Server.Realtime;

internal sealed class IncidentHub(
    IncidentRealtimeTracker tracker) : Hub
{
    public override async Task OnConnectedAsync()
    {
        var httpContext = Context.GetHttpContext();
        var request = httpContext?.Request;
        var connection = tracker.Open(
            Context.ConnectionId,
            request?.Query["userId"].ToString(),
            request?.Query["clientName"].ToString(),
            request?.Query["clientKind"].ToString(),
            httpContext?.Connection.RemoteIpAddress?.ToString());

        await Clients.Caller.SendAsync("ConnectionStatus", connection);
        await Clients.Others.SendAsync(
            "ClientConnectionChanged",
            new ClientConnectionChange(
                ConnectionId: connection.ConnectionId,
                ChangeType: "connected",
                ChangedAtUtc: DateTimeOffset.UtcNow));

        await base.OnConnectedAsync();
    }

    public async Task Ping()
    {
        var connection = tracker.Touch(Context.ConnectionId);
        if (connection is not null)
        {
            await Clients.Caller.SendAsync("ConnectionStatus", connection);
        }
    }

    public override async Task OnDisconnectedAsync(Exception? exception)
    {
        var closedConnection = tracker.Close(Context.ConnectionId);
        if (closedConnection is not null)
        {
            await Clients.Others.SendAsync(
                "ClientConnectionChanged",
                new ClientConnectionChange(
                    ConnectionId: closedConnection.ConnectionId,
                    ChangeType: "disconnected",
                    ChangedAtUtc: DateTimeOffset.UtcNow));
        }

        await base.OnDisconnectedAsync(exception);
    }
}

internal sealed class IncidentChangeBroadcaster(
    IHubContext<IncidentHub> hubContext)
{
    private long _nextSequence;

    public async Task PublishAsync(
        PendingIncidentChange change,
        CancellationToken cancellationToken = default)
    {
        var sequence = Interlocked.Increment(ref _nextSequence);
        var incidentChange = new IncidentChangeEvent(
            Sequence: sequence,
            EventId: $"{DateTimeOffset.UtcNow:yyyyMMddHHmmssffff}-{sequence}",
            ChangeType: change.ChangeType,
            EntityType: change.EntityType,
            EntityId: change.EntityId,
            IncidentId: change.IncidentId,
            Version: change.Version,
            ActorId: change.ActorId,
            Summary: change.Summary,
            OccurredAtUtc: DateTimeOffset.UtcNow);

        await hubContext.Clients.All.SendAsync(
            "IncidentChanged",
            incidentChange,
            cancellationToken);
    }
}

internal sealed class IncidentRealtimeTracker
{
    private readonly ConcurrentDictionary<string, IncidentClientConnection> _connections = new();

    public IncidentClientConnection Open(
        string connectionId,
        string? userId,
        string? clientName,
        string? clientKind,
        string? remoteAddress)
    {
        var now = DateTimeOffset.UtcNow;
        var connection = new IncidentClientConnection(
            ConnectionId: connectionId,
            UserId: CleanOrDefault(userId, "unknown-user"),
            ClientName: CleanOrDefault(clientName, "FireIT client"),
            ClientKind: CleanOrDefault(clientKind, "desktop"),
            RemoteAddress: remoteAddress ?? "",
            ConnectedAtUtc: now,
            LastSeenAtUtc: now);

        _connections[connectionId] = connection;
        return connection;
    }

    public IncidentClientConnection? Touch(string connectionId)
    {
        if (!_connections.TryGetValue(connectionId, out var connection))
        {
            return null;
        }

        var updatedConnection = connection with
        {
            LastSeenAtUtc = DateTimeOffset.UtcNow
        };
        _connections[connectionId] = updatedConnection;
        return updatedConnection;
    }

    public IncidentClientConnection? Close(string connectionId)
    {
        return _connections.TryRemove(connectionId, out var connection)
            ? connection
            : null;
    }

    public IReadOnlyList<IncidentClientConnection> Snapshot()
    {
        return _connections.Values
            .OrderBy(connection => connection.ConnectedAtUtc)
            .ToList();
    }

    public int RemoveStaleConnections(TimeSpan maxAge)
    {
        var cutoff = DateTimeOffset.UtcNow.Subtract(maxAge);
        var removed = 0;

        foreach (var connection in _connections.Values)
        {
            if (connection.LastSeenAtUtc >= cutoff)
            {
                continue;
            }

            if (_connections.TryRemove(connection.ConnectionId, out _))
            {
                removed++;
            }
        }

        return removed;
    }

    private static string CleanOrDefault(string? value, string fallback)
    {
        return string.IsNullOrWhiteSpace(value)
            ? fallback
            : value.Trim();
    }
}

internal sealed class StaleConnectionCleanupService(
    IncidentRealtimeTracker tracker,
    ILogger<StaleConnectionCleanupService> logger) : BackgroundService
{
    private static readonly TimeSpan CleanupInterval = TimeSpan.FromSeconds(30);
    private static readonly TimeSpan StaleConnectionAge = TimeSpan.FromMinutes(2);

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        using var timer = new PeriodicTimer(CleanupInterval);

        try
        {
            while (await timer.WaitForNextTickAsync(stoppingToken))
            {
                var removed = tracker.RemoveStaleConnections(StaleConnectionAge);
                if (removed > 0)
                {
                    logger.LogInformation(
                        "Removed {RemovedConnectionCount} stale realtime connection(s).",
                        removed);
                }
            }
        }
        catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
        {
        }
    }
}

internal sealed record PendingIncidentChange(
    string ChangeType,
    string EntityType,
    string EntityId,
    string? IncidentId,
    int? Version,
    string ActorId,
    string Summary);

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

internal sealed record IncidentClientConnection(
    string ConnectionId,
    string UserId,
    string ClientName,
    string ClientKind,
    string RemoteAddress,
    DateTimeOffset ConnectedAtUtc,
    DateTimeOffset LastSeenAtUtc);

internal sealed record ClientConnectionChange(
    string ConnectionId,
    string ChangeType,
    DateTimeOffset ChangedAtUtc);
