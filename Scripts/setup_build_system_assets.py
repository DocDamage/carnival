"""Populate building categories on BP_CarnivalPlayerCharacter and setup build input actions.

Run headlessly:
    UnrealEditor-Cmd.exe "CarnivalGame.uproject" -unattended -nullrhi -nosplash
        -ExecutePythonScript="F:\Carnival\Scripts\setup_build_system_assets.py" -ExecCmds="quit"
"""
import unreal

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
eal = unreal.EditorAssetLibrary
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
sdfl = unreal.SubobjectDataBlueprintFunctionLibrary

def log(msg):
    unreal.log_warning("BUILD_SETUP: " + str(msg))

def create_input_action(name, value_type=unreal.InputActionValueType.BOOLEAN):
    path = "/Game/Carnival/Input"
    full_path = f"{path}/{name}"
    if eal.does_asset_exist(full_path):
        ia = unreal.load_asset(full_path)
    else:
        factory = unreal.DataAssetFactory()
        ia = asset_tools.create_asset(name, path, unreal.InputAction, factory)
    if ia:
        ia.set_editor_property("value_type", value_type)
        eal.save_asset(full_path)
    return ia

def setup_build_inputs():
    ia_toggle_build = create_input_action("IA_ToggleBuild", unreal.InputActionValueType.BOOLEAN)
    ia_secondary = create_input_action("IA_SecondaryAction", unreal.InputActionValueType.BOOLEAN)
    ia_rotate = create_input_action("IA_RotatePiece", unreal.InputActionValueType.BOOLEAN)
    ia_cycle_next = create_input_action("IA_CyclePieceNext", unreal.InputActionValueType.BOOLEAN)
    ia_cycle_prev = create_input_action("IA_CyclePiecePrev", unreal.InputActionValueType.BOOLEAN)
    ia_cycle_cat = create_input_action("IA_CycleCategory", unreal.InputActionValueType.BOOLEAN)

    imc_player = unreal.load_asset("/Game/Carnival/Input/IMC_CarnivalPlayer")
    if imc_player:
        # B: Toggle Build
        imc_player.map_key(ia_toggle_build, unreal.Key(unreal.Name("B")))
        # Right Mouse Button: Demolish / Secondary
        imc_player.map_key(ia_secondary, unreal.Key(unreal.Name("RightMouseButton")))
        # R: Rotate
        imc_player.map_key(ia_rotate, unreal.Key(unreal.Name("R")))
        # Q: Cycle Prev
        imc_player.map_key(ia_cycle_prev, unreal.Key(unreal.Name("Q")))
        # T: Cycle Category
        imc_player.map_key(ia_cycle_cat, unreal.Key(unreal.Name("T")))
        # Mouse Wheel Up: Cycle Next
        imc_player.map_key(ia_cycle_next, unreal.Key(unreal.Name("MouseScrollUp")))
        # Mouse Wheel Down: Cycle Prev
        imc_player.map_key(ia_cycle_prev, unreal.Key(unreal.Name("MouseScrollDown")))

        eal.save_asset("/Game/Carnival/Input/IMC_CarnivalPlayer")
        log("Updated IMC_CarnivalPlayer with build mode bindings (B, RMB, R, Q, T, Scroll)")

    pc_bp = unreal.load_asset("/Game/Carnival/Blueprints/BP_CarnivalPlayerController")
    if pc_bp:
        pc_cdo = unreal.get_default_object(pc_bp.generated_class())
        if pc_cdo:
            pc_cdo.set_editor_property("secondary_action", ia_secondary)
            pc_cdo.set_editor_property("toggle_build_action", ia_toggle_build)
            pc_cdo.set_editor_property("rotate_piece_action", ia_rotate)
            pc_cdo.set_editor_property("cycle_piece_next_action", ia_cycle_next)
            pc_cdo.set_editor_property("cycle_piece_prev_action", ia_cycle_prev)
            pc_cdo.set_editor_property("cycle_category_action", ia_cycle_cat)
            eal.save_asset("/Game/Carnival/Blueprints/BP_CarnivalPlayerController")
            log("Assigned build actions to BP_CarnivalPlayerController")

