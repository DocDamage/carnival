"""Complete configuration of Enhanced Input, Controller mappings, and BuildComponent palette.

Run headlessly:
    UnrealEditor-Cmd.exe "CarnivalGame.uproject" -unattended -nullrhi -nosplash
        -ExecutePythonScript="F:\Carnival\Scripts\setup_complete_gameplay.py" -ExecCmds="quit"
"""
import unreal

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
eal = unreal.EditorAssetLibrary
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
sdfl = unreal.SubobjectDataBlueprintFunctionLibrary

def log(msg):
    unreal.log_warning("GAMEPLAY_SETUP: " + str(msg))

def make_key(key_name):
    k = unreal.Key()
    k.import_text(key_name)
    return k

def ensure_dir(path):
    if not eal.does_directory_exist(path):
        eal.make_directory(path)

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

def create_mapping_context(name):
    path = "/Game/Carnival/Input"
    full_path = f"{path}/{name}"
    if eal.does_asset_exist(full_path):
        imc = unreal.load_asset(full_path)
    else:
        factory = unreal.DataAssetFactory()
        imc = asset_tools.create_asset(name, path, unreal.InputMappingContext, factory)
    return imc

def main():
    ensure_dir("/Game/Carnival/Input")

    # 1. Create Actions
    ia_move = create_input_action("IA_Move", unreal.InputActionValueType.AXIS2D)
    ia_look = create_input_action("IA_Look", unreal.InputActionValueType.AXIS2D)
    ia_jump = create_input_action("IA_JumpVault", unreal.InputActionValueType.BOOLEAN)
    ia_sprint = create_input_action("IA_Sprint", unreal.InputActionValueType.BOOLEAN)
    ia_crouch = create_input_action("IA_Crouch", unreal.InputActionValueType.BOOLEAN)
    ia_prone = create_input_action("IA_Prone", unreal.InputActionValueType.BOOLEAN)
    ia_interact = create_input_action("IA_InteractMount", unreal.InputActionValueType.BOOLEAN)
    ia_attack = create_input_action("IA_Attack", unreal.InputActionValueType.BOOLEAN)
    ia_slot1 = create_input_action("IA_WeaponSlot1", unreal.InputActionValueType.BOOLEAN)
    ia_slot2 = create_input_action("IA_WeaponSlot2", unreal.InputActionValueType.BOOLEAN)
    ia_slot3 = create_input_action("IA_WeaponSlot3", unreal.InputActionValueType.BOOLEAN)
    ia_slot0 = create_input_action("IA_WeaponSlot0", unreal.InputActionValueType.BOOLEAN)
    ia_menu = create_input_action("IA_SettingsMenu", unreal.InputActionValueType.BOOLEAN)

    ia_throttle = create_input_action("IA_Throttle", unreal.InputActionValueType.AXIS1D)
    ia_steer = create_input_action("IA_Steer", unreal.InputActionValueType.AXIS1D)
    ia_brake = create_input_action("IA_Brake", unreal.InputActionValueType.AXIS1D)


    ia_toggle_build = create_input_action("IA_ToggleBuild", unreal.InputActionValueType.BOOLEAN)
    ia_secondary = create_input_action("IA_SecondaryAction", unreal.InputActionValueType.BOOLEAN)
    ia_rotate = create_input_action("IA_RotatePiece", unreal.InputActionValueType.BOOLEAN)
    ia_cycle_next = create_input_action("IA_CyclePieceNext", unreal.InputActionValueType.BOOLEAN)
    ia_cycle_prev = create_input_action("IA_CyclePiecePrev", unreal.InputActionValueType.BOOLEAN)
    ia_cycle_cat = create_input_action("IA_CycleCategory", unreal.InputActionValueType.BOOLEAN)

    # 2. IMC_CarnivalPlayer
    imc_player = create_mapping_context("IMC_CarnivalPlayer")
    if imc_player:
        # Clear existing mappings if possible or re-map
        # W
        m_w = imc_player.map_key(ia_move, make_key("W"))
        if m_w:
            swizzle = unreal.InputModifierSwizzleAxis()
            swizzle.set_editor_property("order", unreal.InputAxisSwizzle.YXZ)
            m_w.set_editor_property("modifiers", [swizzle])
        # S
        m_s = imc_player.map_key(ia_move, make_key("S"))
        if m_s:
            swizzle = unreal.InputModifierSwizzleAxis()
            swizzle.set_editor_property("order", unreal.InputAxisSwizzle.YXZ)
            negate = unreal.InputModifierNegate()
            m_s.set_editor_property("modifiers", [swizzle, negate])
        # A
        m_a = imc_player.map_key(ia_move, make_key("A"))
        if m_a:
            negate = unreal.InputModifierNegate()
            m_a.set_editor_property("modifiers", [negate])
        # D
        imc_player.map_key(ia_move, make_key("D"))

        # Look MouseXY
        m_look = imc_player.map_key(ia_look, make_key("MouseXY"))
        if m_look:
            negate_y = unreal.InputModifierNegate()
            negate_y.set_editor_property("y", True)
            negate_y.set_editor_property("x", False)
            m_look.set_editor_property("modifiers", [negate_y])

        # Jump / Vault: SpaceBar
        imc_player.map_key(ia_jump, make_key("SpaceBar"))
        # Sprint: LeftShift
        imc_player.map_key(ia_sprint, make_key("LeftShift"))
        # Crouch: C
        imc_player.map_key(ia_crouch, make_key("C"))
        # Prone: Z
        imc_player.map_key(ia_prone, make_key("Z"))
        # Interact / Mount: E
        imc_player.map_key(ia_interact, make_key("E"))
        # Attack: LeftMouseButton
        imc_player.map_key(ia_attack, make_key("LeftMouseButton"))

        # Weapon Slots: 1, 2, 3, 4
        imc_player.map_key(ia_slot1, make_key("One"))
        imc_player.map_key(ia_slot2, make_key("Two"))
        imc_player.map_key(ia_slot3, make_key("Three"))
        imc_player.map_key(ia_slot0, make_key("Four"))

        # Settings Menu: M and Tab
        imc_player.map_key(ia_menu, make_key("M"))
        imc_player.map_key(ia_menu, make_key("Tab"))


        # Build Mode Bindings
        imc_player.map_key(ia_toggle_build, make_key("B"))
        imc_player.map_key(ia_secondary, make_key("RightMouseButton"))
        imc_player.map_key(ia_rotate, make_key("R"))
        imc_player.map_key(ia_cycle_prev, make_key("Q"))
        imc_player.map_key(ia_cycle_cat, make_key("T"))
        imc_player.map_key(ia_cycle_next, make_key("MouseScrollUp"))
        imc_player.map_key(ia_cycle_prev, make_key("MouseScrollDown"))

        eal.save_asset("/Game/Carnival/Input/IMC_CarnivalPlayer")
        log("Configured and saved IMC_CarnivalPlayer")

    # 3. IMC_CarnivalMotorcycle
    imc_moto = create_mapping_context("IMC_CarnivalMotorcycle")
    if imc_moto:
        # Throttle: W / S
        imc_moto.map_key(ia_throttle, make_key("W"))
        m_ts = imc_moto.map_key(ia_throttle, make_key("S"))
        if m_ts:
            negate = unreal.InputModifierNegate()
            m_ts.set_editor_property("modifiers", [negate])

        # Steer: D / A
        imc_moto.map_key(ia_steer, make_key("D"))
        m_sa = imc_moto.map_key(ia_steer, make_key("A"))
        if m_sa:
            negate = unreal.InputModifierNegate()
            m_sa.set_editor_property("modifiers", [negate])

        # Brake: SpaceBar
        imc_moto.map_key(ia_brake, make_key("SpaceBar"))

        # Look: MouseXY
        m_mlook = imc_moto.map_key(ia_look, make_key("MouseXY"))
        if m_mlook:
            negate_y = unreal.InputModifierNegate()
            negate_y.set_editor_property("y", True)
            negate_y.set_editor_property("x", False)
            m_mlook.set_editor_property("modifiers", [negate_y])

        # Dismount: E
        imc_moto.map_key(ia_interact, make_key("E"))
        # Mounted Attack: LeftMouseButton
        imc_moto.map_key(ia_attack, make_key("LeftMouseButton"))
        # Settings Menu: M and Tab
        imc_moto.map_key(ia_menu, make_key("M"))
        imc_moto.map_key(ia_menu, make_key("Tab"))


        eal.save_asset("/Game/Carnival/Input/IMC_CarnivalMotorcycle")
        log("Configured and saved IMC_CarnivalMotorcycle")

    # 4. Assign all actions to BP_CarnivalPlayerController
    pc_bp = unreal.load_asset("/Game/Carnival/Blueprints/BP_CarnivalPlayerController")
    if pc_bp:
        pc_cdo = unreal.get_default_object(pc_bp.generated_class())
        if pc_cdo:
            pc_cdo.set_editor_property("default_mapping_context", imc_player)
            pc_cdo.set_editor_property("motorcycle_mapping_context", imc_moto)
            pc_cdo.set_editor_property("move_action", ia_move)
            pc_cdo.set_editor_property("look_action", ia_look)
            pc_cdo.set_editor_property("jump_vault_action", ia_jump)
            pc_cdo.set_editor_property("sprint_action", ia_sprint)
            pc_cdo.set_editor_property("crouch_action", ia_crouch)
            pc_cdo.set_editor_property("prone_action", ia_prone)
            pc_cdo.set_editor_property("interact_mount_action", ia_interact)
            pc_cdo.set_editor_property("attack_action", ia_attack)
            pc_cdo.set_editor_property("weapon_slot1_action", ia_slot1)
            pc_cdo.set_editor_property("weapon_slot2_action", ia_slot2)
            pc_cdo.set_editor_property("weapon_slot3_action", ia_slot3)
            pc_cdo.set_editor_property("weapon_slot0_action", ia_slot0)
            pc_cdo.set_editor_property("settings_menu_action", ia_menu)

            pc_cdo.set_editor_property("throttle_action", ia_throttle)
            pc_cdo.set_editor_property("steer_action", ia_steer)
            pc_cdo.set_editor_property("brake_action", ia_brake)


            pc_cdo.set_editor_property("secondary_action", ia_secondary)
            pc_cdo.set_editor_property("toggle_build_action", ia_toggle_build)
            pc_cdo.set_editor_property("rotate_piece_action", ia_rotate)
            pc_cdo.set_editor_property("cycle_piece_next_action", ia_cycle_next)
            pc_cdo.set_editor_property("cycle_piece_prev_action", ia_cycle_prev)
            pc_cdo.set_editor_property("cycle_category_action", ia_cycle_cat)

            eal.save_asset("/Game/Carnival/Blueprints/BP_CarnivalPlayerController")
            log("Assigned all Input Actions & Contexts to BP_CarnivalPlayerController")

    # 5. Setup Build Palette on BP_CarnivalPlayerCharacter
    char_bp = unreal.load_asset("/Game/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter")
    if char_bp:
        build_comp = None
        for h in sds.k2_gather_subobject_data_for_blueprint(char_bp):
            obj = sdfl.get_associated_object(sdfl.get_data(h))
            if obj and "BuildComponent" in obj.get_name():
                build_comp = obj
                break

        if build_comp:
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
            castle_pieces = [unreal.load_asset(p) for p in castle_mesh_paths if unreal.load_asset(p)]

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
            town_pieces = [unreal.load_asset(p) for p in town_mesh_paths if unreal.load_asset(p)]

            # 3. Stunt Ramps & Platforms
            stunt_mesh_paths = [
                "/Game/Medieval_Castle/CastleKit/Props/Meshes/ModularBuildings/SM_WoodPlatformStair_01a",
                "/Game/Medieval_Castle/CastleKit/Props/Meshes/ModularBuildings/SM_WoodPlatform_01b",
                "/Game/Medieval_Castle/CastleKit/Props/Meshes/ModularBuildings/SM_WoodPlatformFloor_01b",
                "/Game/Medieval_Castle/CastleKit/Props/Meshes/Rock_Stone_Wall/SM_RockStoneWall_01a"
            ]
            stunt_pieces = [unreal.load_asset(p) for p in stunt_mesh_paths if unreal.load_asset(p)]

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
        else:
            log("ERROR: BuildComponent not found on BP_CarnivalPlayerCharacter!")

    log("Gameplay setup completed successfully!")

main()

