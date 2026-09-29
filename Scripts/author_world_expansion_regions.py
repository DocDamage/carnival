"""Author project-owned expansion regions and collision-backed connector routes."""
import gc
import json
import math
import traceback
from datetime import datetime
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
LEVEL_DIR = "/Game/Carnival/World/Levels"
REPORT = ROOT / "Saved/WorldExpansion/Region_Authoring.json"
LEVELS = {
    "north_docks": LEVEL_DIR + "/L_CarnivalWorldExpansion_DocksNorth_Layout",
    "prison": LEVEL_DIR + "/L_CarnivalWorldExpansion_Prison",
    "lab_a": LEVEL_DIR + "/L_CarnivalWorldExpansion_LabA",
    "lab_b": LEVEL_DIR + "/L_CarnivalWorldExpansion_LabB",
    "east_docks": LEVEL_DIR + "/L_CarnivalWorldExpansion_DocksEast",
    "sewers": LEVEL_DIR + "/L_CarnivalWorldExpansion_Sewers",
    "atlantis": LEVEL_DIR + "/L_CarnivalWorldExpansion_Atlantis",
    "shipwreck": LEVEL_DIR + "/L_CarnivalWorldExpansion_Shipwreck",
    # The earlier failed pass left an unregistered partial package with the
    # non-Layout name. Use a clean name so Asset Registry state cannot mask it.
    "connectors": LEVEL_DIR + "/L_CarnivalWorldExpansion_Connections_Layout",
}
SOURCES = {
    "prison": "/Game/HAUNTED_PRISON/Levels/L_Overview",
    "lab_a": "/Game/SciFiWorld/Maps/SciFiCreaturesResearchRoomA",
    "lab_b": "/Game/SciFiWorld/Maps/SciFiCreaturesResearchRoomB",
    "sewers": "/Game/Sewer/Levels/L_Sewers_Corridor",
    "shipwreck": "/Game/UnderwaterShip/Levels/UnderwaterShip_Showcase_Exterior",
}

NORTH = (-55000.0, -55000.0, 600.0)
PRISON_GATE = (-30000.0, -25000.0, 600.0)
LAB_DOOR = (-41000.0, -8000.0, 600.0)
EAST = (70000.0, 15000.0, 600.0)
HOSPITAL = (95849.499, 129003.284, 642.781)
SEWER_DOOR = (-27000.0, -12500.0, -1800.0)
ATLANTIS_DOOR = (-19000.0, -11000.0, -1800.0)
SHIPWRECK_DOOR = (-6000.0, -10000.0, -2000.0)
PRISON_STAIR_TOP = (-27000.0, -19000.0, 600.0)

GEOMETRY_GENERATED = "WorldExpansionGenerated"
GLOBAL_CLASSES = {
    "SkyLight", "DirectionalLight", "SkyAtmosphere", "ExponentialHeightFog",
    "VolumetricCloud", "PostProcessVolume", "CameraActor", "CineCameraActor",
    "PlayerStart", "LandscapeGizmoActiveActor",
}
STREAM_ALLOWED_SHIP = ("/ship", "/setdressing_interior", "/setdressing_exterior")
OUTER_CONTROLS = [
    # End of the already tested Mansion driveway in mansion_route_config.py.
    (-69105.9781633031, -84621.55039658632, 598.0),
    (-66000.0, -78000.0, 540.0), (-60000.0, -68000.0, 570.0),
    (-55000.0, -55000.0, 600.0),
    (-50000.0, -46000.0, 600.0), (-43000.0, -38000.0, 600.0),
    (-35000.0, -30000.0, 600.0), PRISON_GATE,
    (-25000.0, -22000.0, 600.0), (-15000.0, -18000.0, 600.0),
    (0.0, -13000.0, 600.0), (20000.0, -6000.0, 600.0),
    (35000.0, 0.0, 600.0), (50000.0, 8000.0, 600.0), EAST,
    (85000.0, 50000.0, 620.0), HOSPITAL,
]
LAB_CONTROLS = [PRISON_GATE, (-35000.0, -20000.0, 600.0), (-39000.0, -12000.0, 600.0), LAB_DOOR]

REPORT_DATA = {"success": False, "levels": [], "errors": [], "warnings": [],
               "connections": [], "started_utc": datetime.utcnow().isoformat() + "Z"}
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EDITOR = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
if not CUBE:
    raise RuntimeError("Unreal basic cube mesh is missing")

