"""Build and configure all gameplay blueprints, input actions, and character assets.

Run headlessly:
    UnrealEditor-Cmd.exe "CarnivalGame.uproject" -unattended -nullrhi -nosplash
        -ExecutePythonScript="F:\Carnival\Scripts\build_gameplay_assets.py" -ExecCmds="quit"
"""
import unreal

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
eal = unreal.EditorAssetLibrary
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
sdfl = unreal.SubobjectDataBlueprintFunctionLibrary

def log(msg):
    unreal.log_warning("CARNIVAL_SETUP: " + str(msg))

def ensure_dir(path):
    if not eal.does_directory_exist(path):
        eal.make_directory(path)

def create_blueprint(name, path, parent_class_name):
    full_path = f"{path}/{name}"
    if eal.does_asset_exist(full_path):
        eal.delete_asset(full_path)
        try:
            unreal.SystemLibrary.collect_garbage()
        except Exception:
            pass

    parent_class = unreal.load_class(None, parent_class_name)
    if not parent_class:
        log(f"Failed to load parent class: {parent_class_name}")
        return None

    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", parent_class)
    bp = asset_tools.create_asset(name, path, unreal.Blueprint, factory)
    log(f"Created Blueprint {full_path} with parent {parent_class_name}")
    return bp

def create_montage_from_sequence(seq_path, montage_name, montage_dir):
    full_path = f"{montage_dir}/{montage_name}"
    if eal.does_asset_exist(full_path):
        return unreal.load_asset(full_path)

    seq = unreal.load_asset(seq_path)
    if not seq:
        log(f"Animation sequence not found: {seq_path}")
        return None

    factory = unreal.AnimMontageFactory()
    factory.set_editor_property("source_animation", seq)
    montage = asset_tools.create_asset(montage_name, montage_dir, unreal.AnimMontage, factory)
    if montage:
        eal.save_asset(full_path)
        log(f"Created Montage: {full_path}")
    return montage

def setup_weapons():
    ensure_dir("/Game/Carnival/Weapons")
    
    # 1. Sword
    sword_bp = create_blueprint("BP_CarnivalSword", "/Game/Carnival/Weapons", "/Script/CarnivalGame.CarnivalWeaponBase")
    if sword_bp:
        sword_cdo = unreal.get_default_object(sword_bp.generated_class())
        if sword_cdo:
            sword_cdo.set_editor_property("weapon_type", unreal.CarnivalWeaponType.SWORD)
            sword_cdo.set_editor_property("base_damage", 35.0)
            sword_mesh = unreal.load_asset("/Game/Gladiator_Arena/Mesh/SM_Sword_A")
            if not sword_mesh:
                sword_mesh = unreal.load_asset("/Game/RamsterZ_FreeAnims_Volume1/Mesh/OneHandSword_Mesh")
            
            # Find static mesh component on CDO or Blueprint subobjects
            for h in sds.k2_gather_subobject_data_for_blueprint(sword_bp):
                obj = sdfl.get_associated_object(sdfl.get_data(h))
                if obj and "WeaponStaticMesh" in obj.get_name() and sword_mesh:
                    obj.set_editor_property("static_mesh", sword_mesh)
                    log("Assigned SM_Sword_A to BP_CarnivalSword")
        eal.save_asset("/Game/Carnival/Weapons/BP_CarnivalSword")

    # 2. Shield
    shield_bp = create_blueprint("BP_CarnivalShield", "/Game/Carnival/Weapons", "/Script/CarnivalGame.CarnivalWeaponBase")
    if shield_bp:
        shield_cdo = unreal.get_default_object(shield_bp.generated_class())
        if shield_cdo:
            shield_cdo.set_editor_property("weapon_type", unreal.CarnivalWeaponType.SWORD_AND_SHIELD)
            shield_cdo.set_editor_property("equip_socket_name", unreal.Name("hand_lSocket"))
            shield_cdo.set_editor_property("holster_socket_name", unreal.Name("weapon_backSocket"))
            shield_mesh = unreal.load_asset("/Game/Gladiator_Arena/Mesh/SM_Shield")
            for h in sds.k2_gather_subobject_data_for_blueprint(shield_bp):
                obj = sdfl.get_associated_object(sdfl.get_data(h))
                if obj and "WeaponStaticMesh" in obj.get_name() and shield_mesh:
                    obj.set_editor_property("static_mesh", shield_mesh)
                    log("Assigned SM_Shield to BP_CarnivalShield")
        eal.save_asset("/Game/Carnival/Weapons/BP_CarnivalShield")

    # 3. Knife
    knife_bp = create_blueprint("BP_CarnivalKnife", "/Game/Carnival/Weapons", "/Script/CarnivalGame.CarnivalWeaponBase")
    if knife_bp:
        knife_cdo = unreal.get_default_object(knife_bp.generated_class())
        if knife_cdo:
            knife_cdo.set_editor_property("weapon_type", unreal.CarnivalWeaponType.KNIFE)
            knife_cdo.set_editor_property("base_damage", 25.0)
            knife_cdo.set_editor_property("attack_range", 120.0)
            knife_mesh = unreal.load_asset("/Game/RamsterZ_FreeAnims_Volume1/Props/Mesh/BP_Knife_Mann")
            for h in sds.k2_gather_subobject_data_for_blueprint(knife_bp):
                obj = sdfl.get_associated_object(sdfl.get_data(h))
                if obj and "WeaponStaticMesh" in obj.get_name() and knife_mesh:
                    obj.set_editor_property("static_mesh", knife_mesh)
        eal.save_asset("/Game/Carnival/Weapons/BP_CarnivalKnife")

