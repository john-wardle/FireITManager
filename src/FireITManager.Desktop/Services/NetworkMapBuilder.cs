using FireITManager.Desktop.Models;
using System.Globalization;
using System.Windows.Media;

namespace FireITManager.Desktop.Services;

internal sealed class NetworkMapBuilder
{
    public const string AllStatusesFilter = "All statuses";
    public const string AllTypesFilter = "All types";
    public const string AllNetworksFilter = "All networks";
    public const string AllCampsFilter = "All camps";
    public const string AllDeviceTypesFilter = "All device types";

    private const double NodeWidth = 178;
    private const double NodeHeight = 76;
    private const double CampNodeWidth = 210;
    private const double CampNodeHeight = 88;
    private const double BuildingNodeWidth = 166;
    private const double BuildingNodeHeight = 70;
    private const double ColumnSpacing = 226;
    private const double RowSpacing = 144;
    private const double LeftPadding = 32;
    private const double TopPadding = 28;

    private static readonly IReadOnlyDictionary<string, StatusDefinition> StatusDefinitions =
        new Dictionary<string, StatusDefinition>(StringComparer.OrdinalIgnoreCase)
        {
            ["down"] = new("down", "Down", 60, "#B42318", "Failed or unreachable."),
            ["degraded"] = new("degraded", "Degraded", 50, "#B7791F", "Working with reduced capability."),
            ["unknown"] = new("unknown", "Unknown", 40, "#667085", "No reliable current signal."),
            ["maintenance"] = new("maintenance", "Maintenance", 30, "#6D5BD0", "Intentionally worked on or reserved."),
            ["disabled"] = new("disabled", "Disabled", 20, "#475467", "Intentionally not in service."),
            ["planned"] = new("planned", "Planned", 10, "#2E6DA4", "Designed but not active yet."),
            ["up"] = new("up", "Up", 0, "#218451", "Available and healthy.")
        };

    private static readonly Brush DefaultBrush = BuildBrush("#667085");

    public IReadOnlyList<StatusLegendItem> BuildLegend() =>
        StatusDefinitions.Values
            .OrderByDescending(item => item.Priority)
            .Select(item => new StatusLegendItem(
                item.Status,
                item.Label,
                item.Brush,
                item.Priority,
                item.Meaning))
            .ToList();

    public NetworkMapBuildResult Build(
        IReadOnlyCollection<EntityListItem> camps,
        IReadOnlyCollection<EntityListItem> locations,
        IReadOnlyCollection<EntityListItem> devices,
        IReadOnlyCollection<EntityListItem> networks,
        IReadOnlyCollection<EntityListItem> links,
        string searchText,
        string statusFilter,
        string typeFilter,
        string networkFilter,
        string campFilter,
        string deviceTypeFilter)
    {
        var allNodes = new Dictionary<string, NodeDraft>(StringComparer.OrdinalIgnoreCase);
        var networkById = networks.ToDictionary(item => item.Id, StringComparer.OrdinalIgnoreCase);
        var campById = camps.ToDictionary(item => item.Id, StringComparer.OrdinalIgnoreCase);
        var deviceById = devices.ToDictionary(item => item.Id, StringComparer.OrdinalIgnoreCase);
        var locationById = BuildLocationLookup(locations, devices, links, networkById, campById);
        var resolvedLocations = locationById.Values.ToList();
        var selectedNetworkId = ResolveFilterId(networks, networkFilter, AllNetworksFilter);
        var selectedCampId = ResolveFilterId(camps, campFilter, AllCampsFilter);

        if (camps.Count == 0 && locationById.Count == 0 && devices.Count == 0 && networks.Count == 0 && links.Count == 0)
        {
            allNodes["map-empty"] = new NodeDraft(
                "map-empty",
                "No incident network data",
                "Camp",
                "unknown",
                LeftPadding,
                TopPadding,
                "Connect to the incident server or load a cache to populate the map.",
                DateTimeOffset.UtcNow,
                false,
                null,
                null,
                "",
                "no incident network data unknown");
        }

        AddCampNodes(camps, resolvedLocations, networks, devices, links, allNodes, networkById, locationById);
        AddBuildingNodes(resolvedLocations, allNodes, campById);
        AddNetworkNodes(networks, allNodes, campById);
        AddDeviceNodes(devices, allNodes, campById, locationById);

        var mapLinks = BuildLinks(links, allNodes, networkById, campById, deviceById, locationById);
        PositionEndpointNodes(allNodes.Values.Where(node => node.ObjectType == "Endpoint").ToList());

        var nodes = allNodes.Values
            .Select(node => node.ToNode())
            .ToList();

        mapLinks = mapLinks
            .Select(link => RepositionLink(link, nodes))
            .ToList();

        var matchingLinks = mapLinks
            .Where(link => MatchesLink(link, searchText, statusFilter, typeFilter, selectedNetworkId, selectedCampId))
            .ToList();

        var visibleNodeIds = nodes
            .Where(node => MatchesNode(
                node,
                searchText,
                statusFilter,
                typeFilter,
                selectedNetworkId,
                selectedCampId,
                deviceTypeFilter))
            .Select(node => node.Id)
            .ToHashSet(StringComparer.OrdinalIgnoreCase);

        foreach (var link in matchingLinks)
        {
            visibleNodeIds.Add(link.SourceNodeId);
            visibleNodeIds.Add(link.TargetNodeId);
        }

        var visibleNodes = nodes
            .Where(node => visibleNodeIds.Contains(node.Id))
            .OrderBy(node => node.Y)
            .ThenBy(node => node.X)
            .ThenBy(node => node.Title, StringComparer.OrdinalIgnoreCase)
            .ToList();

        var visibleLinks = matchingLinks
            .Where(link => visibleNodeIds.Contains(link.SourceNodeId) && visibleNodeIds.Contains(link.TargetNodeId))
            .OrderByDescending(link => link.StatusPriority)
            .ThenBy(link => link.Title, StringComparer.OrdinalIgnoreCase)
            .ToList();

        var canvasWidth = Math.Max(820, visibleNodes.Select(node => node.X + node.Width + LeftPadding).DefaultIfEmpty(820).Max());
        var canvasHeight = Math.Max(520, visibleNodes.Select(node => node.Y + node.Height + TopPadding).DefaultIfEmpty(520).Max());

        return new NetworkMapBuildResult(
            visibleNodes,
            visibleLinks,
            canvasWidth,
            canvasHeight,
            BuildSummary(visibleNodes, visibleLinks));
    }