DOCK_WOOD = unreal.load_asset("/Game/Docks/VOL2_Powell/Materials/Instances/MI_Wooden_Planks_Beams_01")
DOCK_SAND = unreal.load_asset("/Game/Docks/VOL2_Powell/Materials/Instances/MI_Sand_01a")
DOCK_ROCK = unreal.load_asset("/Game/Docks/VOL2_Powell/Materials/Instances/MI_Rock_29a")
SEWER_CONCRETE = unreal.load_asset("/Game/Sewer/Meshes/Kit_Concrete/Arch/MI_Concrete_Arch")
SEWER_FLOOR = unreal.load_asset("/Game/Sewer/Meshes/Kit_Concrete/Floor/MI_SMI_Sewer_Floor_01a")
SWITCHBOARD = unreal.load_asset("/Game/Carnival/WorldExpansion/IndustrialSwitchboard/SM_IndustrialSwitchboard")


def vec(point):
    return unreal.Vector(float(point[0]), float(point[1]), float(point[2]))


def rot(pitch=0.0, yaw=0.0, roll=0.0):
    return unreal.Rotator(pitch=float(pitch), yaw=float(yaw), roll=float(roll))


def rotate_xy(point, yaw):
    r = math.radians(yaw)
    return (point[0] * math.cos(r) - point[1] * math.sin(r),
            point[0] * math.sin(r) + point[1] * math.cos(r))


def translation_for_anchor(local, target, yaw):
    rx, ry = rotate_xy(local, yaw)
    return (target[0] - rx, target[1] - ry, target[2] - local[2])


def map_file(package):
    return ROOT / ("Content" + package.replace("/Game", "").replace("/", "\\") + ".umap")


def delete_package_if_present(path):
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        if not unreal.EditorAssetLibrary.delete_asset(path):
            raise RuntimeError("Could not replace previous generated map " + path)
    # EditorLevelLibrary.new_level can leave an unregistered blank .umap after
    # an unattended attempt. This is safe here because every call targets a
    # namespaced World Expansion map owned by this script.
    package_file = map_file(path)
    for stale_file in (package_file, package_file.with_suffix(".uexp"), package_file.with_suffix(".ubulk")):
        if stale_file.exists():
            stale_file.unlink()


def load_clone(source, destination, allowed_child_tokens=None):
    delete_package_if_present(destination)
    source_object = unreal.load_asset(source)
    if not source_object:
        raise RuntimeError("Could not load source level " + source)
    pieces = destination.rsplit("/", 1)
    clone = unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset(pieces[1], pieces[0], source_object)
    if not clone:
        raise RuntimeError("Could not duplicate source level " + source)
    if not unreal.EditorAssetLibrary.save_loaded_asset(clone, False):
        raise RuntimeError("Could not save duplicated level " + destination)
    source_object = None
    clone = None
    gc.collect()
    world = unreal.EditorLoadingAndSavingUtils.load_map(destination)
    if not world:
        raise RuntimeError("Could not open duplicated level " + destination)
    dropped_children = []
    if allowed_child_tokens is not None:
        for level in list(unreal.EditorLevelUtils.get_levels(world)):
            package = level.get_path_name().split(":PersistentLevel")[0].split(".")[0]
            if package == destination:
                continue
            lower = package.lower()
            if not any(token in lower for token in allowed_child_tokens):
                if not unreal.EditorLevelUtils.remove_level_from_world(level):
                    raise RuntimeError("Could not remove sample sublevel " + package)
                dropped_children.append(package)
    return world, dropped_children


def actor_label(actor):
    try:
        return actor.get_actor_label()
    except Exception:
        return actor.get_name()


def clean_environment(world, remove_landscape=False, label_substrings=()):
    removed = []
    for actor in list(EAS.get_all_level_actors()):
        kind = actor.get_class().get_name()
        label = actor_label(actor)
        lower = label.lower()
        remove = kind in GLOBAL_CLASSES or kind.startswith("BP_Fog_Cards")
        if remove_landscape and kind == "Landscape":
            remove = True
        if any(term.lower() in lower for term in label_substrings):
            remove = True
        if kind == "InstancedFoliageActor":
            remove = True
        if remove:
            EAS.destroy_actor(actor)
            removed.append({"label": label, "class": kind})
    return removed


def mark_generated(actor, label):
    try:
        actor.set_actor_label(label, True)
    except Exception:
        actor.set_editor_property("actor_label", label)
    tags = list(actor.get_editor_property("tags"))
    name = unreal.Name(GEOMETRY_GENERATED)
    if name not in tags:
        tags.append(name)
    actor.set_editor_property("tags", tags)
    return actor


def set_component_collision(component, profile="BlockAll"):
    try:
        component.set_collision_profile_name(profile)
    except Exception:
        component.set_editor_property("collision_profile_name", profile)
    try:
        component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    except Exception:
        component.set_editor_property("collision_enabled", unreal.CollisionEnabled.QUERY_AND_PHYSICS)


