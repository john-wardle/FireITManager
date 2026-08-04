using FireITManager.Desktop.Models;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Text;
using System.Text.Json;

namespace FireITManager.Desktop.Services;

internal sealed class OutputWorkflowService
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web)
    {
        WriteIndented = true
    };

    public string OutputDirectory { get; } = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "FireITManager",
        "Outputs");

    public async Task<string> ExportIncidentBundleAsync(
        DesktopCache cache,
        CancellationToken cancellationToken = default)
    {
        Directory.CreateDirectory(OutputDirectory);
        var timestamp = DateTimeOffset.Now.ToString("yyyyMMdd-HHmmss");
        var workingDirectory = Path.Combine(OutputDirectory, $"incident-bundle-{timestamp}");
        Directory.CreateDirectory(workingDirectory);

        var jsonPath = Path.Combine(workingDirectory, "incident-data.json");
        await using (var stream = File.Create(jsonPath))
        {
            await JsonSerializer.SerializeAsync(stream, cache, JsonOptions, cancellationToken);
        }

        var summaryPath = Path.Combine(workingDirectory, "incident-summary.html");
        await File.WriteAllTextAsync(summaryPath, BuildSummaryHtml(cache), cancellationToken);

        var zipPath = Path.Combine(OutputDirectory, $"incident-bundle-{timestamp}.zip");
        if (File.Exists(zipPath))
        {
            File.Delete(zipPath);
        }

        ZipFile.CreateFromDirectory(workingDirectory, zipPath);
        Directory.Delete(workingDirectory, recursive: true);
        return zipPath;
    }

    public async Task<string> CreatePrintSummaryAsync(
        DesktopCache cache,
        CancellationToken cancellationToken = default)
    {
        Directory.CreateDirectory(OutputDirectory);
        var timestamp = DateTimeOffset.Now.ToString("yyyyMMdd-HHmmss");
        var path = Path.Combine(OutputDirectory, $"incident-print-summary-{timestamp}.txt");
        await File.WriteAllTextAsync(path, BuildPlainTextSummary(cache), cancellationToken);
        return path;
    }

    public void OpenOutputFolder()
    {
        Directory.CreateDirectory(OutputDirectory);
        Process.Start(new ProcessStartInfo
        {
            FileName = OutputDirectory,
            UseShellExecute = true
        });
    }

    private static string BuildPlainTextSummary(DesktopCache cache)
    {
        var builder = new StringBuilder();
        builder.AppendLine("FireIT Manager Incident Summary");
        builder.AppendLine($"Cached UTC: {cache.CachedAtUtc:O}");
        builder.AppendLine($"User: {cache.UserId} ({cache.UserRole})");
        builder.AppendLine();

        if (cache.Incident is null)
        {
            builder.AppendLine("No incident summary is loaded.");
            return builder.ToString();
        }

        builder.AppendLine($"Incident: {cache.Incident.IncidentNumber} - {cache.Incident.Name}");
        builder.AppendLine($"Agency: {cache.Incident.Agency}");
        builder.AppendLine($"Version: {cache.Incident.Version}");
        builder.AppendLine($"Updated UTC: {cache.Incident.UpdatedAtUtc:O}");
        builder.AppendLine();
        AppendCount(builder, "Camps", cache.Camps);
        AppendCount(builder, "Buildings / Locations", cache.Locations ?? []);
        AppendCount(builder, "Devices", cache.Devices);
        AppendCount(builder, "Networks", cache.Networks);
        AppendCount(builder, "Links", cache.Links);
        AppendCount(builder, "Checklist Runs", cache.ChecklistRuns);
        return builder.ToString();
    }

    private static string BuildSummaryHtml(DesktopCache cache)
    {
        var incidentName = cache.Incident?.Name ?? "No incident loaded";
        return $$"""
            <!doctype html>
            <html lang="en">
            <head>
                <meta charset="utf-8">
                <title>FireIT Manager Incident Summary</title>
                <style>
                    body { font-family: Segoe UI, Arial, sans-serif; color: #16202a; margin: 32px; }
                    h1 { margin-bottom: 4px; }
                    table { border-collapse: collapse; width: 100%; margin-top: 20px; }
                    th, td { border: 1px solid #c9d2dc; padding: 7px 9px; text-align: left; }
                    th { background: #eef2f5; }
                </style>
            </head>
            <body>
                <h1>{{Escape(incidentName)}}</h1>
                <p>{{Escape(cache.UserId)}} / {{Escape(cache.UserRole)}} / {{cache.CachedAtUtc:O}}</p>
                <table>
                    <tr><th>Area</th><th>Count</th></tr>
                    <tr><td>Camps</td><td>{{cache.Camps.Count}}</td></tr>
                    <tr><td>Buildings / Locations</td><td>{{cache.Locations?.Count ?? 0}}</td></tr>
                    <tr><td>Devices</td><td>{{cache.Devices.Count}}</td></tr>
                    <tr><td>Networks</td><td>{{cache.Networks.Count}}</td></tr>
                    <tr><td>Links</td><td>{{cache.Links.Count}}</td></tr>
                    <tr><td>Checklist Runs</td><td>{{cache.ChecklistRuns.Count}}</td></tr>
                </table>
            </body>
            </html>
            """;
    }

    private static void AppendCount(
        StringBuilder builder,
        string label,
        IReadOnlyList<EntityListItem> items)
    {
        builder.AppendLine($"{label}: {items.Count}");
    }

    private static string Escape(string value) =>
        System.Net.WebUtility.HtmlEncode(value);
}