def setup_motorcycle():
    ensure_dir("/Game/Carnival/Vehicles/Motorcycle/Blueprints")
    bike_bp = create_blueprint("BP_CarnivalMotorcycle", "/Game/Carnival/Vehicles/Motorcycle/Blueprints", "/Script/CarnivalGame.CarnivalMotorcycle")
    if bike_bp:
        bike_cdo = unreal.get_default_object(bike_bp.generated_class())
        if bike_cdo:
            bike_cdo.set_editor_property("physics_mode", unreal.MotorcyclePhysicsMode.ARCADE)
            bike_cdo.set_editor_property("max_speed", 2200.0)
            bike_cdo.set_editor_property("acceleration", 1300.0)
            bike_cdo.set_editor_property("turn_rate", 80.0)
            bike_cdo.set_editor_property("max_lean_angle", 30.0)
            
            # Setup exhaust particle if SmokePack has a Niagara system
            smoke_fx = unreal.load_asset("/Game/SmokePack/Particles/NS_Smoke_01")
            if smoke_fx:
                for h in sds.k2_gather_subobject_data_for_blueprint(bike_bp):
                    obj = sdfl.get_associated_object(sdfl.get_data(h))
                    if obj and "ExhaustVFX" in obj.get_name():
                        obj.set_editor_property("asset", smoke_fx)
                        log("Assigned Niagara exhaust to BP_CarnivalMotorcycle")

        eal.save_asset("/Game/Carnival/Vehicles/Motorcycle/Blueprints/BP_CarnivalMotorcycle")
        log("Saved BP_CarnivalMotorcycle")

