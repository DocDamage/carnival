"""Place drivable boats, hovercrafts, and 12+ new themed interactive activities across all 7 maps.

Run headlessly:
    UnrealEditor-Cmd.exe "CarnivalGame.uproject" -unattended -nullrhi -nosplash
        -ExecutePythonScript="F:\Carnival\Scripts\setup_expanded_world_activities.py" -ExecCmds="quit"
"""
import unreal

eal = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def log(msg):
    unreal.log_warning("EXPANDED_ACTIVITIES: " + str(msg))

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

def spawn_boat(name, loc, rot=unreal.Rotator(0, 0, 0), mesh_path="/Game/LightHouse_Meshingun/Meshes/Props/Boat_Trailer/SM_Prop_Speed_Boat"):
    boat = eas.spawn_actor_from_class(unreal.CarnivalBoat, loc, rot)
    if boat:
        boat.set_actor_label(name)
        if mesh_path and eal.does_asset_exist(mesh_path):
            m = unreal.load_asset(mesh_path)
            if m:
                mesh_comp = boat.get_editor_property("boat_mesh")
                if mesh_comp:
                    mesh_comp.set_static_mesh(m)
        log(f"Spawned Boat: {name} at {loc}")
    return boat

def spawn_hovercraft(name, loc, rot=unreal.Rotator(0, 0, 0), mesh_path="/Game/Mars_Futuristic_Cars/Static_Meshes/SM_rover4_SM"):
    hover = eas.spawn_actor_from_class(unreal.CarnivalHovercraft, loc, rot)
    if hover:
        hover.set_actor_label(name)
        if mesh_path and eal.does_asset_exist(mesh_path):
            m = unreal.load_asset(mesh_path)
            if m:
                mesh_comp = hover.get_editor_property("craft_mesh")
                if mesh_comp:
                    mesh_comp.set_static_mesh(m)
        log(f"Spawned Hovercraft: {name} at {loc}")
    return hover

# ==============================================================================
# 1. LIGHTHOUSE (LV_LightHouse) - Drivable Boats & Coastal Activities
# ==============================================================================
def setup_lighthouse():
    path = "/Game/LightHouse_Meshingun/Map/LV_LightHouse"
    w = unreal.EditorLoadingAndSavingUtils.load_map(path)
    if not w: return

    # Clean old extra boats / activities
    for a in eas.get_all_level_actors():
        lbl = a.get_actor_label()
        if lbl.startswith("Boat_") or lbl in ["Activity_OceanSpeedboatSlalom", "Activity_LighthouseKeeperTargetRange"] or lbl.startswith("Target_Ocean_"):
            eas.destroy_actor(a)

    # 1. Spawn Drivable Speed Boat
    speed_boat_mesh = "/Game/LightHouse_Meshingun/Meshes/Props/Boat_Trailer/SM_Prop_Speed_Boat"
    spawn_boat("Boat_SpeedBoat_Alpha", unreal.Vector(300, 1900, 15), unreal.Rotator(0, 45, 0), speed_boat_mesh)

    # 2. Spawn Drivable Inflatable Zodiac Boat
    inflatable_mesh = "/Game/LightHouse_Meshingun/Meshes/Props/Boat_Trailer/SM_Prop_Inflatable_Boat"
    spawn_boat("Boat_Inflatable_Beta", unreal.Vector(750, 2100, 15), unreal.Rotator(0, 30, 0), inflatable_mesh)

    # 3. Activity: Ocean Speedboat Slalom
    boat_cps = [
        (unreal.Vector(800, 3200, 20), 600.0, "Ocean Buoy 1 (Coastal Shallows)"),
        (unreal.Vector(1800, 4800, 20), 600.0, "Ocean Buoy 2 (Sea Stack Gate)"),
        (unreal.Vector(3200, 3900, 20), 600.0, "Ocean Buoy 3 (Outer Reef Turn)"),
        (unreal.Vector(2500, 1800, 20), 600.0, "Ocean Buoy 4 (Rocky Archway Pass)"),
        (unreal.Vector(1200, 800, 20), 600.0, "Ocean Buoy 5 (Lighthouse Cliffside)"),
        (unreal.Vector(400, 1700, 20), 600.0, "Finish Line (Harbor Beach)")
    ]
    spawn_activity("Activity_OceanSpeedboatSlalom", unreal.Vector(350, 1750, 25),
                   unreal.CarnivalChallengeType.STUNT_RALLY,
                   "Pilot the Speed Boat through all 6 ocean buoy gates around the rocky reefs!",
                   80.0, 35.0, 52.0, 75.0, boat_cps, target_score=600)

    # 4. Activity: Lighthouse Keeper Target Range
    act_sniper = spawn_activity("Activity_LighthouseKeeperTargetRange", unreal.Vector(850, 1200, 1520),
                                unreal.CarnivalChallengeType.TARGET_SHOOTING,
                                "Equip Revolver [2] and snipe the 5 offshore floating barrel targets!",
                                50.0, 18.0, 30.0, 45.0, target_score=500)
    barrel_targets = []
    target_locs = [
        unreal.Vector(1200, 2200, 25),
        unreal.Vector(1600, 1500, 25),
        unreal.Vector(2100, 1100, 25),
        unreal.Vector(900, 2800, 25),
        unreal.Vector(500, 2400, 25)
    ]
    for i, tloc in enumerate(target_locs):
        t = spawn_target(tloc, point_val=100, is_relic=False, parent_activity=act_sniper)
        if t:
            t.set_actor_label(f"Target_Ocean_{i+1}")
            barrel_targets.append(t)
    if act_sniper:
        act_sniper.set_editor_property("targets", barrel_targets)

    unreal.EditorLoadingAndSavingUtils.save_current_level()
    log("Saved Lighthouse boats and activities!")