    public static string NormalizeStatus(string status)
    {
        var value = Clean(status).ToLowerInvariant();
        return value switch
        {
            "healthy" or "online" or "active" or "operational" or "ok" => "up",
            "warning" or "limited" or "partial" => "degraded",
            "offline" or "failed" or "unreachable" or "outage" => "down",
            "maint" or "work" or "repair" => "maintenance",
            "inactive" or "off" => "disabled",
            "" => "unknown",
            _ when StatusDefinitions.ContainsKey(value) => value,
            _ => "unknown"
        };
    }

    private static void AddCampNodes(
        IReadOnlyCollection<EntityListItem> camps,
        IReadOnlyCollection<EntityListItem> locations,
        IReadOnlyCollection<EntityListItem> networks,
        IReadOnlyCollection<EntityListItem> devices,
        IReadOnlyCollection<EntityListItem> links,
        Dictionary<string, NodeDraft> nodes,
        IReadOnlyDictionary<string, EntityListItem> networkById,
        IReadOnlyDictionary<string, EntityListItem> locationById)
    {
        var ordered = camps
            .OrderBy(item => item.Title, StringComparer.OrdinalIgnoreCase)
            .ToList();

        for (var index = 0; index < ordered.Count; index++)
        {
            var camp = ordered[index];
            var childStatuses = networks
                .Where(network => string.Equals(network.CampId, camp.Id, StringComparison.OrdinalIgnoreCase))
                .Select(network => network.Status)
                .Concat(locations
                    .Where(location => string.Equals(location.CampId, camp.Id, StringComparison.OrdinalIgnoreCase))
                    .Select(location => location.Status))
                .Concat(devices
                    .Where(device => DeviceBelongsToCamp(device, camp.Id, locationById))
                    .Select(device => device.Status))
                .Concat(links
                    .Where(link => LinkCampId(link, networkById, locationById) == camp.Id)
                    .Select(link => link.Status));

            var status = PickHighestPriorityStatus(new[] { camp.Status }.Concat(childStatuses));
            var detail = JoinNonBlank(camp.CampType, camp.Detail, camp.Notes);

            nodes[camp.Id] = new NodeDraft(
                camp.Id,
                camp.Title,
                "Camp",
                status,
                LeftPadding + (index * ColumnSpacing),
                TopPadding,
                detail,
                camp.UpdatedAtUtc,
                camp.ManualOverride,
                camp.Id,
                null,
                "",
                BuildSearchText(camp, detail),
                CampNodeWidth,
                CampNodeHeight);
        }
    }

