import unreal

k = unreal.Key()
unreal.log_warning(f"Key to_dict: {k.to_dict()}")
unreal.log_warning(f"Key export_text: {k.export_text()}")
k.import_text("B")
unreal.log_warning(f"Key after import_text('B'): {k.export_text()}, {k.to_dict()}")