# ==============================================================================
# 2. MARS OUTPOST (Playmap) - Drivable Hovercraft & Canyon Activities
# ==============================================================================
def setup_mars():
    path = "/Game/Mars_Futuristic_Cars/Maps/Playmap"
    w = unreal.EditorLoadingAndSavingUtils.load_map(path)
    if not w: return

    for a in eas.get_all_level_actors():
        lbl = a.get_actor_label()
        if lbl.startswith("Hovercraft_") or lbl in ["Activity_HoverCanyonSpeedRun", "Activity_AlienSpecimenHunt"] or lbl.startswith("Relic_Martian_"):
            eas.destroy_actor(a)

    # 1. Spawn Drivable Sci-Fi Hovercraft
    hover_mesh = "/Game/Mars_Futuristic_Cars/Static_Meshes/SM_rover4_SM"
    spawn_hovercraft("Hovercraft_Mars_Alpha", unreal.Vector(150, 300, 180), unreal.Rotator(0, 0, 0), hover_mesh)

    # 2. Activity: Hovercraft Canyon Speed Run
    hover_cps = [
        (unreal.Vector(800, 800, 190), 600.0, "Canyon Entrance Gate"),
        (unreal.Vector(2100, 1800, 260), 600.0, "Red Dune Ridge Leap"),
        (unreal.Vector(3600, 2600, 240), 600.0, "Alien Crater Rim Slalom"),
        (unreal.Vector(4500, 1600, 190), 600.0, "Colony Power Station"),
        (unreal.Vector(5200, 400, 220), 600.0, "Outpost Hangar Finish")
    ]
    spawn_activity("Activity_HoverCanyonSpeedRun", unreal.Vector(150, 450, 180),
                   unreal.CarnivalChallengeType.STUNT_RALLY,
                   "Pilot the Sci-Fi Hovercraft at high speed through 5 canyon checkpoint gates!",
                   60.0, 26.0, 40.0, 56.0, hover_cps, target_score=500)

    # 3. Activity: Alien Specimen Hunt
    act_alien = spawn_activity("Activity_AlienSpecimenHunt", unreal.Vector(300, 0, 160),
                               unreal.CarnivalChallengeType.RELIC_HUNT,
                               "Recover the 4 glowing alien crystal specimens scattered across the dunes!",
                               75.0, 30.0, 50.0, 70.0, target_score=400)
    crystal_locs = [
        unreal.Vector(1500, -800, 180),
        unreal.Vector(2800, 400, 210),
        unreal.Vector(3200, -1200, 240),
        unreal.Vector(4200, -400, 190)
    ]
    crystals = []
    for i, cloc in enumerate(crystal_locs):
        r = spawn_target(cloc, point_val=100, is_relic=True, parent_activity=act_alien)
        if r:
            r.set_actor_label(f"Relic_Martian_{i+1}")
            crystals.append(r)
    if act_alien:
        act_alien.set_editor_property("targets", crystals)

    unreal.EditorLoadingAndSavingUtils.save_current_level()
    log("Saved Mars hovercraft and activities!")

