"""Author and exercise the key-door/music-box mission path in connected-world PIE."""

import json
import math
import shutil
import time
import traceback
from pathlib import Path

import unreal


ROOT = Path(r"F:\Carnival")
MAP = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
MAP_FILE = ROOT / "Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap"
OUT = ROOT / "Saved/MissionAuthoring"
REPORT_PATH = OUT / "MusicRoomInteractions_PIE_Authoring.json"
LIVE_PATH = OUT / "MusicRoomInteractions_PIE_Authoring_Live.json"
REPORTS = {
    "board": OUT / "NoticeBoard_PIE_Authoring.json",
    "entrance": OUT / "MansionEntrance_PIE_Authoring.json",
    "clue": OUT / "FoyerClue_PIE_Authoring.json",
    "study": OUT / "StudyLogKey_PIE_Authoring.json",
    "music_route": ROOT / "Saved/MansionConnection/RoomWalk_PIE_study_to_music_path.json",
    "door_route": ROOT / "Saved/MansionConnection/RoomWalk_PIE_door7_gate_acceptance.json",
}
LABEL = {
    "board": "Mission_NoticeBoard_Interaction",
    "entrance": "Mission_MansionEntrance_Interaction",
    "clue": "Mission_Foyer_Glove_Note",
    "study": "Mission_Study_Log_ServiceKey",
    "door": "Mission_MusicRoom_KeyedDoor",
    "box": "Mission_MusicBox_Interaction",
    "doll": "Mission_Mansion_Doll",
    "exit": "Mission_MansionExit_Interaction",
    "return": "Mission_CarnivalReturn_Trigger",
    "worker": "Mission_Eli_Worker_Interaction",
    "worker_character": "Mission_Eli_Mercer_Character",
    "key_prop": "Mission_ServiceKey_VisibleProp",
}
TABLE_LABEL = "SM_DiningTable2"
STUDY_TABLE_LABEL = "SM_WoodTable2"
BOX_MESH_PATH = "/Game/Carnival/Props/Mission/SM_BrassMusicBox"
GLOVE_MESH_PATH = "/Game/Carnival/Props/Mission/SM_WetWorkGlove"
SERVICE_KEY_MESH_PATH = "/Game/Carnival/Props/Mission/SM_BrassServiceKey"
DOLL_MESH_PATH = "/Game/Carnival/Characters/PossessedDoll/SK_Doll"
HEAD_SNAP_PATH = "/Game/Carnival/Characters/PossessedDoll/Animations/Original/Doll_Head_Snap"
LUNGE_PATH = "/Game/Carnival/Characters/PossessedDoll/Animations/Original/Doll_Jumpscare_Lunge"
IDLE_PATH = "/Game/Carnival/Characters/PossessedDoll/Animations/Original/Doll_Idle_Possessed_Loop"
SCARE_SOUND_PATH = "/Game/Carnival/Audio/IndustrialHospital/Smiling_Doll_in_the_Dark"
RADIUS = 245.0
DOLL_RADIUS = 25.0
DOLL_HALF_HEIGHT = 71.0

OUT.mkdir(parents=True, exist_ok=True)
if not all(path.exists() for path in REPORTS.values()):
    raise RuntimeError("Accepted board, foyer, study, and route reports are required")

def read_approach(key, field="player_approach"):
    return unreal.Vector(*json.loads(REPORTS[key].read_text(encoding="utf-8"))[field])

board_approach = read_approach("board")
entrance_approach = read_approach("entrance")
clue_approach = read_approach("clue")
study_approach = read_approach("study")
music_approach = read_approach("music_route", "goal_approach")
door_data = json.loads(REPORTS["door_route"].read_text(encoding="utf-8"))
door_side_a = unreal.Vector(*door_data["start_approach"])
door_side_b = unreal.Vector(*door_data["goal_approach"])

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise RuntimeError(f"Could not load {MAP}")
actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
by_label = {actor.get_actor_label(): actor for actor in actor_subsystem.get_all_level_actors()}
for required in (LABEL["board"], LABEL["entrance"], LABEL["clue"], LABEL["study"],
                LABEL["worker"], LABEL["worker_character"], "BP_Door7", "SM_DiningTable2"):
    if required not in by_label:
        raise RuntimeError(f"Missing accepted prerequisite: {required}")

report = {
    "map": MAP,
    "saved_map_modified": False,
    "success": False,
    "errors": [],
    "acceptance_limits": [
        "PIE checks use the native context-interaction API, not physical keyboard or controller input.",
        "Eli uses the saved MetaHuman crowd actor and gated talk interaction. Rendered face/clothing review and his walk-away animation remain open.",
        "NullRHI PIE does not accept rendered lighting, animation appearance, or audio mix.",
        "This run does not walk the complete room-to-room route.",
    ],
}

def hit_tuple(value):
    return value.to_tuple() if value else None

