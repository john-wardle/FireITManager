using FireITManager.Server.Data;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddSingleton(IncidentDatabase.Create(builder.Configuration));

var app = builder.Build();

var database = app.Services.GetRequiredService<IncidentDatabase>();
await database.MigrateAsync();

app.MapGet("/health", async (
    IncidentDatabase incidentDatabase,
    CancellationToken cancellationToken) =>
{
    var databaseHealth = await incidentDatabase.CheckHealthAsync(cancellationToken);

    return Results.Ok(new HealthResponse(
        Status: "Healthy",
        Service: "FireIT Manager Incident Server",
        DatabaseStatus: databaseHealth.Status,
        AppliedMigrations: databaseHealth.AppliedMigrations,
        CheckedAtUtc: DateTimeOffset.UtcNow));
});

app.MapGet("/api/incident-summary", async (
    IncidentDatabase incidentDatabase,
    CancellationToken cancellationToken) =>
{
    var incidentSummary = await incidentDatabase.GetIncidentSummaryAsync(cancellationToken);

    return incidentSummary is null
        ? Results.NotFound(new ApiMessage("No incident summary has been configured."))
        : Results.Ok(incidentSummary);
});

app.MapGet("/api/camps", async (
    IncidentDatabase incidentDatabase,
    CancellationToken cancellationToken) =>
{
    var camps = await incidentDatabase.ListCampsAsync(cancellationToken);

    return Results.Ok(camps);
});

app.MapGet("/api/devices", async (
    IncidentDatabase incidentDatabase,
    CancellationToken cancellationToken) =>
{
    var devices = await incidentDatabase.ListDevicesAsync(cancellationToken);

    return Results.Ok(devices);
});

await app.RunAsync();

internal sealed record HealthResponse(
    string Status,
    string Service,
    string DatabaseStatus,
    IReadOnlyList<string> AppliedMigrations,
    DateTimeOffset CheckedAtUtc);

internal sealed record ApiMessage(string Message);
