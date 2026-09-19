import unreal

eal = unreal.EditorAssetLibrary
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
sdfl = unreal.SubobjectDataBlueprintFunctionLibrary

def assign_anim_bp():
    char_bp = unreal.load_asset("/Game/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter")
    if not char_bp:
        unreal.log_warning("BP_CarnivalPlayerCharacter not found!")
        return

    anim_bp = unreal.load_asset("/Game/Gladiator_Arena/Demo/StarterContent/Characters/Mannequins/Animations/ABP_Manny")
    if not anim_bp:
        unreal.log_warning("ABP_Manny not found!")
        return

    anim_class = anim_bp.generated_class()
    manny_mesh = unreal.load_asset("/Game/Gladiator_Arena/Demo/StarterContent/Characters/Mannequins/Meshes/SKM_Manny_Simple")
    if not manny_mesh:
        manny_mesh = unreal.load_asset("/Game/FreeAnimationLibrary/Demo/Characters/Mannequins/Meshes/SKM_Manny_Simple")

    for h in sds.k2_gather_subobject_data_for_blueprint(char_bp):
        obj = sdfl.get_associated_object(sdfl.get_data(h))
        if obj and "SkeletalMeshComponent" in obj.get_class().get_name():
            if manny_mesh:
                obj.set_editor_property("skeletal_mesh", manny_mesh)
            if anim_class:
                obj.set_editor_property("anim_class", anim_class)
                unreal.log_warning("ASSIGNED ABP_Manny to BP_CarnivalPlayerCharacter!")

    eal.save_asset("/Game/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter")

assign_anim_bp()