def floor_trace(x, y, z):
    hit = hit_tuple(unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(x, y, z + 250.0), unreal.Vector(x, y, z - 550.0),
        unreal.TraceTypeQuery.ECC_VISIBILITY, False, [], unreal.DrawDebugTrace.NONE, True,
    ))
    if not hit or not hit[0] or hit[7].z < 0.65:
        return None
    return {"point": hit[5], "actor": hit[9].get_actor_label() if hit[9] else None}

def capsule_clear(position, radius=42.0, half_height=96.0):
    hit = hit_tuple(unreal.SystemLibrary.capsule_trace_single(
        world, position, position + unreal.Vector(0.0, 0.0, 0.1), radius, half_height,
        unreal.TraceTypeQuery.ECC_VISIBILITY, False, [], unreal.DrawDebugTrace.NONE, True,
    ))
    return not bool(hit and hit[0]), hit

interaction_class = getattr(unreal, "CarnivalMissionInteractionActor", None)
if not interaction_class:
    interaction_class = unreal.load_class(None, "/Script/CarnivalGame.CarnivalMissionInteractionActor")
mission_enum = getattr(unreal, "CarnivalMissionInteraction", None)
if not interaction_class or not mission_enum:
    raise RuntimeError("Mission interaction class or enum is unavailable")
for enum_name in ("MUSIC_ROOM_DOOR", "WORKER", "MUSIC_BOX", "MANSION_EXIT", "CARNIVAL_RETURN"):
    if not hasattr(mission_enum, enum_name):
        raise RuntimeError(f"Mission enum is missing {enum_name}")

def get_or_spawn(label, actor_class, location, rotation=None):
    actor = by_label.get(label)
    if actor:
        return actor, False
    actor = actor_subsystem.spawn_actor_from_class(
        actor_class, location, rotation or unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0)
    )
    if not actor:
        raise RuntimeError(f"Could not spawn {label}")
    actor.set_actor_label(label)
    return actor, True


glove_mesh = unreal.load_asset(GLOVE_MESH_PATH)
service_key_mesh = unreal.load_asset(SERVICE_KEY_MESH_PATH)
if not glove_mesh or not service_key_mesh:
    raise RuntimeError("The wet glove and brass service-key meshes must be imported before authoring")

clue_actor = by_label[LABEL["clue"]]
clue_floor = floor_trace(
    clue_actor.get_actor_location().x, clue_actor.get_actor_location().y, clue_actor.get_actor_location().z
)
if not clue_floor:
    raise RuntimeError("Could not locate walkable floor beneath the foyer glove interaction")
glove_location = unreal.Vector(
    clue_actor.get_actor_location().x,
    clue_actor.get_actor_location().y,
    clue_floor["point"].z + 0.2,
)
clue_actor.set_editor_property("interaction_mesh", glove_mesh)
clue_actor.set_editor_property("interaction_mesh_offset", unreal.Vector(
    0.0, 0.0, glove_location.z - clue_actor.get_actor_location().z
))
clue_actor.set_editor_property("interaction_mesh_scale", unreal.Vector(1.0, 1.0, 1.0))

study_actor = by_label[LABEL["study"]]
study_table = by_label[STUDY_TABLE_LABEL]
table_origin, table_extent = study_table.get_actor_bounds(False)
table_top = table_origin.z + table_extent.z
book_component = study_actor.get_component_by_class(unreal.StaticMeshComponent)
book_mesh = book_component.get_editor_property("static_mesh") if book_component else None
book_bounds = book_mesh.get_bounding_box() if book_mesh else None
book_half = (
    ((book_bounds.max.x - book_bounds.min.x) * 0.5, (book_bounds.max.y - book_bounds.min.y) * 0.5)
    if book_bounds else (7.0, 9.0)
)
key_bounds = service_key_mesh.get_bounding_box()
key_half = ((key_bounds.max.x - key_bounds.min.x) * 0.5, (key_bounds.max.y - key_bounds.min.y) * 0.5)
table_half = (table_extent.x, table_extent.y)
axis_candidates = []
for axis in (0, 1):
    fit_offset = table_half[axis] - key_half[axis] - 2.0
    clear_offset = book_half[axis] + key_half[axis] + 2.0
    axis_candidates.append((fit_offset - clear_offset, axis, fit_offset, clear_offset))
_, key_axis, key_fit_offset, key_clear_offset = max(axis_candidates)
key_offset = min(key_fit_offset, key_clear_offset + 2.0)
key_offset_clear = key_fit_offset >= key_clear_offset
table_center = study_table.get_actor_location()
key_location = unreal.Vector(
    table_center.x + (key_offset if key_axis == 0 else 0.0),
    table_center.y + (key_offset if key_axis == 1 else 0.0),
    table_top + 0.3,
)
key_actor = by_label.get("Mission_ServiceKey_VisibleProp")
key_actor_created = key_actor is None
if not key_actor:
    key_actor = actor_subsystem.spawn_actor_from_class(
        unreal.StaticMeshActor, key_location, unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0)
    )
if not key_actor:
    raise RuntimeError("Could not create the visible service-key prop actor")
