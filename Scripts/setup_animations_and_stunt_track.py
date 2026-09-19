"""Import motorcycle animations, create and assign AnimMontages to BP_CarnivalPlayerCharacter,
and strategically place a stunt course with ramps, jumps, and drift slaloms in LV_Carnival.

Run headlessly:
    UnrealEditor-Cmd.exe "CarnivalGame.uproject" -unattended -nullrhi -nosplash
        -ExecutePythonScript="F:\Carnival\Scripts\setup_animations_and_stunt_track.py" -ExecCmds="quit"
"""
import unreal

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
eal = unreal.EditorAssetLibrary

def log(msg):
    unreal.log_warning("STUNT_AND_ANIM_SETUP: " + str(msg))

def ensure_dir(path):
    if not eal.does_directory_exist(path):
        eal.make_directory(path)

def import_fbx_anim(fbx_file_path, anim_name, destination_path, skeleton):
    full_path = f"{destination_path}/{anim_name}"
    if eal.does_asset_exist(full_path):
        return unreal.load_asset(full_path)

    task = unreal.AssetImportTask()
    task.filename = fbx_file_path
    task.destination_path = destination_path
    task.destination_name = anim_name
    task.replace_existing = True
    task.automated = True
    task.save = True

    fbx_ui = unreal.FbxImportUI()
    fbx_ui.import_animations = True
    fbx_ui.import_mesh = False
    fbx_ui.skeleton = skeleton
    fbx_ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_ANIMATION
    task.options = fbx_ui

    asset_tools.import_asset_tasks([task])
    imported = unreal.load_asset(full_path)
    if imported:
        log(f"Imported AnimSequence: {full_path}")
    return imported

def create_montage(anim_seq, montage_name, destination_path, skeleton):
    if not anim_seq:
        return None
    full_path = f"{destination_path}/{montage_name}"
    if eal.does_asset_exist(full_path):
        return unreal.load_asset(full_path)

    factory = unreal.AnimMontageFactory()
    factory.set_editor_property("source_animation", anim_seq)
    factory.set_editor_property("target_skeleton", skeleton)

    montage = asset_tools.create_asset(montage_name, destination_path, unreal.AnimMontage, factory)
    if montage:
        eal.save_asset(full_path)
        log(f"Created AnimMontage: {full_path}")
    return montage

