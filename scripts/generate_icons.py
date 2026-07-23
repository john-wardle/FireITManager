"""Generate the FireIT Manager topology SVG icon pack.

The generated icons are transparent SVG files designed for network maps,
toolbars, and asset palettes. They intentionally use simple diagram-style
geometry instead of AI-rendered raster art so the icon set stays consistent.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "assets" / "icons" / "topology"
MANIFEST_PATH = OUT_DIR / "manifest.json"
CONTACT_SHEET_PATH = OUT_DIR / "contact_sheet.svg"

SIZE = 512
BLUE = "#2F75B5"
BLUE_LIGHT = "#DDEBFA"
GRAY = "#3F4A56"
GRAY_LIGHT = "#C7CDD5"
MANILLA = "#D8B56A"
ORANGE = "#EA580C"
TEAL = "#0F766E"
CYAN = "#0891B2"
SLATE = "#475569"
GREEN = "#16A34A"
RED = "#DC2626"
AMBER = "#F59E0B"
MAINT_BLUE = "#3B82F6"
UNKNOWN = "#94A3B8"
WHITE = "#FFFFFF"


@dataclass(frozen=True)
class IconSpec:
    """Definition for one generated icon."""

    filename: str
    display_name: str
    category: str
    use: str
    draw: Callable[[], str]


def main() -> None:
    """Generate every topology icon and a JSON manifest."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest = []
    for spec in icon_specs():
        (OUT_DIR / spec.filename).write_text(svg(spec.draw()), encoding="utf-8")
        manifest.append(
            {
                "file": spec.filename,
                "display_name": spec.display_name,
                "category": spec.category,
                "use": spec.use,
                "format": "svg",
                "size": f"{SIZE}x{SIZE}",
                "transparent_background": True,
            }
        )

    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    CONTACT_SHEET_PATH.write_text(contact_sheet(icon_specs()), encoding="utf-8")
    print(f"Generated {len(manifest)} icons in {OUT_DIR}")


