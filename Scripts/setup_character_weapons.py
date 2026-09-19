import unreal

eal = unreal.EditorAssetLibrary

def inspect_bp(path):
    bp = unreal.load_asset(path)
    if bp:
        cdo = unreal.get_default_object(bp.generated_class())
        unreal.log_warning(f"Inspected {path}: CDO={cdo}")
        return cdo
    return None

cdo_sword = inspect_bp("/Game/Carnival/Weapons/BP_CarnivalSword")
cdo_knife = inspect_bp("/Game/Carnival/Weapons/BP_CarnivalKnife")
cdo_gm = inspect_bp("/Game/Carnival/Blueprints/BP_CarnivalGameMode")
cdo_char = inspect_bp("/Game/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter")

if cdo_char:
    # Assign DefaultSwordClass and DefaultKnifeClass
    sword_class = unreal.load_class(None, "/Game/Carnival/Weapons/BP_CarnivalSword.BP_CarnivalSword_C")
    knife_class = unreal.load_class(None, "/Game/Carnival/Weapons/BP_CarnivalKnife.BP_CarnivalKnife_C")
    if sword_class:
        cdo_char.set_editor_property("default_sword_class", sword_class)
        unreal.log_warning("Assigned DefaultSwordClass")
    if knife_class:
        cdo_char.set_editor_property("default_knife_class", knife_class)
        unreal.log_warning("Assigned DefaultKnifeClass")
    eal.save_asset("/Game/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter")

if cdo_gm:
    char_class = unreal.load_class(None, "/Game/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter.BP_CarnivalPlayerCharacter_C")
    pc_class = unreal.load_class(None, "/Game/Carnival/Blueprints/BP_CarnivalPlayerController.BP_CarnivalPlayerController_C")
    if char_class:
        cdo_gm.set_editor_property("default_pawn_class", char_class)
        unreal.log_warning("Assigned DefaultPawnClass to BP_CarnivalGameMode")
    if pc_class:
        cdo_gm.set_editor_property("player_controller_class", pc_class)
        unreal.log_warning("Assigned PlayerControllerClass to BP_CarnivalGameMode")
    eal.save_asset("/Game/Carnival/Blueprints/BP_CarnivalGameMode")