def spawn_mesh(mesh_path, location, rotation=(0, 0, 0), scale=(1, 1, 1),
               label="WorldExpansionAsset", collision_profile="BlockAll", required=True):
    mesh = unreal.load_asset(mesh_path)
    if not mesh:
        if required:
            raise RuntimeError("Required source mesh is missing: " + mesh_path)
        REPORT_DATA["warnings"].append("Optional mesh missing: " + mesh_path)
        return None
    actor = EAS.spawn_actor_from_class(unreal.StaticMeshActor, vec(location), rot(*rotation))
    if not actor:
        raise RuntimeError("Could not spawn mesh actor for " + mesh_path)
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    comp.set_editor_property("static_mesh", mesh)
    set_component_collision(comp, collision_profile)
    actor.set_actor_scale3d(vec(scale))
    return mark_generated(actor, label)


def spawn_box(location, size, material, label, rotation=(0, 0, 0), collision_profile="BlockAll"):
    actor = EAS.spawn_actor_from_class(unreal.StaticMeshActor, vec(location), rot(*rotation))
    if not actor:
        raise RuntimeError("Could not spawn collision box " + label)
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    comp.set_editor_property("static_mesh", CUBE)
    if material:
        comp.set_material(0, material)
    set_component_collision(comp, collision_profile)
    actor.set_actor_scale3d(vec((size[0] / 100.0, size[1] / 100.0, size[2] / 100.0)))
    return mark_generated(actor, label)


def spawn_point_light(location, color, radius, intensity, label):
    actor = EAS.spawn_actor_from_class(unreal.PointLight, vec(location), rot())
    if not actor:
        return None
    comp = actor.get_component_by_class(unreal.PointLightComponent)
    comp.set_editor_property("intensity", float(intensity))
    comp.set_editor_property("attenuation_radius", float(radius))
    comp.set_editor_property("light_color", unreal.Color(int(color[0]), int(color[1]), int(color[2]), 255))
    comp.set_editor_property("cast_shadows", False)
    return mark_generated(actor, label)


def create_new_map(package):
    # Duplicate a small supplied map, then clear its sample actors. This avoids
    # the unattended editor's modal New Level save flow while leaving no
    # demonstration content in the project-owned map.
    world, _ = load_clone("/Game/Docks/VOL2_Powell/Maps/LIGHTING_DAY", package)
    for actor in list(EAS.get_all_level_actors()):
        EAS.destroy_actor(actor)
    return world


def load_existing_map(package, allowed_child_tokens=None):
    world = unreal.EditorLoadingAndSavingUtils.load_map(package)
    if not world:
        raise RuntimeError("Could not reopen existing authored level " + package)
    dropped_children = []
    if allowed_child_tokens is not None:
        for level in list(unreal.EditorLevelUtils.get_levels(world)):
            child_package = level.get_path_name().split(":PersistentLevel")[0].split(".")[0]
            if child_package == package:
                continue
            if not any(token in child_package.lower() for token in allowed_child_tokens):
                if not unreal.EditorLevelUtils.remove_level_from_world(level):
                    raise RuntimeError("Could not remove sample sublevel " + child_package)
                dropped_children.append(child_package)
    return world, dropped_children


def save_authored(world, key, package, metadata=None):
    if not unreal.EditorLoadingAndSavingUtils.save_map(world, package):
        raise RuntimeError("Could not save authored map " + package)
    actors = list(EAS.get_all_level_actors())
    REPORT_DATA["levels"].append({
        "key": key, "package": package, "file": str(map_file(package)),
        "actor_count": len(actors),
        "generated_actor_count": sum(1 for a in actors if unreal.Name(GEOMETRY_GENERATED) in list(a.get_editor_property("tags"))),
        "metadata": metadata or {},
    })
    return len(actors)


def retire_world(*refs):
    for value in refs:
        value = None
    gc.collect()


def add_lamp(location, mesh_label, yaw=0.0):
    bp = unreal.EditorAssetLibrary.load_blueprint_class("/Game/Docks/VOL2_Powell/Blueprints/BP_Lamp_01a")
    if bp:
        actor = EAS.spawn_actor_from_class(bp, vec(location), rot(0, yaw, 0))
        if actor:
            return mark_generated(actor, mesh_label)
    return spawn_mesh("/Game/Docks/VOL2_Powell/Meshes/SM_Lamp", location,
                      (0, yaw, 0), (5, 5, 5), mesh_label, required=False)