key_actor.set_actor_label("Mission_ServiceKey_VisibleProp")
key_actor.set_folder_path("Mission/Mansion/Study Log and Key")
key_actor.set_actor_location(key_location, False, True)
key_visual = key_actor.get_component_by_class(unreal.StaticMeshComponent)
if not key_visual:
    raise RuntimeError("The service-key prop actor has no static mesh component")
key_visual.set_static_mesh(service_key_mesh)
key_visual.set_collision_profile_name("NoCollision")
key_visual.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
key_visual.set_editor_property("generate_overlap_events", False)

def configure_interaction(actor, label, folder, location, kind, radius, prompt, feedback="", rotation=None):
    actor.set_actor_label(label)
    actor.set_folder_path(folder)
    actor.set_actor_location(location, False, True)
    if rotation:
        actor.set_actor_rotation(rotation, True)
    actor.set_editor_property("interaction", kind)
    actor.set_editor_property("interaction_radius", float(radius))
    actor.set_editor_property("prompt_override", unreal.Text(prompt))
    actor.set_editor_property("accepted_feedback", unreal.Text(feedback))
    actor.set_editor_property("world_label_text", unreal.Text(prompt))
    actor.set_editor_property("world_label_size", 16.0)

door = by_label["BP_Door7"]
door_center = door.get_actor_location()
door_location = door_center + unreal.Vector(0.0, 0.0, 98.0)
door_yaw = door.get_actor_rotation().yaw
door_actor, door_created = get_or_spawn(
    LABEL["door"], interaction_class, door_location,
    unreal.Rotator(pitch=0.0, yaw=door_yaw, roll=0.0),
)
to_door_x = door_center.x - door_side_a.x
to_door_y = door_center.y - door_side_a.y
to_door_length = math.hypot(to_door_x, to_door_y)
door_approach_candidates = []
for offset in (45.0, 70.0, 95.0, 120.0, 145.0):
    candidate = unreal.Vector(
        door_side_a.x + to_door_x / to_door_length * offset,
        door_side_a.y + to_door_y / to_door_length * offset,
        door_side_a.z,
    )
    sight = hit_tuple(unreal.SystemLibrary.line_trace_single(
        world,
        door_side_a + unreal.Vector(0.0, 0.0, 50.0),
        candidate + unreal.Vector(0.0, 0.0, 40.0),
        unreal.TraceTypeQuery.ECC_VISIBILITY,
        False,
        [door, door_actor],
        unreal.DrawDebugTrace.NONE,
        True,
    ))
    door_approach_candidates.append({
        "offset_toward_door_cm": offset,
        "location": list(candidate.to_tuple()),
        "sight_clear": not bool(sight and sight[0]),
        "blocker": sight[9].get_actor_label() if sight and sight[0] and sight[9] else None,
    })
    if not sight or not sight[0]:
        door_location = candidate
        break
door_actor.set_actor_location(door_location, False, True)
configure_interaction(
    door_actor, LABEL["door"], "Mission/Mansion/Music Room Door", door_location,
    mission_enum.MUSIC_ROOM_DOOR, 255.0, "",
    "The service key turns. The music room opens.",
    unreal.Rotator(pitch=0.0, yaw=door_yaw, roll=0.0),
)
door_actor.set_editor_property("world_label_text", unreal.Text("Music-room door"))
door_actor.set_editor_property("controlled_door_actor_name", unreal.Name(str(door.get_name())))
door_actor.set_editor_property("controlled_door_actor_location", door.get_actor_location())
door_actor.set_editor_property("door_open_angle_degrees", 90.0)
door_actor.set_editor_property("door_animation_seconds", 0.55)

table = by_label["SM_DiningTable2"]
table_origin, table_extent = table.get_actor_bounds(False)
table_top = table_origin.z + table_extent.z
box_location = unreal.Vector(table_origin.x, table_origin.y, table_top + 1.0)
music_mesh = unreal.load_asset(BOX_MESH_PATH)
if not music_mesh:
    raise RuntimeError(f"Could not load music box mesh {BOX_MESH_PATH}")
box_actor, box_created = get_or_spawn(LABEL["box"], interaction_class, box_location)
configure_interaction(
    box_actor, LABEL["box"], "Mission/Mansion/Music Box", box_location,
    mission_enum.MUSIC_BOX, RADIUS, "Take the brass music box",
    "You take Eli's brass music box.",
)
box_actor.set_editor_property("interaction_mesh", music_mesh)
box_actor.set_editor_property("interaction_mesh_offset", unreal.Vector(0.0, 0.0, 7.0))
box_actor.set_editor_property("interaction_mesh_scale", unreal.Vector(1.0, 1.0, 1.0))
box_actor.set_editor_property("world_label_text", unreal.Text("Brass music box"))
box_actor.set_editor_property("world_label_offset", unreal.Vector(0.0, 0.0, 43.0))

