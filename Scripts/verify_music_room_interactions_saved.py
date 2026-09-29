"""Reload LV_Carnival and verify the persisted music-room mission actors."""

import json
import traceback
from pathlib import Path

import unreal


ROOT = Path(r"F:\Carnival")
MAP = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
REPORT = ROOT / "Saved/MissionAuthoring/MusicRoomInteractions_SavedMap_Verification.json"
LABELS = {
    "board": "Mission_NoticeBoard_Interaction",
    "entrance": "Mission_MansionEntrance_Interaction",
    "clue": "Mission_Foyer_Glove_Note",
    "study": "Mission_Study_Log_ServiceKey",
    "door": "Mission_MusicRoom_KeyedDoor",
    "box": "Mission_MusicBox_Interaction",
    "doll": "Mission_Mansion_Doll",
    "exit": "Mission_MansionExit_Interaction",
    "return": "Mission_CarnivalReturn_Trigger",
}
TRANSIENT_LABEL = "Transient_WorkerStateProbe"
WORKER_LABEL = "Mission_Eli_Mercer_Character"
WORKER_INTERACTION_LABEL = "Mission_Eli_Worker_Interaction"
WORKER_INSTANCE = "/Game/Carnival/Crowd/Instances/ExpandedFinal2/MHI_Dean"
KEY_PROP_LABEL = "Mission_ServiceKey_VisibleProp"
NOTE_PROP_LABEL = "Mission_Foyer_Eli_Physical_Note"
MUSIC_BOX_MESH = "/Game/Carnival/Props/Mission/SM_BrassMusicBox.SM_BrassMusicBox"
GLOVE_MESH = "/Game/Carnival/Props/Mission/SM_WetWorkGlove.SM_WetWorkGlove"
SERVICE_KEY_MESH = "/Game/Carnival/Props/Mission/SM_BrassServiceKey.SM_BrassServiceKey"
NOTE_MESH = "/Game/Carnival/Props/Mission/SM_EliFoyerNote.SM_EliFoyerNote"
DOLL_MESH = "/Game/Carnival/Characters/PossessedDoll/SK_Doll.SK_Doll"
IDLE = "/Game/Carnival/Characters/PossessedDoll/Animations/Original/Doll_Idle_Possessed_Loop.Doll_Idle_Possessed_Loop"
HEAD_SNAP = "/Game/Carnival/Characters/PossessedDoll/Animations/Original/Doll_Head_Snap.Doll_Head_Snap"
LUNGE = "/Game/Carnival/Characters/PossessedDoll/Animations/Original/Doll_Jumpscare_Lunge.Doll_Jumpscare_Lunge"
SCARE_SOUND = "/Game/Carnival/Audio/IndustrialHospital/Smiling_Doll_in_the_Dark.Smiling_Doll_in_the_Dark"

result = {"map": MAP, "read_only": True, "success": False, "errors": []}

