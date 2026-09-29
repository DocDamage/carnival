"""Place Eli's physical foyer note beside the work glove and verify the floor before saving."""

import json
import shutil
import time
from pathlib import Path

import unreal


ROOT = Path(r"F:\Carnival")
MAP = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
MAP_FILE = ROOT / "Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap"
BACKUP_DIR = ROOT / "Saved/MissionAuthoring/Backups"
REPORT = ROOT / "Saved/MissionAuthoring/FoyerNote_Placement.json"
CLUE_LABEL = "Mission_Foyer_Glove_Note"
NOTE_LABEL = "Mission_Foyer_Eli_Physical_Note"
NOTE_MESH_PATH = "/Game/Carnival/Props/Mission/SM_EliFoyerNote"

if not MAP_FILE.is_file():
    raise RuntimeError(f"Missing saved map file: {MAP_FILE}")
backup = BACKUP_DIR / f"LV_Carnival.before_foyer_note_{time.strftime('%Y%m%d_%H%M%S')}.umap"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
shutil.copy2(MAP_FILE, backup)

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise RuntimeError(f"Could not load {MAP}")
editor_actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
by_label = {actor.get_actor_label(): actor for actor in editor_actors.get_all_level_actors()}
clue = by_label.get(CLUE_LABEL)
if not clue:
    raise RuntimeError(f"Could not find accepted glove interaction {CLUE_LABEL}")
mesh = unreal.load_asset(NOTE_MESH_PATH)
if not mesh:
    raise RuntimeError(f"Could not load authored note mesh {NOTE_MESH_PATH}")

clue_location = clue.get_actor_location()
candidate_x = clue_location.x + 31.0
candidate_y = clue_location.y + 5.0
floor_hit = unreal.SystemLibrary.line_trace_single(
    world,
    unreal.Vector(candidate_x, candidate_y, clue_location.z + 250.0),
    unreal.Vector(candidate_x, candidate_y, clue_location.z - 550.0),
    unreal.TraceTypeQuery.ECC_VISIBILITY,
    False,
    [clue],
    unreal.DrawDebugTrace.NONE,
    True,
).to_tuple()
if not floor_hit or not floor_hit[0] or floor_hit[7].z < 0.65:
    raise RuntimeError(f"No walkable foyer floor beneath the note candidate: {floor_hit}")
floor_actor = floor_hit[9].get_actor_label() if floor_hit[9] else None
if floor_actor != "SM_InnerFloor91":
    raise RuntimeError(f"Note would land on {floor_actor}, expected SM_InnerFloor91")
note_location = unreal.Vector(candidate_x, candidate_y, floor_hit[5].z + 0.04)
note = by_label.get(NOTE_LABEL)
if not note:
    note = editor_actors.spawn_actor_from_class(unreal.StaticMeshActor, note_location, unreal.Rotator())
if not note:
    raise RuntimeError("Could not spawn the physical note visual")
note.set_actor_label(NOTE_LABEL)
note.set_folder_path("Mission/Mansion/Foyer Clue")
note.set_actor_location(note_location, False, True)
note.set_actor_rotation(unreal.Rotator(0.0, 14.0, 0.0), False)
component = note.get_component_by_class(unreal.StaticMeshComponent)
component.set_static_mesh(mesh)
component.set_collision_profile_name("NoCollision")
component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
component.set_editor_property("generate_overlap_events", False)

if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAP):
    raise RuntimeError("Unreal failed to save LV_Carnival after placing the note")

bounds = mesh.get_bounding_box()
result = {
    "success": True,
    "map": MAP,
    "backup": str(backup),
    "clue_actor": CLUE_LABEL,
    "note_actor": NOTE_LABEL,
    "note_mesh": mesh.get_path_name(),
    "note_location": list(note_location.to_tuple()),
    "floor_actor": floor_actor,
    "floor_normal": list(floor_hit[7].to_tuple()),
    "collision_profile": str(component.get_collision_profile_name()),
    "collision_enabled": str(component.get_collision_enabled()),
    "source_dimensions_cm": [bounds.max.x - bounds.min.x, bounds.max.y - bounds.min.y, bounds.max.z - bounds.min.z],
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log("MISSION_FOYER_NOTE_PLACED " + json.dumps(result))
unreal.SystemLibrary.quit_editor()
