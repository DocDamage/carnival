import unreal

unreal.log_warning(f"Montage classes: {[x for x in dir(unreal) if 'Montage' in x]}")
if hasattr(unreal, "AnimMontageFactory"):
    f = unreal.AnimMontageFactory()
    unreal.log_warning(f"AnimMontageFactory: {dir(f)}")