entrance_actor = by_label[LABEL["entrance"]]
exit_actor, exit_created = get_or_spawn(LABEL["exit"], interaction_class, entrance_actor.get_actor_location())
configure_interaction(
    exit_actor, LABEL["exit"], "Mission/Mansion/Exit", entrance_actor.get_actor_location(),
    mission_enum.MANSION_EXIT, 250.0, "Leave the mansion",
    "The mansion is behind you. Return to the Carnival.",
)
board = by_label[LABEL["board"]]
return_actor, return_created = get_or_spawn(LABEL["return"], interaction_class, board.get_actor_location())
configure_interaction(
    return_actor, LABEL["return"], "Mission/Carnival/Return", board.get_actor_location(),
    mission_enum.CARNIVAL_RETURN, 230.0, "Return to Carnival free play",
    "Worker found. Music box recovered. Carnival free play is open.",
)
return_actor.set_editor_property("trigger_on_overlap", True)

doll_mesh = unreal.load_asset(DOLL_MESH_PATH)
head_snap = unreal.load_asset(HEAD_SNAP_PATH)
lunge = unreal.load_asset(LUNGE_PATH)
idle = unreal.load_asset(IDLE_PATH)
scare_sound = unreal.load_asset(SCARE_SOUND_PATH)
if not all((doll_mesh, head_snap, lunge, idle, scare_sound)):
    raise RuntimeError("A doll mesh, animation, or scare cue could not be loaded")
doll_class = getattr(unreal, "CarnivalHauntedDoll", None)
if not doll_class:
    doll_class = unreal.load_class(None, "/Script/CarnivalGame.CarnivalHauntedDoll")
if not doll_class:
    raise RuntimeError("CarnivalHauntedDoll class is unavailable")

floor_anchor = floor_trace(music_approach.x, music_approach.y, music_approach.z)
if not floor_anchor:
    raise RuntimeError("The music-room approach does not have walkable floor support")
doll_candidates = []
selected_doll_position = None
for offset_x, offset_y in (
    (170.0, 285.0), (-170.0, 285.0), (230.0, 245.0), (-230.0, 245.0),
    (0.0, -310.0), (300.0, 0.0), (-300.0, 0.0), (250.0, -240.0),
):
    floor = floor_trace(table_origin.x + offset_x, table_origin.y + offset_y, table_top)
    if not floor:
        doll_candidates.append({"offset": [offset_x, offset_y], "clear": False, "reason": "no walkable floor"})
        continue
    root = floor["point"] + unreal.Vector(0.0, 0.0, DOLL_HALF_HEIGHT + 1.0)
    clear, blocker = capsule_clear(root, DOLL_RADIUS, DOLL_HALF_HEIGHT)
    distance = (root - music_approach).length()
    row = {
        "offset_from_table_cm": [offset_x, offset_y],
        "floor_actor": floor["actor"],
        "position": list(root.to_tuple()),
        "capsule_clear": clear,
        "distance_to_music_approach_cm": round(distance, 2),
        "blocker": blocker[9].get_actor_label() if blocker and blocker[9] else None,
    }
    doll_candidates.append(row)
    if clear and floor["actor"] == floor_anchor["actor"] and 130.0 <= distance <= 320.0:
        selected_doll_position = root
        break

doll = by_label.get(LABEL["doll"])
doll_created = doll is None
if doll is None:
    if not selected_doll_position:
        raise RuntimeError("No clear doll capsule position was found beside the music-room table")
    doll = actor_subsystem.spawn_actor_from_class(
        doll_class, selected_doll_position, unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0)
    )
    if not doll:
        raise RuntimeError("Could not spawn the mission doll")
elif not selected_doll_position:
    selected_doll_position = doll.get_actor_location()

doll.set_actor_label(LABEL["doll"])
doll.set_folder_path("Mission/Mansion/Doll Encounter")
doll.set_actor_location(selected_doll_position, False, True)
to_player = music_approach - selected_doll_position
doll.set_actor_rotation(unreal.Rotator(
    pitch=0.0, yaw=math.degrees(math.atan2(to_player.y, to_player.x)), roll=0.0
), True)
doll_mesh_component = doll.get_component_by_class(unreal.SkeletalMeshComponent)
if not doll_mesh_component:
    raise RuntimeError("The mission doll has no skeletal mesh component")
doll_mesh_component.set_skeletal_mesh_asset(doll_mesh)
doll_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
for property_name, asset in (
    ("mission_head_snap_animation", head_snap),
    ("scare_animation", lunge),
    ("idle_animation", idle),
    ("scare_sound", scare_sound),
):
    doll.set_editor_property(property_name, asset)
doll.set_editor_property("mission_controlled_instance", True)
doll.set_editor_property("encounter_enabled", False)
doll.set_editor_property("mission_blackout_seconds", 0.35)
doll.set_editor_property("mission_aftermath_seconds", 0.8)
doll.set_editor_property("scare_volume", 0.65)

