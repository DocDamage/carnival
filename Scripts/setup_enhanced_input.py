"""Create Enhanced Input Actions and Mapping Contexts for Carnival Character & Motorcycle.
Add Fast Travel actions F1-F7 to IMC_CarnivalPlayer & IMC_CarnivalMotorcycle and assign to BP_CarnivalPlayerController.

Run headlessly:
    UnrealEditor-Cmd.exe "CarnivalGame.uproject" -unattended -nullrhi -nosplash
        -ExecutePythonScript="F:\Carnival\Scripts\setup_enhanced_input.py" -ExecCmds="quit"
"""
import unreal

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
eal = unreal.EditorAssetLibrary

def log(msg):
    unreal.log_warning("INPUT_SETUP: " + str(msg))

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
        log(f"Created/Configured InputAction {full_path}")
    return ia

def create_mapping_context(name):
    path = "/Game/Carnival/Input"
    full_path = f"{path}/{name}"
    if eal.does_asset_exist(full_path):
        imc = unreal.load_asset(full_path)
    else:
        factory = unreal.DataAssetFactory()
        imc = asset_tools.create_asset(name, path, unreal.InputMappingContext, factory)
    if imc:
        eal.save_asset(full_path)
        log(f"Created InputMappingContext {full_path}")
    return imc

