"""Import SK_RSG_Bike.fbx into Unreal and assign to BP_CarnivalMotorcycle.

Run headlessly:
    UnrealEditor-Cmd.exe "CarnivalGame.uproject" -unattended -nullrhi -nosplash
        -ExecutePythonScript="F:\Carnival\Scripts\import_motorcycle_mesh.py" -ExecCmds="quit"
"""
import unreal

eal = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
sdfl = unreal.SubobjectDataBlueprintFunctionLibrary

def log(msg):
    unreal.log_warning("BIKE_IMPORT: " + str(msg))

def import_bike():
    fbx_file = "F:/Carnival/Content/Carnival/Vehicles/Motorcycle/Mesh/SK_RSG_Bike.fbx"
    dest_path = "/Game/Carnival/Vehicles/Motorcycle/Mesh"
    asset_name = "SK_RSG_Bike"
    full_asset_path = f"{dest_path}/{asset_name}"

    if not eal.does_asset_exist(full_asset_path):
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", fbx_file)
        task.set_editor_property("destination_path", dest_path)
        task.set_editor_property("destination_name", asset_name)
        task.set_editor_property("replace_existing", True)
        task.set_editor_property("automated", True)
        task.set_editor_property("save", True)

        options = unreal.FbxImportUI()
        options.set_editor_property("import_mesh", True)
        
        # Determine import type enum
        try:
            options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
        except Exception:
            try:
                options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
            except Exception as e:
                log(f"Enum setting warning: {e}")

        options.set_editor_property("import_materials", True)
        options.set_editor_property("import_textures", True)

        task.set_editor_property("options", options)
        asset_tools.import_asset_tasks([task])
        log(f"Import task executed for {full_asset_path}")

    bike_mesh = unreal.load_asset(full_asset_path)
    log(f"Loaded bike mesh: {bike_mesh}")

    bike_bp = unreal.load_asset("/Game/Carnival/Vehicles/Motorcycle/Blueprints/BP_CarnivalMotorcycle")
    if bike_bp and bike_mesh:
        for h in sds.k2_gather_subobject_data_for_blueprint(bike_bp):
            obj = sdfl.get_associated_object(sdfl.get_data(h))
            if obj and "BikeMesh" in obj.get_name():
                try:
                    obj.set_editor_property("skeletal_mesh_asset", bike_mesh)
                    log("Assigned SK_RSG_Bike to BP_CarnivalMotorcycle as SkeletalMesh")
                except Exception:
                    try:
                        obj.set_editor_property("skeletal_mesh", bike_mesh)
                        log("Assigned SK_RSG_Bike to BP_CarnivalMotorcycle")
                    except Exception as e2:
                        log(f"Could not assign bike mesh: {e2}")

        eal.save_asset("/Game/Carnival/Vehicles/Motorcycle/Blueprints/BP_CarnivalMotorcycle")

import_bike()
