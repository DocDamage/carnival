import unreal

eal = unreal.EditorAssetLibrary
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
sdfl = unreal.SubobjectDataBlueprintFunctionLibrary

def assign_bike():
    mesh_path = "/Game/Carnival/Vehicles/Motorcycle/Mesh/SK_rsg_LastGuns_bike_01"
    bike_mesh = unreal.load_asset(mesh_path)
    if not bike_mesh:
        unreal.log_warning(f"Could not load {mesh_path}")
        return

    bp_path = "/Game/Carnival/Vehicles/Motorcycle/Blueprints/BP_CarnivalMotorcycle"
    bike_bp = unreal.load_asset(bp_path)
    if not bike_bp:
        unreal.log_warning(f"Could not load {bp_path}")
        return

    for h in sds.k2_gather_subobject_data_for_blueprint(bike_bp):
        obj = sdfl.get_associated_object(sdfl.get_data(h))
        if obj and "BikeMesh" in obj.get_name():
            try:
                obj.set_editor_property("skeletal_mesh_asset", bike_mesh)
                unreal.log_warning("SUCCESS: Assigned SK_rsg_LastGuns_bike_01 to BP_CarnivalMotorcycle!")
            except Exception:
                try:
                    obj.set_editor_property("skeletal_mesh", bike_mesh)
                    unreal.log_warning("SUCCESS: Assigned SK_rsg_LastGuns_bike_01 (fallback)!")
                except Exception as e:
                    unreal.log_warning(f"Failed to assign bike mesh: {e}")

    eal.save_asset(bp_path)

assign_bike()