def author_docks_north():
    package = LEVELS["north_docks"]
    if map_file(package).exists():
        REPORT_DATA["levels"].append({"key": "north_docks", "package": package,
                                      "file": str(map_file(package)), "verified_existing_file": True})
        return
    world = create_new_map(package)
    # A compact landward arrival bends around a timber quay and two broken piers.
    spawn_box((-2700, 0, -60), (7600, 6200, 100), DOCK_SAND, "NorthDock_Sandy_Arrival")
    spawn_box((-5600, 0, -5), (5200, 1100, 80), DOCK_WOOD, "NorthDock_West_Approach")
    spawn_box((-2000, 3700, 0), (1500, 7200, 70), DOCK_WOOD, "NorthDock_Main_Pier")
    spawn_box((1950, 6900, 0), (8100, 1500, 70), DOCK_WOOD, "NorthDock_Bent_Quay")
    spawn_box((4700, 3500, 0), (1500, 7000, 70), DOCK_WOOD, "NorthDock_Side_Pier")
    spawn_box((-800, 9400, 10), (3800, 1350, 70), DOCK_WOOD, "NorthDock_End_Platform")
    for x, y in [(-2600, 1200), (-2600, 3200), (-2600, 5200),
                 (-1000, 10400), (1000, 10400), (3000, 10400),
                 (4800, 1500), (4800, 3400), (4800, 5400), (4800, 7400)]:
        spawn_mesh("/Game/Docks/VOL2_Powell/Meshes/SM_Pier_Pillar_01a",
                   (x, y, -360), (0, 0, 0), (1, 1, 1), "NorthDock_Pile")
    for x, y in [(-2700, 1400), (-2700, 3100), (-2700, 4800),
                 (4800, 2400), (4800, 4200), (4800, 6100),
                 (-2200, 10200), (700, 10200), (2500, 10200)]:
        add_lamp((x, y, 70), "NorthDock_Lantern", 90)
    spawn_mesh("/Game/Docks/VOL2_Powell/Meshes/SM_Mooring_post_NN_01h",
               (-2450, 7600, 35), (0, 0, 0), (1.2, 1.2, 1.2), "NorthDock_Mooring_Post", required=False)
    spawn_mesh("/Game/Docks/VOL2_Powell/Meshes/SM_Boat_17a",
               (-4700, 7600, -240), (0, 35, 0), (1.0, 1.0, 1.0), "NorthDock_Tied_Skiff", required=False)
    for loc in [(-2400, 2200, 280), (2800, 6900, 260), (4700, 4400, 260)]:
        spawn_point_light(loc, (255, 183, 112), 950, 2200, "NorthDock_LocalLanternLight")
    save_authored(world, "north_docks", package, {
        "layout": "compact L-shaped quay with separate side pier and landward arrival",
        "shared_asset_root": "/Game/Docks/VOL2_Powell",
        "walk_surface_collision": "BlockAll on apron, approach, and deck cubes",
        "local_entry_cm": [0, 0, 0],
    })
    world = None
    retire_world(world)


def author_docks_east():
    package = LEVELS["east_docks"]
    if map_file(package).exists():
        REPORT_DATA["levels"].append({"key": "east_docks", "package": package,
                                      "file": str(map_file(package)), "verified_existing_file": True})
        return
    world = create_new_map(package)
    # A broad, ordered service yard feeds three parallel loading fingers.
    spawn_box((0, 0, -70), (9200, 7400, 100), DOCK_SAND, "EastDock_Quay_Approach")
    spawn_box((0, 3000, 5), (8500, 1700, 80), DOCK_WOOD, "EastDock_Main_Quay")
    for x, y, length in [(-2700, 7200, 7200), (0, 7200, 8400), (2700, 7200, 7200)]:
        spawn_box((x, y + length / 2, 20), (1250, length, 80), DOCK_WOOD, "EastDock_Loading_Finger")
        for py in range(int(y + 400), int(y + length), 1600):
            spawn_mesh("/Game/Docks/VOL2_Powell/Meshes/SM_Pier_Pillar_01a",
                       (x - 600, py, -350), (0, 0, 0), (1, 1, 1), "EastDock_Pile")
            spawn_mesh("/Game/Docks/VOL2_Powell/Meshes/SM_Pier_Pillar_01a",
                       (x + 600, py, -350), (0, 0, 0), (1, 1, 1), "EastDock_Pile")
    # A through lane on the western edge stays clear of cargo and mooring props.
    spawn_box((-3900, 0, -5), (1000, 7800, 60), DOCK_WOOD, "EastDock_Through_Walk")
    for loc in [(-3000, 1400, 320), (3000, 2300, 320), (-1500, 6000, 290),
                (1500, 11200, 290), (3000, 16700, 290)]:
        add_lamp(loc, "EastDock_Service_Lantern", 0)
    spawn_mesh("/Game/Docks/VOL2_Powell/Meshes/SM_Metal_Bouy_NN_02a",
               (4300, 15100, -30), (0, 0, 0), (1, 1, 1), "EastDock_Channel_Buoy", required=False)
    spawn_mesh("/Game/Docks/VOL2_Powell/Meshes/SM_Boat_NN_17a",
               (5000, 4500, -240), (0, -65, 0), (1, 1, 1), "EastDock_Mooring_Skiff", required=False)
    for loc in [(-3000, 1800, 280), (3000, 3000, 280), (0, 9700, 280)]:
        spawn_point_light(loc, (255, 195, 132), 1050, 2400, "EastDock_LocalLanternLight")
    save_authored(world, "east_docks", package, {
        "layout": "separate linear quay with three loading fingers and an inland through lane",
        "shared_asset_root": "/Game/Docks/VOL2_Powell",
        "walk_surface_collision": "BlockAll on yard, quay, lane, and loading fingers",
        "local_entry_cm": [0, 0, 0],
    })
    world = None
    retire_world(world)


