using FireITManager.Server.Data;
using FireITManager.Server.Realtime;

try
{
    if (IncidentDatabaseCommands.IsDatabaseCommand(args))
    {
        return await IncidentDatabaseCommands.ExecuteAsync(args);
    }

    var appDirectory = AppContext.BaseDirectory;
    var builder = WebApplication.CreateBuilder(new WebApplicationOptions
    {
        Args = args,
        ContentRootPath = appDirectory,
        WebRootPath = Path.Combine(appDirectory, "wwwroot")
    });

    builder.Logging.ClearProviders();
    builder.Logging.AddSimpleConsole(options =>
    {
        options.SingleLine = true;
        options.TimestampFormat = "yyyy-MM-dd HH:mm:ss ";
    });
    builder.Logging.AddDebug();

    builder.Services.AddSingleton(IncidentDatabase.Create(builder.Configuration));
    builder.Services.AddSignalR();
    builder.Services.AddSingleton<IncidentRealtimeTracker>();
    builder.Services.AddSingleton<IncidentChangeBroadcaster>();
    builder.Services.AddHostedService<StaleConnectionCleanupService>();

    var app = builder.Build();

    var database = app.Services.GetRequiredService<IncidentDatabase>();
    await database.MigrateAsync();

    app.UseDefaultFiles();
    app.UseStaticFiles();

    app.MapHub<IncidentHub>("/hubs/incident");

    app.MapGet("/", () => Results.Redirect("/mobile/"));

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
    IncidentChangeBroadcaster changeBroadcaster,
    HttpContext httpContext,
    CancellationToken cancellationToken) =>
{
    if (string.IsNullOrWhiteSpace(request.Name))
    {
        return Results.BadRequest(new ApiMessage("Incident name is required."));
    }

    var result = await incidentDatabase.CreateIncidentSummaryAsync(
        request,
        actorId: ReadActorId(httpContext),
        cancellationToken);

    if (result.Status != DatabaseSaveStatus.Saved || result.Value is null)
    {
        return ToSaveResult(result, value => Results.Created("/api/incident-summary", value));
    }

    await changeBroadcaster.PublishAsync(
        ToIncidentChange(result.Value, "create", ReadActorId(httpContext), "Created incident summary."),
        cancellationToken);

    return Results.Created("/api/incident-summary", result.Value);
});

app.MapPut("/api/incident-summary", async (
    IncidentSummaryRequest request,
    IncidentDatabase incidentDatabase,
    IncidentChangeBroadcaster changeBroadcaster,
    HttpContext httpContext,
    CancellationToken cancellationToken) =>
{
    if (string.IsNullOrWhiteSpace(request.Name))
    {
        return Results.BadRequest(new ApiMessage("Incident name is required."));
    }

    var result = await incidentDatabase.UpdateIncidentSummaryAsync(
        request,
        actorId: ReadActorId(httpContext),
        cancellationToken);

    if (result.Status != DatabaseSaveStatus.Saved || result.Value is null)
    {
        return ToSaveResult(result, value => Results.Ok(value));
    }

    await changeBroadcaster.PublishAsync(
        ToIncidentChange(result.Value, "update", ReadActorId(httpContext), "Updated incident summary."),
        cancellationToken);

    return Results.Ok(result.Value);
});

app.MapDelete("/api/incident-summary", async (
    IncidentDatabase incidentDatabase,
    IncidentChangeBroadcaster changeBroadcaster,
    HttpContext httpContext,
    int? expectedVersion,
    CancellationToken cancellationToken) =>
{
    var result = await incidentDatabase.DeleteIncidentSummaryAsync(
        actorId: ReadActorId(httpContext),
        expectedVersion,
        cancellationToken);

    if (result.Status != DatabaseSaveStatus.Saved || result.Value is null)
    {
        return ToSaveResult(result, _ => Results.NoContent());
    }

    await changeBroadcaster.PublishAsync(
        ToEntityChange(result.Value, ReadActorId(httpContext)),
        cancellationToken);

    return Results.NoContent();
});

app.MapGet("/api/realtime/connections", (
    IncidentRealtimeTracker realtimeTracker) =>
{
    return Results.Ok(realtimeTracker.Snapshot());
});

app.MapGet("/api/camps", async (
    IncidentDatabase incidentDatabase,
    CancellationToken cancellationToken) =>
{
    var camps = await incidentDatabase.ListCampsAsync(cancellationToken);

    return Results.Ok(camps);
});

app.MapPut("/api/camps/{id}/status", async (
    string id,
    EntityStatusUpdateRequest request,
    IncidentDatabase incidentDatabase,
    IncidentChangeBroadcaster changeBroadcaster,
    HttpContext httpContext,
    CancellationToken cancellationToken) =>
{
    return await UpdateTrackedStatusAsync(
        request,
        () => incidentDatabase.UpdateCampStatusAsync(id, request, ReadActorId(httpContext), cancellationToken),
        changeBroadcaster,
        ReadActorId(httpContext),
        cancellationToken);
});