def icon_specs() -> list[IconSpec]:
    """Return every icon in the FireIT Manager topology pack."""
    return [
        IconSpec("laptop.svg", "Laptop", "Core Network Equipment", "Portable workstation", laptop),
        IconSpec(
            "desktop_monitor.svg",
            "Desktop Monitor",
            "Core Network Equipment",
            "Monitor or desktop endpoint",
            desktop_monitor,
        ),
        IconSpec(
            "workstation_tower.svg",
            "Workstation Tower",
            "Core Network Equipment",
            "Desktop tower endpoint",
            workstation_tower,
        ),
        IconSpec("printer.svg", "Printer", "Core Network Equipment", "Network printer", printer),
        IconSpec(
            "wifi_access_point.svg",
            "WiFi Access Point",
            "Core Network Equipment",
            "Wireless access point",
            wifi_access_point,
        ),
        IconSpec("router.svg", "Router", "Core Network Equipment", "Router", router),
        IconSpec(
            "network_switch.svg",
            "Network Switch",
            "Core Network Equipment",
            "Switch",
            network_switch,
        ),
        IconSpec(
            "firewall.svg",
            "Firewall",
            "Core Network Equipment",
            "Firewall appliance",
            firewall,
        ),
        IconSpec(
            "server_tower.svg",
            "Server Tower",
            "Core Network Equipment",
            "Tower server",
            server_tower,
        ),
        IconSpec(
            "rack_server.svg",
            "Rack Server",
            "Core Network Equipment",
            "Rack server",
            rack_server,
        ),
        IconSpec(
            "server_rack.svg",
            "Server Rack",
            "Core Network Equipment",
            "Server rack or cabinet",
            server_rack,
        ),
        IconSpec("voip_phone.svg", "VoIP Phone", "Core Network Equipment", "VoIP handset", voip_phone),
        IconSpec(
            "satellite_dish.svg",
            "Satellite Dish",
            "Core Network Equipment",
            "Satellite internet terminal",
            satellite_dish,
        ),
        IconSpec("antenna_mast.svg", "Antenna Mast", "Core Network Equipment", "Antenna mast", antenna_mast),
        IconSpec(
            "radio_repeater.svg",
            "Radio Repeater",
            "Core Network Equipment",
            "Radio repeater",
            radio_repeater,
        ),
        IconSpec(
            "cellular_modem.svg",
            "Cellular Modem",
            "Core Network Equipment",
            "Cellular modem",
            cellular_modem,
        ),
        IconSpec("ethernet_cable.svg", "Ethernet Cable", "Cabling and Power", "Copper network cable", ethernet_cable),
        IconSpec("fiber_cable.svg", "Fiber Cable", "Cabling and Power", "Fiber network cable", fiber_cable),
        IconSpec("cable_spool.svg", "Cable Spool", "Cabling and Power", "Cable spool", cable_spool),
        IconSpec("patch_panel.svg", "Patch Panel", "Cabling and Power", "Patch panel", patch_panel),
        IconSpec("ups_battery.svg", "UPS Battery", "Cabling and Power", "UPS battery backup", ups_battery),
        IconSpec("generator.svg", "Generator", "Cabling and Power", "Generator", generator),
        IconSpec(
            "portable_battery.svg",
            "Portable Battery",
            "Cabling and Power",
            "Portable power pack",
            portable_battery,
        ),
        IconSpec("it_staging_tent.svg", "IT Staging Tent", "Incident Site Objects", "IT staging tent", it_staging_tent),
        IconSpec(
            "command_post_trailer.svg",
            "Command Post Trailer",
            "Incident Site Objects",
            "Command post trailer",
            command_post_trailer,
        ),
        IconSpec("equipment_case.svg", "Equipment Case", "Incident Site Objects", "Equipment case", equipment_case),
        IconSpec("folder.svg", "Folder", "Incident Site Objects", "Folder or workspace group", folder),
        IconSpec(
            "connected_computers.svg",
            "Connected Computers",
            "Network Diagrams",
            "Two connected endpoints",
            connected_computers,
        ),
        IconSpec(
            "laptop_to_server.svg",
            "Laptop to Server",
            "Network Diagrams",
            "Endpoint connected to server",
            laptop_to_server,
        ),
        IconSpec("command_post.svg", "Command Post", "Incident Site Objects", "Command post building", command_post),
        IconSpec("online_status.svg", "Online Status", "Status Overlays", "Online state overlay", online_status),
        IconSpec("offline_status.svg", "Offline Status", "Status Overlays", "Offline state overlay", offline_status),
        IconSpec(
            "degraded_status.svg",
            "Degraded Status",
            "Status Overlays",
            "Degraded state overlay",
            degraded_status,
        ),
        IconSpec(
            "maintenance_status.svg",
            "Maintenance Status",
            "Status Overlays",
            "Maintenance state overlay",
            maintenance_status,
        ),
        IconSpec("unknown_status.svg", "Unknown Status", "Status Overlays", "Unknown state overlay", unknown_status),
        IconSpec("warning_status.svg", "Warning Status", "Status Overlays", "Warning state overlay", warning_status),
        IconSpec("selected_outline.svg", "Selected Outline", "Status Overlays", "Selection state overlay", selected_outline),
        IconSpec("locked_status.svg", "Locked Status", "Status Overlays", "Locked item overlay", locked_status),
    ]


