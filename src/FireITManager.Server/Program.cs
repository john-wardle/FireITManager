using FireITManager.Server.Data;

if (IncidentDatabaseCommands.IsDatabaseCommand(args))
{
    return await IncidentDatabaseCommands.ExecuteAsync(args);
}

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

app.MapPost("/api/incident-summary", async (
    IncidentSummaryRequest request,
    IncidentDatabase incidentDatabase,
    CancellationToken cancellationToken) =>
{
    if (string.IsNullOrWhiteSpace(request.Name))
    {
        return Results.BadRequest(new ApiMessage("Incident name is required."));
    }

    var incidentSummary = await incidentDatabase.CreateIncidentSummaryAsync(
        request,
        actorId: "local-admin",
        cancellationToken);

    return incidentSummary is null
        ? Results.Conflict(new ApiMessage("An incident summary already exists."))
        : Results.Created("/api/incident-summary", incidentSummary);
});

app.MapPut("/api/incident-summary", async (
    IncidentSummaryRequest request,
    IncidentDatabase incidentDatabase,
    CancellationToken cancellationToken) =>
{
    if (string.IsNullOrWhiteSpace(request.Name))
    {
        return Results.BadRequest(new ApiMessage("Incident name is required."));
    }

    var incidentSummary = await incidentDatabase.UpdateIncidentSummaryAsync(
        request,
        actorId: "local-admin",
        cancellationToken);

    return incidentSummary is null
        ? Results.NotFound(new ApiMessage("No incident summary has been configured."))
        : Results.Ok(incidentSummary);
});

app.MapDelete("/api/incident-summary", async (
    IncidentDatabase incidentDatabase,
    CancellationToken cancellationToken) =>
{
    var deleted = await incidentDatabase.DeleteIncidentSummaryAsync(
        actorId: "local-admin",
        cancellationToken);

    return deleted
        ? Results.NoContent()
        : Results.NotFound(new ApiMessage("No incident summary has been configured."));
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

app.MapGet("/api/networks", async (
    IncidentDatabase incidentDatabase,
    CancellationToken cancellationToken) =>
{
    var networks = await incidentDatabase.ListNetworksAsync(cancellationToken);

    return Results.Ok(networks);
});

app.MapGet("/api/links", async (
    IncidentDatabase incidentDatabase,
    CancellationToken cancellationToken) =>
{
    var links = await incidentDatabase.ListLinksAsync(cancellationToken);

    return Results.Ok(links);
});

app.MapGet("/api/checklist-templates", async (
    IncidentDatabase incidentDatabase,
    CancellationToken cancellationToken) =>
{
    var checklistTemplates = await incidentDatabase.ListChecklistTemplatesAsync(cancellationToken);

    return Results.Ok(checklistTemplates);
});

app.MapGet("/api/checklist-runs", async (
    IncidentDatabase incidentDatabase,
    CancellationToken cancellationToken) =>
{
    var checklistRuns = await incidentDatabase.ListChecklistRunsAsync(cancellationToken);

    return Results.Ok(checklistRuns);
});

app.MapGet("/api/audit-events", async (
    IncidentDatabase incidentDatabase,
    CancellationToken cancellationToken) =>
{
    var auditEvents = await incidentDatabase.ListAuditEventsAsync(cancellationToken);

    return Results.Ok(auditEvents);
});

await app.RunAsync();

return 0;

internal sealed record HealthResponse(
    string Status,
    string Service,
    string DatabaseStatus,
    IReadOnlyList<string> AppliedMigrations,
    DateTimeOffset CheckedAtUtc);

internal sealed record ApiMessage(string Message);
