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

await app.RunAsync();

internal sealed record HealthResponse(
    string Status,
    string Service,
    string DatabaseStatus,
    IReadOnlyList<string> AppliedMigrations,
    DateTimeOffset CheckedAtUtc);
