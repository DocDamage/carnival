"""Read-only inspection of the two exterior stair actors and mesh collision."""

import json
from pathlib import Path

import unreal


ROOT = Path(r"F:\Carnival")
MAP = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
OUT = ROOT / "Saved/MansionConnection/Mission_Stair_Collision_Setup.json"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise RuntimeError(f"Could not load {MAP}")

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
report = {"map": MAP, "saved_map_modified": False, "stairs": []}
for actor in actor_subsystem.get_all_level_actors():
    if actor.get_actor_label() not in ("SM_OuterStairs8", "SM_OuterStairs10"):
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    actor_entry = {
        "label": actor.get_actor_label(),
        "path": actor.get_path_name(),
        "location": list(actor.get_actor_location().to_tuple()),
        "rotation": list(actor.get_actor_rotation().to_tuple()),
        "bounds": [list(item.to_tuple()) for item in actor.get_actor_bounds(False)],
    }
    if component:
        try:
            mesh = component.get_editor_property("static_mesh")
            actor_entry["component"] = component.get_path_name()
            actor_entry["mesh"] = mesh.get_path_name() if mesh else None
            actor_entry["component_collision_enabled"] = str(component.get_collision_enabled())
            try:
                actor_entry["collision_profile"] = str(component.get_collision_profile_name())
            except Exception as error:
                actor_entry["collision_profile_error"] = str(error)
            if mesh:
                body = mesh.get_editor_property("body_setup")
                actor_entry["mesh_bounds"] = str(mesh.get_bounding_box())
                actor_entry["collision_trace_flag"] = str(body.get_editor_property("collision_trace_flag")) if body else None
                if body:
                    aggregate = body.get_editor_property("agg_geom")
                    actor_entry["simple_collision"] = {}
                    for prop in ("box_elems", "sphere_elems", "sphyl_elems", "convex_elems"):
                        try:
                            actor_entry["simple_collision"][prop] = len(aggregate.get_editor_property(prop))
                        except Exception as error:
                            actor_entry["simple_collision"][prop] = f"unavailable: {error}"
                    try:
                        actor_entry["collision_boxes"] = [
                            {
                                "center_cm": list(box.get_editor_property("center").to_tuple()),
                                "rotation": list(box.get_editor_property("rotation").to_tuple()),
                                # FKBoxElem stores full X/Y/Z sizes; Chaos halves them when creating the box.
                                "size_cm": [float(box.get_editor_property(axis)) for axis in ("x", "y", "z")],
                            }
                            for box in aggregate.get_editor_property("box_elems")
                        ]
                    except Exception as error:
                        actor_entry["collision_boxes_error"] = str(error)
        except Exception as error:
            actor_entry["component_error"] = str(error)
    report["stairs"].append(actor_entry)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log(f"MANSION_STAIR_COLLISION_SETUP {OUT} {json.dumps(report['stairs'])}")
unreal.SystemLibrary.quit_editor()
