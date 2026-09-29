"""Exercise MetaHuman actor initialization in the mansion map without saving it."""

import json
from pathlib import Path

import unreal


ROOT = Path(r"F:\Carnival")
MAP = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
INSTANCE = "/Game/Carnival/Crowd/Instances/ExpandedFinal2/MHI_Dean"
REPORT = ROOT / "Saved/MissionAuthoring/Worker_Initialization_Probe.json"
LABEL = "Transient_MissionWorker_Initialization_Probe"
result = {"read_only": True, "success": False, "map": MAP, "instance": INSTANCE}
actor = None

try:
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    if not world:
        raise RuntimeError(f"Could not load {MAP}")
    instance = unreal.load_asset(INSTANCE)
    if not instance:
        raise RuntimeError(f"Could not load {INSTANCE}")
    library = unreal.CarnivalCrowdEditorLibrary
    place = library.place_initialized_meta_human_actor
    result["place_function"] = getattr(place, "__doc__", None)

    try:
        out_error = unreal.StringRef()
        actor = place(
            instance,
            LABEL,
            unreal.Vector(-71000.0, -89000.0, 1000.0),
            unreal.Rotator(),
            out_error,
        )
        result["out_error_ref"] = str(out_error)
    except Exception as first_error:
        result["first_call_error"] = str(first_error)
        actor = place(
            instance,
            LABEL,
            unreal.Vector(-71000.0, -89000.0, 1000.0),
            unreal.Rotator(),
        )

    if isinstance(actor, tuple):
        result["return_tuple"] = [str(value) for value in actor]
        actor = next((value for value in actor if isinstance(value, unreal.Actor)), None)
    if actor:
        result["actor_class"] = actor.get_class().get_path_name()
        result["actor_label"] = actor.get_actor_label()
        result["components"] = []
        for component in actor.get_components_by_class(unreal.SkeletalMeshComponent):
            mesh = component.get_editor_property("skeletal_mesh_asset")
            item = {
                "name": component.get_name(),
                "mesh": mesh.get_path_name() if mesh else None,
                "anim_class": component.get_editor_property("anim_class").get_path_name()
                if component.get_editor_property("anim_class") else None,
                "animation_mode": str(component.get_editor_property("animation_mode")),
            }
            get_animation = getattr(component, "get_animation", None)
            if get_animation:
                animation = get_animation()
                item["animation"] = animation.get_path_name() if animation else None
            get_anim_instance = getattr(component, "get_anim_instance", None)
            if get_anim_instance:
                anim_instance = get_anim_instance()
                item["anim_instance"] = anim_instance.get_class().get_path_name() if anim_instance else None
            result["components"].append(item)
        result["success"] = any(item["mesh"] for item in result["components"])
        unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(actor)
        actor = None
    else:
        result["error"] = "The helper did not return a MetaHuman actor."
except Exception as exc:
    result["error"] = str(exc)
    if actor:
        unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(actor)

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log("CARNIVAL_WORKER_INITIALIZATION_PROBE " + json.dumps(result))
unreal.SystemLibrary.quit_editor()
