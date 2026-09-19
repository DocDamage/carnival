import unreal

def inspect_assets():
    mesh_paths = [
        "/Game/FreeAnimationLibrary/Demo/Characters/Mannequins/Meshes/SKM_Manny_Simple",
        "/Game/FreeAnimationLibrary/Demo/Characters/Mannequins/Meshes/SK_Mannequin"
    ]
    for p in mesh_paths:
        mesh = unreal.load_asset(p)
        if mesh:
            skel = mesh.get_editor_property("skeleton")
            unreal.log_warning(f"MESH: {p} -> Skeleton: {skel.get_path_name() if skel else 'None'}")
        else:
            unreal.log_warning(f"MESH NOT FOUND: {p}")

    # Inspect some animations in FreeAnimationLibrary
    anim_samples = [
        "/Game/FreeAnimationLibrary/Animations/Walk/anim_Walk_Fwd_Loop_L",
        "/Game/FreeAnimationLibrary/Animations/Jog/anim_Jog_Loop_Left_L",
        "/Game/FreeAnimationLibrary/Animations/Jump/anim_jog_jump_R",
        "/Game/FreeAnimationLibrary/Animations/LandingRoll/anim_LandRoll_R",
        "/Game/FreeAnimationLibrary/Animations/Mantle/anim_Mantle_1M_R",
        "/Game/FreeAnimationLibrary/Animations/Vault/anim_Vault",
        "/Game/FreeAnimationLibrary/Animations/UnarmedProne/anim_Prone_Idle",
        "/Game/FreeAnimationLibrary/Animations/Swim/anim_SwimIdle"
    ]
    for a in anim_samples:
        anim = unreal.load_asset(a)
        if anim:
            skel = anim.get_editor_property("skeleton")
            unreal.log_warning(f"ANIM: {a} -> Skeleton: {skel.get_path_name() if skel else 'None'}")
        else:
            unreal.log_warning(f"ANIM NOT FOUND: {a}")

inspect_assets()

