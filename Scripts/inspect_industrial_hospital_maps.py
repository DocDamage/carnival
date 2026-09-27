"""Inspect staged authored levels without saving or changing their source maps."""
import json
import traceback
import unreal
from pathlib import Path

ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/IndustrialHospital"
OUT.mkdir(parents=True, exist_ok=True)
MAPS = [
    "/Game/IndustrialSlums/Levels/L_Night",
    "/Game/IndustrialSlums/Levels/L_DemoScene",
    "/Game/Hospital_Meshingun/Environment/Map/MainMap",
    "/Game/Hospital_Meshingun/Environment/Map/LV_Hospital_Main_Architecture",
    "/Game/Hospital_Meshingun/Environment/Map/LV_Hospital_Main_SetDress",
]

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
results = []
for asset_path in MAPS:
    item = {"asset_path": asset_path}
    try:
        world = unreal.EditorLoadingAndSavingUtils.load_map(asset_path)
        item["world"] = world.get_path_name()
        levels = list(unreal.EditorLevelUtils.get_levels(world))
        item["levels"] = [level.get_path_name() for level in levels]
        actors = list(eas.get_all_level_actors())
        item["actor_count"] = len(actors)
        counts = {}
        level_counts = {}
        bounds = []
        interesting = []
        actor_details = []
        for actor in actors:
            cls = actor.get_class().get_name()
            counts[cls] = counts.get(cls, 0) + 1
            try:
                level_path = actor.get_level().get_path_name()
            except Exception:
                level_path = ""
            level_counts[level_path] = level_counts.get(level_path, 0) + 1
            location = actor.get_actor_location().to_tuple()
            rotation = actor.get_actor_rotation().to_tuple()
            label = actor.get_actor_label()
            try:
                origin, extent = actor.get_actor_bounds(False, True)
                actor_bounds = {"center": origin.to_tuple(), "extent": extent.to_tuple()}
            except Exception:
                actor_bounds = None
            mesh_path = None
            try:
                components = actor.get_components_by_class(unreal.StaticMeshComponent)
                mesh = components[0].get_editor_property("static_mesh") if components else None
                mesh_path = mesh.get_path_name() if mesh else None
            except Exception:
                pass
            actor_details.append({
                "label": label,
                "class": cls,
                "location": location,
                "rotation": rotation,
                "level": level_path,
                "bounds": actor_bounds,
                "mesh": mesh_path,
            })
            if cls in ("StaticMeshActor", "Landscape", "InstancedFoliageActor"):
                try:
                    origin, extent = actor.get_actor_bounds(False, True)
                    center = origin.to_tuple()
                    half = extent.to_tuple()
                    if max(abs(x) for x in center) < 1_000_000 and max(half) < 1_000_000:
                        bounds.append((center, half))
                except Exception:
                    pass
            if cls in ("PlayerStart", "ExponentialHeightFog", "DirectionalLight",
                       "SkyLight", "SkyAtmosphere", "VolumetricCloud", "PostProcessVolume"):
                interesting.append({"label": label, "class": cls, "location": location})
        item["class_counts"] = dict(sorted(counts.items(), key=lambda pair: (-pair[1], pair[0])))
        item["level_actor_counts"] = level_counts
        item["actors"] = actor_details
        item["interesting_actors"] = interesting[:160]
        if bounds:
            item["bounds"] = {
                "min": [min(center[i] - half[i] for center, half in bounds) for i in range(3)],
                "max": [max(center[i] + half[i] for center, half in bounds) for i in range(3)],
                "mesh_actor_count": len(bounds),
            }
        results.append(item)
        unreal.log(f"INDUSTRIAL_HOSPITAL_INSPECT {asset_path} actors={len(actors)} levels={len(levels)}")
    except Exception as exc:
        item["error"] = repr(exc)
        item["traceback"] = traceback.format_exc()
        results.append(item)
        unreal.log_error(f"INDUSTRIAL_HOSPITAL_INSPECT_FAILED {asset_path}: {exc}")

(OUT / "Map_Inspection.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
unreal.log("INDUSTRIAL_HOSPITAL_MAP_INSPECTION_SAVED")