# ==============================================================================
# 3. MEDIEVAL CASTLE (Medieval_Castle_Level) - Viking Boat & Castle Activities
# ==============================================================================
def setup_castle():
    path = "/Game/Medieval_Castle/Level/Medieval_Castle_Level"
    w = unreal.EditorLoadingAndSavingUtils.load_map(path)
    if not w: return

    for a in eas.get_all_level_actors():
        lbl = a.get_actor_label()
        if lbl.startswith("Boat_Viking_") or lbl in ["Activity_VikingBoatRiverRaid", "Activity_ArcheryTowerChallenge"] or lbl.startswith("Target_Heraldic_"):
            eas.destroy_actor(a)

    # 1. Spawn Drivable Viking Boat in Castle River / Moat
    viking_mesh = "/Game/Medieval_Castle/CastleKit/Props/Meshes/Props/VikingBoat/SM_VikingBoat_01a"
    spawn_boat("Boat_Viking_01", unreal.Vector(-600, 1200, 30), unreal.Rotator(0, 90, 0), viking_mesh)

    # 2. Activity: Viking Boat River Raid
    viking_cps = [
        (unreal.Vector(-600, 2000, 30), 500.0, "Outer River Bend"),
        (unreal.Vector(-400, 3200, 30), 500.0, "Drawbridge Archway Pass"),
        (unreal.Vector(400, 3800, 30), 500.0, "Castle Water Gate"),
        (unreal.Vector(1200, 3200, 30), 500.0, "Moat Pier Finish")
    ]
    spawn_activity("Activity_VikingBoatRiverRaid", unreal.Vector(-600, 1050, 40),
                   unreal.CarnivalChallengeType.STUNT_RALLY,
                   "Pilot the Viking Boat along the river moat and pass under the drawbridge archways!",
                   60.0, 25.0, 40.0, 55.0, viking_cps, target_score=400)

    # 3. Activity: Archery Tower Challenge
    act_archery = spawn_activity("Activity_ArcheryTowerChallenge", unreal.Vector(0, 300, 120),
                                 unreal.CarnivalChallengeType.TARGET_SHOOTING,
                                 "Equip Revolver [2] and shoot down the 6 heraldic shield targets on high watchtowers!",
                                 50.0, 20.0, 32.0, 46.0, target_score=600)
    tower_locs = [
        unreal.Vector(400, 600, 350),
        unreal.Vector(700, 800, 450),
        unreal.Vector(1100, 500, 520),
        unreal.Vector(1400, 900, 600),
        unreal.Vector(800, 1200, 400),
        unreal.Vector(300, 1100, 320)
    ]
    shields = []
    for i, tloc in enumerate(tower_locs):
        t = spawn_target(tloc, point_val=100, is_relic=False, parent_activity=act_archery)
        if t:
            t.set_actor_label(f"Target_Heraldic_{i+1}")
            shields.append(t)
    if act_archery:
        act_archery.set_editor_property("targets", shields)

    unreal.EditorLoadingAndSavingUtils.save_current_level()
    log("Saved Castle viking boat and activities!")

# ==============================================================================
# 4. CARNIVAL (LV_Carnival) - Ferris Wheel Climb & Balloon Pop
# ==============================================================================
def setup_carnival():
    path = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
    w = unreal.EditorLoadingAndSavingUtils.load_map(path)
    if not w: return

    for a in eas.get_all_level_actors():
        lbl = a.get_actor_label()
        if lbl in ["Activity_FerrisWheelApexClimb", "Activity_MidwayBalloonPop"] or lbl.startswith("Target_Balloon_"):
            eas.destroy_actor(a)

    # 1. Activity: Ferris Wheel Apex Climb
    ferris_cps = [
        (unreal.Vector(-2400, -3200, 250), 300.0, "Climb Base Loading Platform"),
        (unreal.Vector(-2400, -3200, 650), 300.0, "Scale Diagonal Support Girder"),
        (unreal.Vector(-2400, -3200, 1150), 300.0, "Traverse Outer Wheel Strut"),
        (unreal.Vector(-2400, -3200, 1650), 350.0, "Reach the Ferris Wheel Summit Axle!")
    ]
    spawn_activity("Activity_FerrisWheelApexClimb", unreal.Vector(-2400, -3350, 180),
                   unreal.CarnivalChallengeType.PARKOUR_RUSH,
                   "Sprint, vault, and mantle up the Ferris Wheel girders to reach the summit!",
                   60.0, 25.0, 42.0, 58.0, ferris_cps, target_score=400)

    # 2. Activity: Midway Balloon Pop
    act_balloon = spawn_activity("Activity_MidwayBalloonPop", unreal.Vector(-4700, -6400, 110),
                                 unreal.CarnivalChallengeType.TARGET_SHOOTING,
                                 "Equip Revolver [2] and pop 8 floating balloon targets above the prize booths!",
                                 45.0, 16.0, 28.0, 42.0, target_score=800)
    balloons = []
    for i in range(8):
        bx = -4800 + (i * 70)
        by = -6300 + (i % 2 * 40)
        bz = 220 + (i % 3 * 35)
        t = spawn_target(unreal.Vector(bx, by, bz), point_val=100, is_relic=False, parent_activity=act_balloon)
        if t:
            t.set_actor_label(f"Target_Balloon_{i+1}")
            balloons.append(t)
    if act_balloon:
        act_balloon.set_editor_property("targets", balloons)

    unreal.EditorLoadingAndSavingUtils.save_current_level()
    log("Saved Carnival new activities!")

