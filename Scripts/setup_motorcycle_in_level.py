import unreal

eal = unreal.EditorAssetLibrary
level_path = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"

# Load level
world = unreal.EditorLoadingAndSavingUtils.load_map(level_path)
if world:
    # Check if BP_CarnivalMotorcycle is already in level
    moto_bp = unreal.load_asset("/Game/Carnival/Vehicles/Motorcycle/Blueprints/BP_CarnivalMotorcycle")
    moto_class = unreal.load_class(None, "/Game/Carnival/Vehicles/Motorcycle/Blueprints/BP_CarnivalMotorcycle.BP_CarnivalMotorcycle_C")

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = eas.get_all_level_actors()
    moto_exists = False
    player_start_loc = unreal.Vector(0, 0, 100)

    for a in all_actors:
        if "CarnivalMotorcycle" in a.get_name():
            moto_exists = True
            unreal.log_warning(f"Found existing motorcycle: {a.get_name()} at {a.get_actor_location()}")
        if "PlayerStart" in a.get_name():
            player_start_loc = a.get_actor_location()
            unreal.log_warning(f"Found PlayerStart at: {player_start_loc}")

    if not moto_exists and moto_class:
        # Spawn near PlayerStart (offset by 250 units to the right)
        spawn_loc = unreal.Vector(player_start_loc.x + 250, player_start_loc.y, player_start_loc.z + 50)
        spawn_rot = unreal.Rotator(0, 0, 0)
        new_bike = unreal.EditorActorSubsystem().spawn_actor_from_class(moto_class, spawn_loc, spawn_rot)
        if new_bike:
            new_bike.set_actor_label("BP_CarnivalMotorcycle_Start")
            unreal.log_warning(f"Spawned BP_CarnivalMotorcycle at {spawn_loc}!")

    unreal.EditorLoadingAndSavingUtils.save_current_level()
    unreal.log_warning("Saved LV_Carnival!")

