import unreal

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
eal = unreal.EditorAssetLibrary

skeleton = unreal.load_asset("/Game/FreeAnimationLibrary/Demo/Characters/Mannequins/Meshes/SK_Mannequin")
unreal.log_warning(f"Skeleton: {skeleton}")

fbx_path = "F:/Carnival/Assets/Motorcycle Animations/Motorcyc8536e49c7f27V4/MotoInteractionAnims/Animations/Mounted/Mount/AS_Mount_Left.fbx"

task = unreal.AssetImportTask()
task.filename = fbx_path
task.destination_path = "/Game/Carnival/Vehicles/Motorcycle/Animations"
task.destination_name = "AS_Mount_Left"
task.replace_existing = True
task.automated = True
task.save = True

fbx_ui = unreal.FbxImportUI()
fbx_ui.import_animations = True
fbx_ui.import_mesh = False
fbx_ui.skeleton = skeleton
fbx_ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_ANIMATION

task.options = fbx_ui

asset_tools.import_asset_tasks([task])
imported = unreal.load_asset("/Game/Carnival/Vehicles/Motorcycle/Animations/AS_Mount_Left")
unreal.log_warning(f"Imported AS_Mount_Left: {imported}")