# ==============================================================================
# 5. HAUNTED MANSION (LV_Haunted_Mansion) - Graveyard Trial & Rooftop Mantle
# ==============================================================================
def setup_mansion():
    path = "/Game/Mansion/Levels/LV_Haunted_Mansion"
    w = unreal.EditorLoadingAndSavingUtils.load_map(path)
    if not w: return

    for a in eas.get_all_level_actors():
        lbl = a.get_actor_label()
        if lbl in ["Activity_GraveyardSurvivalTrial", "Activity_MansionRooftopMantle"] or lbl.startswith("Target_Gargoyle_"):
            eas.destroy_actor(a)

    # 1. Activity: Graveyard Survival Trial
    act_grave = spawn_activity("Activity_GraveyardSurvivalTrial", unreal.Vector(-200, 4200, 160),
                               unreal.CarnivalChallengeType.MELEE_TRIAL,
                               "Equip Sword & Shield [1] and destroy the 6 cursed gargoyles in the foggy graveyard!",
                               60.0, 22.0, 38.0, 55.0, target_score=600)
    gargoyle_locs = [
        unreal.Vector(-450, 4400, 160),
        unreal.Vector(-100, 4600, 160),
        unreal.Vector(250, 4350, 160),
        unreal.Vector(400, 4650, 160),
        unreal.Vector(-300, 4800, 180),
        unreal.Vector(150, 4900, 180)
    ]
    gargoyles = []
    for i, gloc in enumerate(gargoyle_locs):
        t = spawn_target(gloc, point_val=100, is_relic=False, parent_activity=act_grave)
        if t:
            t.set_actor_label(f"Target_Gargoyle_{i+1}")
            gargoyles.append(t)
    if act_grave:
        act_grave.set_editor_property("targets", gargoyles)

    # 2. Activity: Mansion Rooftop Mantle
    roof_cps = [
        (unreal.Vector(-1200, 2600, 280), 250.0, "Mantle Gothic Balustrade"),
        (unreal.Vector(-1400, 2100, 520), 250.0, "Scale Sloped Slate Roof"),
        (unreal.Vector(-1100, 1600, 780), 250.0, "Traverse Attic Dormer Ridge"),
        (unreal.Vector(-800, 1200, 1050), 300.0, "Ring the Mansion Spire Bell!")
    ]
    spawn_activity("Activity_MansionRooftopMantle", unreal.Vector(-1050, 2800, 160),
                   unreal.CarnivalChallengeType.PARKOUR_RUSH,
                   "Parkour vault balustrades and mantle roof gables to reach the attic spire!",
                   55.0, 24.0, 38.0, 52.0, roof_cps, target_score=400)

    unreal.EditorLoadingAndSavingUtils.save_current_level()
    log("Saved Mansion new activities!")