def setup_animations():
    skeleton = unreal.load_asset("/Game/FreeAnimationLibrary/Demo/Characters/Mannequins/Meshes/SK_Mannequin")
    if not skeleton:
        log("ERROR: SK_Mannequin not found!")
        return

    anim_dest = "/Game/Carnival/Vehicles/Motorcycle/Animations"
    montage_dest = "/Game/Carnival/Character/Animations"
    ensure_dir(anim_dest)
    ensure_dir(montage_dest)

    base_fbx = "F:/Carnival/Assets/Motorcycle Animations/Motorcyc8536e49c7f27V4/MotoInteractionAnims/Animations"

    moto_anims_to_import = [
        ("Mounted/Mount/AS_Mount_Left.fbx", "AS_Mount_Left"),
        ("Mounted/Mount/AS_Mount_Right.fbx", "AS_Mount_Right"),
        ("Mounted/Dismount/AS_Dismount_Left.fbx", "AS_Dismount_Left"),
        ("Mounted/Dismount/AS_Dismount_Right.fbx", "AS_Dismount_Right"),
        ("Mounted/Idle/AS_Idle_Riding.fbx", "AS_Idle_Riding"),
        ("Mounted/Transitions/AS_Mounted_to_Ride.fbx", "AS_Mounted_to_Ride"),
        ("Mounted/Transitions/AS_Ride_to_Mounted.fbx", "AS_Ride_to_Mounted"),
        ("Riding/Turn_V1/AS_Turn_V1_Left_Loop.fbx", "AS_Turn_V1_Left_Loop"),
        ("Riding/Turn_V1/AS_Turn_V1_Right_Loop.fbx", "AS_Turn_V1_Right_Loop"),
        ("Combat/Punch/AS_Punch_Left.fbx", "AS_Punch_Left"),
        ("Combat/Punch/AS_Punch_Right.fbx", "AS_Punch_Right"),
        ("Combat/Pistol/AS_Pistol_Shoot_Right.fbx", "AS_Pistol_Shoot_Right"),
    ]

    imported_moto = {}
    for rel_path, anim_name in moto_anims_to_import:
        full_fbx = f"{base_fbx}/{rel_path}"
        seq = import_fbx_anim(full_fbx, anim_name, anim_dest, skeleton)
        imported_moto[anim_name] = seq

    # Create Montages
    # 1. Motorcycle Montages
    am_mount_l = create_montage(imported_moto.get("AS_Mount_Left"), "AM_Mount_Left", montage_dest, skeleton)
    am_mount_r = create_montage(imported_moto.get("AS_Mount_Right"), "AM_Mount_Right", montage_dest, skeleton)
    am_dismount_l = create_montage(imported_moto.get("AS_Dismount_Left"), "AM_Dismount_Left", montage_dest, skeleton)
    am_dismount_r = create_montage(imported_moto.get("AS_Dismount_Right"), "AM_Dismount_Right", montage_dest, skeleton)
    am_riding_idle = create_montage(imported_moto.get("AS_Idle_Riding"), "AM_Riding_Idle", montage_dest, skeleton)
    am_punch_l = create_montage(imported_moto.get("AS_Punch_Left"), "AM_Mounted_Punch_Left", montage_dest, skeleton)
    am_punch_r = create_montage(imported_moto.get("AS_Punch_Right"), "AM_Mounted_Punch_Right", montage_dest, skeleton)
    am_shoot = create_montage(imported_moto.get("AS_Pistol_Shoot_Right"), "AM_Mounted_Shoot", montage_dest, skeleton)

    # 2. Locomotion Montages from FreeAnimationLibrary
    seq_vault = unreal.load_asset("/Game/FreeAnimationLibrary/Animations/Vault/anim_Vault")
    seq_m1 = unreal.load_asset("/Game/FreeAnimationLibrary/Animations/Mantle/anim_Mantle_1M_R")
    seq_m2 = unreal.load_asset("/Game/FreeAnimationLibrary/Animations/Mantle/anim_Mantle_2M_R")
    seq_roll = unreal.load_asset("/Game/FreeAnimationLibrary/Animations/LandingRoll/anim_LandRoll_R")
    seq_s2p = unreal.load_asset("/Game/FreeAnimationLibrary/Animations/UnarmedProne/anim_Stand_To_Prone")
    seq_p2s = unreal.load_asset("/Game/FreeAnimationLibrary/Animations/UnarmedProne/anim_Prone_To_Stand")
    seq_punch = unreal.load_asset("/Game/FreeAnimationLibrary/Animations/Counter-Finisher/anim_Counter_Attack_01")
    seq_kick = unreal.load_asset("/Game/FreeAnimationLibrary/Animations/Counter-Finisher/anim_Counter_Attack_08")

    am_vault = create_montage(seq_vault, "AM_Vault", montage_dest, skeleton)
    am_m1 = create_montage(seq_m1, "AM_Mantle_1M", montage_dest, skeleton)
    am_m2 = create_montage(seq_m2, "AM_Mantle_2M", montage_dest, skeleton)
    am_roll = create_montage(seq_roll, "AM_LandingRoll", montage_dest, skeleton)
    am_s2p = create_montage(seq_s2p, "AM_StandToProne", montage_dest, skeleton)
    am_p2s = create_montage(seq_p2s, "AM_ProneToStand", montage_dest, skeleton)
    am_punch = create_montage(seq_punch, "AM_UnarmedPunch", montage_dest, skeleton)
    am_kick = create_montage(seq_kick, "AM_UnarmedKick", montage_dest, skeleton)

    # Assign all montages to BP_CarnivalPlayerCharacter CDO
    char_bp = unreal.load_asset("/Game/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter")
    if char_bp:
        cdo = unreal.get_default_object(char_bp.generated_class())
        if cdo:
            cdo.set_editor_property("vault_montage", am_vault)
            cdo.set_editor_property("mantle1m_montage", am_m1)
            cdo.set_editor_property("mantle2m_montage", am_m2)
            cdo.set_editor_property("landing_roll_montage", am_roll)
            cdo.set_editor_property("stand_to_prone_montage", am_s2p)
            cdo.set_editor_property("prone_to_stand_montage", am_p2s)
            cdo.set_editor_property("mount_left_montage", am_mount_l)
            cdo.set_editor_property("mount_right_montage", am_mount_r)
            cdo.set_editor_property("dismount_left_montage", am_dismount_l)
            cdo.set_editor_property("dismount_right_montage", am_dismount_r)
            cdo.set_editor_property("riding_idle_montage", am_riding_idle)
            cdo.set_editor_property("mounted_punch_left_montage", am_punch_l)
            cdo.set_editor_property("mounted_punch_right_montage", am_punch_r)
            cdo.set_editor_property("mounted_shoot_montage", am_shoot)
            cdo.set_editor_property("unarmed_punch_montage", am_punch)
            cdo.set_editor_property("unarmed_kick_montage", am_kick)

            eal.save_asset("/Game/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter")
            log("Successfully assigned all 16 Montages to BP_CarnivalPlayerCharacter!")

def spawn_stunt_piece(eas, mesh_path, label, location, rotation, scale=unreal.Vector(1, 1, 1)):
    mesh = unreal.load_asset(mesh_path)
    if not mesh:
        return None
    actor = eas.spawn_actor_from_class(unreal.StaticMeshActor, location, rotation)
    if actor:
        actor.set_actor_label(label)
        actor.static_mesh_component.set_static_mesh(mesh)
        actor.set_actor_scale3d(scale)
        actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        actor.static_mesh_component.set_collision_profile_name("BlockAll")
    return actor