def setup_build_palette():
    char_bp = unreal.load_asset("/Game/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter")
    if not char_bp:
        log("BP_CarnivalPlayerCharacter not found!")
        return

    # Find the BuildComponent on the blueprint
    build_comp = None
    for h in sds.k2_gather_subobject_data_for_blueprint(char_bp):
        obj = sdfl.get_associated_object(sdfl.get_data(h))
        if obj and "BuildComponent" in obj.get_name():
            build_comp = obj
            break

    if not build_comp:
        log("BuildComponent not found on BP_CarnivalPlayerCharacter!")
        return

    # 1. Castle Category
    castle_mesh_paths = [
        "/Game/Medieval_Castle/CastleKit/Walls_Stone/SM_Castle_Stone_Wall_01a_NN",
        "/Game/Medieval_Castle/CastleKit/Walls_Stone/SM_Castle_Stone_Wall_02a_NN",
        "/Game/Medieval_Castle/CastleKit/Walls_Stone/SM_Castle_Stone_Pillar_01a_NN",
        "/Game/Medieval_Castle/CastleKit/Walls_Stone/SM_Castle_Stone_Arch_01a_NN",
        "/Game/Medieval_Castle/CastleKit/Walls_Stone/SM_Castle_Tower_Wall_01a_NN",
        "/Game/Medieval_Castle/CastleKit/Props/Meshes/ModularBuildings/SM_WoodPlatformFloor_01b",
        "/Game/Medieval_Castle/CastleKit/Props/Meshes/ModularBuildings/SM_WoodPlatformStair_01a",
        "/Game/Medieval_Castle/CastleKit/Props/Meshes/ModularBuildings/SM_WoodFence_01a"
    ]
    castle_pieces = []
    for p in castle_mesh_paths:
        m = unreal.load_asset(p)
        if m:
            castle_pieces.append(m)

    # 2. Town Category
    town_mesh_paths = [
        "/Game/Town/Meshes/Barn/SM_Barn_Wall_01",
        "/Game/Town/Meshes/Barn/SM_Barn_Floor_01",
        "/Game/Town/Meshes/Barn/SM_Barn_Pillar_01",
        "/Game/Town/Meshes/Barn/SM_Fence_01",
        "/Game/Town/Meshes/House/SM_Floor_4m",
        "/Game/Town/Meshes/House/SM_Pillar",
        "/Game/Town/Meshes/House/SM_Stairs_01"
    ]
    town_pieces = []
    for p in town_mesh_paths:
        m = unreal.load_asset(p)
        if m:
            town_pieces.append(m)

    # 3. Stunt Ramps & Platforms (for Motorcycle stunts!)
    stunt_mesh_paths = [
        "/Game/Medieval_Castle/CastleKit/Props/Meshes/ModularBuildings/SM_WoodPlatformStair_01a",
        "/Game/Medieval_Castle/CastleKit/Props/Meshes/ModularBuildings/SM_WoodPlatform_01b",
        "/Game/Medieval_Castle/CastleKit/Props/Meshes/ModularBuildings/SM_WoodPlatformFloor_01b",
        "/Game/Medieval_Castle/CastleKit/Props/Meshes/Rock_Stone_Wall/SM_RockStoneWall_01a"
    ]
    stunt_pieces = []
    for p in stunt_mesh_paths:
        m = unreal.load_asset(p)
        if m:
            stunt_pieces.append(m)

    # Build category structs
    cat_castle = unreal.CarnivalBuildCategory()
    cat_castle.set_editor_property("category_name", "Castle Fortress")
    cat_castle.set_editor_property("pieces", castle_pieces)

    cat_town = unreal.CarnivalBuildCategory()
    cat_town.set_editor_property("category_name", "Town & Village")
    cat_town.set_editor_property("pieces", town_pieces)

    cat_stunt = unreal.CarnivalBuildCategory()
    cat_stunt.set_editor_property("category_name", "Stunt Ramps & Platforms")
    cat_stunt.set_editor_property("pieces", stunt_pieces)

    all_categories = [cat_castle, cat_town, cat_stunt]
    build_comp.set_editor_property("categories", all_categories)
    build_comp.set_editor_property("grid_snap_size", 100.0)
    build_comp.set_editor_property("max_build_distance", 1500.0)

    eal.save_asset("/Game/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter")
    log(f"Configured BuildComponent with {len(all_categories)} categories and {len(castle_pieces) + len(town_pieces) + len(stunt_pieces)} modular building pieces!")

def main():
    setup_build_inputs()
    setup_build_palette()
    log("Build system setup complete!")

main()

