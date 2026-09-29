"""Place the assembled Eli actor and his gated talk interaction in the music room."""

import json
import math
import shutil
import time
from pathlib import Path

import unreal


ROOT = Path(r"F:\Carnival")
MAP = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
MAP_FILE = ROOT / "Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap"
BACKUP_DIR = ROOT / "Saved/MissionAuthoring/Backups"
REPORT = ROOT / "Saved/MissionAuthoring/MissionWorker_Placement.json"
INSTANCE_PATH = "/Game/Carnival/Crowd/Instances/ExpandedFinal2/MHI_Dean"
WORKER_LABEL = "Mission_Eli_Mercer_Character"
INTERACTION_LABEL = "Mission_Eli_Worker_Interaction"
MUSIC_APPROACH = unreal.Vector(-71082.33, -88852.89, 913.764)
BOX_LOCATION = unreal.Vector(-71082.8658, -89031.9645, 913.6424)
DOLL_LOCATION = unreal.Vector(-71252.8658, -88746.9645, 888.7641)

if not MAP_FILE.is_file():
    raise RuntimeError(f"Missing saved map file: {MAP_FILE}")
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
backup = BACKUP_DIR / f"LV_Carnival.before_worker_{time.strftime('%Y%m%d_%H%M%S')}.umap"
shutil.copy2(MAP_FILE, backup)

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise RuntimeError(f"Could not load {MAP}")
actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
by_label = {actor.get_actor_label(): actor for actor in actor_subsystem.get_all_level_actors()}


def hit_tuple(hit):
    return hit.to_tuple() if hit else None


def horizontal_distance(first, second):
    return math.hypot(first.x - second.x, first.y - second.y)

placement_candidates = []
placement_attempts = []
for candidate_x in (-71100.0, -71050.0, -71000.0, -70950.0, -70900.0, -70850.0):
    for candidate_y in (-88850.0, -88900.0, -88950.0, -89000.0, -89050.0, -89100.0):
        floor_hit = hit_tuple(unreal.SystemLibrary.line_trace_single(
            world,
            unreal.Vector(candidate_x, candidate_y, 1500.0),
            unreal.Vector(candidate_x, candidate_y, 500.0),
            unreal.TraceTypeQuery.ECC_VISIBILITY,
            False,
            [],
            unreal.DrawDebugTrace.NONE,
            True,
        ))
        if not floor_hit or not floor_hit[0] or floor_hit[7].z < 0.70:
            placement_attempts.append({"x": candidate_x, "y": candidate_y, "floor": "no walkable hit"})
            continue
        floor_actor = floor_hit[9].get_actor_label() if floor_hit[9] else None
        if not floor_actor or not floor_actor.startswith("SM_InnerFloor"):
            placement_attempts.append({"x": candidate_x, "y": candidate_y, "floor": floor_actor})
            continue
        location = unreal.Vector(candidate_x, candidate_y, floor_hit[5].z + 0.5)
        approach_distance = horizontal_distance(location, MUSIC_APPROACH)
        box_distance = horizontal_distance(location, BOX_LOCATION)
        doll_distance = horizontal_distance(location, DOLL_LOCATION)
        attempt = {
            "x": candidate_x,
            "y": candidate_y,
            "floor": floor_actor,
            "approach_distance": round(approach_distance, 1),
            "box_distance": round(box_distance, 1),
            "doll_distance": round(doll_distance, 1),
        }
        if not 100.0 <= approach_distance <= 270.0 or box_distance < 120.0 or doll_distance < 210.0:
            attempt["rejected"] = "distance"
            placement_attempts.append(attempt)
            continue
        capsule_hit = hit_tuple(unreal.SystemLibrary.capsule_trace_single(
            world,
            location + unreal.Vector(0.0, 0.0, 96.0),
            location + unreal.Vector(0.0, 0.0, 96.1),
            42.0,
            96.0,
            unreal.TraceTypeQuery.ECC_VISIBILITY,
            False,
            [],
            unreal.DrawDebugTrace.NONE,
            True,
        ))
        if capsule_hit and capsule_hit[0]:
            attempt["rejected"] = "capsule blocked"
            attempt["capsule_blocker"] = capsule_hit[9].get_actor_label() if capsule_hit[9] else None
            placement_attempts.append(attempt)
            continue
        view_hit = hit_tuple(unreal.SystemLibrary.line_trace_single(
            world,
            MUSIC_APPROACH + unreal.Vector(0.0, 0.0, 50.0),
            location + unreal.Vector(0.0, 0.0, 130.0),
            unreal.TraceTypeQuery.ECC_VISIBILITY,
            False,
            [],
            unreal.DrawDebugTrace.NONE,
            True,
        ))
        if view_hit and view_hit[0]:
            attempt["rejected"] = "line of sight blocked"
            attempt["view_blocker"] = view_hit[9].get_actor_label() if view_hit[9] else None
            placement_attempts.append(attempt)
            continue
        attempt["rejected"] = None
        placement_attempts.append(attempt)
        placement_candidates.append({
            "location": location,
            "floor_hit": floor_hit,
            "floor_actor": floor_actor,
            "approach_distance": approach_distance,
            "box_distance": box_distance,
            "doll_distance": doll_distance,
        })

if not placement_candidates:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({"success": False, "attempts": placement_attempts}, indent=2), encoding="utf-8")
    raise RuntimeError("No clear, visible music-room floor location met the approach and prop clearances")
