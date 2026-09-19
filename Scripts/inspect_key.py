import unreal

k = unreal.Key()
unreal.log_warning(f"Key dir: {dir(k)}")
for prop in dir(k):
    if not prop.startswith("_"):
        unreal.log_warning(f"Key prop: {prop}")

