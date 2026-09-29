"""Inspect candidate mansion mission doors and floor traces without saving changes."""

import json
from pathlib import Path

import unreal


MAP_PATH = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
REPORT_PATH = Path(r"F:\Carnival\Saved\MansionConnection\Door_Inspection.json")
world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
if not world:
    raise RuntimeError(f"Could not load {MAP_PATH}")

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
report = {"doors": [], "traces": [], "door_blueprint": {}}
for actor in actors:
    label = actor.get_actor_label()
    if label not in {"BP_Door10", "BP_Door7", "BP_Door02", "SM_Door02_E"}:
        continue
    components = []
    for component in actor.get_components_by_class(unreal.ActorComponent):
        item = {"name": component.get_name(), "class": component.get_class().get_name()}
        if isinstance(component, unreal.SceneComponent):
            transform = component.get_world_transform()
            item["location"] = [transform.translation.x, transform.translation.y, transform.translation.z]
            item["rotation"] = [transform.rotation.rotator().pitch, transform.rotation.rotator().yaw, transform.rotation.rotator().roll]
        if isinstance(component, unreal.StaticMeshComponent):
            mesh = component.get_editor_property("static_mesh")
            item["mesh"] = mesh.get_path_name() if mesh else None
        components.append(item)
    report["doors"].append({
        "label": label,
        "class": actor.get_class().get_name(),
        "path": actor.get_path_name(),
        "location": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z],
        "rotation": [actor.get_actor_rotation().pitch, actor.get_actor_rotation().yaw, actor.get_actor_rotation().roll],
        "components": components,
    })

try:
    bp = unreal.load_asset("/Game/Mansion/Mesh/Assets/Doors/BP_Door02")
    for prop in ("function_graphs", "ubergraph_pages"):
        try:
            graphs = bp.get_editor_property(prop)
            report["door_blueprint"][prop] = [g.get_name() for g in graphs]
        except Exception as error:
            report["door_blueprint"][prop] = str(error)
    try:
        generated = bp.generated_class()
        report["door_blueprint"]["class"] = generated.get_path_name()
        report["door_blueprint"]["functions"] = [fn.get_name() for fn in generated.get_functions()]
    except Exception as error:
        report["door_blueprint"]["functions"] = str(error)
except Exception as error:
    report["door_blueprint"]["error"] = str(error)

for name, location in {
    "foyer_candidate": (-70270.0, -86736.0, 820.0),
    "study_candidate": (-70163.0, -88076.0, 820.0),
    "west_room_candidate": (-69972.0, -88961.0, 820.0),
}.items():
    start = unreal.Vector(location[0], location[1], location[2] + 800.0)
    end = unreal.Vector(location[0], location[1], location[2] - 1000.0)
    trace = {"name": name, "start": [start.x, start.y, start.z], "end": [end.x, end.y, end.z]}
    try:
        hit = unreal.SystemLibrary.line_trace_single(
            world, start, end, unreal.TraceTypeQuery.ECC_VISIBILITY, False, [],
            unreal.DrawDebugTrace.NONE, True
        )
        data = hit.to_tuple() if hit else None
        trace["hit"] = bool(data and data[0])
        if data and data[0]:
            point = data[5]
            # HitResult tuple layout used by the other UE Python probes in this project:
            # actor at 9 and component at 10. Keeping these indices consistent prevents
            # reporting a false empty blocker for the door/floor traces.
            actor = data[9] if len(data) > 9 else None
            component = data[10] if len(data) > 10 else None
            trace["actor"] = actor.get_actor_label() if actor and hasattr(actor, "get_actor_label") else None
            trace["location"] = [point.x, point.y, point.z]
            trace["normal"] = [data[7].x, data[7].y, data[7].z]
            trace["component"] = component.get_name() if component and hasattr(component, "get_name") else None
            trace["hit_tuple_types"] = [type(value).__name__ for value in data]
    except Exception as error:
        trace["error"] = str(error)
    report["traces"].append(trace)

REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log(f"MANSION_DOOR_INSPECTION {REPORT_PATH}")
unreal.SystemLibrary.quit_editor()
