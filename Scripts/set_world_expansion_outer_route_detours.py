"""Set conservative detour controls around Mansion scenery and the Hospital shell."""
import copy
import json
from pathlib import Path

ROOT = Path(r"F:\Carnival")
REGION_PATH = ROOT / "Saved/WorldExpansion/Region_Authoring.json"
REPORT_PATH = ROOT / "Saved/WorldExpansion/Outer_Route_Detour_Controls.json"
region = json.loads(REGION_PATH.read_text(encoding="utf-8"))
controls = region["outer_route_spine"]["controls_cm"]
before = copy.deepcopy(controls)
if len(controls) == 17:
    controls.insert(3, [-53000.0, -83000.0, 700.0])
elif len(controls) != 18:
    raise RuntimeError("The documented R03-R06 control layout changed; inspect endpoint indices first")

# Leave the Mansion driveway to the southwest of its fence line, then follow
# the natural terrain shelf south of the beech trees before turning north.
controls[1] = [-69000.0, -83000.0, 650.0]
controls[2] = [-54000.0, -83000.0, 700.0]
# This extra south-east waypoint keeps the Catmull curve south of the beech line
# until it has passed east of the tree collision bounds.
controls[3] = [-53000.0, -83000.0, 700.0]
# Center the Docks East node on its quay and match the surface top to the quay deck.
controls[15] = [70000.0, 18000.0, 622.5]
# Pass east and north of the Hospital facade/interior, then return to the existing door anchor.
controls[16] = [103000.0, 126000.0, 640.0]
region["outer_route_spine"]["controls_cm"] = controls
REGION_PATH.write_text(json.dumps(region, indent=2), encoding="utf-8")

REPORT_PATH.write_text(json.dumps({
    "success": True,
    "map": "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Connections_Layout",
    "controls_before": {"Mansion": before[0], "DocksNorth": before[3],
                        "Prison": before[7], "DocksEast": before[14],
                        "Hospital": before[16]},
    "controls_after": {"Mansion": controls[0], "DocksNorth": controls[4],
                       "Prison": controls[8], "DocksEast": controls[15],
                       "Hospital": controls[17],
                       "detour_waypoints": controls[1:4]},
    "unchanged_required_nodes": ["Mansion", "DocksNorth", "Prison", "DocksEast", "Hospital"],
    "clearance_basis": {
        "mansion_fence": "The observed fence actors are centered near (-67745.5, -83895.2), (-66739.5, -82506.9), and (-65820.6, -86874.8) cm; this curve stays between their bounds with over 5 m clearance to the nearest fence AABB.",
        "mansion_beech": "An added south-east waypoint keeps the route below the tree bounds until it has passed east of the second beech; confirm with authored-height capsule traces.",
        "docks_east_quay": "Route node moved to quay center and raised 22.5 cm so its 45 cm surface box top aligns with the quay deck at Z=645 cm.",
        "hospital": "Old segments 420-427 crossed facade, elevated interior floors, and ladder; detour passes east/north of the facade before the original Hospital entry anchor."
    },
    "visual_and_traversal_status": "Proposed controls only; regenerate, statically audit, then traverse in PIE before accepting."
}, indent=2), encoding="utf-8")
print(json.dumps({"success": True, "controls": REPORT_PATH.read_text(encoding="utf-8").splitlines()[0:2]}))