    private static void AddBuildingNodes(
        IReadOnlyCollection<EntityListItem> locations,
        Dictionary<string, NodeDraft> nodes,
        IReadOnlyDictionary<string, EntityListItem> campById)
    {
        var ordered = locations
            .OrderBy(item => ResolveCampTitle(item.CampId, campById), StringComparer.OrdinalIgnoreCase)
            .ThenBy(item => item.Title, StringComparer.OrdinalIgnoreCase)
            .ToList();

        for (var index = 0; index < ordered.Count; index++)
        {
            var location = ordered[index];
            var campName = ResolveCampTitle(location.CampId, campById);
            var detail = JoinNonBlank(location.LocationType, campName, location.Detail, location.Notes);
            var x = location.MapX ?? LeftPadding + (index * ColumnSpacing);
            var y = location.MapY ?? TopPadding + RowSpacing;
            var width = Math.Max(120, location.MapWidth ?? BuildingNodeWidth);
            var height = Math.Max(58, location.MapHeight ?? BuildingNodeHeight);

            nodes[location.Id] = new NodeDraft(
                location.Id,
                location.Title,
                "Building",
                location.Status,
                x,
                y,
                detail,
                location.UpdatedAtUtc,
                location.ManualOverride,
                location.CampId,
                null,
                "",
                BuildSearchText(location, detail, campName),
                width,
                height);
        }
    }

    private static void AddNetworkNodes(
        IReadOnlyCollection<EntityListItem> networks,
        Dictionary<string, NodeDraft> nodes,
        IReadOnlyDictionary<string, EntityListItem> campById)
    {
        var ordered = networks
            .OrderBy(item => item.Title, StringComparer.OrdinalIgnoreCase)
            .ToList();

        for (var index = 0; index < ordered.Count; index++)
        {
            var network = ordered[index];
            var campName = network.CampId is not null && campById.TryGetValue(network.CampId, out var camp)
                ? camp.Title
                : "";
            var objectType = DetermineNetworkObjectType(network.NetworkType, network.Title);
            var detail = JoinNonBlank(network.NetworkType, campName, network.Detail, network.Notes);

            nodes[network.Id] = new NodeDraft(
                network.Id,
                network.Title,
                objectType,
                NormalizeStatus(network.Status),
                LeftPadding + (index * ColumnSpacing),
                TopPadding + (RowSpacing * 2),
                detail,
                network.UpdatedAtUtc,
                network.ManualOverride,
                network.CampId,
                network.Id,
                "",
                BuildSearchText(network, detail, campName));
        }
    }

    private static void AddDeviceNodes(
        IReadOnlyCollection<EntityListItem> devices,
        Dictionary<string, NodeDraft> nodes,
        IReadOnlyDictionary<string, EntityListItem> campById,
        IReadOnlyDictionary<string, EntityListItem> locationById)
    {
        var ordered = devices
            .OrderBy(item => item.Title, StringComparer.OrdinalIgnoreCase)
            .ToList();

        for (var index = 0; index < ordered.Count; index++)
        {
            var device = ordered[index];
            var location = device.LocationId is not null && locationById.TryGetValue(device.LocationId, out var matchedLocation)
                ? matchedLocation
                : null;
            var campId = location?.CampId;
            if (campId is null && device.LocationId is not null && campById.ContainsKey(device.LocationId))
            {
                campId = device.LocationId;
            }

            var campName = campId is not null && campById.TryGetValue(campId, out var camp)
                ? camp.Title
                : "";
            var locationName = location?.Title ?? "";
            var detail = JoinNonBlank(device.DeviceType, campName, locationName, device.Detail, device.Notes);

            nodes[device.Id] = new NodeDraft(
                device.Id,
                device.Title,
                "Device",
                NormalizeStatus(device.Status),
                LeftPadding + (index * ColumnSpacing),
                TopPadding + (RowSpacing * 3),
                detail,
                device.UpdatedAtUtc,
                device.ManualOverride,
                campId,
                null,
                device.DeviceType,
                BuildSearchText(device, detail, campName, locationName));
        }
    }

    private static bool DeviceBelongsToCamp(
        EntityListItem device,
        string campId,
        IReadOnlyDictionary<string, EntityListItem> locationById)
    {
        if (string.Equals(device.LocationId, campId, StringComparison.OrdinalIgnoreCase))
        {
            return true;
        }

        return device.LocationId is not null &&
            locationById.TryGetValue(device.LocationId, out var location) &&
            string.Equals(location.CampId, campId, StringComparison.OrdinalIgnoreCase);
    }

