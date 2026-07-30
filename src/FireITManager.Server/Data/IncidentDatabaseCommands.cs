using Microsoft.Data.Sqlite;
using SQLitePCL;
using System.IO.Compression;
using System.Text.Json;

namespace FireITManager.Server.Data;

internal static class IncidentDatabaseCommands
{
    private const string DatabaseEntryName = "fireitmanager.incident.sqlite";
    private const string ManifestEntryName = "manifest.json";

    public static bool IsDatabaseCommand(string[] args)
    {
        return args.Length > 0
            && (args[0].Equals("backup", StringComparison.OrdinalIgnoreCase)
                || args[0].Equals("restore", StringComparison.OrdinalIgnoreCase));
    }

    public static async Task<int> ExecuteAsync(string[] args)
    {
        try
        {
            return args[0].ToLowerInvariant() switch
            {
                "backup" => await BackupAsync(args),
                "restore" => await RestoreAsync(args),
                _ => WriteUsage()
            };
        }
        catch (Exception ex) when (ex is ArgumentException or IOException or InvalidDataException or SqliteException)
        {
            Console.Error.WriteLine(ex.Message);
            return 1;
        }
    }

    private static async Task<int> BackupAsync(string[] args)
    {
        var databasePath = GetRequiredOption(args, "--database-path");
        var outputPath = GetRequiredOption(args, "--output");

        if (!File.Exists(databasePath))
        {
            throw new FileNotFoundException($"Database file does not exist: {databasePath}");
        }

        var outputDirectory = Path.GetDirectoryName(Path.GetFullPath(outputPath));
        if (!string.IsNullOrWhiteSpace(outputDirectory))
        {
            Directory.CreateDirectory(outputDirectory);
        }

        Batteries_V2.Init();

        var tempSnapshot = Path.Combine(Path.GetTempPath(), $"{Guid.NewGuid()}.sqlite");
        try
        {
            await using (var source = new SqliteConnection(CreateUnpooledConnectionString(databasePath)))
            await using (var destination = new SqliteConnection(CreateUnpooledConnectionString(tempSnapshot)))
            {
                await source.OpenAsync();
                await destination.OpenAsync();
                source.BackupDatabase(destination);
            }
            SqliteConnection.ClearAllPools();

            if (File.Exists(outputPath))
            {
                File.Delete(outputPath);
            }

            using var archive = ZipFile.Open(outputPath, ZipArchiveMode.Create);
            archive.CreateEntryFromFile(tempSnapshot, DatabaseEntryName, CompressionLevel.Optimal);

            var manifest = new BackupManifest(
                Format: "FireITManager.IncidentBundle",
                FormatVersion: 1,
                CreatedAtUtc: DateTimeOffset.UtcNow,
                DatabaseEntry: DatabaseEntryName);
            var manifestEntry = archive.CreateEntry(ManifestEntryName, CompressionLevel.Optimal);
            await using var manifestStream = manifestEntry.Open();
            await JsonSerializer.SerializeAsync(manifestStream, manifest);
        }
        finally
        {
            if (File.Exists(tempSnapshot))
            {
                File.Delete(tempSnapshot);
            }
        }

        Console.WriteLine($"Backup written: {outputPath}");
        return 0;
    }

    private static async Task<int> RestoreAsync(string[] args)
    {
        var inputPath = GetRequiredOption(args, "--input");
        var databasePath = GetRequiredOption(args, "--database-path");
        var overwrite = args.Any(arg => arg.Equals("--overwrite", StringComparison.OrdinalIgnoreCase));

        if (!File.Exists(inputPath))
        {
            throw new FileNotFoundException($"Backup bundle does not exist: {inputPath}");
        }

        if (File.Exists(databasePath) && !overwrite)
        {
            throw new IOException(
                $"Database file already exists: {databasePath}. Use --overwrite to replace it.");
        }

        var databaseDirectory = Path.GetDirectoryName(Path.GetFullPath(databasePath));
        if (!string.IsNullOrWhiteSpace(databaseDirectory))
        {
            Directory.CreateDirectory(databaseDirectory);
        }

        using var archive = ZipFile.OpenRead(inputPath);
        var manifestEntry = archive.GetEntry(ManifestEntryName)
            ?? throw new InvalidDataException("Backup bundle is missing manifest.json.");
        var databaseEntry = archive.GetEntry(DatabaseEntryName)
            ?? throw new InvalidDataException($"Backup bundle is missing {DatabaseEntryName}.");

        await using (var manifestStream = manifestEntry.Open())
        {
            var manifest = await JsonSerializer.DeserializeAsync<BackupManifest>(manifestStream)
                ?? throw new InvalidDataException("Backup manifest is invalid.");

            if (manifest.Format != "FireITManager.IncidentBundle" || manifest.DatabaseEntry != DatabaseEntryName)
            {
                throw new InvalidDataException("Backup bundle is not a FireIT Manager incident bundle.");
            }
        }

        var tempRestorePath = Path.Combine(Path.GetTempPath(), $"{Guid.NewGuid()}.sqlite");
        try
        {
            databaseEntry.ExtractToFile(tempRestorePath, overwrite: true);
            File.Copy(tempRestorePath, databasePath, overwrite: true);
        }
        finally
        {
            if (File.Exists(tempRestorePath))
            {
                File.Delete(tempRestorePath);
            }
        }

        Console.WriteLine($"Database restored: {databasePath}");
        return 0;
    }

    private static string GetRequiredOption(string[] args, string name)
    {
        var index = Array.FindIndex(args, arg => arg.Equals(name, StringComparison.OrdinalIgnoreCase));
        if (index < 0 || index + 1 >= args.Length || args[index + 1].StartsWith("--", StringComparison.Ordinal))
        {
            throw new ArgumentException($"Missing required option: {name}");
        }

        return args[index + 1];
    }

    private static string CreateUnpooledConnectionString(string databasePath)
    {
        return new SqliteConnectionStringBuilder
        {
            DataSource = databasePath,
            Pooling = false,
        }.ToString();
    }

    private static int WriteUsage()
    {
        Console.Error.WriteLine("Usage:");
        Console.Error.WriteLine("  backup --database-path <path> --output <bundle.zip>");
        Console.Error.WriteLine("  restore --input <bundle.zip> --database-path <path> [--overwrite]");
        return 1;
    }

    private sealed record BackupManifest(
        string Format,
        int FormatVersion,
        DateTimeOffset CreatedAtUtc,
        string DatabaseEntry);
}