def main():
    ensure_dir("/Game/Carnival/Input")

    # 1. Create Actions
    # Base Actions
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

    # 2. Setup IMC_CarnivalPlayer
    # Fast Travel Actions (F1 - F7)
    ia_travel_carnival = create_input_action("IA_TravelCarnival", unreal.InputActionValueType.BOOLEAN)
    ia_travel_mansion = create_input_action("IA_TravelMansion", unreal.InputActionValueType.BOOLEAN)
    ia_travel_town = create_input_action("IA_TravelTown", unreal.InputActionValueType.BOOLEAN)
    ia_travel_lighthouse = create_input_action("IA_TravelLighthouse", unreal.InputActionValueType.BOOLEAN)
    ia_travel_castle = create_input_action("IA_TravelCastle", unreal.InputActionValueType.BOOLEAN)
    ia_travel_arena = create_input_action("IA_TravelArena", unreal.InputActionValueType.BOOLEAN)
    ia_travel_mars = create_input_action("IA_TravelMars", unreal.InputActionValueType.BOOLEAN)

    # IMC_CarnivalPlayer
    imc_player = create_mapping_context("IMC_CarnivalPlayer")
    if imc_player:
        # WASD for Move
        # W
        m_w = imc_player.map_key(ia_move, unreal.Key(unreal.Name("W")))
        if m_w:
            swizzle = unreal.InputModifierSwizzleAxis()
            swizzle.set_editor_property("order", unreal.InputModifierSwizzleAxisOrder.YXZ)
            m_w.set_editor_property("modifiers", [swizzle])
        # S
        m_s = imc_player.map_key(ia_move, unreal.Key(unreal.Name("S")))
        if m_s:
            swizzle = unreal.InputModifierSwizzleAxis()
            swizzle.set_editor_property("order", unreal.InputModifierSwizzleAxisOrder.YXZ)
            negate = unreal.InputModifierNegate()
            m_s.set_editor_property("modifiers", [swizzle, negate])
        # A
        m_a = imc_player.map_key(ia_move, unreal.Key(unreal.Name("A")))
        if m_a:
            negate = unreal.InputModifierNegate()
            m_a.set_editor_property("modifiers", [negate])
        # D
        imc_player.map_key(ia_move, unreal.Key(unreal.Name("D")))

        # Mouse for Look
        m_look = imc_player.map_key(ia_look, unreal.Key(unreal.Name("MouseXY")))
        if m_look:
            negate_y = unreal.InputModifierNegate()
            negate_y.set_editor_property("y", True)
            negate_y.set_editor_property("x", False)
            m_look.set_editor_property("modifiers", [negate_y])

        # Jump / Vault: SpaceBar
        imc_player.map_key(ia_jump, unreal.Key(unreal.Name("SpaceBar")))
        # Sprint: LeftShift
        imc_player.map_key(ia_sprint, unreal.Key(unreal.Name("LeftShift")))
        # Crouch: C
        imc_player.map_key(ia_crouch, unreal.Key(unreal.Name("C")))
        # Prone: Z
        imc_player.map_key(ia_prone, unreal.Key(unreal.Name("Z")))
        # Interact / Mount: E
        imc_player.map_key(ia_interact, unreal.Key(unreal.Name("E")))
        # Attack: LeftMouseButton
        imc_player.map_key(ia_attack, unreal.Key(unreal.Name("LeftMouseButton")))

        # Weapon Slots: 1, 2, 3, 4
        imc_player.map_key(ia_slot1, unreal.Key(unreal.Name("One")))
        imc_player.map_key(ia_slot2, unreal.Key(unreal.Name("Two")))
        imc_player.map_key(ia_slot3, unreal.Key(unreal.Name("Three")))
        imc_player.map_key(ia_slot0, unreal.Key(unreal.Name("Four")))

        # Settings Menu: M and Tab
        imc_player.map_key(ia_menu, unreal.Key(unreal.Name("M")))
        imc_player.map_key(ia_menu, unreal.Key(unreal.Name("Tab")))

        imc_player.map_key(ia_travel_carnival, unreal.Key(unreal.Name("F1")))
        imc_player.map_key(ia_travel_mansion, unreal.Key(unreal.Name("F2")))
        imc_player.map_key(ia_travel_town, unreal.Key(unreal.Name("F3")))
        imc_player.map_key(ia_travel_lighthouse, unreal.Key(unreal.Name("F4")))
        imc_player.map_key(ia_travel_castle, unreal.Key(unreal.Name("F5")))
        imc_player.map_key(ia_travel_arena, unreal.Key(unreal.Name("F6")))
        imc_player.map_key(ia_travel_mars, unreal.Key(unreal.Name("F7")))
        eal.save_asset("/Game/Carnival/Input/IMC_CarnivalPlayer")
        log("Configured IMC_CarnivalPlayer")

    # 3. Setup IMC_CarnivalMotorcycle
    # IMC_CarnivalMotorcycle
    imc_moto = create_mapping_context("IMC_CarnivalMotorcycle")
    if imc_moto:
        # Throttle: W (positive) / S (negative)
        m_tw = imc_moto.map_key(ia_throttle, unreal.Key(unreal.Name("W")))
        m_ts = imc_moto.map_key(ia_throttle, unreal.Key(unreal.Name("S")))
        if m_ts:
            negate = unreal.InputModifierNegate()
            m_ts.set_editor_property("modifiers", [negate])

        # Steer: D (positive) / A (negative)
        m_sd = imc_moto.map_key(ia_steer, unreal.Key(unreal.Name("D")))
        m_sa = imc_moto.map_key(ia_steer, unreal.Key(unreal.Name("A")))
        if m_sa:
            negate = unreal.InputModifierNegate()
            m_sa.set_editor_property("modifiers", [negate])

        # Brake: SpaceBar
        imc_moto.map_key(ia_brake, unreal.Key(unreal.Name("SpaceBar")))

        # Look: MouseXY
        m_mlook = imc_moto.map_key(ia_look, unreal.Key(unreal.Name("MouseXY")))
        if m_mlook:
            negate_y = unreal.InputModifierNegate()
            negate_y.set_editor_property("y", True)
            negate_y.set_editor_property("x", False)
            m_mlook.set_editor_property("modifiers", [negate_y])

        # Dismount: E
        imc_moto.map_key(ia_interact, unreal.Key(unreal.Name("E")))
        # Mounted Attack: LeftMouseButton
        imc_moto.map_key(ia_attack, unreal.Key(unreal.Name("LeftMouseButton")))
        # Settings Menu: M and Tab
        imc_moto.map_key(ia_menu, unreal.Key(unreal.Name("M")))
        imc_moto.map_key(ia_menu, unreal.Key(unreal.Name("Tab")))

        imc_moto.map_key(ia_travel_carnival, unreal.Key(unreal.Name("F1")))
        imc_moto.map_key(ia_travel_mansion, unreal.Key(unreal.Name("F2")))
        imc_moto.map_key(ia_travel_town, unreal.Key(unreal.Name("F3")))
        imc_moto.map_key(ia_travel_lighthouse, unreal.Key(unreal.Name("F4")))
        imc_moto.map_key(ia_travel_castle, unreal.Key(unreal.Name("F5")))
        imc_moto.map_key(ia_travel_arena, unreal.Key(unreal.Name("F6")))
        imc_moto.map_key(ia_travel_mars, unreal.Key(unreal.Name("F7")))
        eal.save_asset("/Game/Carnival/Input/IMC_CarnivalMotorcycle")
        log("Configured IMC_CarnivalMotorcycle")

    # 4. Assign to BP_CarnivalPlayerController
    # Assign to BP_CarnivalPlayerController
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

            pc_cdo.set_editor_property("travel_carnival_action", ia_travel_carnival)
            pc_cdo.set_editor_property("travel_mansion_action", ia_travel_mansion)
            pc_cdo.set_editor_property("travel_town_action", ia_travel_town)
            pc_cdo.set_editor_property("travel_lighthouse_action", ia_travel_lighthouse)
            pc_cdo.set_editor_property("travel_castle_action", ia_travel_castle)
            pc_cdo.set_editor_property("travel_arena_action", ia_travel_arena)
            pc_cdo.set_editor_property("travel_mars_action", ia_travel_mars)
            eal.save_asset("/Game/Carnival/Blueprints/BP_CarnivalPlayerController")
            log("Assigned all Input Actions & Mapping Contexts to BP_CarnivalPlayerController")
            log("Assigned Travel Actions F1-F7 to BP_CarnivalPlayerController!")

main()

