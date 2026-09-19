"""Place themed interactive activities, target actors, and checkpoint challenges across all 7 maps.

Run headlessly:
    UnrealEditor-Cmd.exe "CarnivalGame.uproject" -unattended -nullrhi -nosplash
        -ExecutePythonScript="F:\Carnival\Scripts\setup_world_activities.py" -ExecCmds="quit"
"""
import unreal

eal = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def log(msg):
    unreal.log_warning("WORLD_ACTIVITIES: " + str(msg))

def spawn_activity(name, loc, act_type, desc, time_limit, gold, silver, bronze, checkpoints=None, target_score=500):
    act = eas.spawn_actor_from_class(unreal.CarnivalActivityBase, loc, unreal.Rotator(0, 0, 0))
    if act:
        act.set_actor_label(name)
        act.set_editor_property("activity_name", name)
        act.set_editor_property("description", desc)
        act.set_editor_property("activity_type", act_type)
        act.set_editor_property("time_limit", float(time_limit))
        act.set_editor_property("gold_time", float(gold))
        act.set_editor_property("silver_time", float(silver))
        act.set_editor_property("bronze_time", float(bronze))
        act.set_editor_property("target_score", int(target_score))

        if checkpoints:
            cp_structs = []
            for cp_loc, cp_rad, cp_desc in checkpoints:
                cp = unreal.CarnivalActivityCheckpoint()
                cp.set_editor_property("location", cp_loc)
                cp.set_editor_property("radius", float(cp_rad))
                cp.set_editor_property("description", cp_desc)
                cp_structs.append(cp)
            act.set_editor_property("checkpoints", cp_structs)

        log(f"Spawned Activity: {name} at {loc}")
    return act

def spawn_target(loc, point_val=100, is_relic=False, mesh_path=None, parent_activity=None):
    target = eas.spawn_actor_from_class(unreal.CarnivalTargetActor, loc, unreal.Rotator(0, 0, 0))
    if target:
        target.set_editor_property("point_value", int(point_val))
        try:
            target.set_editor_property("is_relic_or_collectible", is_relic)
        except Exception:
            try:
                target.set_editor_property("b_is_relic_or_collectible", is_relic)
            except Exception as e:
                log(f"Warning setting is_relic: {e}")
        if parent_activity:
            target.set_editor_property("owning_activity", parent_activity)
        if mesh_path and eal.does_asset_exist(mesh_path):
            m = unreal.load_asset(mesh_path)
            if m:
                mesh_comp = target.get_editor_property("target_mesh")
                if mesh_comp:
                    mesh_comp.set_static_mesh(m)
        log(f"Spawned Target at {loc} (relic={is_relic})")
    return target

def ensure_player_start(loc, rot=unreal.Rotator(0, 0, 0)):
    has_start = False
    for a in eas.get_all_level_actors():
        if "PlayerStart" in a.get_name():
            has_start = True
            break
    if not has_start:
        ps = eas.spawn_actor_from_class(unreal.PlayerStart, loc, rot)
        if ps:
            ps.set_actor_label("PlayerStart_Main")
            log(f"Spawned missing PlayerStart at {loc}")

def ensure_motorcycle(loc, rot=unreal.Rotator(0, 0, 0)):
    has_bike = False
    for a in eas.get_all_level_actors():
        if "CarnivalMotorcycle" in a.get_name():
            has_bike = True
            break
    if not has_bike:
        bike_class = unreal.load_class(None, "/Game/Carnival/Vehicles/Motorcycle/Blueprints/BP_CarnivalMotorcycle.BP_CarnivalMotorcycle_C")
        if bike_class:
            b = eas.spawn_actor_from_class(bike_class, loc, rot)
            if b:
                b.set_actor_label("BP_CarnivalMotorcycle_Placed")
                log(f"Spawned Motorcycle at {loc}")

