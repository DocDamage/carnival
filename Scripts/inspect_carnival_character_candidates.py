"""Read-only inventory of adult character assets that could fit Eli's worker role."""

import json
from pathlib import Path

import unreal


ROOT = Path(r"F:\Carnival")
REPORT = ROOT / "Saved/MissionAuthoring/Character_Candidate_Inventory.json"
registry = unreal.AssetRegistryHelpers.get_asset_registry()
registry.wait_for_completion()
selected_names = {
    "Mason", "Dean", "Skye", "MHC_Kabir", "MHC_Seo", "MHC_Hannah", "MHC_Advika",
    "SKM_Manny", "SKM_Quinn", "MHI_Mason", "MHI_Dean", "MHI_Skye", "BP_CarnivalGuest",
}
paths = (
    "/Game/Carnival/MetaHumans",
    "/Game/Carnival/Crowd/Instances",
    "/Game/Carnival/Blueprints/Guests",
    "/Game/IndustrialSlums/Characters/Mannequins/Meshes",
    "/Game/PlayMusicAnim/Demo/Mannequins/Meshes",
)
entries = []
for folder in paths:
    for data in registry.get_assets_by_path(folder, recursive=True):
        name = str(data.asset_name)
        if name not in selected_names:
            continue
        asset = data.get_asset()
        entry = {
            "name": name,
            "asset_path": str(data.package_name),
            "asset_class": str(data.asset_class_path.asset_name),
        }
        if asset:
            entry["loaded_class"] = asset.get_class().get_name()
            if isinstance(asset, unreal.SkeletalMesh):
                skeleton = asset.get_editor_property("skeleton")
                entry["skeleton"] = skeleton.get_path_name() if skeleton else None
                entry["materials"] = [
                    slot.material_interface.get_path_name() if slot.material_interface else None
                    for slot in asset.get_editor_property("materials")
                ]
            generated_class = None
            if asset.get_class().get_name() == "Blueprint":
                generated_class = asset.generated_class()
            if generated_class:
                cdo = unreal.get_default_object(generated_class)
                entry["generated_class"] = generated_class.get_name()
                entry["skeletal_mesh_components"] = []
                for component in cdo.get_components_by_class(unreal.SkeletalMeshComponent):
                    mesh = component.get_editor_property("skeletal_mesh_asset")
                    anim = component.get_editor_property("anim_class")
                    entry["skeletal_mesh_components"].append({
                        "name": component.get_name(),
                        "mesh": mesh.get_path_name() if mesh else None,
                        "anim_class": anim.get_path_name() if anim else None,
                    })
            if name.startswith("MHI_"):
                properties = {}
                try:
                    collection = asset.get_meta_human_collection()
                    properties["collection"] = collection.get_path_name() if collection else None
                    if collection:
                        properties["collection_class"] = collection.get_class().get_name()
                        try:
                            pipeline = collection.get_editor_property("pipeline")
                            properties["pipeline"] = pipeline.get_path_name() if pipeline else None
                            properties["pipeline_class"] = pipeline.get_class().get_name() if pipeline else None
                            if pipeline:
                                try:
                                    actor_class = pipeline.get_editor_property("actor_class")
                                    properties["pipeline_actor_class"] = actor_class.get_path_name() if actor_class else None
                                except Exception as exc:
                                    properties["pipeline_actor_class_error"] = str(exc)
                        except Exception as exc:
                            properties["pipeline_error"] = str(exc)
                        try:
                            built_data = collection.get_editor_property("built_data")
                            properties["built_data_class"] = built_data.get_class().get_name()
                            palette_data = built_data.get_editor_property("palette_built_data")
                            properties["palette_built_data_class"] = palette_data.get_class().get_name()
                            properties["palette_built_data"] = str(palette_data)
                        except Exception as exc:
                            properties["built_data_error"] = str(exc)
                except Exception as exc:
                    properties["collection_error"] = str(exc)
                for property_name in ("collection", "skeletal_mesh", "body_mesh", "character", "body", "face"):
                    try:
                        value = asset.get_editor_property(property_name)
                        properties[property_name] = value.get_path_name() if value else None
                        if property_name == "collection" and value:
                            collection = value
                            properties["collection_class"] = collection.get_class().get_name()
                            try:
                                pipeline = collection.get_editor_property("pipeline")
                                properties["pipeline"] = pipeline.get_path_name() if pipeline else None
                                properties["pipeline_class"] = pipeline.get_class().get_name() if pipeline else None
                                if pipeline:
                                    try:
                                        actor_class = pipeline.get_editor_property("actor_class")
                                        properties["pipeline_actor_class"] = actor_class.get_path_name() if actor_class else None
                                    except Exception as exc:
                                        properties["pipeline_actor_class_error"] = str(exc)
                            except Exception as exc:
                                properties["pipeline_error"] = str(exc)
                            try:
                                built_data = collection.get_editor_property("built_data")
                                properties["built_data_class"] = built_data.get_class().get_name()
                                palette_data = built_data.get_editor_property("palette_built_data")
                                properties["palette_built_data_class"] = palette_data.get_class().get_name()
                                properties["palette_built_data"] = str(palette_data)
                            except Exception as exc:
                                properties["built_data_error"] = str(exc)
                    except Exception:
                        pass
                try:
                    entry["instance_assembled"] = bool(asset.is_assembled())
                except Exception as exc:
                    entry["instance_assembled_error"] = str(exc)
                try:
                    entry["cook_behavior"] = str(asset.get_editor_property("should_cook_as_assembled"))
                except Exception:
                    pass
                try:
                    output = asset.get_existing_assembly_output()
                    entry["assembly_output"] = str(output)
                except Exception as exc:
                    entry["assembly_output_error"] = str(exc)
                entry["candidate_properties"] = properties
        entries.append(entry)

result = {"read_only": True, "success": bool(entries), "candidates": entries}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log("CARNIVAL_CHARACTER_CANDIDATES " + json.dumps(result))
unreal.SystemLibrary.quit_editor()
