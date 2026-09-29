"""Place a curated portrait and archival-photo set on clear Research Lab B walls."""
import json
import traceback
from pathlib import Path

import unreal


ROOT = Path(r"F:\Carnival")
MAP = "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_LabB"
BASE = "/Game/HorrorPaintVol48"
OUT = ROOT / "Saved/WorldExpansion/HorrorPaintVol48_LabB_WallArt_Placement.json"
PREFIX = "WorldExpansion_WallArt_LabB_"

# These are the three blank 700 x 350 cm panels centered at X=325, -375,
# and -1075 on the north side of Lab B. The room is on the -Y side of the
# panels. Portrait frames face local +Y, so yaw 180 turns them into the room.
# The smaller photo frames face local +X, so yaw -90 turns them into the room.
# The panel pivot does not identify its visible face; derive the mounting
# plane from its actual transformed bounds below. Target values refer to
# visible mesh bounds rather than actor pivots; several pack meshes use an
# edge pivot, which otherwise leaves inconsistent gaps between frames.
PORTRAITS = [
    # A restrained row of three on each of the two wider portrait panels.
    ("Portrait_01", "SM_Picture_01", -1265.0, 180.0),
    ("Portrait_02", "SM_Picture_02", -1075.0, 180.0),
    ("Portrait_05", "SM_Picture_05", -885.0, 180.0),
    ("Portrait_06", "SM_Picture_06", -565.0, 180.0),
    ("Portrait_08", "SM_Picture_08", -375.0, 180.0),
    ("Portrait_10", "SM_Picture_10", -185.0, 180.0),
]

# The smaller photo frames are scaled to read as archival wall photographs.
# Their spacing is wider than their scaled bounds, leaving the panel visually
# light beside the larger portraits.
PHOTOS = [
    ("Photo_01", "SM_Photo_01", 105.0, 1.7),
    ("Photo_02", "SM_Photo_02", 215.0, 1.7),
    ("Photo_03", "SM_Photo_03", 325.0, 1.7),
    ("Photo_04", "SM_Photo_04", 435.0, 1.7),
    ("Photo_05", "SM_Photo_05", 545.0, 1.7),
]

PLACEMENTS = []
for label, mesh, x, z in PORTRAITS:
    PLACEMENTS.append({
        "label": PREFIX + label,
        "asset": f"{BASE}/Meshes/{mesh}",
        "rotation_deg": [0.0, 180.0, 0.0],
        "scale": 1.0,
        "target_bounds_center_x_cm": x,
        "target_bounds_center_z_cm": z,
        "wall_face_y_cm": 1447.0,
        "group": "portrait",
    })
for label, mesh, x, scale in PHOTOS:
    PLACEMENTS.append({
        "label": PREFIX + label,
        "asset": f"{BASE}/Meshes/{mesh}",
        "rotation_deg": [0.0, -90.0, 0.0],
        "scale": scale,
        "target_bounds_center_x_cm": x,
        "target_bounds_center_z_cm": 180.0,
        "wall_face_y_cm": 1447.0,
        "group": "archival_photo",
    })

report = {"success": False, "map": MAP, "placements": [], "errors": []}

try:
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    if not world:
        raise RuntimeError("Could not load " + MAP)

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in list(actor_subsystem.get_all_level_actors()):
        if actor and actor.get_actor_label().startswith(PREFIX):
            actor_subsystem.destroy_actor(actor)

    for spec in PLACEMENTS:
        faces=[]
        for wall in actor_subsystem.get_all_level_actors():
            wall_comp=wall.get_component_by_class(unreal.StaticMeshComponent)
            wall_mesh=wall_comp.get_editor_property('static_mesh') if wall_comp else None
            if not wall_mesh or 'mwall' not in wall_mesh.get_name().lower(): continue
            wc,we=wall.get_actor_bounds(False,True)
            if we.y<50 and wc.y>1400 and abs(spec['target_bounds_center_x_cm']-wc.x)<=we.x:
                faces.append(wc.y-we.y)
        if not faces: raise RuntimeError('No wall panel for '+spec['label'])
        spec['wall_face_y_cm']=min(faces)-.5
        mesh = unreal.load_asset(spec["asset"])
        if not mesh:
            raise RuntimeError("Could not load mesh " + spec["asset"])

        # These source meshes carry their own frame and artwork material
        # instances. Confirm both slots survived migration before placement.
        slots = list(mesh.get_editor_property("static_materials"))
        if len(slots) < 2:
            raise RuntimeError("Expected frame and artwork materials on " + spec["asset"])
        materials = [slot.material_interface for slot in slots]
        if any(material is None for material in materials[:2]):
            raise RuntimeError("Missing frame or artwork material on " + spec["asset"])

        pitch, yaw, roll = spec["rotation_deg"]
        rot = unreal.Rotator(pitch=pitch, yaw=yaw, roll=roll)
        actor = actor_subsystem.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(0.0, 0.0, 0.0), rot
        )
        if not actor:
            raise RuntimeError("Could not spawn " + spec["label"])

        actor.set_actor_label(spec["label"])
        actor.set_folder_path("WorldExpansion/WallArt/ResearchLab")
        actor.set_actor_scale3d(unreal.Vector(spec["scale"], spec["scale"], spec["scale"]))
        component = actor.get_component_by_class(unreal.StaticMeshComponent)
        if not component:
            raise RuntimeError("No StaticMeshComponent on " + spec["label"])
        component.set_static_mesh(mesh)
        component.set_collision_profile_name('NoCollision')
        component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        component.set_cast_shadow(True)

        # Correct the source pivots using each rotated/scaled mesh's real
        # bounds. This centers the artwork evenly and places its back edge at
        # the inner wall face, regardless of how each source mesh was modeled.
        center, extent = actor.get_actor_bounds(False, True)
        loc = unreal.Vector(
            spec["target_bounds_center_x_cm"] - center.x,
            spec["wall_face_y_cm"] - (center.y + extent.y),
            spec["target_bounds_center_z_cm"] - center.z,
        )
        actor.set_actor_location(loc, False, True)
        center, extent = actor.get_actor_bounds(False, True)
        wall_edge_y = center.y + extent.y
        if abs(center.x - spec["target_bounds_center_x_cm"]) > 0.1:
            raise RuntimeError("Could not center " + spec["label"] + " on its panel")
        if abs(center.z - spec["target_bounds_center_z_cm"]) > 0.1:
            raise RuntimeError("Could not set height for " + spec["label"])
        if abs(wall_edge_y - spec["wall_face_y_cm"]) > 0.1:
            raise RuntimeError("Could not align " + spec["label"] + " to the wall")
        report["placements"].append({
            **spec,
            "mesh": mesh.get_path_name(),
            "material_slots": [m.get_path_name() if m else None for m in materials],
            "actual_location_cm": list(actor.get_actor_location().to_tuple()),
            "actual_rotation_deg": list(actor.get_actor_rotation().to_tuple()),
            "bounds_center_cm": list(center.to_tuple()),
            "bounds_extent_cm": list(extent.to_tuple()),
            "wall_edge_y_cm": wall_edge_y,
            "collision": "NoCollision",
        })

    if len(report["placements"]) != len(PLACEMENTS):
        raise RuntimeError("Placement count does not match the requested authored set")
    if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAP):
        raise RuntimeError("Could not save " + MAP)
    report["success"] = True
except Exception:
    report["errors"].append(traceback.format_exc())
finally:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("HORROR_PAINT_VOL48_LABB_WALL_ART_" + ("SAVED" if report["success"] else "FAILED"))
    unreal.SystemLibrary.quit_editor()
