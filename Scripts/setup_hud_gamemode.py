import unreal

eal = unreal.EditorAssetLibrary

gm_bp = unreal.load_asset("/Game/Carnival/Blueprints/BP_CarnivalGameMode")
if gm_bp:
    cdo = unreal.get_default_object(gm_bp.generated_class())
    if cdo:
        hud_class = unreal.load_class(None, "/Script/CarnivalGame.CarnivalHUD")
        if hud_class:
            cdo.set_editor_property("hud_class", hud_class)
            unreal.log_warning(f"Assigned HUDClass to BP_CarnivalGameMode: {hud_class}")
        eal.save_asset("/Game/Carnival/Blueprints/BP_CarnivalGameMode")
        unreal.log_warning("Saved BP_CarnivalGameMode!")