def author_cloned_region(key, remove_landscape=False, label_substrings=(), allowed_child_tokens=None):
    if map_file(LEVELS[key]).exists():
        if key != "shipwreck":
            REPORT_DATA["levels"].append({"key": key, "package": LEVELS[key],
                                          "file": str(map_file(LEVELS[key])), "verified_existing_file": True})
            return
        world, removed_children = load_existing_map(LEVELS[key], allowed_child_tokens)
    else:
        world, removed_children = load_clone(SOURCES[key], LEVELS[key], allowed_child_tokens)
    removed = clean_environment(world, remove_landscape, label_substrings)
    if key == "lab_a":
        for actor in list(EAS.get_all_level_actors()):
            if actor_label(actor) == "SM_MWall03-700x350-8":
                EAS.destroy_actor(actor)
                removed.append({"label": "SM_MWall03-700x350-8", "class": actor.get_class().get_name(), "purpose": "open west lab connector"})
    if key == "lab_b":
        if SWITCHBOARD:
            spawn_mesh("/Game/Carnival/WorldExpansion/IndustrialSwitchboard/SM_IndustrialSwitchboard",
                       (0, -615, 160), (0, 0, 0), (1, 1, 1), "Lab_Control_Switchboard")
        for actor in list(EAS.get_all_level_actors()):
            if "BP_MGate01" in actor_label(actor):
                EAS.destroy_actor(actor)
                removed.append({"label": actor_label(actor), "class": actor.get_class().get_name(), "purpose": "keep lab room connector reversible and unlocked"})
    if key == "sewers":
        for actor in list(EAS.get_all_level_actors()):
            if actor_label(actor) == "SM_Sewer_Tube_Door_01b":
                EAS.destroy_actor(actor)
                removed.append({"label": actor_label(actor), "class": actor.get_class().get_name(), "purpose": "open the Prison stair connection into the sewer corridor"})
    count = save_authored(world, key, LEVELS[key], {
        "source": SOURCES[key], "removed_sample_actors": removed,
        "removed_sample_sublevels": removed_children,
        "collision": "source assembly collision retained; connector decks are in L_WExp_Connections",
    })
    world = None
    removed = None
    removed_children = None
    retire_world(world, removed, removed_children)


def author_atlantis():
    package = LEVELS["atlantis"]
    if map_file(package).exists():
        REPORT_DATA["levels"].append({"key": "atlantis", "package": package,
                                      "file": str(map_file(package)), "verified_existing_file": True})
        return
    world = create_new_map(package)
    concrete = SEWER_CONCRETE or DOCK_ROCK
    floor_mat = SEWER_FLOOR or concrete
    # Long interior hall joins a collapsed gate to the ship passage.
    for x in range(-6000, 6001, 2000):
        spawn_box((x, 0, 0), (2050, 3400, 100), floor_mat, "Atlantis_Ruin_Floor_Tile")
    for x in [-5600, -2800, 0, 2800, 5600]:
        for y in [-1200, 1200]:
            mesh = "/Game/Atlantis_Ruins/Meshes/SM_Column_00" if (x + int(y)) % 2 else "/Game/Atlantis_Ruins/Meshes/SM_Column_02"
            spawn_mesh(mesh, (x, y, 0), (0, 0, 0), (1.05, 1.05, 1.0), "Atlantis_Ruin_Column")
        spawn_mesh("/Game/Atlantis_Ruins/Meshes/SM_Arch_00", (x, 0, 620), (0, 90, 0), (3.5, 3.5, 3.0), "Atlantis_Ruin_Arch", required=False)
    for x, y, scale in [(-4500, 3000, 2.0), (-1800, -3300, 2.5), (2400, 3200, 1.8), (5000, -3100, 2.4)]:
        spawn_mesh("/Game/Atlantis_Ruins/Meshes/SM_Rocks_Large_02", (x, y, -120), (0, 20, 0), (scale, scale, scale), "Atlantis_Collapsed_Masonry", required=False)
    spawn_mesh("/Game/Atlantis_Ruins/Meshes/SM_Statue_00", (0, 0, 0), (0, 0, 0), (1.4, 1.4, 1.4), "Atlantis_Central_Statue")
    for x, y in [(-4200, 2500), (4200, 2500), (-4200, -2500), (4200, -2500)]:
        spawn_mesh("/Game/Atlantis_Ruins/Meshes/SM_Coral_00", (x, y, -60), (0, 25, 0), (2.0, 2.0, 1.8), "Atlantis_Coral_Rubble", required=False)
    # Portal floors are explicit collision pads at both ends of the hall.
    spawn_box((-7300, 0, 0), (2800, 3000, 100), floor_mat, "Atlantis_Sewer_Entry_Pad")
    spawn_box((7300, 0, -100), (2800, 3000, 100), floor_mat, "Atlantis_Ship_Exit_Pad")
    spawn_point_light((-1000, 0, 1200), (76, 215, 235), 3300, 4400, "Atlantis_Teal_Central_Light")
    spawn_point_light((4600, 900, 1050), (61, 153, 225), 2800, 2700, "Atlantis_Side_Light")
    save_authored(world, "atlantis", package, {
        "layout": "ruined axial hall with statue, paired columns, rubble, and two distinct passages",
        "source_meshes": "/Game/Atlantis_Ruins/Meshes",
        "collision": "floor tiles and both passage pads use BlockAll; imported columns retain generated collision",
    })
    world = None
    retire_world(world)


