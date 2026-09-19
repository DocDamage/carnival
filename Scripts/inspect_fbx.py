import unreal

unreal.log_warning(f"FBX in unreal: {[x for x in dir(unreal) if 'FBX' in x or 'Fbx' in x]}")
if hasattr(unreal, "FBXImportType"):
    unreal.log_warning(f"FBXImportType: {dir(unreal.FBXImportType)}")