    private static List<NetworkMapLink> BuildLinks(
        IReadOnlyCollection<EntityListItem> links,
        Dictionary<string, NodeDraft> nodes,
        IReadOnlyDictionary<string, EntityListItem> networkById,
        IReadOnlyDictionary<string, EntityListItem> campById,
        IReadOnlyDictionary<string, EntityListItem> deviceById,
        IReadOnlyDictionary<string, EntityListItem> locationById)
    {
        var mapLinks = new List<NetworkMapLink>();
        var ordered = links
            .OrderBy(item => item.Title, StringComparer.OrdinalIgnoreCase)
            .ToList();

        foreach (var link in ordered)
        {
            var sourceNode = ResolveEndpoint(
                link,
                isSource: true,
                nodes,
                campById,
                deviceById,
                locationById);
            var targetNode = ResolveEndpoint(
                link,
                isSource: false,
                nodes,
                campById,
                deviceById,
                locationById);

            if (sourceNode.Id == targetNode.Id && link.NetworkId is not null && nodes.TryGetValue(link.NetworkId, out var networkNode))
            {
                targetNode = networkNode;
            }

            var status = NormalizeStatus(link.Status);
            var objectType = DetermineLinkObjectType(link.LinkCategory, link.LinkType, link.Title);
            var networkName = link.NetworkId is not null && networkById.TryGetValue(link.NetworkId, out var network)
                ? network.Title
                : "";
            var campId = LinkCampId(link, networkById, locationById);
            var detail = JoinNonBlank(
                link.Label,
                link.LinkCategory,
                link.LinkType,
                networkName,
                link.Length,
                link.Path,
                link.Detail,
                link.Notes);
            var title = Clean(link.Title);
            if (string.IsNullOrWhiteSpace(title) || title == "->")
            {
                title = $"{sourceNode.Title} -> {targetNode.Title}";
            }

            mapLinks.Add(new NetworkMapLink(
                link.Id,
                title,
                objectType,
                status,
                GetStatusPriority(status),
                GetStatusBrush(status),
                CenterX(sourceNode),
                CenterY(sourceNode),
                CenterX(targetNode),
                CenterY(targetNode),
                Midpoint(CenterX(sourceNode), CenterX(targetNode)),
                Midpoint(CenterY(sourceNode), CenterY(targetNode)),
                sourceNode.Id,
                targetNode.Id,
                sourceNode.Title,
                targetNode.Title,
                link.LinkCategory,
                link.LinkType,
                detail,
                link.UpdatedAtUtc,
                link.ManualOverride,
                campId,
                link.NetworkId,
                BuildSearchText(link, detail, networkName, sourceNode.Title, targetNode.Title)));
        }

        return mapLinks;
    }

    private static NodeDraft ResolveEndpoint(
        EntityListItem link,
        bool isSource,
        Dictionary<string, NodeDraft> nodes,
        IReadOnlyDictionary<string, EntityListItem> campById,
        IReadOnlyDictionary<string, EntityListItem> deviceById,
        IReadOnlyDictionary<string, EntityListItem> locationById)
    {
        var deviceId = isSource ? link.SourceDeviceId : link.DestinationDeviceId;
        if (deviceId is not null && nodes.TryGetValue(deviceId, out var deviceNode))
        {
            return deviceNode;
        }

        var locationId = isSource ? link.SourceLocationId : link.DestinationLocationId;
        if (locationId is not null && nodes.TryGetValue(locationId, out var locationNode))
        {
            return locationNode;
        }

        var reference = isSource ? link.SourceRef : link.DestinationRef;
        if (!string.IsNullOrWhiteSpace(reference))
        {
            var matchedNode = nodes.Values.FirstOrDefault(node =>
                string.Equals(node.Id, reference, StringComparison.OrdinalIgnoreCase) ||
                string.Equals(node.Title, reference, StringComparison.OrdinalIgnoreCase));

            if (matchedNode is not null)
            {
                return matchedNode;
            }
        }

        var endpointId = $"endpoint:{link.Id}:{(isSource ? "source" : "destination")}";
        if (nodes.TryGetValue(endpointId, out var endpointNode))
        {
            return endpointNode;
        }

        var endpointTitle = Clean(reference);
        if (string.IsNullOrWhiteSpace(endpointTitle))
        {
            endpointTitle = isSource ? "Source endpoint" : "Destination endpoint";
        }

        var campId = locationId is not null && campById.ContainsKey(locationId)
            ? locationId
            : locationId is not null && locationById.TryGetValue(locationId, out var location)
                ? location.CampId
                : null;
        var deviceType = deviceId is not null && deviceById.TryGetValue(deviceId, out var device)
            ? device.DeviceType
            : "";

        endpointNode = new NodeDraft(
            endpointId,
            endpointTitle,
            "Endpoint",
            NormalizeStatus(link.Status),
            LeftPadding,
            TopPadding + (RowSpacing * 4),
            JoinNonBlank(link.LinkCategory, link.LinkType, link.Detail, link.Notes),
            link.UpdatedAtUtc,
            link.ManualOverride,
            campId,
            link.NetworkId,
            deviceType,
            BuildSearchText(link, endpointTitle));

        nodes[endpointId] = endpointNode;
        return endpointNode;
    }

