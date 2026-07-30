using FireITManager.Desktop.Models;
using System.IO;
using System.Text.Json;

namespace FireITManager.Desktop.Services;

internal sealed class LocalCacheService
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web)
    {
        WriteIndented = true
    };

    public string CachePath { get; } = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "FireITManager",
        "desktop-cache.json");

    public async Task SaveAsync(DesktopCache cache, CancellationToken cancellationToken = default)
    {
        var directory = Path.GetDirectoryName(CachePath);
        if (!string.IsNullOrWhiteSpace(directory))
        {
            Directory.CreateDirectory(directory);
        }

        await using var stream = File.Create(CachePath);
        await JsonSerializer.SerializeAsync(stream, cache, JsonOptions, cancellationToken);
    }

    public async Task<DesktopCache?> LoadAsync(CancellationToken cancellationToken = default)
    {
        if (!File.Exists(CachePath))
        {
            return null;
        }

        await using var stream = File.OpenRead(CachePath);
        return await JsonSerializer.DeserializeAsync<DesktopCache>(stream, JsonOptions, cancellationToken);
    }
}