def catmull_rom(controls, step=800.0):
    points = []
    for i in range(len(controls) - 1):
        p0, p1 = controls[max(i - 1, 0)], controls[i]
        p2, p3 = controls[i + 1], controls[min(i + 2, len(controls) - 1)]
        distance = math.sqrt(sum((p2[k] - p1[k]) ** 2 for k in range(3)))
        count = max(2, int(math.ceil(distance / step)))
        for j in range(count):
            t = j / float(count)
            t2, t3 = t * t, t * t * t
            points.append(tuple(0.5 * (
                2 * p1[k] + (-p0[k] + p2[k]) * t
                + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3
            ) for k in range(3)))
    points.append(tuple(controls[-1]))
    return points


def path_length(points):
    return sum(math.dist(a, b) for a, b in zip(points, points[1:]))


def build_surface_path(controls, name, width, material, target_segment=700.0, floor_thickness=45.0):
    points = catmull_rom(controls)
    pieces = 0
    length_cm = path_length(points)
    for a, b in zip(points, points[1:]):
        d = math.dist(a, b)
        n = max(1, int(math.ceil(d / target_segment)))
        for j in range(n):
            t0, t1 = j / float(n), (j + 1) / float(n)
            p = tuple(a[k] * (1 - t0) + b[k] * t0 for k in range(3))
            q = tuple(a[k] * (1 - t1) + b[k] * t1 for k in range(3))
            dx, dy, dz = q[0] - p[0], q[1] - p[1], q[2] - p[2]
            horizontal = max(1.0, math.hypot(dx, dy))
            heading = math.degrees(math.atan2(dy, dx))
            pitch = math.degrees(math.atan2(dz, horizontal))
            center = tuple((p[k] + q[k]) * 0.5 for k in range(3))
            spawn_box(center, (math.sqrt(dx * dx + dy * dy + dz * dz) + 24, width, floor_thickness),
                      material, name + "_Segment", (pitch, heading, 0))
            pieces += 1
    return {"name": name, "length_m": length_cm / 100.0, "segment_count": pieces,
            "surface_width_cm": width, "controls_cm": controls}


def build_tunnel(start, end, name, width=360.0, height=460.0, step=900.0):
    d = math.dist(start, end)
    count = max(1, int(math.ceil(d / step)))
    dx, dy, dz = (end[i] - start[i] for i in range(3))
    horizontal = max(1.0, math.hypot(dx, dy))
    heading = math.degrees(math.atan2(dy, dx))
    pitch = math.degrees(math.atan2(dz, horizontal))
    rotation = (pitch, heading, 0)
    for i in range(count):
        t0, t1 = i / float(count), (i + 1) / float(count)
        p = tuple(start[k] * (1 - t0) + end[k] * t0 for k in range(3))
        q = tuple(start[k] * (1 - t1) + end[k] * t1 for k in range(3))
        seg_len = math.dist(p, q) + 25
        center = tuple((p[k] + q[k]) * 0.5 for k in range(3))
        spawn_box(center, (seg_len, width, 35), SEWER_FLOOR or SEWER_CONCRETE,
                  name + "_Walkway", rotation)
        side_offset = width * 0.5 - 20
        for side in (-1, 1):
            wall_center = (center[0] - math.sin(math.radians(heading)) * side_offset * side,
                           center[1] + math.cos(math.radians(heading)) * side_offset * side,
                           center[2] + height * 0.5)
            spawn_box(wall_center, (seg_len, 35, height), SEWER_CONCRETE, name + "_Wall", rotation)
        roof = (center[0], center[1], center[2] + height)
        spawn_box(roof, (seg_len, width, 35), SEWER_CONCRETE, name + "_Ceiling", rotation)
    spawn_point_light(start, (92, 168, 205), 1200, 1250, name + "_EntryLight")
    spawn_point_light(end, (92, 168, 205), 1200, 1250, name + "_ExitLight")
    return {"name": name, "length_m": d / 100.0, "walkway_count": count,
            "width_cm": width, "clear_height_cm": height, "start_cm": start, "end_cm": end}