selected = min(
    placement_candidates,
    key=lambda item: abs(item["approach_distance"] - 185.0) + abs(item["box_distance"] - 155.0),
)
floor_hit = selected["floor_hit"]
floor_actor = selected["floor_actor"]
worker_location = selected["location"]
to_approach = MUSIC_APPROACH - worker_location
worker_rotation = unreal.Rotator(0.0, math.degrees(math.atan2(to_approach.y, to_approach.x)), 0.0)

instance = unreal.load_asset(INSTANCE_PATH)
if not instance:
    raise RuntimeError(f"Could not load Eli's MetaHuman instance: {INSTANCE_PATH}")
worker, out_error = unreal.CarnivalCrowdEditorLibrary.place_initialized_meta_human_actor(
    instance,
    WORKER_LABEL,
    worker_location,
    worker_rotation,
)
if not worker:
    raise RuntimeError(f"Could not place Eli: {out_error}")
if out_error:
    raise RuntimeError(f"Eli was assembled without a usable idle animation: {out_error}")
worker.set_folder_path("Mission/Mansion/Music Room")

interaction_class = getattr(unreal, "CarnivalMissionInteractionActor", None)
if not interaction_class:
    interaction_class = unreal.load_class(None, "/Script/CarnivalGame.CarnivalMissionInteractionActor")
mission_enum = getattr(unreal, "CarnivalMissionInteraction", None)
if not interaction_class or not mission_enum or not hasattr(mission_enum, "WORKER"):
    raise RuntimeError("The Carnival mission worker interaction type is unavailable")
interaction = by_label.get(INTERACTION_LABEL)
interaction_created = interaction is None
if not interaction:
    interaction = actor_subsystem.spawn_actor_from_class(
        interaction_class,
        worker_location + unreal.Vector(0.0, 0.0, 100.0),
        worker_rotation,
    )
if not interaction:
    raise RuntimeError("Could not create Eli's talk interaction")
interaction.set_actor_label(INTERACTION_LABEL)
interaction.set_folder_path("Mission/Mansion/Music Room")
interaction.set_actor_location(worker_location + unreal.Vector(0.0, 0.0, 100.0), False, True)
interaction.set_actor_rotation(worker_rotation, True)
interaction.set_editor_property("interaction", mission_enum.WORKER)
interaction.set_editor_property("interaction_target_actor", worker)
interaction.set_editor_property("interaction_radius", 270.0)
interaction.set_editor_property("prompt_override", unreal.Text("Talk to Eli Mercer"))
interaction.set_editor_property(
    "accepted_feedback",
    unreal.Text("Eli: I heard the music box playing. The doll moved when the tune began. Please take it and get out."),
)
interaction.set_editor_property("world_label_text", unreal.Text("Talk to Eli Mercer"))
interaction.set_editor_property("world_label_size", 16.0)

skeletal_components = []
for component in worker.get_components_by_class(unreal.SkeletalMeshComponent):
    mesh = component.get_editor_property("skeletal_mesh_asset")
    skeletal_components.append({
        "name": component.get_name(),
        "mesh": mesh.get_path_name() if mesh else None,
        "animation_mode": str(component.get_editor_property("animation_mode")),
    })
if not any(item["name"] == "Body" and item["mesh"] for item in skeletal_components):
    raise RuntimeError("Eli's body mesh was not assembled")

if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAP):
    raise RuntimeError("Unreal failed to save the mansion worker")

result = {
    "success": True,
    "map": MAP,
    "backup": str(backup),
    "worker_actor": WORKER_LABEL,
    "worker_class": worker.get_class().get_path_name(),
    "worker_instance": INSTANCE_PATH,
    "worker_location": list(worker_location.to_tuple()),
    "worker_rotation": list(worker_rotation.to_tuple()),
    "worker_floor_actor": floor_actor,
    "candidate_count": len(placement_candidates),
    "worker_floor_normal": list(floor_hit[7].to_tuple()),
    "worker_distance_to_music_approach_cm": round((worker_location - MUSIC_APPROACH).length(), 2),
    "horizontal_distance_to_music_approach_cm": round(horizontal_distance(worker_location, MUSIC_APPROACH), 2),
    "placement_candidates": [
        {
            "location": list(item["location"].to_tuple()),
            "approach_cm": round(item["approach_distance"], 2),
            "box_cm": round(item["box_distance"], 2),
            "doll_cm": round(item["doll_distance"], 2),
        }
        for item in placement_candidates
    ],
    "worker_collision_enabled": worker.get_actor_enable_collision(),
    "skeletal_components": skeletal_components,
    "interaction_actor": INTERACTION_LABEL,
    "interaction_created": interaction_created,
    "interaction_type": str(mission_enum.WORKER),
    "interaction_location": list(interaction.get_actor_location().to_tuple()),
    "interaction_radius_cm": interaction.get_editor_property("interaction_radius"),
    "interaction_prompt": str(interaction.get_prompt_text()),
    "dialogue_feedback": str(interaction.get_editor_property("accepted_feedback")),
    "interaction_collision": str(interaction.get_editor_property("interaction_volume").get_collision_enabled()),
    "map_saved": True,
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log("MISSION_WORKER_PLACED " + json.dumps(result))
unreal.SystemLibrary.quit_editor()
