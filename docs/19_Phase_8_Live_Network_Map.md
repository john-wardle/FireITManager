# Phase 8 Live Network Map

## Decision

FireIT Manager will present the incident network map inside the WPF desktop client as a local-first operational view derived from the incident server data. The first implementation uses the existing camp, device, network, link, audit, and SignalR APIs. It does not require internet access or cloud mapping services.

## Map Object Types

The map model supports these operational object types:

| Object type | Current source | Notes |
| --- | --- | --- |
| Camp | Camp records | Shown as top-level incident operating areas. |
| Building | Future location records | Defined now for field layout work after location APIs are added. |
| Device | Device records | Routers, switches, APs, servers, printers, terminals, and other IT assets. |
| Link | Link records | Generic physical path when no more specific type is known. |
| Service | Network/link records | DNS, DHCP, print, HTTP/HTTPS, SSH, SNMP, or other logical services. |
| VLAN | Network/link records | VLANs, subnets, tunnels, VPNs, and virtual links. |
| WAN | Network/link records | Internet, satellite, Starlink, carrier, or other upstream paths. |
| Wireless | Network/link records | Wi-Fi, WLAN, point-to-point wireless, or AP backhaul. |

Generic network records remain visible as `Network` objects when the data does not yet identify them as service, VLAN, WAN, or wireless.

## Status Labels, Colors, And Priority

When several signals conflict, the highest-priority status wins for grouped objects such as camps. Link and device rows keep their direct status.

| Priority | Status | Color | Meaning |
| --- | --- | --- | --- |
| 60 | down | Red `#B42318` | Failed or unreachable. |
| 50 | degraded | Amber `#B7791F` | Working with reduced capability. |
| 40 | unknown | Gray `#667085` | No reliable current signal. |
| 30 | maintenance | Violet `#6D5BD0` | Intentionally worked on or reserved. |
| 20 | disabled | Slate `#475467` | Intentionally not in service. |
| 10 | planned | Blue `#2E6DA4` | Designed but not active yet. |
| 0 | up | Green `#218451` | Available and healthy. |

Synonyms are normalized before display. Examples: `healthy`, `online`, and `operational` display as `up`; `offline`, `failed`, and `unreachable` display as `down`.

## Desktop Implementation

The WPF client now includes a `Map` workspace before the raw `Network` workspace. It:

- Draws camp, network, device, and unresolved endpoint nodes on a scrollable canvas.
- Draws physical, virtual, WAN, satellite, internet, and wireless links from the current link records.
- Shows link direction and link type/category labels where available.
- Uses status colors on every node and link.
- Shows hover details for nodes and links.
- Lets users click nodes on the map and links in the link table to inspect details.
- Shows last-seen time from the record update timestamp.
- Reserves a manual override indicator in the map model for the future link-state history schema.
- Shows audit-backed history for selected links and objects when matching audit events exist.
- Filters by status, object type, network, camp, and device type.
- Searches across ID, device name, hostname/title, network/link text, source/destination refs, MAC addresses, and notes.
- Rebuilds automatically after SignalR incident-change refreshes, so status changes appear for connected desktop users.

## Telemetry Source Evaluation

Telemetry collectors should run on the incident LAN server and write normalized status updates back through the server. The WPF map should remain a consumer of authoritative server state.

| Source | First-use recommendation | Reason |
| --- | --- | --- |
| Manual ITSS override | First | Works immediately in air-gapped camps and provides auditable operator intent. |
| ICMP ping | First telemetry collector | Simple reachability signal for routers, switches, servers, and printers. |
| HTTP/HTTPS checks | First telemetry collector | Useful for captive portals, dashboards, local web tools, and application services. |
| SSH reachability | Later | Useful for network gear but depends on credentials and role permissions. |
| SNMP | Later | High value for switches/APs, but requires community/user configuration and security handling. |
| Router/switch API | Later | Vendor-specific and should be added per-device family after field testing. |
| LLDP/CDP | Later | Excellent topology validation, but depends on switch access and parser support. |

The next implementation step is adding manual status override controls and persistent link state history records, then adding ICMP/HTTP collectors that publish status updates through the existing SignalR change channel.
