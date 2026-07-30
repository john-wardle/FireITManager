using FireITManager.Desktop.Models;
using Microsoft.AspNetCore.SignalR.Client;

namespace FireITManager.Desktop.Services;

internal sealed class IncidentRealtimeClient : IAsyncDisposable
{
    private HubConnection? _connection;

    public event EventHandler<string>? StatusChanged;
    public event EventHandler<IncidentChangeEvent>? IncidentChanged;
    public event EventHandler<ClientConnectionChange>? ClientConnectionChanged;
    public event EventHandler<IncidentClientConnection>? ConnectionStatusReceived;

    public async Task ConnectAsync(
        string serverUrl,
        string userId,
        string clientName,
        string clientKind,
        CancellationToken cancellationToken = default)
    {
        await DisposeAsync();

        var hubUrl = BuildHubUrl(serverUrl, userId, clientName, clientKind);
        _connection = new HubConnectionBuilder()
            .WithUrl(hubUrl)
            .WithAutomaticReconnect()
            .Build();

        _connection.On<IncidentChangeEvent>("IncidentChanged", change =>
            IncidentChanged?.Invoke(this, change));
        _connection.On<ClientConnectionChange>("ClientConnectionChanged", change =>
            ClientConnectionChanged?.Invoke(this, change));
        _connection.On<IncidentClientConnection>("ConnectionStatus", connection =>
            ConnectionStatusReceived?.Invoke(this, connection));

        _connection.Reconnecting += exception =>
        {
            StatusChanged?.Invoke(this, exception?.Message ?? "Reconnecting to incident server.");
            return Task.CompletedTask;
        };

        _connection.Reconnected += async _ =>
        {
            StatusChanged?.Invoke(this, "Live updates connected.");
            if (_connection is not null)
            {
                await _connection.InvokeAsync("Ping", cancellationToken);
            }
        };

        _connection.Closed += exception =>
        {
            StatusChanged?.Invoke(this, exception?.Message ?? "Live updates disconnected.");
            return Task.CompletedTask;
        };

        await _connection.StartAsync(cancellationToken);
        StatusChanged?.Invoke(this, "Live updates connected.");
    }

    public async Task PingAsync(CancellationToken cancellationToken = default)
    {
        if (_connection?.State == HubConnectionState.Connected)
        {
            await _connection.InvokeAsync("Ping", cancellationToken);
        }
    }

    public async ValueTask DisposeAsync()
    {
        if (_connection is null)
        {
            return;
        }

        await _connection.DisposeAsync();
        _connection = null;
    }

    private static string BuildHubUrl(
        string serverUrl,
        string userId,
        string clientName,
        string clientKind)
    {
        var normalized = IncidentServerClient.NormalizeServerUrl(serverUrl);
        var query = string.Join(
            "&",
            $"userId={Uri.EscapeDataString(Clean(userId, "desktop-user"))}",
            $"clientName={Uri.EscapeDataString(Clean(clientName, Environment.MachineName))}",
            $"clientKind={Uri.EscapeDataString(Clean(clientKind, "desktop"))}");

        return $"{normalized}/hubs/incident?{query}";
    }

    private static string Clean(string value, string fallback) =>
        string.IsNullOrWhiteSpace(value) ? fallback : value.Trim();
}