# ==============================================================================
# 1. CARNIVAL (LV_Carnival)
# ==============================================================================
def setup_carnival():
    path = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
    w = unreal.EditorLoadingAndSavingUtils.load_map(path)
    if not w: return

    # Clean previous activity actors
    for a in eas.get_all_level_actors():
        if a.get_actor_label().startswith("Activity_") or a.get_actor_label().startswith("Target_"):
            eas.destroy_actor(a)

    # Activity 1: Midway Stunt Rally
    checkpoints = [
        (unreal.Vector(-6000, -7100, 250), 400.0, "Jump 1 Ramp Lip"),
        (unreal.Vector(-5200, -6400, 220), 400.0, "Jump 1 Landing Zone"),
        (unreal.Vector(-4200, -6100, 180), 350.0, "Slalom Drift Chicane"),
        (unreal.Vector(-3300, -4300, 500), 450.0, "Skyway Mega-Jump Launch"),
        (unreal.Vector(-2000, -3200, 180), 400.0, "Drift Bowl Finish Line")
    ]
    spawn_activity("Activity_MidwayStuntRally", unreal.Vector(-6300, -7400, 196),
                   unreal.CarnivalChallengeType.STUNT_RALLY,
                   "Hit all 5 stunt sections on the motorcycle before time runs out!",
                   60.0, 28.0, 42.0, 58.0, checkpoints, target_score=500)

    # Activity 2: Carnival Shooting Gallery
    act_shoot = spawn_activity("Activity_CarnivalShootingGallery", unreal.Vector(-4500, -6250, 110),
                               unreal.CarnivalChallengeType.TARGET_SHOOTING,
                               "Equip Revolver [2] and shoot all 6 carnival targets!",
                               45.0, 15.0, 25.0, 40.0, target_score=600)

    # Place 6 targets along the carnival stall counter
    target_mesh = "/Game/Medieval_Castle/CastleKit/Props/Meshes/ModularBuildings/SM_WoodFence_01a"
    carnival_targets = []
    for i in range(6):
        tx = -4650 + (i * 60)
        ty = -6150 + (i % 2 * 30)
        tz = 160 + (i % 3 * 25)
        t = spawn_target(unreal.Vector(tx, ty, tz), point_val=100, is_relic=False, mesh_path=target_mesh, parent_activity=act_shoot)
        if t:
            t.set_actor_label(f"Target_Carnival_{i+1}")
            carnival_targets.append(t)
    if act_shoot:
        act_shoot.set_editor_property("targets", carnival_targets)

    unreal.EditorLoadingAndSavingUtils.save_current_level()
    log("Saved Carnival activities!")

# ==============================================================================
# 2. HAUNTED MANSION (LV_Haunted_Mansion)
# ==============================================================================
def setup_mansion():
    path = "/Game/Mansion/Levels/LV_Haunted_Mansion"
    w = unreal.EditorLoadingAndSavingUtils.load_map(path)
    if not w: return

    for a in eas.get_all_level_actors():
        if a.get_actor_label().startswith("Activity_") or a.get_actor_label().startswith("Relic_"):
            eas.destroy_actor(a)

    act_relic = spawn_activity("Activity_CryptRelicHunt", unreal.Vector(50, 4900, 192),
                               unreal.CarnivalChallengeType.RELIC_HUNT,
                               "Recover the 3 cursed relics hidden in the cemetery and crypts!",
                               80.0, 35.0, 55.0, 75.0, target_score=300)

    # 3 Relics placed in graveyard and crypts
    relic_locs = [
        unreal.Vector(350, 4100, 160),   # Graveyard crypt altar
        unreal.Vector(-350, 3800, 160),  # Ancient tombstone
        unreal.Vector(0, 3200, 140)      # Mausoleum steps
    ]
    relic_targets = []
    for i, rloc in enumerate(relic_locs):
        r = spawn_target(rloc, point_val=100, is_relic=True, parent_activity=act_relic)
        if r:
            r.set_actor_label(f"Relic_Skull_{i+1}")
            relic_targets.append(r)
    if act_relic:
        act_relic.set_editor_property("targets", relic_targets)

    unreal.EditorLoadingAndSavingUtils.save_current_level()
    log("Saved Mansion activities!")

