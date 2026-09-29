"""Hang the imported seven-image Gothic set on solid inner prison-tower wall panels."""
import json
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
MAP = "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Prison"
BASE = "/Game/Carnival/WorldExpansion/WallArt/GothicPaintings"
OUT = ROOT / "Saved/WorldExpansion/Gothic_Prison_WallArt_Placement.json"
PREFIX = "WorldExpansion_WallArt_Prison_"

# Locations are calculated from the exposed, solid 600 x 750 cm wall panels in
# BP_MainTower and BP_Tower. Their imported mesh bounds put local X along each
# panel and local Z from its lower edge. Each placement faces into the room.
PLACEMENTS = [
    {"label": PREFIX + "MainTower_A", "tower": "BP_MainTower", "panel": "SM_Wall_A28",
     "mesh": "A", "painting": "A", "scale": 1.0,
     "location_cm": [-222.0845, -1731.7305, 2247.2057], "rotation_deg": [0, -90, 0]},
    {"label": PREFIX + "MainTower_B", "tower": "BP_MainTower", "panel": "SM_Wall_A26",
     "mesh": "B", "painting": "B", "scale": 1.2,
     "location_cm": [-222.0845, -979.1805, 2192.6499], "rotation_deg": [0, -90, 0]},
    {"label": PREFIX + "MainTower_C", "tower": "BP_MainTower", "panel": "SM_Wall_A26",
     "mesh": "C", "painting": "C", "scale": 1.2,
     "location_cm": [-222.0845, -1278.8345, 2197.7875], "rotation_deg": [0, -90, 0]},
    {"label": PREFIX + "Tower_D", "tower": "BP_Tower", "panel": "SM_Wall_B23",
     "mesh": "B", "painting": "D", "scale": 1.2,
     "location_cm": [1981.4655, -841.0, 2192.6499], "rotation_deg": [0, 0, 0]},
    {"label": PREFIX + "Tower_E", "tower": "BP_Tower", "panel": "SM_Wall_B23",
     "mesh": "C", "painting": "E", "scale": 1.2,
     "location_cm": [1682.2855, -841.0, 2197.7875], "rotation_deg": [0, 0, 0]},
    {"label": PREFIX + "Tower_F", "tower": "BP_Tower", "panel": "SM_Wall_B14",
     "mesh": "B", "painting": "F", "scale": 1.2,
     "location_cm": [940.0, -1284.4555, 3992.6499], "rotation_deg": [0, 90, 0]},
    {"label": PREFIX + "Tower_G", "tower": "BP_Tower", "panel": "SM_Wall_B14",
     "mesh": "C", "painting": "G", "scale": 1.2,
     "location_cm": [940.0, -984.7865, 3997.7875], "rotation_deg": [0, 90, 0]},
]

report = {"success": False, "map": MAP, "placements": [], "errors": []}
eal = unreal.EditorAssetLibrary
try:
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    if not world:
        raise RuntimeError("Could not load " + MAP)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    # Make repeated runs idempotent; these labels belong only to this authored set.
    for actor in list(eas.get_all_level_actors()):
        if actor and actor.get_actor_label().startswith(PREFIX):
            eas.destroy_actor(actor)

    for spec in PLACEMENTS:
        mesh = unreal.load_asset(BASE + f"/Meshes/SM_GothicFrame_{spec['mesh']}")
        image = unreal.load_asset(BASE + f"/Materials/MI_GothicPainting_{spec['painting']}")
        if not mesh or not image:
            raise RuntimeError("Missing imported frame or painting material for " + spec["label"])
        loc = unreal.Vector(*spec["location_cm"])
        pitch, yaw, roll = spec["rotation_deg"]
        rot = unreal.Rotator(pitch=pitch, yaw=yaw, roll=roll)
        actor = eas.spawn_actor_from_class(unreal.StaticMeshActor, loc, rot)
        if not actor:
            raise RuntimeError("Could not spawn " + spec["label"])
        actor.set_actor_label(spec["label"])
        actor.set_folder_path("WorldExpansion/WallArt/Prison")
        actor.set_actor_scale3d(unreal.Vector(spec["scale"], spec["scale"], spec["scale"]))
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        if not comp:
            raise RuntimeError("No StaticMeshComponent on " + spec["label"])
        comp.set_static_mesh(mesh)
        comp.set_material(0, unreal.load_asset(BASE + "/Materials/M_GothicFrame"))
        comp.set_material(1, image)
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        comp.set_cast_shadow(True)
        center, extent = actor.get_actor_bounds(False, True)
        report["placements"].append({**spec, "asset": mesh.get_path_name(),
                                     "material": image.get_path_name(),
                                     "actual_rotation_deg": list(actor.get_actor_rotation().to_tuple()),
                                     "bounds_center_cm": list(center.to_tuple()),
                                     "bounds_extent_cm": list(extent.to_tuple()),
                                     "collision": "NoCollision"})

    if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAP):
        raise RuntimeError("Could not save " + MAP)
    report["success"] = True
except Exception:
    report["errors"].append(traceback.format_exc())
finally:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("GOTHIC_PRISON_WALL_ART_" + ("SAVED" if report["success"] else "FAILED"))
    unreal.SystemLibrary.quit_editor()
