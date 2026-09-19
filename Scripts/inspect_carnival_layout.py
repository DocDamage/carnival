import unreal

level_path = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
world = unreal.EditorLoadingAndSavingUtils.load_map(level_path)

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
all_actors = eas.get_all_level_actors()

player_start = None
nearby_actors = []

for a in all_actors:
    if "PlayerStart" in a.get_name():
        player_start = a
        break

if player_start:
    p_loc = player_start.get_actor_location()
    unreal.log_warning(f"PlayerStart location: {p_loc}")
    
    # Find actors within 5000 units
    for a in all_actors:
        dist = a.get_actor_location().distance(p_loc)
        if dist < 4000 and "StaticMesh" in a.get_class().get_name():
            nearby_actors.append((a.get_name(), a.get_actor_location(), dist))

    nearby_actors.sort(key=lambda x: x[2])
    for name, loc, dist in nearby_actors[:20]:
        unreal.log_warning(f"Nearby: {name} at {loc} (dist: {dist:.0f})")

