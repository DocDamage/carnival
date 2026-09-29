import unreal

asset_path = "/Game/Carnival/Crowd/Mass/DA_CarnivalCrowdEntityConfig"
asset = unreal.load_asset(asset_path)
if not asset:
    raise RuntimeError("Missing crowd entity config: " + asset_path)

required_traits = [
    ("/Script/CarnivalPopulation.CarnivalMassPrerequisiteTrait", "core Mass actor/transform fragments"),
    ("/Script/MassLOD.MassDistanceLODCollectorTrait", "distance LOD viewer data"),
]
config = asset.get_editor_property("config")
traits = list(config.get_editor_property("traits"))
existing = {trait.get_class().get_name() for trait in traits if trait}
for class_path, label in required_traits:
    trait_class = unreal.load_class(None, class_path)
    if not trait_class:
        raise RuntimeError("Could not load required crowd trait " + class_path)
    class_name = trait_class.get_name()
    if class_name in existing:
        print("CROWD_TRAIT_PRESENT", class_name, label)
        continue
    added = unreal.new_object(trait_class, asset)
    if not added:
        raise RuntimeError("Could not add required crowd trait " + class_path)
    traits.append(added)
    config.set_editor_property("traits", traits)
    asset.set_editor_property("config", config)
    existing.add(class_name)
    print("CROWD_TRAIT_ADDED", class_name, label)

final_config = asset.get_editor_property("config")
for trait in final_config.get_editor_property("traits"):
    print("CROWD_TRAIT_FINAL", trait.get_class().get_name())
if not unreal.EditorAssetLibrary.save_loaded_asset(asset, False):
    raise RuntimeError("Failed to save " + asset_path)
print("CROWD_CONFIG_SAVED", asset_path)
unreal.SystemLibrary.quit_editor()