def setup_stunt_track():
    level_path = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
    world = unreal.EditorLoadingAndSavingUtils.load_map(level_path)
    if not world:
        log("Failed to load LV_Carnival!")
        return

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    # Clean up any existing stunt course actors
    for a in eas.get_all_level_actors():
        if a.get_actor_label().startswith("Stunt_"):
            eas.destroy_actor(a)

    stair_mesh = "/Game/Medieval_Castle/CastleKit/Props/Meshes/ModularBuildings/SM_WoodPlatformStair_01a"
    platform_mesh = "/Game/Medieval_Castle/CastleKit/Props/Meshes/ModularBuildings/SM_WoodPlatformFloor_01b"
    pillar_mesh = "/Game/Medieval_Castle/CastleKit/CastleKit/Walls_Stone/SM_Castle_Stone_Pillar_01a_NN"
    if not eal.does_asset_exist(pillar_mesh):
        pillar_mesh = "/Game/Medieval_Castle/CastleKit/Walls_Stone/SM_Castle_Stone_Pillar_01a_NN"
    wall_mesh = "/Game/Medieval_Castle/CastleKit/Props/Meshes/Rock_Stone_Wall/SM_RockStoneWall_01a"
    arch_mesh = "/Game/Medieval_Castle/CastleKit/Walls_Stone/SM_Castle_Stone_Arch_01a_NN"

    # SECTION 1: Launch Jump 1 (Near Motorcycle Spawn at -6400, -7596)
    # Heading 50 degrees toward carnival entrance
    spawn_stunt_piece(eas, stair_mesh, "Stunt_Jump1_Ramp", 
                      unreal.Vector(-6000, -7100, 190), unreal.Rotator(0, 50, 0), unreal.Vector(2.0, 2.0, 1.5))
    spawn_stunt_piece(eas, stair_mesh, "Stunt_Jump1_Landing", 
                      unreal.Vector(-5200, -6400, 190), unreal.Rotator(0, 230, 0), unreal.Vector(2.0, 2.0, 1.5))

    # SECTION 2: Slalom Drift Chicane (Along central path)
    slalom_coords = [
        (-4800, -6100, 105),
        (-4500, -5900, 105),
        (-4200, -6100, 105),
        (-3900, -5900, 105),
        (-3600, -6100, 105)
    ]
    for i, (x, y, z) in enumerate(slalom_coords):
        spawn_stunt_piece(eas, pillar_mesh, f"Stunt_Slalom_Pillar_{i+1}", 
                          unreal.Vector(x, y, z), unreal.Rotator(0, 0, 0), unreal.Vector(1.5, 1.5, 1.5))

    # SECTION 3: The Elevated Skyway Bridge & Mega-Leap
    # Ramp up to skyway
    spawn_stunt_piece(eas, stair_mesh, "Stunt_Skyway_RampUp", 
                      unreal.Vector(-5000, -5300, 110), unreal.Rotator(0, 30, 0), unreal.Vector(2.0, 2.0, 1.8))
    
    # 4 skyway platform sections
    for i in range(4):
        offset_x = -4700 + (i * 350)
        offset_y = -5100 + (i * 200)
        spawn_stunt_piece(eas, platform_mesh, f"Stunt_Skyway_Floor_{i+1}", 
                          unreal.Vector(offset_x, offset_y, 470), unreal.Rotator(0, 30, 0), unreal.Vector(2.5, 2.5, 1.0))

    # Mega-Jump Ramp at end of skyway
    spawn_stunt_piece(eas, stair_mesh, "Stunt_MegaJump_Ramp", 
                      unreal.Vector(-3300, -4300, 470), unreal.Rotator(0, 30, 0), unreal.Vector(2.5, 2.5, 2.0))
    
    # Mega-Jump Landing Ramp across the plaza gap
    spawn_stunt_piece(eas, stair_mesh, "Stunt_MegaJump_Landing", 
                      unreal.Vector(-2400, -3800, 110), unreal.Rotator(0, 210, 0), unreal.Vector(3.0, 3.0, 2.0))

    # SECTION 4: High-Speed Wallride & Drift Bowl Curve
    bowl_angles = [0, 30, 60, 90, 120, 150]
    for i, ang in enumerate(bowl_angles):
        rad = ang * 3.14159 / 180.0
        bx = -2000 + 800 * unreal.MathLibrary.cos(rad)
        by = -3200 + 800 * unreal.MathLibrary.sin(rad)
        spawn_stunt_piece(eas, wall_mesh, f"Stunt_DriftWall_{i+1}", 
                          unreal.Vector(bx, by, 110), unreal.Rotator(0, ang + 90, 0), unreal.Vector(2.0, 2.0, 2.0))

    unreal.EditorLoadingAndSavingUtils.save_current_level()
    log("Successfully strategically placed full motorcycle stunt course & race track in LV_Carnival and saved level!")

def main():
    setup_animations()
    setup_stunt_track()
    log("ALL ANIMATIONS AND STUNT COURSE SETUP COMPLETE!")

main()

