import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

check_maps = [
    ("Town", "/Game/Town/Level/L_Main_Level"),
    ("Lighthouse", "/Game/LightHouse_Meshingun/Map/LV_LightHouse"),
    ("Castle", "/Game/Medieval_Castle/Level/Medieval_Castle_Level"),
    ("Mars", "/Game/Mars_Futuristic_Cars/Maps/Playmap")
]

for label, path in check_maps:
    w = unreal.EditorLoadingAndSavingUtils.load_map(path)
    if w:
        all_actors = eas.get_all_level_actors()
        cameras = [a for a in all_actors if "Camera" in a.get_name() or "Cine" in a.get_name()]
        unreal.log_warning(f"MAP_INFO: {label} has {len(all_actors)} actors, {len(cameras)} cameras")
        for c in cameras[:5]:
            unreal.log_warning(f"  {label} Camera: {c.get_name()} at {c.get_actor_location()}")
        if len(cameras) == 0:
            # find central static mesh
            meshes = [a for a in all_actors if "StaticMesh" in a.get_class().get_name()]
            if meshes:
                avg_x = sum(m.get_actor_location().x for m in meshes[:20]) / min(len(meshes), 20)
                avg_y = sum(m.get_actor_location().y for m in meshes[:20]) / min(len(meshes), 20)
                avg_z = sum(m.get_actor_location().z for m in meshes[:20]) / min(len(meshes), 20)
                unreal.log_warning(f"  {label} Sample mesh loc: {meshes[0].get_actor_location()}, avg: ({avg_x:.0f}, {avg_y:.0f}, {avg_z:.0f})")