def author_connectors():
    package = LEVELS["connectors"]
    if map_file(package).exists():
        REPORT_DATA["levels"].append({"key": "connectors", "package": package,
                                      "file": str(map_file(package)), "verified_existing_file": True})
        return
    world = create_new_map(package)
    outer = build_surface_path(OUTER_CONTROLS, "OuterRoute", 760.0, DOCK_SAND, 650.0, 45.0)
    lab = build_surface_path(LAB_CONTROLS, "PrisonToLabRoute", 500.0, SEWER_CONCRETE, 600.0, 40.0)
    service = build_surface_path([PRISON_GATE, (-29200, -23600, 600), (-28200, -21600, 600), PRISON_STAIR_TOP],
                                 "PrisonToSewerServiceWalk", 450.0, SEWER_CONCRETE, 500.0, 40.0)
    # 120 shallow steps descend 24 m over 65 m; side walls and a roof enclose the reversible stair.
    step_count = 120
    step_run = 6500.0 / step_count
    step_rise = 2400.0 / step_count
    for i in range(step_count):
        y = PRISON_STAIR_TOP[1] + (i + 0.5) * step_run
        top = PRISON_STAIR_TOP[2] - i * step_rise
        spawn_box((PRISON_STAIR_TOP[0], y, top - 18), (320, step_run + 25, 40), SEWER_FLOOR or SEWER_CONCRETE,
                  "PrisonSewer_StairTread")
    roll = math.degrees(math.atan2(-2400.0, 6500.0))
    tunnel_rot = (0.0, 0.0, roll)
    flight_len = math.hypot(6500, 2400)
    mid_y = PRISON_STAIR_TOP[1] + 3250
    mid_z = (PRISON_STAIR_TOP[2] + SEWER_DOOR[2]) * 0.5
    section_count = int(math.ceil(flight_len / 800.0))
    for i in range(section_count):
        y0 = PRISON_STAIR_TOP[1] + i * flight_len / section_count * math.cos(math.radians(abs(roll)))
        y1 = PRISON_STAIR_TOP[1] + (i + 1) * flight_len / section_count * math.cos(math.radians(abs(roll)))
        z0 = PRISON_STAIR_TOP[2] - i * flight_len / section_count * math.sin(math.radians(abs(roll)))
        z1 = PRISON_STAIR_TOP[2] - (i + 1) * flight_len / section_count * math.sin(math.radians(abs(roll)))
        c = ((PRISON_STAIR_TOP[0]), (y0 + y1) * 0.5, (z0 + z1) * 0.5)
        segment = y1 - y0 + 35
        for side in (-1, 1):
            spawn_box((c[0] + side * 220, c[1], c[2] + 230), (35, segment, 500), SEWER_CONCRETE,
                      "PrisonSewer_StairWall", tunnel_rot)
        spawn_box((c[0], c[1], c[2] + 500), (500, segment, 35), SEWER_CONCRETE,
                  "PrisonSewer_StairCeiling", tunnel_rot)
        if i % 3 == 0:
            spawn_point_light((c[0], c[1], c[2] + 350), (204, 164, 101), 1150, 1000,
                              "PrisonSewer_StairLight")
    stairs = {"step_count": step_count, "horizontal_length_m": 65.0,
              "vertical_drop_m": 24.0, "start_cm": PRISON_STAIR_TOP, "end_cm": SEWER_DOOR,
              "reversible": True, "tunnel_clear_width_cm": 430, "tunnel_clear_height_cm": 465}
    sewer_exit = (-27100.0, -9654.0, -1800.0)
    sewer_atlantis = build_tunnel(sewer_exit, ATLANTIS_DOOR, "SewerToAtlantisPassage")
    atlantis_ship_start = (-7000.0, -11000.0, -1800.0)
    atlantis_ship = build_tunnel(atlantis_ship_start, SHIPWRECK_DOOR, "AtlantisToShipwreckPassage",
                                 width=420.0, height=520.0)
    # Stilt supports retain the coastal road over the two dock approaches.
    for node in [(-62000, -70000, 560), (-56500, -59000, 590), (-53500, -52000, 600),
                 (65000, 12000, 600), (74000, 23000, 605), (83000, 44000, 615)]:
        spawn_box((node[0], node[1], node[2] - 480), (90, 90, 960), DOCK_WOOD, "CoastalRoute_TrestlePile")
    REPORT_DATA["connections"] = [
        {"id": "R03", "from": "Mansion", "to": "DocksNorth", "type": "surface", "route": outer},
        {"id": "R04", "from": "DocksNorth", "to": "Prison", "type": "surface", "route": outer},
        {"id": "R05", "from": "Prison", "to": "DocksEast", "type": "surface", "route": outer},
        {"id": "R06", "from": "DocksEast", "to": "Hospital", "type": "surface", "route": outer},
        {"id": "R09", "from": "Prison", "to": "ResearchLab", "type": "surface", "route": lab},
        {"id": "R10", "from": "Prison", "to": "Sewers", "type": "interior stair", "route": service, "stair": stairs},
        {"id": "R11", "from": "Sewers", "to": "AtlantisRuins", "type": "sealed tunnel", "route": sewer_atlantis},
        {"id": "R12", "from": "AtlantisRuins", "to": "Shipwreck", "type": "sealed tunnel", "route": atlantis_ship},
    ]
    save_authored(world, "connectors", package, {
        "outer_route_width_cm": 760, "material": "/Game/Docks/VOL2_Powell/Materials/Instances/MI_Sand_01a",
        "lab_branch_width_cm": 500,
        "no_unrequested_links": True,
    })
    world = None
    retire_world(world)


