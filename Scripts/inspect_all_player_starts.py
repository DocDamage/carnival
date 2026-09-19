import unreal

eal = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

maps = [
    ("Carnival", "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"),
    ("Mansion", "/Game/Mansion/Levels/LV_Haunted_Mansion"),
    ("Town", "/Game/Town/Level/L_Main_Level"),
    ("Lighthouse", "/Game/LightHouse_Meshingun/Map/LV_LightHouse"),
    ("Castle", "/Game/Medieval_Castle/Level/Medieval_Castle_Level"),
    ("Arena", "/Game/Gladiator_Arena/Maps/Gladiators_Land"),
    ("Mars", "/Game/Mars_Futuristic_Cars/Maps/Playmap")
]

for label, path in maps:
    w = unreal.EditorLoadingAndSavingUtils.load_map(path)
    if w:
        p_start = None
        for a in eas.get_all_level_actors():
            if "PlayerStart" in a.get_name():
                p_start = a
                break
        if p_start:
            unreal.log_warning(f"MAP_CHECK: {label} PlayerStart at {p_start.get_actor_location()} (rot {p_start.get_actor_rotation()})")
        else:
            unreal.log_warning(f"MAP_CHECK: {label} NO PlayerStart found!")