# ==============================================================================
# 6. MODULAR TOWN (L_Main_Level) - Motorcycle Slalom & Barn Ledge Loot
# ==============================================================================
def setup_town():
    path = "/Game/Town/Level/L_Main_Level"
    w = unreal.EditorLoadingAndSavingUtils.load_map(path)
    if not w: return

    for a in eas.get_all_level_actors():
        lbl = a.get_actor_label()
        if lbl in ["Activity_TownSquareMotorcycleSlalom", "Activity_BarnLedgeLootRun"] or lbl.startswith("Relic_Coin_"):
            eas.destroy_actor(a)

    # 1. Activity: Town Square Motorcycle Slalom
    town_cps = [
        (unreal.Vector(400, -200, 110), 400.0, "Market Alley Entrance"),
        (unreal.Vector(800, -600, 110), 400.0, "Wagon Chicane Slalom"),
        (unreal.Vector(1400, -400, 110), 400.0, "Cobblestone Plaza Curve"),
        (unreal.Vector(1800, 200, 110), 400.0, "Water Well High-Speed Turn"),
        (unreal.Vector(1200, 800, 110), 400.0, "Town Gate Finish Line")
    ]
    spawn_activity("Activity_TownSquareMotorcycleSlalom", unreal.Vector(100, -100, 110),
                   unreal.CarnivalChallengeType.STUNT_RALLY,
                   "Navigate the motorcycle through market alleys, wagon chicanes, and tight cobblestone turns!",
                   50.0, 20.0, 32.0, 48.0, town_cps, target_score=500)

    # 2. Activity: Barn Ledge Loot Run
    act_loot = spawn_activity("Activity_BarnLedgeLootRun", unreal.Vector(200, 300, 110),
                              unreal.CarnivalChallengeType.RELIC_HUNT,
                              "Discover and collect 3 antique coin pouches hidden high on barn rafters and catwalks!",
                              65.0, 25.0, 42.0, 60.0, target_score=300)
    coin_locs = [
        unreal.Vector(550, 800, 280),
        unreal.Vector(850, 1300, 480),
        unreal.Vector(1150, 1900, 680)
    ]
    coins = []
    for i, cloc in enumerate(coin_locs):
        r = spawn_target(cloc, point_val=100, is_relic=True, parent_activity=act_loot)
        if r:
            r.set_actor_label(f"Relic_Coin_{i+1}")
            coins.append(r)
    if act_loot:
        act_loot.set_editor_property("targets", coins)

    unreal.EditorLoadingAndSavingUtils.save_current_level()
    log("Saved Town new activities!")

# ==============================================================================
# 7. GLADIATOR ARENA (Gladiators_Land) - Chariot Lap & Emperor Audience
# ==============================================================================
def setup_arena():
    path = "/Game/Gladiator_Arena/Maps/Gladiators_Land"
    w = unreal.EditorLoadingAndSavingUtils.load_map(path)
    if not w: return

    for a in eas.get_all_level_actors():
        lbl = a.get_actor_label()
        if lbl in ["Activity_ArenaChariotLapTrial", "Activity_EmperorAudienceRelic"] or lbl.startswith("Relic_Wreath_"):
            eas.destroy_actor(a)

    # 1. Activity: Arena Chariot Lap Trial
    chariot_cps = [
        (unreal.Vector(700, 1500, 720), 450.0, "North Sand Curve"),
        (unreal.Vector(-120, 2300, 720), 450.0, "East Imperial Gate"),
        (unreal.Vector(-950, 1500, 720), 450.0, "South Sand Curve"),
        (unreal.Vector(-120, 700, 720), 450.0, "West Gladiator Tunnel"),
        (unreal.Vector(500, 1500, 720), 450.0, "Colosseum Lap Finish")
    ]
    spawn_activity("Activity_ArenaChariotLapTrial", unreal.Vector(-120, 1300, 720),
                   unreal.CarnivalChallengeType.STUNT_RALLY,
                   "High-speed motorcycle time trial racing around the perimeter of the colosseum sand ring!",
                   45.0, 18.0, 28.0, 42.0, chariot_cps, target_score=500)

    # 2. Activity: Emperor Audience Relic
    emperor_cps = [
        (unreal.Vector(-120, 1500, 720), 300.0, "Arena Sand Floor"),
        (unreal.Vector(-450, 1500, 950), 300.0, "Mantle Imperial Podium Ledge"),
        (unreal.Vector(-750, 1500, 1250), 300.0, "Scale Colosseum Arch Columns"),
        (unreal.Vector(-1050, 1500, 1550), 350.0, "Claim the Emperor's Golden Laurel Wreath!")
    ]
    spawn_activity("Activity_EmperorAudienceRelic", unreal.Vector(-120, 1400, 720),
                   unreal.CarnivalChallengeType.PARKOUR_RUSH,
                   "Parkour leap and mantle up imperial columns to claim the Golden Laurel Wreath!",
                   50.0, 20.0, 32.0, 48.0, emperor_cps, target_score=400)

    unreal.EditorLoadingAndSavingUtils.save_current_level()
    log("Saved Arena new activities!")

def main():
    setup_lighthouse()
    setup_mars()
    setup_castle()
    setup_carnival()
    setup_mansion()
    setup_town()
    setup_arena()
    log("ALL MAPS SUCCESSFULLY UPDATED WITH DRIVABLE VEHICLES AND EXPANDED ACTIVITIES!")

main()

