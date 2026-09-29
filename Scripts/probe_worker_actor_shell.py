"""Inspect whether a saved crowd instance can initialize the supported MetaHuman actor class."""

import json
from pathlib import Path

import unreal


REPORT = Path(r"F:\Carnival\Saved\MissionAuthoring\Worker_Actor_Shell_Probe.json")
INSTANCE_PATH = "/Game/Carnival/Crowd/Instances/ExpandedFinal2/MHI_Dean"
ACTOR_CLASS_PATH = "/MetaHumanCrowd/BP_CrowdActor.BP_CrowdActor_C"
result = {"read_only": True, "instance_path": INSTANCE_PATH, "actor_class_path": ACTOR_CLASS_PATH, "success": False}
instance = unreal.EditorAssetLibrary.load_asset(INSTANCE_PATH)
actor_class = unreal.load_class(None, ACTOR_CLASS_PATH)
if instance is None or actor_class is None:
    result["error"] = "Could not load the MetaHuman instance or actor class"
else:
    result["actor_class"] = actor_class.get_path_name()
    cdo = unreal.get_default_object(actor_class)
    result["default_components"] = []
    for component in cdo.get_components_by_class(unreal.SkeletalMeshComponent):
        mesh = component.get_editor_property("skeletal_mesh_asset")
        anim = component.get_editor_property("anim_class")
        result["default_components"].append({
            "name": component.get_name(),
            "mesh": mesh.get_path_name() if mesh else None,
            "anim_class": anim.get_path_name() if anim else None,
        })
    try:
        actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        world = unreal.EditorLevelLibrary.get_editor_world()
        result["world"] = world.get_path_name() if world else None
        actor = unreal.EditorLevelLibrary.spawn_actor_from_object(
            instance, unreal.Vector(0, 0, 100000), unreal.Rotator()
        )
        if actor is None:
            result["error"] = "MetaHuman asset factory could not create an actor in the editor world"
        else:
            result["spawned_actor_class"] = actor.get_class().get_path_name()
            result["setter_available"] = hasattr(actor, "set_meta_human_instance")
            try:
                output = instance.get_assembly_output()
                result["assembly_struct"] = str(output)
                result["assembly_assets"] = {}
                for property_name in ("actor_face_mesh", "actor_body_mesh", "instanced_face_mesh", "instanced_body_mesh"):
                    try:
                        mesh = output.get_editor_property(property_name)
                        result["assembly_assets"][property_name] = (
                            mesh.get_path_name() if mesh else None
                        )
                    except Exception as exc:
                        result["assembly_assets"][property_name + "_error"] = str(exc)
            except Exception as exc:
                result["assembly_error"] = str(exc)
            result["initialized_components"] = []
            for component in actor.get_components_by_class(unreal.SkeletalMeshComponent):
                mesh = component.get_editor_property("skeletal_mesh_asset")
                anim = component.get_editor_property("anim_class")
                result["initialized_components"].append({
                    "name": component.get_name(),
                    "mesh": mesh.get_path_name() if mesh else None,
                    "anim_class": anim.get_path_name() if anim else None,
                })
            result["instance_assembled"] = bool(instance.is_assembled())
            result["success"] = any(item["mesh"] for item in result["initialized_components"])
            actors.destroy_actor(actor)
    except Exception as exc:
        result["probe_error"] = str(exc)

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log("CARNIVAL_WORKER_ACTOR_SHELL_PROBE " + json.dumps(result))
unreal.SystemLibrary.quit_editor()