    private static void PositionEndpointNodes(IReadOnlyList<NodeDraft> endpoints)
    {
        for (var index = 0; index < endpoints.Count; index++)
        {
            endpoints[index].X = LeftPadding + (index * ColumnSpacing);
            endpoints[index].Y = TopPadding + (RowSpacing * 4);
        }
    }

    private static NetworkMapLink RepositionLink(
        NetworkMapLink link,
        IReadOnlyList<NetworkMapNode> nodes)
    {
        var source = nodes.FirstOrDefault(node => string.Equals(node.Id, link.SourceNodeId, StringComparison.OrdinalIgnoreCase));
        var target = nodes.FirstOrDefault(node => string.Equals(node.Id, link.TargetNodeId, StringComparison.OrdinalIgnoreCase));

        if (source is null || target is null)
        {
            return link;
        }

        return link with
        {
            SourceX = source.X + (source.Width / 2),
            SourceY = source.Y + (source.Height / 2),
            TargetX = target.X + (target.Width / 2),
            TargetY = target.Y + (target.Height / 2),
            LabelX = Midpoint(source.X + (source.Width / 2), target.X + (target.Width / 2)),
            LabelY = Midpoint(source.Y + (source.Height / 2), target.Y + (target.Height / 2))
        };
    }

    private static bool MatchesNode(
        NetworkMapNode node,
        string searchText,
        string statusFilter,
        string typeFilter,
        string? selectedNetworkId,
        string? selectedCampId,
        string deviceTypeFilter)
    {
        if (!MatchesSearch(node.SearchText, searchText))
        {
            return false;
        }

        if (!MatchesFilter(statusFilter, AllStatusesFilter, node.Status))
        {
            return false;
        }

        if (!MatchesFilter(typeFilter, AllTypesFilter, node.ObjectType))
        {
            return false;
        }

        if (selectedNetworkId is not null &&
            !string.Equals(node.NetworkId, selectedNetworkId, StringComparison.OrdinalIgnoreCase))
        {
            return false;
        }

        if (selectedCampId is not null &&
            !string.Equals(node.CampId, selectedCampId, StringComparison.OrdinalIgnoreCase) &&
            !string.Equals(node.Id, selectedCampId, StringComparison.OrdinalIgnoreCase))
        {
            return false;
        }

        if (!MatchesFilter(deviceTypeFilter, AllDeviceTypesFilter, node.DeviceType))
        {
            return false;
        }

        return true;
    }

    private static bool MatchesLink(
        NetworkMapLink link,
        string searchText,
        string statusFilter,
        string typeFilter,
        string? selectedNetworkId,
        string? selectedCampId)
    {
        if (!MatchesSearch(link.SearchText, searchText))
        {
            return false;
        }

        if (!MatchesFilter(statusFilter, AllStatusesFilter, link.Status))
        {
            return false;
        }

        if (!MatchesFilter(typeFilter, AllTypesFilter, link.ObjectType) &&
            !MatchesFilter(typeFilter, AllTypesFilter, "Link"))
        {
            return false;
        }

        if (selectedNetworkId is not null &&
            !string.Equals(link.NetworkId, selectedNetworkId, StringComparison.OrdinalIgnoreCase))
        {
            return false;
        }

        if (selectedCampId is not null &&
            !string.Equals(link.CampId, selectedCampId, StringComparison.OrdinalIgnoreCase))
        {
            return false;
        }

        return true;
    }

    private static bool MatchesFilter(string filter, string allFilter, string value)
    {
        if (string.IsNullOrWhiteSpace(filter) || string.Equals(filter, allFilter, StringComparison.OrdinalIgnoreCase))
        {
            return true;
        }

        return string.Equals(value, filter, StringComparison.OrdinalIgnoreCase);
    }

