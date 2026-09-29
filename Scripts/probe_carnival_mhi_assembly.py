"""Inspect one saved MetaHuman instance by assembling it transiently in the editor."""

import json
from pathlib import Path

import unreal


REPORT = Path(r"F:\Carnival\Saved\MissionAuthoring\MHI_Assembly_Probe.json")
asset_path = "/Game/Carnival/Crowd/Instances/ExpandedFinal2/MHI_Dean"
instance = unreal.EditorAssetLibrary.load_asset(asset_path)
result = {"read_only": True, "asset_path": asset_path, "success": False}
if instance is None:
    result["error"] = "Could not load MetaHuman instance"
else:
    result["instance_class"] = instance.get_class().get_name()
    collection = instance.get_meta_human_collection()
    result["collection"] = collection.get_path_name() if collection else None
    if collection:
        try:
            pipeline = collection.get_editor_property("pipeline")
            result["pipeline"] = pipeline.get_path_name() if pipeline else None
            result["pipeline_actor_class"] = (
                pipeline.get_editor_property("actor_class").get_path_name() if pipeline else None
            )
        except Exception as exc:
            result["pipeline_inspection_error"] = str(exc)
    try:
        result["assembled_before"] = bool(instance.is_assembled())
        output = instance.get_assembly_output()
        result["assembly_output"] = str(output)
        result["assembly_output_repr"] = repr(output)
        result["assembly_output_methods"] = [
            name for name in dir(output)
            if any(token in name.lower() for token in ("valid", "struct", "value", "property", "memory"))
        ]
        result["assembly_assets"] = {}
        for property_name in (
            "actor_face_mesh", "actor_body_mesh", "instanced_face_mesh", "instanced_body_mesh",
            "anim_bp_animations", "baked_anim_root_provider", "actor_clothing", "actor_grooms",
        ):
            try:
                value = output.get_editor_property(property_name)
                if isinstance(value, (list, tuple)):
                    result["assembly_assets"][property_name] = [
                        item.get_path_name() if item and hasattr(item, "get_path_name") else str(item)
                        for item in value
                    ]
                else:
                    result["assembly_assets"][property_name] = (
                        value.get_path_name() if value and hasattr(value, "get_path_name") else str(value)
                    )
            except Exception as exc:
                result["assembly_assets"][property_name + "_error"] = str(exc)
        for method_name in ("is_valid", "get_script_struct", "get_value", "get_struct_memory"):
            try:
                method = getattr(output, method_name)
                value = method() if callable(method) else method
                result[method_name] = str(value)
                if method_name == "get_script_struct" and value:
                    result["assembly_output_struct"] = value.get_path_name()
                    result["assembly_output_struct_fields"] = [
                        name for name in dir(value)
                        if any(token in name.lower() for token in ("face", "body", "mesh", "anim", "clothing", "groom"))
                    ]
            except Exception as exc:
                result[method_name + "_error"] = str(exc)
        result["assembled_after"] = bool(instance.is_assembled())
        result["success"] = bool(instance.is_assembled())
    except Exception as exc:
        result["assembly_error"] = str(exc)

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log("CARNIVAL_MHI_ASSEMBLY_PROBE " + json.dumps(result))
unreal.SystemLibrary.quit_editor()
