using FireITManager.Desktop.Models;
using System.Net;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json;

namespace FireITManager.Desktop.Services;

internal sealed class IncidentServerClient
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web)
    {
        WriteIndented = true
    };

    private readonly HttpClient _httpClient = new();

    public void Configure(string serverUrl)
    {
        _httpClient.BaseAddress = new Uri(NormalizeServerUrl(serverUrl));
    }

    public async Task<HealthResponse> GetHealthAsync(CancellationToken cancellationToken = default)
    {
        using var response = await _httpClient.GetAsync("/health", cancellationToken);
        return await ReadJsonOrThrowAsync<HealthResponse>(response, cancellationToken)
            ?? throw new IncidentServerException("The server returned an empty health response.", response.StatusCode);
    }

    public async Task<IncidentSummary?> GetIncidentSummaryAsync(CancellationToken cancellationToken = default)
    {
        using var response = await _httpClient.GetAsync("/api/incident-summary", cancellationToken);
        if (response.StatusCode == HttpStatusCode.NotFound)
        {
            return null;
        }

        return await ReadJsonOrThrowAsync<IncidentSummary>(response, cancellationToken);
    }

    public async Task<IncidentSummary> CreateIncidentSummaryAsync(
        IncidentSummaryRequest request,
        string userId,
        CancellationToken cancellationToken = default)
    {
        return await SendIncidentSummaryAsync(HttpMethod.Post, request, userId, cancellationToken);
    }

    public async Task<IncidentSummary> UpdateIncidentSummaryAsync(
        IncidentSummaryRequest request,
        string userId,
        CancellationToken cancellationToken = default)
    {
        return await SendIncidentSummaryAsync(HttpMethod.Put, request, userId, cancellationToken);
    }

    public Task<IReadOnlyList<EntityListItem>> ListCampsAsync(CancellationToken cancellationToken = default) =>
        ListEntitiesAsync("/api/camps", "camp", cancellationToken);

    public Task<IReadOnlyList<EntityListItem>> ListDevicesAsync(CancellationToken cancellationToken = default) =>
        ListEntitiesAsync("/api/devices", "device", cancellationToken);

    public Task<IReadOnlyList<EntityListItem>> ListNetworksAsync(CancellationToken cancellationToken = default) =>
        ListEntitiesAsync("/api/networks", "network", cancellationToken);

    public Task<IReadOnlyList<EntityListItem>> ListLinksAsync(CancellationToken cancellationToken = default) =>
        ListEntitiesAsync("/api/links", "link", cancellationToken);

    public Task<IReadOnlyList<EntityListItem>> ListChecklistRunsAsync(CancellationToken cancellationToken = default) =>
        ListEntitiesAsync("/api/checklist-runs", "checklist-run", cancellationToken);

    public async Task<IReadOnlyList<IncidentClientConnection>> ListRealtimeConnectionsAsync(CancellationToken cancellationToken = default)
    {
        using var response = await _httpClient.GetAsync("/api/realtime/connections", cancellationToken);
        return await ReadJsonOrThrowAsync<IReadOnlyList<IncidentClientConnection>>(response, cancellationToken)
            ?? [];
    }

    public async Task<IReadOnlyList<AuditEventItem>> ListAuditEventsAsync(CancellationToken cancellationToken = default)
    {
        using var response = await _httpClient.GetAsync("/api/audit-events", cancellationToken);
        return await ReadJsonOrThrowAsync<IReadOnlyList<AuditEventItem>>(response, cancellationToken)
            ?? [];
    }

    public static string NormalizeServerUrl(string serverUrl)
    {
        var cleaned = string.IsNullOrWhiteSpace(serverUrl)
            ? "http://localhost:5000"
            : serverUrl.Trim();

        return cleaned.EndsWith("/", StringComparison.Ordinal)
            ? cleaned.TrimEnd('/')
            : cleaned;
    }

    private async Task<IncidentSummary> SendIncidentSummaryAsync(
        HttpMethod method,
        IncidentSummaryRequest request,
        string userId,
        CancellationToken cancellationToken)
    {
        using var message = new HttpRequestMessage(method, "/api/incident-summary")
        {
            Content = JsonContent.Create(request, options: JsonOptions)
        };

        message.Headers.TryAddWithoutValidation("X-FireIT-User", userId);

        using var response = await _httpClient.SendAsync(message, cancellationToken);
        return await ReadJsonOrThrowAsync<IncidentSummary>(response, cancellationToken)
            ?? throw new IncidentServerException("The server returned an empty incident response.", response.StatusCode);
    }

    private async Task<IReadOnlyList<EntityListItem>> ListEntitiesAsync(
        string path,
        string kind,
        CancellationToken cancellationToken)
    {
        using var response = await _httpClient.GetAsync(path, cancellationToken);
        await ThrowIfFailedAsync(response, cancellationToken);

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        var items = await JsonSerializer.DeserializeAsync<IReadOnlyList<JsonElement>>(
            stream,
            JsonOptions,
            cancellationToken);

        return items?
            .Select(item => MapEntity(item, kind))
            .OrderBy(item => item.Title, StringComparer.OrdinalIgnoreCase)
            .ToList()
            ?? [];
    }

    private static EntityListItem MapEntity(JsonElement item, string kind)
    {
        var id = ReadString(item, "id");
        var sourceRef = ReadString(item, "sourceRef");
        var destinationRef = ReadString(item, "destinationRef");
        var sourceDeviceId = ReadOptionalString(item, "sourceDeviceId");
        var destinationDeviceId = ReadOptionalString(item, "destinationDeviceId");
        var linkCategory = ReadString(item, "linkCategory");
        var linkType = ReadString(item, "linkType");
        var networkType = ReadString(item, "networkType");
        var deviceType = ReadString(item, "deviceType");
        var campType = ReadString(item, "campType");
        var label = ReadString(item, "label");
        var length = ReadString(item, "length");
        var path = ReadString(item, "path");
        var notes = ReadString(item, "notes");
        var macAddresses = ReadStringList(item, "macAddresses");
        var title = kind switch
        {
            "camp" => ReadString(item, "name"),
            "device" => ReadString(item, "hostname"),
            "network" => ReadString(item, "name"),
            "link" => Prefer(label, $"{Prefer(sourceRef, sourceDeviceId ?? "")} -> {Prefer(destinationRef, destinationDeviceId ?? "")}"),
            "checklist-run" => ReadString(item, "templateTitle"),
            _ => id
        };

        var detail = kind switch
        {
            "camp" => JoinNonBlank(campType, ReadString(item, "addressOrDirections"), notes),
            "device" => JoinNonBlank(
                deviceType,
                ReadString(item, "manufacturer"),
                ReadString(item, "model"),
                ReadString(item, "serialNumber"),
                ReadOptionalString(item, "primaryIpAssignmentId") ?? "",
                string.Join(", ", macAddresses),
                ReadOptionalString(item, "assetId") ?? "",
                notes),
            "network" => JoinNonBlank(networkType, ReadString(item, "description")),
            "link" => JoinNonBlank(label, linkCategory, linkType, sourceRef, destinationRef, length, path, notes),
            "checklist-run" => JoinNonBlank(ReadString(item, "assignedTo"), ReadString(item, "completedAtUtc")),
            _ => ""
        };
        var status = Prefer(ReadString(item, "status"), "unknown");
        var searchText = JoinNonBlank(
            id,
            title,
            status,
            detail,
            sourceRef,
            destinationRef,
            linkCategory,
            linkType,
            networkType,
            deviceType,
            campType,
            label,
            length,
            path,
            notes,
            string.Join(" ", macAddresses));

        return new EntityListItem(
            Id: id,
            Title: string.IsNullOrWhiteSpace(title) ? id : title,
            Status: status,
            Version: ReadInt(item, "version"),
            Detail: detail,
            UpdatedAtUtc: ReadDateTimeOffset(item, "updatedAtUtc"),
            Kind: kind,
            IncidentId: ReadOptionalString(item, "incidentId"),
            CampId: ReadOptionalString(item, "campId"),
            NetworkId: ReadOptionalString(item, "networkId"),
            LocationId: ReadOptionalString(item, "locationId"),
            SourceDeviceId: sourceDeviceId,
            DestinationDeviceId: destinationDeviceId,
            SourceLocationId: ReadOptionalString(item, "sourceLocationId"),
            DestinationLocationId: ReadOptionalString(item, "destinationLocationId"),
            SourceRef: sourceRef,
            DestinationRef: destinationRef,
            LinkCategory: linkCategory,
            LinkType: linkType,
            NetworkType: networkType,
            DeviceType: deviceType,
            CampType: campType,
            Label: label,
            Length: length,
            Path: path,
            Notes: notes,
            SearchText: searchText,
            ManualOverride: ReadBool(item, "manualOverride") || ReadBool(item, "isManualOverride"));
    }

    private static async Task<T?> ReadJsonOrThrowAsync<T>(
        HttpResponseMessage response,
        CancellationToken cancellationToken)
    {
        await ThrowIfFailedAsync(response, cancellationToken);
        return await response.Content.ReadFromJsonAsync<T>(JsonOptions, cancellationToken);
    }

    private static async Task ThrowIfFailedAsync(
        HttpResponseMessage response,
        CancellationToken cancellationToken)
    {
        if (response.IsSuccessStatusCode)
        {
            return;
        }

        if (response.StatusCode == HttpStatusCode.Conflict)
        {
            var conflict = await response.Content.ReadFromJsonAsync<ConflictMessage>(JsonOptions, cancellationToken);
            throw new IncidentConflictException(
                conflict?.Message ?? "The record was changed by another client.",
                response.StatusCode,
                conflict?.CurrentVersion);
        }

        var body = await response.Content.ReadAsStringAsync(cancellationToken);
        throw new IncidentServerException(
            string.IsNullOrWhiteSpace(body)
                ? $"Server request failed with {(int)response.StatusCode} {response.ReasonPhrase}."
                : body,
            response.StatusCode);
    }

    private static string ReadString(JsonElement item, string propertyName)
    {
        if (!TryGetProperty(item, propertyName, out var property) || property.ValueKind is JsonValueKind.Null or JsonValueKind.Undefined)
        {
            return "";
        }

        return property.ValueKind == JsonValueKind.String
            ? property.GetString() ?? ""
            : property.ToString();
    }

    private static string? ReadOptionalString(JsonElement item, string propertyName)
    {
        var value = ReadString(item, propertyName);
        return string.IsNullOrWhiteSpace(value) ? null : value;
    }

    private static int ReadInt(JsonElement item, string propertyName)
    {
        return TryGetProperty(item, propertyName, out var property) && property.TryGetInt32(out var value)
            ? value
            : 0;
    }

    private static bool ReadBool(JsonElement item, string propertyName)
    {
        if (!TryGetProperty(item, propertyName, out var property) || property.ValueKind is JsonValueKind.Null or JsonValueKind.Undefined)
        {
            return false;
        }

        return property.ValueKind switch
        {
            JsonValueKind.True => true,
            JsonValueKind.False => false,
            JsonValueKind.String => bool.TryParse(property.GetString(), out var parsed) && parsed,
            _ => false
        };
    }

    private static IReadOnlyList<string> ReadStringList(JsonElement item, string propertyName)
    {
        if (!TryGetProperty(item, propertyName, out var property) || property.ValueKind != JsonValueKind.Array)
        {
            return [];
        }

        return property
            .EnumerateArray()
            .Select(value => value.ValueKind == JsonValueKind.String ? value.GetString() ?? "" : value.ToString())
            .Where(value => !string.IsNullOrWhiteSpace(value))
            .ToList();
    }

    private static DateTimeOffset? ReadDateTimeOffset(JsonElement item, string propertyName)
    {
        var value = ReadString(item, propertyName);
        return DateTimeOffset.TryParse(value, out var parsed)
            ? parsed
            : null;
    }

    private static bool TryGetProperty(JsonElement item, string propertyName, out JsonElement property)
    {
        foreach (var candidate in item.EnumerateObject())
        {
            if (string.Equals(candidate.Name, propertyName, StringComparison.OrdinalIgnoreCase))
            {
                property = candidate.Value;
                return true;
            }
        }

        property = default;
        return false;
    }

    private static string Prefer(params string[] values) =>
        values.FirstOrDefault(value => !string.IsNullOrWhiteSpace(value)) ?? "";

    private static string JoinNonBlank(params string[] values) =>
        string.Join(" | ", values.Where(value => !string.IsNullOrWhiteSpace(value)));
}

internal class IncidentServerException(
    string message,
    HttpStatusCode statusCode) : Exception(message)
{
    public HttpStatusCode StatusCode { get; } = statusCode;
}

internal sealed class IncidentConflictException(
    string message,
    HttpStatusCode statusCode,
    int? currentVersion) : IncidentServerException(message, statusCode)
{
    public int? CurrentVersion { get; } = currentVersion;
}