try:
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    if not world:
        raise RuntimeError(f"Could not load {MAP}")
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    by_label = {actor.get_actor_label(): actor for actor in actors}
    found = {name: by_label.get(label) for name, label in LABELS.items()}
    worker = by_label.get(WORKER_LABEL)
    worker_interaction = by_label.get(WORKER_INTERACTION_LABEL)
    key_prop = by_label.get(KEY_PROP_LABEL)
    note_prop = by_label.get(NOTE_PROP_LABEL)
    result.update({
        "loaded_world": world.get_path_name(),
        "actor_presence": {name: actor is not None for name, actor in found.items()},
        "worker_actor_present": worker is not None,
        "worker_interaction_present": worker_interaction is not None,
        "service_key_prop_present": key_prop is not None,
        "physical_note_prop_present": note_prop is not None,
        "transient_worker_probe_absent": TRANSIENT_LABEL not in by_label,
    })

    worker_components = []
    body_component = None
    if worker:
        for component in worker.get_components_by_class(unreal.SkeletalMeshComponent):
            mesh = component.get_skeletal_mesh_asset()
            anim_mode = component.get_editor_property("animation_mode")
            item = {
                "name": component.get_name(),
                "mesh": mesh.get_path_name() if mesh else None,
                "animation_mode": str(anim_mode),
            }
            if component.get_name() == "Body":
                body_component = component
                anim_instance = component.get_anim_instance()
                item["anim_instance"] = anim_instance.get_class().get_path_name() if anim_instance else None
                get_current_asset = getattr(anim_instance, "get_current_asset", None) if anim_instance else None
                if get_current_asset:
                    current_asset = get_current_asset()
                    item["current_animation"] = current_asset.get_path_name() if current_asset else None
                is_playing = getattr(anim_instance, "is_playing", None) if anim_instance else None
                if is_playing:
                    item["is_playing"] = bool(is_playing())
            worker_components.append(item)
        result["worker"] = {
            "class": worker.get_class().get_path_name(),
            "instance_asset_expected": WORKER_INSTANCE,
            "location": list(worker.get_actor_location().to_tuple()),
            "actor_collision_enabled": worker.get_actor_enable_collision(),
            "tags": [str(tag) for tag in worker.get_editor_property("tags")],
            "skeletal_components": worker_components,
        }
    if worker_interaction:
        result["worker_interaction"] = {
            "interaction": str(worker_interaction.get_editor_property("interaction")),
            "prompt": str(worker_interaction.get_prompt_text()),
            "accepted_feedback": str(worker_interaction.get_editor_property("accepted_feedback")),
            "radius_cm": worker_interaction.get_editor_property("interaction_radius"),
            "target_actor": (
                worker_interaction.get_editor_property("interaction_target_actor").get_actor_label()
                if worker_interaction.get_editor_property("interaction_target_actor") else None
            ),
            "location": list(worker_interaction.get_actor_location().to_tuple()),
        }

    door = found["door"]
    box = found["box"]
    doll = found["doll"]
    if door:
        location = door.get_editor_property("controlled_door_actor_location")
        pointer = door.get_editor_property("controlled_door_actor")
        result["door_identity"] = {
            "actor_name": str(door.get_editor_property("controlled_door_actor_name")),
            "actor_location": list(location.to_tuple()),
            "hard_actor_pointer_null": pointer is None,
            "interaction": str(door.get_editor_property("interaction")),
        }
    if box:
        mesh = box.get_editor_property("interaction_mesh")
        result["music_box"] = {
            "interaction": str(box.get_editor_property("interaction")),
            "mesh": mesh.get_path_name() if mesh else None,
            "location": list(box.get_actor_location().to_tuple()),
        }
    if found["clue"]:
        glove = found["clue"].get_editor_property("interaction_mesh")
        result["foyer_glove"] = {
            "mesh": glove.get_path_name() if glove else None,
            "location": list(found["clue"].get_actor_location().to_tuple()),
            "mesh_offset": list(found["clue"].get_editor_property("interaction_mesh_offset").to_tuple()),
        }
    if key_prop:
        key_component = key_prop.get_component_by_class(unreal.StaticMeshComponent)
        key_mesh = key_component.get_editor_property("static_mesh") if key_component else None
        result["service_key_prop"] = {
            "actor_class": key_prop.get_class().get_name(),
            "mesh": key_mesh.get_path_name() if key_mesh else None,
            "location": list(key_prop.get_actor_location().to_tuple()),
            "collision": str(key_component.get_collision_enabled()) if key_component else None,
            "collision_profile": str(key_component.get_collision_profile_name()) if key_component else None,
        }
    if note_prop:
        note_component = note_prop.get_component_by_class(unreal.StaticMeshComponent)
        note_mesh = note_component.get_editor_property("static_mesh") if note_component else None
        result["physical_note_prop"] = {
            "actor_class": note_prop.get_class().get_name(),
            "mesh": note_mesh.get_path_name() if note_mesh else None,
            "location": list(note_prop.get_actor_location().to_tuple()),
            "collision": str(note_component.get_collision_enabled()) if note_component else None,
            "collision_profile": str(note_component.get_collision_profile_name()) if note_component else None,
        }
    if doll:
        mesh_component = doll.get_component_by_class(unreal.SkeletalMeshComponent)
        mesh = mesh_component.get_skeletal_mesh_asset() if mesh_component else None
        fields = ("idle_animation", "mission_head_snap_animation", "scare_animation", "scare_sound")
        result["doll"] = {
            "mesh": mesh.get_path_name() if mesh else None,
            "mission_controlled_instance": doll.get_editor_property("mission_controlled_instance"),
            "encounter_enabled": doll.get_editor_property("encounter_enabled"),
            "assets": {
                field: (doll.get_editor_property(field).get_path_name()
                        if doll.get_editor_property(field) else None)
                for field in fields
            },
            "location": list(doll.get_actor_location().to_tuple()),
        }

    door_name = str(door.get_editor_property("controlled_door_actor_name")) if door else ""
    door_location = door.get_editor_property("controlled_door_actor_location") if door else None
    box_mesh = box.get_editor_property("interaction_mesh") if box else None
    glove_mesh = found["clue"].get_editor_property("interaction_mesh") if found["clue"] else None
    doll_mesh_component = doll.get_component_by_class(unreal.SkeletalMeshComponent) if doll else None
    doll_mesh = doll_mesh_component.get_skeletal_mesh_asset() if doll_mesh_component else None
    checks = {
        "all_mission_actors_present": all(found.values()) and worker is not None and worker_interaction is not None,
        "worker_probe_absent": TRANSIENT_LABEL not in by_label,
        "worker_character_assembled_and_nonblocking": bool(
            worker
            and worker.get_class().get_path_name() == "/MetaHumanCrowd/BP_CrowdActor.BP_CrowdActor_C"
            and not worker.get_actor_enable_collision()
            and body_component
            and body_component.get_skeletal_mesh_asset()
            and body_component.get_editor_property("animation_mode") == unreal.AnimationMode.ANIMATION_SINGLE_NODE
        ),
        "worker_talk_interaction_persisted": bool(
            worker_interaction
            and worker_interaction.get_editor_property("interaction") == unreal.CarnivalMissionInteraction.WORKER
            and str(worker_interaction.get_prompt_text()) == "Talk to Eli Mercer"
            and worker_interaction.get_editor_property("interaction_radius") == 270.0
            and worker_interaction.get_editor_property("interaction_target_actor") is worker
        ),
        "music_box_mesh_correct": bool(box_mesh and box_mesh.get_path_name() == MUSIC_BOX_MESH),
        "foyer_glove_mesh_correct": bool(glove_mesh and glove_mesh.get_path_name() == GLOVE_MESH),
        "study_key_mesh_correct_and_nonblocking": bool(
            key_prop
            and key_prop.get_class().get_name() == "StaticMeshActor"
            and (key_component := key_prop.get_component_by_class(unreal.StaticMeshComponent))
            and key_component.get_editor_property("static_mesh")
            and key_component.get_editor_property("static_mesh").get_path_name() == SERVICE_KEY_MESH
            and key_component.get_collision_enabled() == unreal.CollisionEnabled.NO_COLLISION
            and "NOCOLLISION" in str(key_component.get_collision_profile_name()).replace("_", "").upper()
        ),
        "physical_note_mesh_correct_and_nonblocking": bool(
            note_prop
            and note_prop.get_class().get_name() == "StaticMeshActor"
            and (note_component := note_prop.get_component_by_class(unreal.StaticMeshComponent))
            and note_component.get_editor_property("static_mesh")
            and note_component.get_editor_property("static_mesh").get_path_name() == NOTE_MESH
            and note_component.get_collision_enabled() == unreal.CollisionEnabled.NO_COLLISION
            and "NOCOLLISION" in str(note_component.get_collision_profile_name()).replace("_", "").upper()
        ),
        "door_identity_saved_without_hard_reference": bool(
            door and door_name == "BP_Door02_C_2" and door_location
            and door.get_editor_property("controlled_door_actor") is None
        ),
        "doll_mesh_correct": bool(doll_mesh and doll_mesh.get_path_name() == DOLL_MESH),
        "doll_is_mission_controlled_and_inert": bool(
            doll and doll.get_editor_property("mission_controlled_instance")
            and not doll.get_editor_property("encounter_enabled")
        ),
    }
    if doll:
        checks["doll_animation_and_sound_assets_correct"] = all(
            doll.get_editor_property(field)
            and doll.get_editor_property(field).get_path_name() == expected
            for field, expected in (
                ("idle_animation", IDLE),
                ("mission_head_snap_animation", HEAD_SNAP),
                ("scare_animation", LUNGE),
                ("scare_sound", SCARE_SOUND),
            )
        )
    result["checks"] = checks
    result["success"] = all(checks.values())
    if not result["success"]:
        result["errors"].append("One or more music-room actors or properties did not survive map reload")
except Exception:
    result["errors"].append(traceback.format_exc())

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log("MUSIC_ROOM_INTERACTIONS_SAVED_MAP_VERIFICATION " + json.dumps(result))
if not result["success"]:
    raise RuntimeError("Music-room saved-map verification failed")
