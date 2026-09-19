"""Create a concrete BP_CarnivalGuest from ACarnivalGuestCharacter.

Assigns the engine tutorial mannequin (mesh + AnimBP) as a placeholder so the
guest is visible and animated, ready to be swapped for MetaHumans later.

Run headlessly:
    UnrealEditor.exe "CarnivalGame.uproject" -unattended -nullrhi -nosplash
        -ExecutePythonScript="<this file>" -ExecCmds="quit"
"""
import unreal

SDFL = unreal.SubobjectDataBlueprintFunctionLibrary
OUTPUT_PATH = "/Game/Carnival/Blueprints/Guests/BP_CarnivalGuest"
OUTPUT_NAME = "BP_CarnivalGuest"
OUTPUT_DIR = "/Game/Carnival/Blueprints/Guests"
PARENT_CLASS = "/Script/CarnivalPopulation.CarnivalGuestCharacter"
MESH_PATH = "/Engine/Tutorial/SubEditors/TutorialAssets/Character/TutorialTPP"
ANIMBP_PATH = "/Engine/Tutorial/SubEditors/TutorialAssets/Character/TutorialTPP_AnimBlueprint"


def log(msg):
    unreal.log_warning("GUEST: " + str(msg))


def _obj(h):
    return SDFL.get_associated_object(SDFL.get_data(h))


def main():
    # Ensure the output folder exists.
    if not unreal.EditorAssetLibrary.does_directory_exist(OUTPUT_DIR):
        unreal.EditorAssetLibrary.make_directory(OUTPUT_DIR)
        log("created dir " + OUTPUT_DIR)

    # Idempotent: delete existing.
    if unreal.EditorAssetLibrary.does_asset_exist(OUTPUT_PATH):
        unreal.EditorAssetLibrary.delete_asset(OUTPUT_PATH)
        try:
            unreal.SystemLibrary.collect_garbage()
        except Exception:
            pass
        log("deleted existing BP_CarnivalGuest")

    parent = unreal.load_class(None, PARENT_CLASS)
    if parent is None:
        log("parent class not found: " + PARENT_CLASS)
        return

    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", parent)
    bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        OUTPUT_NAME, OUTPUT_DIR, unreal.Blueprint, factory)
    if bp is None:
        log("create_asset failed")
        return

    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    mesh_asset = unreal.load_asset(MESH_PATH)
    anim_class = None
    anim_bp = unreal.load_asset(ANIMBP_PATH)
    if anim_bp is not None:
        anim_class = anim_bp.generated_class()

    found = False
    for h in sds.k2_gather_subobject_data_for_blueprint(bp):
        obj = _obj(h)
        if obj is None:
            continue
        if "SkeletalMeshComponent" not in obj.get_class().get_name():
            continue
        found = True
        if mesh_asset is not None and hasattr(obj, "set_editor_property"):
            try:
                obj.set_editor_property("SkeletalMesh", mesh_asset)
                log("set SkeletalMesh -> TutorialTPP")
            except Exception as exc:
                log("set SkeletalMesh failed: %s" % exc)
        if anim_class is not None and hasattr(obj, "set_editor_property"):
            try:
                obj.set_editor_property("AnimClass", anim_class)
                log("set AnimClass -> TutorialTPP_AnimBlueprint")
            except Exception as exc:
                log("set AnimClass failed: %s" % exc)

    if not found:
        log("no SkeletalMeshComponent found on the Blueprint")

    unreal.EditorAssetLibrary.save_asset(OUTPUT_PATH)
    log("saved " + OUTPUT_PATH)


main()