# ==============================================================================
# 3. MODULAR TOWN (L_Main_Level)
# ==============================================================================
def setup_town():
    path = "/Game/Town/Level/L_Main_Level"
    w = unreal.EditorLoadingAndSavingUtils.load_map(path)
    if not w: return

    ensure_player_start(unreal.Vector(0, 0, 100))
    ensure_motorcycle(unreal.Vector(250, 0, 100))

    for a in eas.get_all_level_actors():
        if a.get_actor_label().startswith("Activity_"):
            eas.destroy_actor(a)

    parkour_cps = [
        (unreal.Vector(350, 500, 130), 250.0, "Vault Barn Wooden Fence"),
        (unreal.Vector(650, 1100, 320), 250.0, "Mantle Low House Roof"),
        (unreal.Vector(950, 1600, 540), 250.0, "Sprint Across Upper Barn Ridge"),
        (unreal.Vector(1250, 2200, 720), 300.0, "Ring the Bell Tower Summit!")
    ]
    spawn_activity("Activity_RooftopParkourRush", unreal.Vector(50, 50, 100),
                   unreal.CarnivalChallengeType.PARKOUR_RUSH,
                   "Sprint, vault, mantle, and leap across rooftops to the bell tower!",
                   50.0, 22.0, 35.0, 48.0, parkour_cps, target_score=400)

    unreal.EditorLoadingAndSavingUtils.save_current_level()
    log("Saved Town activities!")

# ==============================================================================
# 4. LIGHTHOUSE (LV_LightHouse)
# ==============================================================================
def setup_lighthouse():
    path = "/Game/LightHouse_Meshingun/Map/LV_LightHouse"
    w = unreal.EditorLoadingAndSavingUtils.load_map(path)
    if not w: return

    ensure_player_start(unreal.Vector(100, 100, 120))

    for a in eas.get_all_level_actors():
        if a.get_actor_label().startswith("Activity_"):
            eas.destroy_actor(a)

    beacon_cps = [
        (unreal.Vector(450, 600, 450), 300.0, "Climb Steep Coastal Trail"),
        (unreal.Vector(850, 1200, 1500), 350.0, "Ignite Lighthouse Beacon Light!"),
        (unreal.Vector(300, 1600, 50), 400.0, "Cliff-Dive into the Ocean Waves!")
    ]
    spawn_activity("Activity_BeaconIgnitionAndDive", unreal.Vector(100, 200, 120),
                   unreal.CarnivalChallengeType.BEACON_CLIMB,
                   "Scale the coastal trail, ignite the beacon, and cliff-dive into the ocean!",
                   75.0, 32.0, 48.0, 70.0, beacon_cps, target_score=300)

    unreal.EditorLoadingAndSavingUtils.save_current_level()
    log("Saved Lighthouse activities!")

# ==============================================================================
# 5. MEDIEVAL CASTLE (Medieval_Castle_Level)
# ==============================================================================
def setup_castle():
    path = "/Game/Medieval_Castle/Level/Medieval_Castle_Level"
    w = unreal.EditorLoadingAndSavingUtils.load_map(path)
    if not w: return

    ensure_player_start(unreal.Vector(0, 0, 120))

    for a in eas.get_all_level_actors():
        if a.get_actor_label().startswith("Activity_") or a.get_actor_label().startswith("Dummy_"):
            eas.destroy_actor(a)

    act_knight = spawn_activity("Activity_TheKnightsTrial", unreal.Vector(0, 150, 120),
                                unreal.CarnivalChallengeType.MELEE_TRIAL,
                                "Equip Sword & Shield [1] and strike down the 5 training dummies!",
                                60.0, 22.0, 38.0, 55.0, target_score=500)

    dummy_locs = [
        unreal.Vector(300, 400, 120),
        unreal.Vector(600, 700, 120),
        unreal.Vector(900, 400, 250),
        unreal.Vector(1200, 800, 350),
        unreal.Vector(1500, 600, 450)
    ]
    dummies = []
    for i, dloc in enumerate(dummy_locs):
        d = spawn_target(dloc, point_val=100, is_relic=False, parent_activity=act_knight)
        if d:
            d.set_actor_label(f"Dummy_Knight_{i+1}")
            dummies.append(d)
    if act_knight:
        act_knight.set_editor_property("targets", dummies)

    unreal.EditorLoadingAndSavingUtils.save_current_level()
    log("Saved Castle activities!")