def svg(body: str) -> str:
    """Wrap SVG body content in the shared 512x512 canvas."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" height="{SIZE}" viewBox="0 0 {SIZE} {SIZE}" role="img">
  {body.strip()}
</svg>
'''


def line(
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    *,
    color: str = GRAY,
    width: int = 28,
) -> str:
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        f'stroke="{color}" stroke-width="{width}" stroke-linecap="round" />'
    )


def rect(
    x: int,
    y: int,
    width: int,
    height: int,
    *,
    rx: int = 14,
    fill: str = "none",
    stroke: str = BLUE,
    stroke_width: int = 28,
) -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{rx}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" />'
    )


def circle(cx: int, cy: int, radius: int, *, fill: str = BLUE, stroke: str = "none", stroke_width: int = 0) -> str:
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="{stroke_width}" />'
    )


def laptop() -> str:
    return f'''
  {rect(124, 128, 264, 172)}
  <path d="M96 344 H416 L382 392 H130 Z" fill="{BLUE}" />
  {line(188, 335, 324, 335, color=GRAY, width=16)}
'''


def desktop_monitor() -> str:
    return f'''
  {rect(116, 116, 280, 194)}
  {line(256, 310, 256, 368)}
  {line(188, 390, 324, 390)}
'''


def workstation_tower() -> str:
    return f'''
  {rect(174, 74, 164, 360, rx=22, fill=BLUE, stroke=BLUE)}
  {line(216, 150, 296, 150, color=BLUE_LIGHT, width=18)}
  {line(216, 202, 296, 202, color=BLUE_LIGHT, width=18)}
  {circle(256, 342, 26, fill=BLUE_LIGHT)}
'''


def printer() -> str:
    return f'''
  {rect(118, 184, 276, 148, rx=20, fill=BLUE, stroke=BLUE)}
  {rect(154, 96, 204, 100, rx=10, fill="none", stroke=GRAY, stroke_width=22)}
  {rect(160, 304, 192, 104, rx=10, fill=BLUE_LIGHT, stroke=BLUE, stroke_width=18)}
  {circle(344, 246, 12, fill=BLUE_LIGHT)}
'''


def wifi_access_point() -> str:
    return f'''
  {rect(132, 176, 248, 160, rx=42, fill=BLUE, stroke=BLUE)}
  <path d="M178 228 Q256 168 334 228" fill="none" stroke="{BLUE_LIGHT}" stroke-width="20" stroke-linecap="round" />
  <path d="M214 268 Q256 238 298 268" fill="none" stroke="{BLUE_LIGHT}" stroke-width="20" stroke-linecap="round" />
  {circle(256, 300, 14, fill=BLUE_LIGHT)}
'''


def router() -> str:
    return f'''
  {rect(88, 202, 336, 136, rx=26, fill=BLUE, stroke=BLUE)}
  {line(170, 168, 170, 118, color=GRAY, width=22)}
  {line(342, 168, 342, 118, color=GRAY, width=22)}
  {circle(170, 112, 16, fill=GRAY)}
  {circle(342, 112, 16, fill=GRAY)}
  {circle(156, 270, 14, fill=BLUE_LIGHT)}
  {circle(216, 270, 14, fill=BLUE_LIGHT)}
  {circle(276, 270, 14, fill=BLUE_LIGHT)}
  {circle(336, 270, 14, fill=BLUE_LIGHT)}
'''


def network_switch() -> str:
    ports = "\n  ".join(
        f'<rect x="{116 + index * 52}" y="242" width="34" height="42" rx="4" fill="{BLUE_LIGHT}" />'
        for index in range(6)
    )
    return f'''
  {rect(74, 172, 364, 168, rx=22, fill=BLUE, stroke=BLUE)}
  {ports}
  {circle(390, 216, 12, fill=GREEN)}
'''


def firewall() -> str:
    return f'''
  <path d="M256 70 L386 126 V246 C386 334 336 398 256 440 C176 398 126 334 126 246 V126 Z" fill="{BLUE}" />
  <path d="M180 214 H332 M180 274 H332 M212 154 V334 M300 154 V334" stroke="{BLUE_LIGHT}" stroke-width="18" stroke-linecap="round" />
'''


def server_tower() -> str:
    return f'''
  {rect(166, 70, 180, 372, rx=22, fill=SLATE, stroke=SLATE)}
  {line(206, 148, 306, 148, color=BLUE_LIGHT, width=18)}
  {line(206, 202, 306, 202, color=BLUE_LIGHT, width=18)}
  {line(206, 256, 306, 256, color=BLUE_LIGHT, width=18)}
  {circle(256, 354, 24, fill=BLUE)}
'''


def rack_server() -> str:
    return f'''
  {rect(78, 188, 356, 136, rx=16, fill=SLATE, stroke=SLATE)}
  {rect(112, 224, 198, 28, rx=6, fill=BLUE_LIGHT, stroke="none", stroke_width=0)}
  {circle(356, 238, 12, fill=GREEN)}
  {circle(392, 238, 12, fill=GREEN)}
  {line(116, 284, 394, 284, color=BLUE_LIGHT, width=16)}
'''


def server_rack() -> str:
    rows = "\n  ".join(
        f'<rect x="150" y="{98 + index * 68}" width="212" height="46" rx="8" fill="{SLATE}" />'
        for index in range(5)
    )
    lights = "\n  ".join(
        f'<circle cx="328" cy="{121 + index * 68}" r="8" fill="{GREEN}" />'
        for index in range(5)
    )
    return f'''
  {rect(124, 66, 264, 386, rx=20, fill="none", stroke=GRAY, stroke_width=22)}
  {rows}
  {lights}
'''


def voip_phone() -> str:
    return f'''
  <path d="M162 128 H350 C382 128 404 150 404 182 V330 C404 362 382 384 350 384 H162 C130 384 108 362 108 330 V182 C108 150 130 128 162 128 Z" fill="{BLUE}" />
  {rect(160, 170, 134, 58, rx=10, fill=BLUE_LIGHT, stroke="none", stroke_width=0)}
  <path d="M174 278 C214 314 298 314 338 278" fill="none" stroke="{BLUE_LIGHT}" stroke-width="24" stroke-linecap="round" />
  {circle(334, 192, 14, fill=BLUE_LIGHT)}
'''


def satellite_dish() -> str:
    return f'''
  <path d="M134 182 C214 96 344 96 424 182 C340 244 218 244 134 182 Z" fill="{BLUE}" />
  {line(278, 226, 218, 346)}
  {line(198, 390, 338, 390)}
  <path d="M118 118 Q256 26 394 118" fill="none" stroke="{GRAY}" stroke-width="20" stroke-linecap="round" />
  <path d="M154 150 Q256 84 358 150" fill="none" stroke="{GRAY}" stroke-width="16" stroke-linecap="round" />
'''


def antenna_mast() -> str:
    return f'''
  {line(256, 96, 256, 414, color=GRAY, width=24)}
  {line(186, 414, 326, 414, color=GRAY, width=24)}
  <path d="M188 148 Q256 82 324 148" fill="none" stroke="{BLUE}" stroke-width="22" stroke-linecap="round" />
  <path d="M152 202 Q256 100 360 202" fill="none" stroke="{BLUE}" stroke-width="18" stroke-linecap="round" />
  <path d="M116 260 Q256 126 396 260" fill="none" stroke="{BLUE}" stroke-width="14" stroke-linecap="round" />
'''


def radio_repeater() -> str:
    return f'''
  {rect(166, 130, 180, 250, rx=22, fill=BLUE, stroke=BLUE)}
  {line(256, 130, 256, 72, color=GRAY, width=18)}
  {circle(256, 68, 13, fill=GRAY)}
  {line(206, 204, 306, 204, color=BLUE_LIGHT, width=18)}
  {line(206, 254, 306, 254, color=BLUE_LIGHT, width=18)}
  {circle(256, 320, 22, fill=BLUE_LIGHT)}
'''


def cellular_modem() -> str:
    return f'''
  {rect(116, 180, 280, 158, rx=26, fill=BLUE, stroke=BLUE)}
  {line(164, 180, 130, 120, color=GRAY, width=18)}
  {line(348, 180, 382, 120, color=GRAY, width=18)}
  {circle(198, 260, 12, fill=BLUE_LIGHT)}
  {circle(246, 260, 12, fill=BLUE_LIGHT)}
  {circle(294, 260, 12, fill=BLUE_LIGHT)}
  {circle(342, 260, 12, fill=GREEN)}
'''


def ethernet_cable() -> str:
    return f'''
  <path d="M112 284 C154 172 246 370 302 226 C334 146 398 186 416 250" fill="none" stroke="{GRAY}" stroke-width="26" stroke-linecap="round" />
  {rect(70, 264, 82, 70, rx=10, fill=BLUE, stroke=BLUE)}
  {rect(368, 214, 82, 70, rx=10, fill=BLUE, stroke=BLUE)}
  {line(96, 288, 126, 288, color=BLUE_LIGHT, width=10)}
  {line(394, 238, 424, 238, color=BLUE_LIGHT, width=10)}
'''


def fiber_cable() -> str:
    return f'''
  <path d="M92 300 C160 114 338 398 420 216" fill="none" stroke="{CYAN}" stroke-width="24" stroke-linecap="round" />
  {circle(92, 300, 28, fill=CYAN)}
  {circle(420, 216, 28, fill=CYAN)}
  {line(114, 300, 164, 300, color=GRAY, width=16)}
  {line(348, 216, 398, 216, color=GRAY, width=16)}
'''


def cable_spool() -> str:
    return f'''
  {circle(256, 256, 150, fill=MANILLA, stroke=GRAY, stroke_width=22)}
  {circle(256, 256, 62, fill=WHITE, stroke=GRAY, stroke_width=18)}
  <path d="M142 256 C174 190 238 176 306 194 C352 206 382 232 400 256" fill="none" stroke="{BLUE}" stroke-width="22" stroke-linecap="round" />
  {line(106, 418, 406, 418, color=GRAY, width=22)}
'''


def patch_panel() -> str:
    ports = "\n  ".join(
        f'<rect x="{96 + column * 54}" y="{206 + row * 62}" width="36" height="36" rx="4" fill="{BLUE_LIGHT}" />'
        for row in range(2)
        for column in range(7)
    )
    return f'''
  {rect(62, 164, 388, 190, rx=18, fill=SLATE, stroke=SLATE)}
  {ports}
'''


def ups_battery() -> str:
    return f'''
  {rect(142, 92, 228, 328, rx=28, fill=SLATE, stroke=SLATE)}
  {rect(184, 136, 144, 58, rx=10, fill=BLUE_LIGHT, stroke="none", stroke_width=0)}
  <path d="M266 224 L226 298 H258 L236 372 L302 274 H268 Z" fill="{GREEN}" />
'''


def generator() -> str:
    return f'''
  {rect(96, 178, 320, 164, rx=24, fill=ORANGE, stroke=ORANGE)}
  {line(132, 158, 380, 158, color=GRAY, width=24)}
  {circle(164, 370, 28, fill=GRAY)}
  {circle(350, 370, 28, fill=GRAY)}
  {rect(142, 214, 118, 62, rx=10, fill=BLUE_LIGHT, stroke="none", stroke_width=0)}
  {line(300, 234, 366, 234, color=BLUE_LIGHT, width=14)}
  {line(300, 270, 366, 270, color=BLUE_LIGHT, width=14)}
'''


def portable_battery() -> str:
    return f'''
  {rect(132, 122, 248, 284, rx=30, fill=BLUE, stroke=BLUE)}
  {rect(202, 78, 108, 54, rx=16, fill=GRAY, stroke=GRAY)}
  <path d="M266 178 L214 270 H252 L228 350 L306 246 H266 Z" fill="{BLUE_LIGHT}" />
'''


def it_staging_tent() -> str:
    return f'''
  <path d="M72 374 L256 112 L440 374 Z" fill="{MANILLA}" stroke="{GRAY}" stroke-width="22" stroke-linejoin="round" />
  <path d="M256 112 V374" stroke="{GRAY}" stroke-width="18" stroke-linecap="round" />
  <path d="M188 374 L256 232 L324 374 Z" fill="{BLUE}" />
'''


def command_post_trailer() -> str:
    return f'''
  {rect(82, 154, 348, 172, rx=24, fill=MANILLA, stroke=GRAY, stroke_width=22)}
  {rect(126, 196, 78, 64, rx=8, fill=BLUE_LIGHT, stroke=BLUE, stroke_width=16)}
  {rect(238, 196, 104, 64, rx=8, fill=BLUE_LIGHT, stroke=BLUE, stroke_width=16)}
  {line(430, 270, 468, 270, color=GRAY, width=18)}
  {circle(158, 358, 30, fill=GRAY)}
  {circle(354, 358, 30, fill=GRAY)}
'''


def equipment_case() -> str:
    return f'''
  {rect(94, 164, 324, 210, rx=24, fill=SLATE, stroke=SLATE)}
  {rect(202, 116, 108, 64, rx=18, fill="none", stroke=GRAY, stroke_width=20)}
  {line(112, 234, 400, 234, color=BLUE_LIGHT, width=14)}
  {rect(224, 244, 64, 46, rx=8, fill=BLUE, stroke="none", stroke_width=0)}
'''


def folder() -> str:
    return f'''
  <path d="M74 160 H202 L232 112 H438 C460 112 474 126 474 148 V380 C474 402 460 416 438 416 H74 C52 416 38 402 38 380 V196 C38 174 52 160 74 160 Z" fill="{MANILLA}" />
  <path d="M38 204 H474" stroke="{GRAY}" stroke-width="18" stroke-linecap="round" />
'''


def connected_computers() -> str:
    return f'''
  {rect(80, 116, 142, 100, rx=10, fill="none", stroke=BLUE, stroke_width=20)}
  {rect(290, 296, 142, 100, rx=10, fill="none", stroke=BLUE, stroke_width=20)}
  {line(151, 216, 151, 260, color=GRAY, width=20)}
  {line(151, 260, 361, 260, color=GRAY, width=20)}
  {line(361, 260, 361, 296, color=GRAY, width=20)}
  {line(112, 242, 190, 242, color=BLUE, width=20)}
  {line(322, 422, 400, 422, color=BLUE, width=20)}
'''


def laptop_to_server() -> str:
    return f'''
  {rect(72, 250, 164, 106, rx=10, fill="none", stroke=BLUE, stroke_width=20)}
  <path d="M52 384 H256 L236 418 H72 Z" fill="{BLUE}" />
  {rect(338, 96, 94, 288, rx=14, fill=BLUE, stroke=BLUE)}
  {line(236, 306, 306, 306, color=GRAY, width=20)}
  {line(306, 306, 306, 238, color=GRAY, width=20)}
  {line(306, 238, 338, 238, color=GRAY, width=20)}
  {line(362, 156, 408, 156, color=BLUE_LIGHT, width=12)}
  {line(362, 202, 408, 202, color=BLUE_LIGHT, width=12)}
  {circle(386, 304, 14, fill=BLUE_LIGHT)}
'''


def command_post() -> str:
    return f'''
  {rect(96, 192, 320, 192, rx=18, fill=MANILLA, stroke=GRAY, stroke_width=20)}
  <path d="M76 198 L256 92 L436 198 Z" fill="{BLUE}" />
  {rect(132, 238, 92, 72, rx=8, fill=BLUE_LIGHT, stroke=BLUE, stroke_width=14)}
  {rect(288, 238, 92, 146, rx=8, fill=BLUE_LIGHT, stroke=BLUE, stroke_width=14)}
'''


def online_status() -> str:
    return f'''
  {circle(256, 256, 150, fill=GREEN)}
  <path d="M190 258 L238 306 L330 208" fill="none" stroke="{WHITE}" stroke-width="34" stroke-linecap="round" stroke-linejoin="round" />
'''


def offline_status() -> str:
    return f'''
  {circle(256, 256, 150, fill=RED)}
  {line(202, 202, 310, 310, color=WHITE, width=34)}
  {line(310, 202, 202, 310, color=WHITE, width=34)}
'''


def degraded_status() -> str:
    return f'''
  <path d="M256 90 L430 392 H82 Z" fill="{AMBER}" />
  {line(256, 188, 256, 286, color=WHITE, width=32)}
  {circle(256, 340, 18, fill=WHITE)}
'''


def maintenance_status() -> str:
    return f'''
  {circle(256, 256, 150, fill=MAINT_BLUE)}
  <path d="M190 322 L310 202" stroke="{WHITE}" stroke-width="34" stroke-linecap="round" />
  <path d="M302 176 L342 216 L314 244 L274 204 Z" fill="{WHITE}" />
  <path d="M170 316 L196 342 L166 372 L140 346 Z" fill="{WHITE}" />
'''


def unknown_status() -> str:
    return f'''
  {circle(256, 256, 150, fill=UNKNOWN)}
  <path d="M214 212 C218 164 294 160 304 208 C312 244 260 250 260 288" fill="none" stroke="{WHITE}" stroke-width="32" stroke-linecap="round" />
  {circle(256, 344, 18, fill=WHITE)}
'''


def warning_status() -> str:
    return f'''
  {circle(256, 256, 150, fill=ORANGE)}
  {line(256, 168, 256, 286, color=WHITE, width=34)}
  {circle(256, 346, 19, fill=WHITE)}
'''


def selected_outline() -> str:
    return f'''
  <rect x="72" y="72" width="368" height="368" rx="48" fill="none" stroke="{MAINT_BLUE}" stroke-width="28" stroke-dasharray="48 28" />
'''


def locked_status() -> str:
    return f'''
  {rect(132, 226, 248, 170, rx=24, fill=GRAY, stroke=GRAY)}
  <path d="M178 226 V174 C178 126 210 94 256 94 C302 94 334 126 334 174 V226" fill="none" stroke="{GRAY}" stroke-width="34" stroke-linecap="round" />
  {circle(256, 306, 22, fill=BLUE_LIGHT)}
'''


def contact_sheet(specs: list[IconSpec]) -> str:
    """Create a quick SVG preview sheet for checking the generated pack."""
    columns = 6
    tile = 160
    rows = (len(specs) + columns - 1) // columns
    width = columns * tile
    height = rows * tile
    content = []
    for index, spec in enumerate(specs):
        column = index % columns
        row = index // columns
        x = column * tile
        y = row * tile
        content.append(
            f'<rect x="{x}" y="{y}" width="{tile}" height="{tile}" fill="#F8FAFC" stroke="#E5E7EB" />'
        )
        content.append(
            f'<g transform="translate({x + 36} {y + 18}) scale(0.171875)">'
            f'{spec.draw()}</g>'
        )
        content.append(
            f'<text x="{x + 80}" y="{y + 132}" text-anchor="middle" '
            f'font-family="Arial, sans-serif" font-size="12" fill="#1F2937">'
            f'{spec.display_name}</text>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n  '
        + "\n  ".join(content)
        + "\n</svg>\n"
    )


if __name__ == "__main__":
    main()
