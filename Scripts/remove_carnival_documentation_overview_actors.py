"""Remove editor documentation placards from the shipped Carnival map."""

import unreal

MAP_PATH = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
ACTOR_SUFFIXES = {
    "BP_DocumentationActor_Website_0",
    "BP_DocumentationActor_Website_1",
}

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
if not world:
    raise RuntimeError(f"Could not load {MAP_PATH}")

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
matches = [
    actor
    for actor in actor_subsystem.get_all_level_actors()
    if actor.get_name() in ACTOR_SUFFIXES
]
found = {actor.get_name() for actor in matches}
if found != ACTOR_SUFFIXES:
    raise RuntimeError(f"Expected exactly {sorted(ACTOR_SUFFIXES)}, found {sorted(found)}")

for actor in matches:
    unreal.log(f"REMOVING_RUNTIME_DOCUMENTATION_ACTOR {actor.get_path_name()}")
    if not actor_subsystem.destroy_actor(actor):
        raise RuntimeError(f"Could not destroy {actor.get_path_name()}")

if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH):
    raise RuntimeError(f"Could not save {MAP_PATH}")

remaining = [
    actor.get_path_name()
    for actor in actor_subsystem.get_all_level_actors()
    if actor.get_name() in ACTOR_SUFFIXES
]
if remaining:
    raise RuntimeError(f"Documentation actors remain after save: {remaining}")

unreal.log("RUNTIME_DOCUMENTATION_OVERVIEW_ACTORS_REMOVED")
unreal.SystemLibrary.quit_editor()