worker_interaction = by_label[LABEL["worker"]]
worker_character = by_label[LABEL["worker_character"]]
if worker_interaction.get_editor_property("interaction") != mission_enum.WORKER:
    raise RuntimeError("Eli's saved talk target is not a Worker interaction")
report["worker_character_class"] = worker_character.get_class().get_path_name()
report["worker_talk_prompt"] = str(worker_interaction.get_prompt_text())
report["worker_dialogue_feedback"] = str(worker_interaction.get_editor_property("accepted_feedback"))
report["worker_target_assigned"] = (
    worker_interaction.get_editor_property("interaction_target_actor") is worker_character
)
if not report["worker_target_assigned"]:
    raise RuntimeError("Eli's talk interaction does not target the saved MetaHuman actor")

door_parts = {
    component.get_name(): component
    for component in door.get_components_by_class(unreal.StaticMeshComponent)
}
left_leaf = door_parts.get("SM_Door02_D")
right_leaf = door_parts.get("SM_Door02_E")
if not left_leaf or not right_leaf:
    raise RuntimeError("BP_Door7 is missing its compatible left/right leaves")
door_rotations_before = [
    left_leaf.get_editor_property("relative_rotation"),
    right_leaf.get_editor_property("relative_rotation"),
]

report.update({
    "routes": {
        "music_table": str(REPORTS["music_route"].relative_to(ROOT)),
        "tested_door_crossing": str(REPORTS["door_route"].relative_to(ROOT)),
        "door_side_a": list(door_side_a.to_tuple()),
        "door_side_b": list(door_side_b.to_tuple()),
    },
    "placements": {
        "controlled_door_actor_name": str(door.get_name()),
        "controlled_door_actor_location": list(door.get_actor_location().to_tuple()),
        "door_interaction": LABEL["door"],
        "door_interaction_location": list(door_location.to_tuple()),
        "door_approach_line_tests": door_approach_candidates,
        "door_interaction_radius_cm": 255.0,
        "door_open_angle_degrees": 90.0,
        "door_animation_seconds": 0.55,
        "music_box_mesh": music_mesh.get_path_name(),
        "music_box_table": TABLE_LABEL,
        "music_box_table_top_z": table_top,
        "music_box_location": list(box_location.to_tuple()),
        "music_box_player_approach": list(music_approach.to_tuple()),
        "music_box_actor_created": box_created,
        "doll_mesh": doll_mesh.get_path_name(),
        "doll_head_snap": head_snap.get_path_name(),
        "doll_lunge": lunge.get_path_name(),
        "doll_idle": idle.get_path_name(),
        "doll_scare_sound": scare_sound.get_path_name(),
        "doll_location": list(selected_doll_position.to_tuple()),
        "doll_distance_to_player_approach_cm": round((selected_doll_position - music_approach).length(), 2),
        "doll_floor_candidate_checks": doll_candidates,
        "doll_actor_created": doll_created,
        "exit_interaction": LABEL["exit"],
        "carnival_return_trigger": LABEL["return"],
        "carnival_return_uses_overlap": True,
        "foyer_glove_mesh": glove_mesh.get_path_name(),
        "foyer_glove_location": list(glove_location.to_tuple()),
        "study_service_key_mesh": service_key_mesh.get_path_name(),
        "study_service_key_location": list(key_location.to_tuple()),
        "study_service_key_actor_created": key_actor_created,
        "study_service_key_axis_clear_of_book": key_offset_clear,
        "study_service_key_offset_from_table_center_cm": key_offset,
        "foyer_glove_clearance_to_floor_cm": round(glove_location.z - clue_floor["point"].z, 2),
        "service_key_clearance_to_table_cm": round(key_location.z - table_top, 2),
        "visible_worker_present": any(
            component.get_name() == "Body" and component.get_skeletal_mesh_asset()
            for component in worker_character.get_components_by_class(unreal.SkeletalMeshComponent)
        ),
    },
})

state = {
    "phase": "wait_pie",
    "busy": False,
    "started": time.monotonic(),
    "deadline": time.monotonic() + 240.0,
    "door_original_rotations": door_rotations_before,
}

def write_reports():
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    LIVE_PATH.write_text(json.dumps({
        "phase": state["phase"],
        "wall_time_seconds": round(time.monotonic() - state["started"], 2),
        "report": report,
    }, indent=2), encoding="utf-8")

def finish(error=None):
    if error:
        report["errors"].append(error)
        report["success"] = False
    report["pie_elapsed_seconds"] = round(time.monotonic() - state["started"], 2)
    state["phase"] = "ending"
    state["deadline"] = time.monotonic() + 20.0
    write_reports()
    level_editor.editor_request_end_play()

def face_player(player, target):
    direction = target.get_actor_location() - player.get_actor_location()
    player.set_actor_rotation(unreal.Rotator(
        pitch=0.0, yaw=math.degrees(math.atan2(direction.y, direction.x)), roll=0.0
    ), True)

def place_player(player, position, target=None):
    player.get_movement_component().stop_movement_immediately()
    player.set_actor_location(position, False, True)
    if target:
        face_player(player, target)