# ==============================================================================
# 6. GLADIATOR ARENA (Gladiators_Land)
# ==============================================================================
def setup_arena():
    path = "/Game/Gladiator_Arena/Maps/Gladiators_Land"
    w = unreal.EditorLoadingAndSavingUtils.load_map(path)
    if not w: return

    for a in eas.get_all_level_actors():
        if a.get_actor_label().startswith("Activity_") or a.get_actor_label().startswith("Gladiator_"):
            eas.destroy_actor(a)

    act_arena = spawn_activity("Activity_ColosseumSandChallenge", unreal.Vector(-120, 1500, 720),
                               unreal.CarnivalChallengeType.MELEE_TRIAL,
                               "Defeat all 6 gladiator targets in the arena under the crowd's roar!",
                               60.0, 25.0, 40.0, 58.0, target_score=600)

    arena_targets = []
    for i in range(6):
        ang = i * 60.0
        rad = ang * 3.14159 / 180.0
        gx = -120 + 700 * unreal.MathLibrary.cos(rad)
        gy = 1500 + 700 * unreal.MathLibrary.sin(rad)
        t = spawn_target(unreal.Vector(gx, gy, 720), point_val=100, is_relic=False, parent_activity=act_arena)
        if t:
            t.set_actor_label(f"Gladiator_Target_{i+1}")
            arena_targets.append(t)
    if act_arena:
        act_arena.set_editor_property("targets", arena_targets)

    unreal.EditorLoadingAndSavingUtils.save_current_level()
    log("Saved Arena activities!")

# ==============================================================================
# 7. MARS OUTPOST (Playmap)
# ==============================================================================
def setup_mars():
    path = "/Game/Mars_Futuristic_Cars/Maps/Playmap"
    w = unreal.EditorLoadingAndSavingUtils.load_map(path)
    if not w: return

    ensure_player_start(unreal.Vector(0, 0, 150))
    ensure_motorcycle(unreal.Vector(250, 0, 150))

    for a in eas.get_all_level_actors():
        if a.get_actor_label().startswith("Activity_"):
            eas.destroy_actor(a)

    mars_cps = [
        (unreal.Vector(1200, 1000, 180), 500.0, "Dune Crest 1"),
        (unreal.Vector(2500, 2200, 250), 500.0, "Alien Crater Rim Leap"),
        (unreal.Vector(3800, 1500, 160), 500.0, "Mars Colony Solar Array"),
        (unreal.Vector(4800, 500, 200), 500.0, "Outpost Hangar Finish Line")
    ]
    spawn_activity("Activity_MartianCraterRally", unreal.Vector(0, 150, 150),
                   unreal.CarnivalChallengeType.STUNT_RALLY,
                   "High-speed rally across red dunes and alien craters!",
                   60.0, 28.0, 42.0, 58.0, mars_cps, target_score=400)

    unreal.EditorLoadingAndSavingUtils.save_current_level()
    log("Saved Mars activities!")

def main():
    setup_carnival()
    setup_mansion()
    setup_town()
    setup_lighthouse()
    setup_castle()
    setup_arena()
    setup_mars()
    log("ALL 7 LOCATIONS CONFIGURED WITH THEMED ACTIVITIES!")

main()