app.MapGet("/api/devices", async (
    IncidentDatabase incidentDatabase,
    CancellationToken cancellationToken) =>
{
    var devices = await incidentDatabase.ListDevicesAsync(cancellationToken);

    return Results.Ok(devices);
});

app.MapPut("/api/devices/{id}/status", async (
    string id,
    EntityStatusUpdateRequest request,
    IncidentDatabase incidentDatabase,
    IncidentChangeBroadcaster changeBroadcaster,
    HttpContext httpContext,
    CancellationToken cancellationToken) =>
{
    return await UpdateTrackedStatusAsync(
        request,
        () => incidentDatabase.UpdateDeviceStatusAsync(id, request, ReadActorId(httpContext), cancellationToken),
        changeBroadcaster,
        ReadActorId(httpContext),
        cancellationToken);
});

app.MapGet("/api/networks", async (
    IncidentDatabase incidentDatabase,
    CancellationToken cancellationToken) =>
{
    var networks = await incidentDatabase.ListNetworksAsync(cancellationToken);

    return Results.Ok(networks);
});

app.MapPut("/api/networks/{id}/status", async (
    string id,
    EntityStatusUpdateRequest request,
    IncidentDatabase incidentDatabase,
    IncidentChangeBroadcaster changeBroadcaster,
    HttpContext httpContext,
    CancellationToken cancellationToken) =>
{
    return await UpdateTrackedStatusAsync(
        request,
        () => incidentDatabase.UpdateNetworkStatusAsync(id, request, ReadActorId(httpContext), cancellationToken),
        changeBroadcaster,
        ReadActorId(httpContext),
        cancellationToken);
});

app.MapGet("/api/links", async (
    IncidentDatabase incidentDatabase,
    CancellationToken cancellationToken) =>
{
    var links = await incidentDatabase.ListLinksAsync(cancellationToken);

    return Results.Ok(links);
});