def find_actor(game, label):
    found = unreal.GameplayStatics.get_all_actors_of_class(game, interaction_class)
    return next((actor for actor in found if actor.get_actor_label() == label), None)

def focus_interact(player, actor, approach, label):
    place_player(player, approach, actor)
    focus = player.find_nearby_mission_interaction()
    report[label + "_focus"] = focus.get_actor_label() if focus else None
    report[label + "_can_interact_before"] = actor.can_interact(player)
    if focus != actor or not actor.can_interact(player):
        return False
    player.try_context_interact()
    report[label + "_context_dispatched"] = True
    return True

def angle_delta(a, b):
    return abs((a - b + 180.0) % 360.0 - 180.0)

def tick(_delta):
    if state["busy"]:
        return
    state["busy"] = True
    try:
        if state["phase"] == "ending":
            if not unreal.EditorLevelLibrary.get_game_world():
                report["saved_worker_retained"] = any(
                    actor.get_actor_label() == LABEL["worker_character"]
                    for actor in actor_subsystem.get_all_level_actors()
                ) and any(
                    actor.get_actor_label() == LABEL["worker"]
                    for actor in actor_subsystem.get_all_level_actors()
                )
                if report["success"]:
                    backup_dir = OUT / "Backups"
                    backup_dir.mkdir(parents=True, exist_ok=True)
                    backup = backup_dir / f"LV_Carnival.before_music_room_interactions_{time.strftime('%Y%m%d_%H%M%S')}.umap"
                    shutil.copy2(MAP_FILE, backup)
                    if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAP):
                        report["success"] = False
                        report["errors"].append("Map save call returned false")
                    else:
                        report["saved_map_modified"] = True
                        report["backup"] = str(backup)
                write_reports()
                unreal.SystemLibrary.quit_editor()
            elif time.monotonic() > state["deadline"]:
                report["success"] = False
                report["errors"].append("PIE did not end before authoring timeout")
                write_reports()
                unreal.SystemLibrary.quit_editor()
            return

        if time.monotonic() > state["deadline"]:
            finish("Timed out waiting for mission interactions")
            return
        game = unreal.EditorLevelLibrary.get_game_world()
        if not game:
            return
        player = unreal.GameplayStatics.get_player_pawn(game, 0)
        if not player:
            return
        board_actor = find_actor(game, LABEL["board"])
        entrance = find_actor(game, LABEL["entrance"])
        clue = find_actor(game, LABEL["clue"])
        study = find_actor(game, LABEL["study"])
        door_interaction = find_actor(game, LABEL["door"])
        box_interaction = find_actor(game, LABEL["box"])
        worker = find_actor(game, LABEL["worker"])
        exit_interaction = find_actor(game, LABEL["exit"])
        return_interaction = find_actor(game, LABEL["return"])
        key_prop = next((actor for actor in unreal.GameplayStatics.get_all_actors_of_class(
            game, unreal.StaticMeshActor
        ) if actor.get_actor_label() == LABEL["key_prop"]), None)
        doll_instance = next((actor for actor in unreal.GameplayStatics.get_all_actors_of_class(game, doll_class)
                              if actor.get_actor_label() == LABEL["doll"]), None)
        if not all((board_actor, entrance, clue, study, door_interaction, box_interaction,
                    worker, exit_interaction, return_interaction, key_prop, doll_instance)):
            finish("PIE is missing one or more saved mission actors")
            return
        key_component = key_prop.get_component_by_class(unreal.StaticMeshComponent)
        pie_key_mesh = key_component.get_editor_property("static_mesh") if key_component else None
        report["pie_foyer_glove_mesh"] = (
            clue.get_editor_property("interaction_mesh").get_path_name()
            if clue.get_editor_property("interaction_mesh") else None
        )
        report["pie_service_key_mesh"] = pie_mesh_path = (
            pie_key_mesh.get_path_name() if pie_key_mesh else None
        )
        report["pie_service_key_collision"] = (
            str(key_component.get_collision_enabled()) if key_component else None
        )
        report["pie_service_key_collision_profile"] = (
            str(key_component.get_collision_profile_name()) if key_component else None
        )
        report["service_key_visual_checks_pass"] = bool(
            report["pie_foyer_glove_mesh"] == GLOVE_MESH_PATH + ".SM_WetWorkGlove"
            and pie_mesh_path == SERVICE_KEY_MESH_PATH + ".SM_BrassServiceKey"
            and key_component
            and key_component.get_collision_enabled() == unreal.CollisionEnabled.NO_COLLISION
            and "NOCOLLISION" in str(key_component.get_collision_profile_name()).replace("_", "").upper()
            and report["placements"]["study_service_key_axis_clear_of_book"]
        )
        if "pie_door_leaves" not in state:
            pie_actors = unreal.GameplayStatics.get_all_actors_of_class(game, unreal.Actor)
            pie_door = next((actor for actor in pie_actors if actor.get_actor_label() == "BP_Door7"), None)
            if not pie_door:
                finish("PIE could not find the music-room BP_Door7 instance")
                return
            pie_parts = {
                component.get_name(): component
                for component in pie_door.get_components_by_class(unreal.StaticMeshComponent)
            }
            pie_left = pie_parts.get("SM_Door02_D")
            pie_right = pie_parts.get("SM_Door02_E")
            if not pie_left or not pie_right:
                finish("PIE music-room door is missing one or both leaves")
                return
            state["pie_door"] = pie_door
            state["pie_door_leaves"] = (pie_left, pie_right)
            state["door_original_rotations"] = [
                pie_left.get_editor_property("relative_rotation"),
                pie_right.get_editor_property("relative_rotation"),
            ]
            report["pie_controlled_door_actor"] = pie_door.get_path_name()
            controlled_ref = door_interaction.get_editor_property("controlled_door_actor")
            report["pie_controlled_door_reference"] = controlled_ref.get_path_name() if controlled_ref else None
            report["pie_controlled_door_reference_world"] = (
                controlled_ref.get_world().get_name() if controlled_ref else None
            )
            report["pie_controlled_door_component_names"] = [
                component.get_name()
                for component in (controlled_ref.get_components_by_class(unreal.StaticMeshComponent) if controlled_ref else [])
            ]

        phase = state["phase"]
        if phase == "wait_pie":
            if not focus_interact(player, board_actor, board_approach, "board_start"):
                finish("Notice board did not win native player focus")
                return
            place_player(player, entrance_approach, entrance)
            report["entrance_available_after_board"] = entrance.can_interact(player)
            if not report["entrance_available_after_board"]:
                finish("Notice board did not enable the mansion entrance")
                return
            state["phase"] = "entrance"
            write_reports()

        elif phase == "entrance":
            if not focus_interact(player, entrance, entrance_approach, "entrance"):
                finish("Mansion entrance did not win native player focus")
                return
            place_player(player, clue_approach, clue)
            report["clue_available_after_entrance"] = clue.can_interact(player)
            if not report["clue_available_after_entrance"]:
                finish("Mansion entrance did not enable the foyer clue")
                return
            state["phase"] = "clue"
            write_reports()

        elif phase == "clue":
            if not focus_interact(player, clue, clue_approach, "clue"):
                finish("Foyer clue did not win native player focus")
                return
            place_player(player, study_approach, study)
            report["study_available_after_clue"] = study.can_interact(player)
            if not report["study_available_after_clue"]:
                finish("Foyer clue did not enable the study log/key")
                return
            state["phase"] = "locked_door"
            write_reports()

        elif phase == "locked_door":
            place_player(player, door_side_a, door_interaction)
            focus = player.find_nearby_mission_interaction()
            report["locked_door_focus"] = focus.get_actor_label() if focus else None
            report["locked_door_prompt"] = str(door_interaction.get_prompt_text())
            report["locked_door_can_interact"] = door_interaction.can_interact(player)
            if focus != door_interaction or not door_interaction.can_interact(player):
                finish("Music-room door did not win focus from the tested study-side approach")
                return
            report["locked_door_key_absent_rejected"] = not door_interaction.try_interact(player)
            report["locked_door_leaf_yaws_unchanged"] = all(
                angle_delta(component.get_editor_property("relative_rotation").yaw, original.yaw) < 1.0
                for component, original in zip(state["pie_door_leaves"], state["door_original_rotations"])
            )
            if not report["locked_door_key_absent_rejected"] or not report["locked_door_leaf_yaws_unchanged"]:
                finish("Music-room door opened without the service key")
                return
            state["phase"] = "study_key"
            write_reports()

        elif phase == "study_key":
            if not focus_interact(player, study, study_approach, "study_key"):
                finish("Study log/key did not win native player focus")
                return
            report["door_prompt_after_key"] = str(door_interaction.get_prompt_text())
            place_player(player, music_approach, worker)
            report["worker_available_after_key"] = worker.can_interact(player)
            if not report["worker_available_after_key"]:
                finish("Study key did not enable FindWorker")
                return
            state["phase"] = "open_keyed_door"
            write_reports()

        elif phase == "open_keyed_door":
            state["door_closed_yaws_for_open"] = [
                component.get_editor_property("relative_rotation").yaw
                for component in state["pie_door_leaves"]
            ]
            report["door_leaf_yaws_before_key"] = list(state["door_closed_yaws_for_open"])
            if not focus_interact(player, door_interaction, door_side_a, "keyed_door"):
                finish("Keyed door did not win focus after taking the key")
                return
            state["phase"] = "wait_door"
            state["door_deadline"] = time.monotonic() + 1.2
            write_reports()

        elif phase == "wait_door":
            if time.monotonic() < state["door_deadline"]:
                return
            rotations = [
                component.get_editor_property("relative_rotation")
                for component in state["pie_door_leaves"]
            ]
            report["door_leaf_yaws_after_key"] = [rotation.yaw for rotation in rotations]
            report["door_leaf_yaw_deltas_after_key"] = [
                angle_delta(rotation.yaw, original_yaw)
                for rotation, original_yaw in zip(rotations, state["door_closed_yaws_for_open"])
            ]
            report["both_door_leaves_opened"] = all(
                angle_delta(rotation.yaw, original_yaw) >= 85.0
                for rotation, original_yaw in zip(rotations, state["door_closed_yaws_for_open"])
            )
            crossing = hit_tuple(unreal.SystemLibrary.capsule_trace_single(
                game, door_side_a, door_side_b, 42.0, 96.0,
                unreal.TraceTypeQuery.ECC_VISIBILITY, False, [player], unreal.DrawDebugTrace.NONE, True,
            ))
            report["open_gate_crossing_blocked"] = bool(crossing and crossing[0])
            report["open_gate_crossing_blocker"] = crossing[9].get_actor_label() if crossing and crossing[0] and crossing[9] else None
            if not report["both_door_leaves_opened"] or report["open_gate_crossing_blocked"]:
                finish("Keyed door did not open a capsule-clear crossing")
                return
            state["phase"] = "find_worker"
            write_reports()

        elif phase == "find_worker":
            if not focus_interact(player, worker, music_approach, "worker"):
                finish("Eli's talk interaction did not win music-room focus")
                return
            report["worker_interaction_accepted"] = True
            report["worker_dialogue_present"] = bool(
                worker.get_editor_property("accepted_feedback")
                and "The doll moved when the tune began" in str(worker.get_editor_property("accepted_feedback"))
            )
            report["music_box_available_after_worker"] = box_interaction.can_interact(player)
            if not report["music_box_available_after_worker"]:
                finish("Finding Eli did not enable the music box")
                return
            state["phase"] = "music_box"
            write_reports()

        elif phase == "music_box":
            if not focus_interact(player, box_interaction, music_approach, "music_box"):
                finish("Music box did not win focus beside the table")
                return
            report["music_box_disabled_after_pickup"] = not box_interaction.can_interact(player)
            report["doll_scare_started"] = doll_instance.get_editor_property("scare_count") == 1
            state["phase"] = "wait_scare"
            state["scare_deadline"] = time.monotonic() + 12.0
            write_reports()

        elif phase == "wait_scare":
            report["doll_scare_count"] = doll_instance.get_editor_property("scare_count")
            report["doll_autonomous_encounter_disabled"] = not doll_instance.get_editor_property("encounter_enabled")
            player_capsule = player.get_component_by_class(unreal.CapsuleComponent)
            report["player_capsule_collision_after_box"] = (
                str(player_capsule.get_collision_enabled()) if player_capsule else None
            )
            report["player_movement_mode_after_box"] = str(
                player.get_movement_component().get_editor_property("movement_mode")
            )
            if time.monotonic() >= state["scare_deadline"] - 7.0:
                place_player(player, entrance_approach, exit_interaction)
            if exit_interaction.can_interact(player):
                report["scripted_scare_completed_to_exit"] = True
                state["phase"] = "mansion_exit"
                write_reports()
                return
            if time.monotonic() > state["scare_deadline"]:
                finish("Mission doll did not finish the scripted scare and enable the exit")

        elif phase == "mansion_exit":
            if not focus_interact(player, exit_interaction, entrance_approach, "mansion_exit"):
                finish("Mansion exit did not win focus after the scare")
                return
            place_player(player, board_approach, return_interaction)
            state["phase"] = "wait_return"
            state["return_deadline"] = time.monotonic() + 3.0
            write_reports()

        elif phase == "wait_return":
            if board_actor.can_interact(player):
                report["carnival_return_overlap_completed_mission"] = True
                report["notice_board_available_after_completion"] = True
                report["success"] = all((
                    report.get("locked_door_key_absent_rejected"),
                    report.get("locked_door_leaf_yaws_unchanged"),
                    report.get("both_door_leaves_opened"),
                    not report.get("open_gate_crossing_blocked"),
                    report.get("worker_interaction_accepted"),
                    report.get("worker_dialogue_present"),
                    report.get("worker_target_assigned"),
                    report.get("music_box_available_after_worker"),
                    report.get("music_box_disabled_after_pickup"),
                    report.get("doll_scare_started"),
                    report.get("service_key_visual_checks_pass"),
                    report.get("scripted_scare_completed_to_exit"),
                    report.get("carnival_return_overlap_completed_mission"),
                    report.get("notice_board_available_after_completion"),
                ))
                if report["success"]:
                    finish()
                else:
                    finish("Mission did not complete the full worker, key, box, scare, exit, and return state flow")
                return
            if time.monotonic() > state["return_deadline"]:
                finish("Carnival return overlap did not complete the mission")

    except Exception:
        finish(traceback.format_exc())
    finally:
        state["busy"] = False

write_reports()
level_editor.editor_request_begin_play()
unreal.register_slate_post_tick_callback(tick)