    private static bool MatchesSearch(string searchable, string searchText)
    {
        if (string.IsNullOrWhiteSpace(searchText))
        {
            return true;
        }

        return searchable.Contains(searchText.Trim(), StringComparison.OrdinalIgnoreCase);
    }

    private static string? ResolveFilterId(
        IEnumerable<EntityListItem> items,
        string filter,
        string allFilter)
    {
        if (string.IsNullOrWhiteSpace(filter) || string.Equals(filter, allFilter, StringComparison.OrdinalIgnoreCase))
        {
            return null;
        }

        return items.FirstOrDefault(item => string.Equals(item.Title, filter, StringComparison.OrdinalIgnoreCase))?.Id;
    }

    private static IReadOnlyDictionary<string, EntityListItem> BuildLocationLookup(
        IReadOnlyCollection<EntityListItem> locations,
        IReadOnlyCollection<EntityListItem> devices,
        IReadOnlyCollection<EntityListItem> links,
        IReadOnlyDictionary<string, EntityListItem> networkById,
        IReadOnlyDictionary<string, EntityListItem> campById)
    {
        var result = new Dictionary<string, EntityListItem>(StringComparer.OrdinalIgnoreCase);
        foreach (var location in locations.Where(item => !string.IsNullOrWhiteSpace(item.Id)))
        {
            result[location.Id] = location;
        }

        var singleCampId = campById.Count == 1
            ? campById.Values.First().Id
            : null;
        var hints = new Dictionary<string, LocationHint>(StringComparer.OrdinalIgnoreCase);
        LocationHint GetHint(string locationId)
        {
            if (!hints.TryGetValue(locationId, out var hint))
            {
                hint = new LocationHint(locationId);
                hints[locationId] = hint;
            }

            return hint;
        }

        foreach (var device in devices)
        {
            var locationId = Clean(device.LocationId);
            if (string.IsNullOrWhiteSpace(locationId) || campById.ContainsKey(locationId) || result.ContainsKey(locationId))
            {
                continue;
            }

            var hint = GetHint(locationId);
            hint.CampId ??= singleCampId;
            hint.DeviceCount++;
            hint.AddTitle(device.LocationId);
            hint.AddTitle(device.Detail);
            hint.Statuses.Add(device.Status);
            hint.UpdatedAtUtc = Latest(hint.UpdatedAtUtc, device.UpdatedAtUtc);
        }

        foreach (var link in links)
        {
            var campId = link.NetworkId is not null &&
                networkById.TryGetValue(link.NetworkId, out var network) &&
                !string.IsNullOrWhiteSpace(network.CampId)
                    ? network.CampId
                    : null;

            AddEndpointHint(link.SourceLocationId, link.SourceRef, link.Status, link.UpdatedAtUtc, campId);
            AddEndpointHint(link.DestinationLocationId, link.DestinationRef, link.Status, link.UpdatedAtUtc, campId);
        }

        foreach (var hint in hints.Values)
        {
            var title = hint.Titles.FirstOrDefault(value => !string.IsNullOrWhiteSpace(value)) ??
                $"Location {ShortId(hint.Id)}";
            var status = PickHighestPriorityStatus(hint.Statuses);
            var detail = JoinNonBlank(
                "Inferred building/location",
                hint.DeviceCount > 0 ? $"{hint.DeviceCount} assigned devices" : "",
                hint.LinkCount > 0 ? $"{hint.LinkCount} endpoint links" : "",
                "No authoritative location record has been synced yet.");

            result[hint.Id] = new EntityListItem(
                Id: hint.Id,
                Title: title,
                Status: status,
                Version: 0,
                Detail: detail,
                UpdatedAtUtc: hint.UpdatedAtUtc,
                Kind: "location",
                CampId: hint.CampId,
                LocationType: "building",
                Notes: "Inferred from existing device or link location references.",
                SearchText: JoinNonBlank(hint.Id, title, status, detail, string.Join(" ", hint.Titles)));
        }

        return result;

        void AddEndpointHint(
            string? locationIdValue,
            string titleValue,
            string status,
            DateTimeOffset? updatedAtUtc,
            string? campId)
        {
            var locationId = Clean(locationIdValue);
            if (string.IsNullOrWhiteSpace(locationId) || campById.ContainsKey(locationId) || result.ContainsKey(locationId))
            {
                return;
            }

            var hint = GetHint(locationId);
            hint.CampId ??= campId ?? singleCampId;
            hint.LinkCount++;
            hint.AddTitle(titleValue);
            hint.Statuses.Add(status);
            hint.UpdatedAtUtc = Latest(hint.UpdatedAtUtc, updatedAtUtc);
        }
    }