def setup_player_character():
    ensure_dir("/Game/Carnival/Character/Blueprints")
    ensure_dir("/Game/Carnival/Character/Montages")

    # Create montages for locomotion actions
    montages_dir = "/Game/Carnival/Character/Montages"
    vault_m = create_montage_from_sequence("/Game/FreeAnimationLibrary/Animations/Vault/anim_Vault", "AM_Vault", montages_dir)
    mantle1m_m = create_montage_from_sequence("/Game/FreeAnimationLibrary/Animations/Mantle/anim_Mantle_1M_R", "AM_Mantle_1M", montages_dir)
    mantle2m_m = create_montage_from_sequence("/Game/FreeAnimationLibrary/Animations/Mantle/anim_Mantle_2M_R", "AM_Mantle_2M", montages_dir)
    roll_m = create_montage_from_sequence("/Game/FreeAnimationLibrary/Animations/LandingRoll/anim_LandRoll_R", "AM_LandingRoll", montages_dir)
    stand_to_prone_m = create_montage_from_sequence("/Game/FreeAnimationLibrary/Animations/UnarmedProne/anim_Stand_To_Prone", "AM_StandToProne", montages_dir)
    prone_to_stand_m = create_montage_from_sequence("/Game/FreeAnimationLibrary/Animations/UnarmedProne/anim_Prone_To_Stand", "AM_ProneToStand", montages_dir)
    punch_m = create_montage_from_sequence("/Game/RamsterZ_FreeAnims_Volume1/AnimationSequence/H2H/H2H_PunchCombo01", "AM_UnarmedPunch", montages_dir)
    kick_m = create_montage_from_sequence("/Game/RamsterZ_FreeAnims_Volume1/AnimationSequence/H2H/H2H_Kick01", "AM_UnarmedKick", montages_dir)

    char_bp = create_blueprint("BP_CarnivalPlayerCharacter", "/Game/Carnival/Character/Blueprints", "/Script/CarnivalGame.CarnivalPlayerCharacter")
    if char_bp:
        char_cdo = unreal.get_default_object(char_bp.generated_class())
        if char_cdo:
            char_cdo.set_editor_property("walk_speed", 200.0)
            char_cdo.set_editor_property("jog_speed", 450.0)
            char_cdo.set_editor_property("sprint_speed", 750.0)
            char_cdo.set_editor_property("crouch_speed", 220.0)
            char_cdo.set_editor_property("prone_speed", 120.0)
            char_cdo.set_editor_property("swim_speed", 300.0)

            # Assign montages
            if vault_m: char_cdo.set_editor_property("vault_montage", vault_m)
            if mantle1m_m: char_cdo.set_editor_property("mantle1m_montage", mantle1m_m)
            if mantle2m_m: char_cdo.set_editor_property("mantle2m_montage", mantle2m_m)
            if roll_m: char_cdo.set_editor_property("landing_roll_montage", roll_m)
            if stand_to_prone_m: char_cdo.set_editor_property("stand_to_prone_montage", stand_to_prone_m)
            if prone_to_stand_m: char_cdo.set_editor_property("prone_to_stand_montage", prone_to_stand_m)
            if punch_m: char_cdo.set_editor_property("unarmed_punch_montage", punch_m)
            if kick_m: char_cdo.set_editor_property("unarmed_kick_montage", kick_m)

            # Default sword class
            sword_class = unreal.load_class(None, "/Game/Carnival/Weapons/BP_CarnivalSword.BP_CarnivalSword_C")
            if sword_class:
                char_cdo.set_editor_property("default_sword_class", sword_class)

            # Assign Manny mesh
            manny_mesh = unreal.load_asset("/Game/FreeAnimationLibrary/Demo/Characters/Mannequins/Meshes/SKM_Manny_Simple")
            for h in sds.k2_gather_subobject_data_for_blueprint(char_bp):
                obj = sdfl.get_associated_object(sdfl.get_data(h))
                if obj and "SkeletalMeshComponent" in obj.get_class().get_name() and manny_mesh:
                    obj.set_editor_property("skeletal_mesh", manny_mesh)
                    obj.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, -96.0))
                    obj.set_editor_property("relative_rotation", unreal.Rotator(0.0, -90.0, 0.0))
                    log("Assigned SKM_Manny_Simple to BP_CarnivalPlayerCharacter")

        eal.save_asset("/Game/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter")
        log("Saved BP_CarnivalPlayerCharacter")

def setup_gamemode_and_controller():
    ensure_dir("/Game/Carnival/Blueprints")
    
    # 1. Player Controller
    pc_bp = create_blueprint("BP_CarnivalPlayerController", "/Game/Carnival/Blueprints", "/Script/CarnivalGame.CarnivalPlayerController")
    if pc_bp:
        eal.save_asset("/Game/Carnival/Blueprints/BP_CarnivalPlayerController")
        log("Saved BP_CarnivalPlayerController")

    # 2. Game Mode
    gm_bp = create_blueprint("BP_CarnivalGameMode", "/Game/Carnival/Blueprints", "/Script/CarnivalGame.CarnivalGameMode")
    if gm_bp:
        gm_cdo = unreal.get_default_object(gm_bp.generated_class())
        if gm_cdo:
            char_class = unreal.load_class(None, "/Game/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter.BP_CarnivalPlayerCharacter_C")
            pc_class = unreal.load_class(None, "/Game/Carnival/Blueprints/BP_CarnivalPlayerController.BP_CarnivalPlayerController_C")
            if char_class:
                gm_cdo.set_editor_property("default_pawn_class", char_class)
                log("Set BP_CarnivalGameMode DefaultPawnClass -> BP_CarnivalPlayerCharacter")
            if pc_class:
                gm_cdo.set_editor_property("player_controller_class", pc_class)
                log("Set BP_CarnivalGameMode PlayerControllerClass -> BP_CarnivalPlayerController")
        eal.save_asset("/Game/Carnival/Blueprints/BP_CarnivalGameMode")
        log("Saved BP_CarnivalGameMode")

def main():
    log("Beginning gameplay assets generation...")
    setup_weapons()
    setup_motorcycle()
    setup_player_character()
    setup_gamemode_and_controller()
    log("Gameplay assets generation complete!")

main()

