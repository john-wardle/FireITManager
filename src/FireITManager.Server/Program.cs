var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.MapGet("/health", () =>
    Results.Ok(new HealthResponse(
        Status: "Healthy",
        Service: "FireIT Manager Incident Server",
        CheckedAtUtc: DateTimeOffset.UtcNow)));

app.Run();

internal sealed record HealthResponse(
    string Status,
    string Service,
    DateTimeOffset CheckedAtUtc);