    private static string? LinkCampId(
        EntityListItem link,
        IReadOnlyDictionary<string, EntityListItem> networkById,
        IReadOnlyDictionary<string, EntityListItem> locationById)
    {
        if (link.NetworkId is not null &&
            networkById.TryGetValue(link.NetworkId, out var network) &&
            !string.IsNullOrWhiteSpace(network.CampId))
        {
            return network.CampId;
        }

        if (!string.IsNullOrWhiteSpace(link.SourceLocationId))
        {
            return ResolveLocationCampId(link.SourceLocationId, locationById) ?? link.SourceLocationId;
        }

        if (!string.IsNullOrWhiteSpace(link.DestinationLocationId))
        {
            return ResolveLocationCampId(link.DestinationLocationId, locationById) ?? link.DestinationLocationId;
        }

        return null;
    }

    private static string? ResolveLocationCampId(
        string? locationId,
        IReadOnlyDictionary<string, EntityListItem> locationById)
    {
        return !string.IsNullOrWhiteSpace(locationId) &&
            locationById.TryGetValue(locationId, out var location) &&
            !string.IsNullOrWhiteSpace(location.CampId)
                ? location.CampId
                : null;
    }

    private static string DetermineNetworkObjectType(string networkType, string title)
    {
        var value = $"{networkType} {title}".ToLowerInvariant();

        if (ContainsAny(value, "vlan", "subnet"))
        {
            return "VLAN";
        }

        if (ContainsAny(value, "wan", "satellite", "internet", "starlink"))
        {
            return "WAN";
        }

        if (ContainsAny(value, "wireless", "wifi", "wi-fi", "wlan"))
        {
            return "Wireless";
        }

        if (ContainsAny(value, "service", "dhcp", "dns", "print"))
        {
            return "Service";
        }

        return "Network";
    }

    private static string DetermineLinkObjectType(string linkCategory, string linkType, string title)
    {
        var value = $"{linkCategory} {linkType} {title}".ToLowerInvariant();

        if (ContainsAny(value, "wan", "satellite", "internet", "starlink"))
        {
            return "WAN";
        }

        if (ContainsAny(value, "wireless", "wifi", "wi-fi", "wlan"))
        {
            return "Wireless";
        }

        if (ContainsAny(value, "virtual", "vpn", "tunnel", "vlan"))
        {
            return "VLAN";
        }

        if (ContainsAny(value, "service", "http", "https", "ssh", "snmp"))
        {
            return "Service";
        }

        return "Link";
    }

    private static bool ContainsAny(string value, params string[] needles) =>
        needles.Any(needle => value.Contains(needle, StringComparison.OrdinalIgnoreCase));

    private static string PickHighestPriorityStatus(IEnumerable<string> statuses) =>
        statuses
            .Select(NormalizeStatus)
            .OrderByDescending(GetStatusPriority)
            .DefaultIfEmpty("unknown")
            .First();

    private static int GetStatusPriority(string status) =>
        StatusDefinitions.TryGetValue(NormalizeStatus(status), out var definition)
            ? definition.Priority
            : StatusDefinitions["unknown"].Priority;

    private static Brush GetStatusBrush(string status) =>
        StatusDefinitions.TryGetValue(NormalizeStatus(status), out var definition)
            ? definition.Brush
            : DefaultBrush;

    private static string BuildSummary(
        IReadOnlyCollection<NetworkMapNode> nodes,
        IReadOnlyCollection<NetworkMapLink> links)
    {
        var objects = nodes.Count + links.Count;
        var down = nodes.Count(node => node.Status == "down") + links.Count(link => link.Status == "down");
        var degraded = nodes.Count(node => node.Status == "degraded") + links.Count(link => link.Status == "degraded");
        var unknown = nodes.Count(node => node.Status == "unknown") + links.Count(link => link.Status == "unknown");

        return $"{objects} visible objects | {links.Count} links | Down {down} | Degraded {degraded} | Unknown {unknown}";
    }

    private static double CenterX(NodeDraft node) => node.X + (node.Width / 2);

    private static double CenterY(NodeDraft node) => node.Y + (node.Height / 2);

    private static double Midpoint(double first, double second) => first + ((second - first) / 2);

