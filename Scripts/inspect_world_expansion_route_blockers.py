"""Read collision actor bounds from the source levels containing route blockers."""
import json
import math
from pathlib import Path

import unreal

ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/WorldExpansion/Route_Blocker_ActorDetails.json"
MAP_TARGETS = {
    "/Game/Carnival/World/Levels/L_HauntedMansionConnected": {
        "mansion_fence_stall": (-67810.0, -81825.3, 696.1),
        "mansion_fence_hit": (-67941.3, -81916.9, 739.9),
        "mansion_tree_hit": (-66579.9, -79091.4, 637.5),
    },
    "/Game/Carnival/World/Levels/L_IndustrialHospitalInteriorArchitecture": {
        "hospital_ladder_hit": (95387.8, 125507.0, 1092.9),
    },
    "/Game/Carnival/World/Levels/L_IndustrialHospitalExterior": {
        "hospital_inner_route": (95089.5, 123009.6, 663.6),
    },
}

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
level_rows = []
for map_path, targets in MAP_TARGETS.items():
    world = unreal.EditorLoadingAndSavingUtils.load_map(map_path)
    if not world:
        raise RuntimeError("Could not open blocker source level: " + map_path)
    actors = actor_subsystem.get_all_level_actors()
    rows = []
    for target_name, target in targets.items():
        point = unreal.Vector(*target)
        nearby = []
        for actor in actors:
            try:
                center, extent = actor.get_actor_bounds(False, True)
                dx = max(0.0, abs(center.x - point.x) - extent.x)
                dy = max(0.0, abs(center.y - point.y) - extent.y)
                dz = max(0.0, abs(center.z - point.z) - extent.z)
                distance = math.sqrt(dx * dx + dy * dy + dz * dz)
                if distance > 1800.0:
                    continue
                row = {
                    "name": actor.get_name(),
                    "label": actor.get_actor_label(),
                    "path": actor.get_path_name(),
                    "class": actor.get_class().get_name(),
                    "distance_to_bounds_cm": distance,
                    "location_cm": actor.get_actor_location().to_tuple(),
                    "rotation_deg": actor.get_actor_rotation().to_tuple(),
                    "scale": actor.get_actor_scale3d().to_tuple(),
                    "bounds_center_cm": center.to_tuple(),
                    "bounds_extent_cm": extent.to_tuple(),
                }
                component = actor.get_component_by_class(unreal.StaticMeshComponent)
                if component:
                    mesh = component.get_editor_property("static_mesh")
                    row["mesh"] = mesh.get_path_name() if mesh else None
                    row["collision_profile"] = str(component.get_editor_property("collision_profile_name"))
                    row["collision_enabled"] = str(component.get_editor_property("collision_enabled"))
                nearby.append(row)
            except Exception:
                continue
        rows.append({"name": target_name, "point_cm": target,
                     "actors": sorted(nearby, key=lambda item: item["distance_to_bounds_cm"])[:40]})
    level_rows.append({"map": map_path, "actor_count": len(actors), "targets": rows})

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"levels": level_rows}, indent=2), encoding="utf-8")
unreal.SystemLibrary.quit_editor()