def main():
    REPORT_DATA["map_placements"] = {
        "north_docks": {"location_cm": NORTH, "yaw_deg": 0.0},
        "prison": {"location_cm": translation_for_anchor((-9741.085, 2428.270, 1637.206), PRISON_GATE, -45.0), "yaw_deg": -45.0,
                   "entry_anchor_local_cm": [-9741.085, 2428.270, 1637.206], "entry_world_cm": PRISON_GATE},
        "lab_a": {"location_cm": translation_for_anchor((1400.0, 400.0, 0.0), LAB_DOOR, -57.0), "yaw_deg": -57.0,
                  "entry_anchor_local_cm": [1400.0, 400.0, 0.0], "entry_world_cm": LAB_DOOR},
        "lab_b": {"location_cm": translation_for_anchor((1425.0, 400.0, 0.0),
                    tuple(translation_for_anchor((1400.0, 400.0, 0.0), LAB_DOOR, -57.0)[i] + rotate_xy((-2825.0, 0.0), -57.0)[i] for i in (0, 1)) + (600.0,), 123.0),
                  "yaw_deg": 123.0, "connector": "aligns the two lab room door openings"},
        "east_docks": {"location_cm": EAST, "yaw_deg": 0.0},
        "sewers": {"location_cm": translation_for_anchor((100.0, -210.0, 0.0), SEWER_DOOR, 0.0), "yaw_deg": 0.0,
                   "entry_anchor_local_cm": [100.0, -210.0, 0.0], "entry_world_cm": SEWER_DOOR},
        "atlantis": {"location_cm": tuple(ATLANTIS_DOOR[i] - (-6000.0 if i == 0 else 0.0) if i < 2 else ATLANTIS_DOOR[i] for i in range(3)),
                     "yaw_deg": 0.0, "entry_local_cm": [-6000.0, 0.0, 0.0], "entry_world_cm": ATLANTIS_DOOR},
        "shipwreck": {"location_cm": tuple(SHIPWRECK_DOOR[i] - (33.089 if i == 0 else 10.0 if i == 1 else 108.649) for i in range(3)),
                      "yaw_deg": 0.0, "entry_anchor_local_cm": [33.089, 10.0, 108.649], "entry_world_cm": SHIPWRECK_DOOR},
        "hospital": {"entry_world_cm": HOSPITAL},
    }
    # Docks are independently built from the same vendor asset root.
    author_docks_north()
    author_docks_east()
    # Retire the temporary duplication probe map created while checking UE APIs.
    delete_package_if_present(LEVEL_DIR + "/L_WExp_Probe_Docks")
    for key in ("prison", "lab_a", "lab_b", "sewers", "shipwreck"):
        allowed = STREAM_ALLOWED_SHIP if key == "shipwreck" else None
        remove_landscape = key == "shipwreck"
        remove_labels = ("BP_Spline_Turtle",) if key == "shipwreck" else ()
        author_cloned_region(key, remove_landscape, remove_labels, allowed)
    author_atlantis()
    author_connectors()
    REPORT_DATA["success"] = True
    REPORT_DATA["finished_utc"] = datetime.utcnow().isoformat() + "Z"


try:
    main()
except Exception as exc:
    REPORT_DATA["errors"].append(repr(exc))
    REPORT_DATA["traceback"] = traceback.format_exc()
finally:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(REPORT_DATA, indent=2), encoding="utf-8")
    unreal.log("WORLD_EXPANSION_REGION_AUTHORING_" + ("COMPLETE" if REPORT_DATA["success"] else "FAILED"))
    unreal.SystemLibrary.quit_editor()