    private static string BuildSearchText(EntityListItem item, params string[] extras) =>
        string.Join(
            " ",
            new[]
            {
                item.Id,
                item.Title,
                item.Status,
                item.Detail,
                item.Kind,
                item.CampId,
                item.NetworkId,
                item.LocationId,
                item.SourceDeviceId,
                item.DestinationDeviceId,
                item.SourceLocationId,
                item.DestinationLocationId,
                item.SourceRef,
                item.DestinationRef,
                item.LinkCategory,
                item.LinkType,
                item.NetworkType,
                item.DeviceType,
                item.CampType,
                item.ParentLocationId,
                item.LocationType,
                item.Label,
                item.Length,
                item.Path,
                item.Notes,
                item.SearchText,
                item.MapX?.ToString(CultureInfo.InvariantCulture),
                item.MapY?.ToString(CultureInfo.InvariantCulture),
                item.MapWidth?.ToString(CultureInfo.InvariantCulture),
                item.MapHeight?.ToString(CultureInfo.InvariantCulture)
            }
            .Concat(extras)
            .Where(value => !string.IsNullOrWhiteSpace(value)));

    private static string JoinNonBlank(params string[] values) =>
        string.Join(" | ", values.Where(value => !string.IsNullOrWhiteSpace(value)));

    private static string Clean(string? value) => value?.Trim() ?? "";

    private static DateTimeOffset? Latest(DateTimeOffset? first, DateTimeOffset? second)
    {
        if (first is null)
        {
            return second;
        }

        if (second is null)
        {
            return first;
        }

        return first > second ? first : second;
    }

    private static string ResolveCampTitle(
        string? campId,
        IReadOnlyDictionary<string, EntityListItem> campById)
    {
        return !string.IsNullOrWhiteSpace(campId) && campById.TryGetValue(campId, out var camp)
            ? camp.Title
            : "";
    }

    private static string ShortId(string value) =>
        string.IsNullOrWhiteSpace(value)
            ? "unknown"
            : value.Trim()[..Math.Min(8, value.Trim().Length)];

    private static Brush BuildBrush(string hex)
    {
        var brush = new SolidColorBrush((Color)ColorConverter.ConvertFromString(hex));
        brush.Freeze();
        return brush;
    }

    private sealed record StatusDefinition(
        string Status,
        string Label,
        int Priority,
        string Color,
        string Meaning)
    {
        public Brush Brush { get; } = BuildBrush(Color);
    }

    private sealed class LocationHint(string id)
    {
        public string Id { get; } = id;

        public string? CampId { get; set; }

        public List<string> Titles { get; } = [];

        public List<string> Statuses { get; } = [];

        public DateTimeOffset? UpdatedAtUtc { get; set; }

        public int DeviceCount { get; set; }

        public int LinkCount { get; set; }

        public void AddTitle(string? title)
        {
            if (!string.IsNullOrWhiteSpace(title))
            {
                var cleaned = title.Trim();
                if (!Titles.Any(value => string.Equals(value, cleaned, StringComparison.OrdinalIgnoreCase)))
                {
                    Titles.Add(cleaned);
                }
            }
        }
    }

    private sealed class NodeDraft(
        string id,
        string title,
        string objectType,
        string status,
        double x,
        double y,
        string detail,
        DateTimeOffset? lastSeenAtUtc,
        bool manualOverride,
        string? campId,
        string? networkId,
        string deviceType,
        string searchText,
        double width = NodeWidth,
        double height = NodeHeight)
    {
        public string Id { get; } = id;

        public string Title { get; } = title;

        public string ObjectType { get; } = objectType;

        public string Status { get; } = NormalizeStatus(status);

        public double X { get; set; } = x;

        public double Y { get; set; } = y;

        public double Width { get; } = width;

        public double Height { get; } = height;

        public string Detail { get; } = detail;

        public DateTimeOffset? LastSeenAtUtc { get; } = lastSeenAtUtc;

        public bool ManualOverride { get; } = manualOverride;

        public string? CampId { get; } = campId;

        public string? NetworkId { get; } = networkId;

        public string DeviceType { get; } = deviceType;

        public string SearchText { get; } = searchText;

        public NetworkMapNode ToNode() =>
            new(
                Id,
                Title,
                ObjectType,
                Status,
                GetStatusPriority(Status),
                GetStatusBrush(Status),
                X,
                Y,
                Width,
                Height,
                Detail,
                LastSeenAtUtc,
                ManualOverride,
                CampId,
                NetworkId,
                DeviceType,
                SearchText);
    }
}

internal sealed record NetworkMapBuildResult(
    IReadOnlyList<NetworkMapNode> Nodes,
    IReadOnlyList<NetworkMapLink> Links,
    double CanvasWidth,
    double CanvasHeight,
    string Summary);
