"""Read source layout anchors, streaming maps, and nested actor components."""
import json
import traceback
from pathlib import Path
from collections import Counter
import unreal

ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/WorldExpansion/Layout_Anchors.json"
MAPS = [
    ("docks_demonstration", "/Game/Docks/VOL2_Powell/Maps/Demonstration"),
    ("prison_overview", "/Game/HAUNTED_PRISON/Levels/L_Overview"),
    ("research_lab_a", "/Game/SciFiWorld/Maps/SciFiCreaturesResearchRoomA"),
    ("sewer_corridor", "/Game/Sewer/Levels/L_Sewers_Corridor"),
    ("sewer_pier", "/Game/Sewer/Levels/L_Sewers_Pier"),
    ("shipwreck_exterior", "/Game/UnderwaterShip/Levels/UnderwaterShip_Showcase_Exterior"),
]
report = {"maps": [], "errors": []}
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
needles = ("pier", "deck", "shore", "sand", "dock", "boat", "prison", "tower", "door",
           "floor", "wall", "room", "corridor", "arch", "ship", "hull", "rock", "main")


for label, path in MAPS:
    try:
        world = unreal.EditorLoadingAndSavingUtils.load_map(path)
        if not world:
            raise RuntimeError("load_map returned null")
        actors = list(eas.get_all_level_actors())
        try:
            level_paths = [level.get_path_name() for level in unreal.EditorLevelUtils.get_levels(world)]
        except Exception:
            level_paths = []
        counts = Counter(actor.get_class().get_name() for actor in actors)
        rows = []
        for actor in actors:
            name = actor.get_actor_label()
            if not any(part in name.lower() for part in needles):
                continue
            row = {"label": name, "class": actor.get_class().get_name(),
                   "location_cm": list(actor.get_actor_location().to_tuple()),
                   "rotation_deg": list(actor.get_actor_rotation().to_tuple()),
                   "scale": list(actor.get_actor_scale3d().to_tuple())}
            try:
                center, extent = actor.get_actor_bounds(False, True)
                row["bounds_center_cm"] = list(center.to_tuple())
                row["bounds_extent_cm"] = list(extent.to_tuple())
            except Exception:
                pass
            components = []
            try:
                for component in actor.get_components_by_class(unreal.ActorComponent):
                    item = {"class": component.get_class().get_name()}
                    try:
                        mesh = component.get_editor_property("static_mesh")
                        if mesh:
                            item["mesh"] = mesh.get_path_name()
                    except Exception:
                        pass
                    components.append(item)
            except Exception:
                pass
            row["components"] = components[:20]
            rows.append(row)
        report["maps"].append({"label": label, "map": path, "actor_count": len(actors),
                               "class_counts": dict(counts), "levels": level_paths,
                               "anchors": rows[:200]})
        OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        unreal.log("WORLD_EXPANSION_LAYOUT_ANCHORS " + label)
    except Exception:
        report["errors"].append({"map": path, "traceback": traceback.format_exc()})
        OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")

OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("WORLD_EXPANSION_LAYOUT_ANCHORS_COMPLETE")
unreal.SystemLibrary.quit_editor()