app.MapPut("/api/links/{id}/status", async (
    string id,
    EntityStatusUpdateRequest request,
    IncidentDatabase incidentDatabase,
    IncidentChangeBroadcaster changeBroadcaster,
    HttpContext httpContext,
    CancellationToken cancellationToken) =>
{
    return await UpdateTrackedStatusAsync(
        request,
        () => incidentDatabase.UpdateLinkStatusAsync(id, request, ReadActorId(httpContext), cancellationToken),
        changeBroadcaster,
        ReadActorId(httpContext),
        cancellationToken);
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

app.MapPost("/api/checklist-runs", async (
    ChecklistRunCreateRequest request,
    IncidentDatabase incidentDatabase,
    IncidentChangeBroadcaster changeBroadcaster,
    HttpContext httpContext,
    CancellationToken cancellationToken) =>
{
    if (string.IsNullOrWhiteSpace(request.TemplateId))
    {
        return Results.BadRequest(new ApiMessage("Checklist template is required."));
    }

    var actorId = ReadActorId(httpContext);
    var result = await incidentDatabase.CreateChecklistRunAsync(
        request,
        actorId,
        cancellationToken);

    if (result.Status != DatabaseSaveStatus.Saved || result.Value is null)
    {
        return ToSaveResult(result, value => Results.Created($"/api/checklist-runs/{value.Id}", value));
    }

    await changeBroadcaster.PublishAsync(
        ToChecklistRunChange(result.Value, "create", actorId, $"Started checklist run {result.Value.Id}."),
        cancellationToken);

    return Results.Created($"/api/checklist-runs/{result.Value.Id}", result.Value);
});

app.MapPut("/api/checklist-runs/{id}/progress", async (
    string id,
    ChecklistRunProgressRequest request,
    IncidentDatabase incidentDatabase,
    IncidentChangeBroadcaster changeBroadcaster,
    HttpContext httpContext,
    CancellationToken cancellationToken) =>
{
    if (string.IsNullOrWhiteSpace(request.Status))
    {
        return Results.BadRequest(new ApiMessage("Checklist run status is required."));
    }

    var actorId = ReadActorId(httpContext);
    var result = await incidentDatabase.UpdateChecklistRunProgressAsync(
        id,
        request,
        actorId,
        cancellationToken);

    if (result.Status != DatabaseSaveStatus.Saved || result.Value is null)
    {
        return ToSaveResult(result, value => Results.Ok(value));
    }

    await changeBroadcaster.PublishAsync(
        ToChecklistRunChange(result.Value, "update", actorId, $"Saved checklist run {result.Value.Id}."),
        cancellationToken);

    return Results.Ok(result.Value);
});

app.MapPut("/api/checklist-runs/{id}/completion", async (
    string id,
    ChecklistCompletionRequest request,
    IncidentDatabase incidentDatabase,
    IncidentChangeBroadcaster changeBroadcaster,
    HttpContext httpContext,
    CancellationToken cancellationToken) =>
{
    if (string.IsNullOrWhiteSpace(request.Status))
    {
        return Results.BadRequest(new ApiMessage("Checklist run status is required."));
    }

    var result = await incidentDatabase.CompleteChecklistRunAsync(
        id,
        request,
        ReadActorId(httpContext),
        cancellationToken);

    if (result.Status != DatabaseSaveStatus.Saved || result.Value is null)
    {
        return ToSaveResult(result, value => Results.Ok(value));
    }

    await changeBroadcaster.PublishAsync(
        ToEntityChange(result.Value, ReadActorId(httpContext)),
        cancellationToken);

    return Results.Ok(result.Value);
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
}
catch (Exception exception)
{
    WriteStartupError(exception);
    Console.Error.WriteLine(exception);
    return 1;
}

static void WriteStartupError(Exception exception)
{
    try
    {
        var logDirectory = Path.Combine(AppContext.BaseDirectory, "logs");
        Directory.CreateDirectory(logDirectory);
        var logPath = Path.Combine(logDirectory, "server-startup-error.log");
        File.AppendAllText(
            logPath,
            $"""
            [{DateTimeOffset.Now:O}]
            {exception}

            """);
    }
    catch
    {
        // Startup logging must never replace the original failure.
    }
}

static string ReadActorId(HttpContext httpContext)
{
    var actorId = httpContext.Request.Headers["X-FireIT-User"].ToString();
    return string.IsNullOrWhiteSpace(actorId)
        ? "local-admin"
        : actorId.Trim();
}

static IResult ToSaveResult<T>(
    DatabaseSaveResult<T> result,
    Func<T, IResult> savedResult)
{
    return result.Status switch
    {
        DatabaseSaveStatus.Saved when result.Value is not null =>
            savedResult(result.Value),

        DatabaseSaveStatus.Conflict =>
            Results.Conflict(new ConflictMessage(
                "The record was changed by another client. Refresh and retry with the current version.",
                result.CurrentVersion ?? 0)),

        DatabaseSaveStatus.Duplicate =>
            Results.Conflict(new ApiMessage("A record already exists.")),

        _ =>
            Results.NotFound(new ApiMessage("The requested record was not found."))
    };
}

static PendingIncidentChange ToIncidentChange(
    IncidentSummary incidentSummary,
    string changeType,
    string actorId,
    string summary)
{
    return new PendingIncidentChange(
        ChangeType: changeType,
        EntityType: "incident",
        EntityId: incidentSummary.Id,
        IncidentId: incidentSummary.Id,
        Version: incidentSummary.Version,
        ActorId: actorId,
        Summary: summary);
}

static PendingIncidentChange ToEntityChange(
    EntityChangeSummary entityChange,
    string actorId)
{
    return new PendingIncidentChange(
        ChangeType: entityChange.ChangeType,
        EntityType: entityChange.EntityType,
        EntityId: entityChange.EntityId,
        IncidentId: entityChange.IncidentId,
        Version: entityChange.Version,
        ActorId: actorId,
        Summary: $"{entityChange.EntityType} {entityChange.EntityId} changed: {entityChange.Status}.");
}

static PendingIncidentChange ToChecklistRunChange(
    ChecklistRunSummary checklistRun,
    string changeType,
    string actorId,
    string summary)
{
    return new PendingIncidentChange(
        ChangeType: changeType,
        EntityType: "checklist-run",
        EntityId: checklistRun.Id,
        IncidentId: checklistRun.IncidentId,
        Version: checklistRun.Version,
        ActorId: actorId,
        Summary: summary);
}

static async Task<IResult> UpdateTrackedStatusAsync(
    EntityStatusUpdateRequest request,
    Func<Task<DatabaseSaveResult<EntityChangeSummary>>> save,
    IncidentChangeBroadcaster changeBroadcaster,
    string actorId,
    CancellationToken cancellationToken)
{
    if (string.IsNullOrWhiteSpace(request.Status))
    {
        return Results.BadRequest(new ApiMessage("Status is required."));
    }

    var result = await save();

    if (result.Status != DatabaseSaveStatus.Saved || result.Value is null)
    {
        return ToSaveResult(result, value => Results.Ok(value));
    }

    await changeBroadcaster.PublishAsync(
        ToEntityChange(result.Value, actorId),
        cancellationToken);

    return Results.Ok(result.Value);
}

internal sealed record HealthResponse(
    string Status,
    string Service,
    string DatabaseStatus,
    IReadOnlyList<string> AppliedMigrations,
    DateTimeOffset CheckedAtUtc);

internal sealed record ApiMessage(string Message);

internal sealed record ConflictMessage(
    string Message,
    int CurrentVersion);
