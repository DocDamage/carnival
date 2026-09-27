"""Author the one-way industrial branch and connect the explorable hospital."""
import json
import math
import shutil
import traceback
from collections import Counter
from datetime import datetime
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/IndustrialHospital"
OUT.mkdir(parents=True, exist_ok=True)
REPORT_PATH = OUT / "Industrial_Hospital_Authoring.json"
sys_path = str(ROOT / "Scripts")
import sys
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)
from industrial_hospital_route_config import (
    FACADE_LOCAL, FACADE_LOCAL_YAW, GATE, HOSPITAL_ARCH_LEVEL,
    HOSPITAL_DOOR_LOCAL, HOSPITAL_DOOR_ROUTE_POINT, HOSPITAL_EXTERIOR_LEVEL,
    HOSPITAL_LIGHT_LEVEL, HOSPITAL_YAW, MAIN_MAP, ROAD_CONTROL_POINTS,
    ROUTE_LEVEL, ROUTE_WORLD_YAW, SLUM_LEVEL, OUT as CONFIG_OUT,
    hospital_level_transform, route_manifest, slum_level_transform,
)

REPORT = {"phase": "starting", "created_levels": [], "connected_levels": [], "errors": []}
LEVEL_DIR = ROOT / "Content/Carnival/World/Levels"
MAIN_MAP_FILE = ROOT / "Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap"


def package_file(path):
    return ROOT / ("Content" + path.replace("/Game", "").replace("/", "\\") + ".umap")


def vec(value):
    return unreal.Vector(float(value[0]), float(value[1]), float(value[2]))


def tagged(actor):
    try:
        return any(str(tag) == "IndustrialHospitalGenerated" for tag in actor.get_editor_property("tags"))
    except Exception:
        return False


def tag(actor):
    actor.set_editor_property("tags", [unreal.Name("IndustrialHospitalGenerated")])


def mark_collision(mesh):
    setup = mesh.get_editor_property("body_setup")
    if setup:
        setup.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)


def empty_or_open_level(path):
    file = package_file(path)
    if file.exists():
        world = unreal.EditorLoadingAndSavingUtils.load_map(path)
        actors = list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
        for actor in actors:
            if actor.get_class().get_name() != "WorldSettings":
                unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(actor)
        return world
    if not unreal.EditorLevelLibrary.new_level(path):
        raise RuntimeError("Could not create authored level " + path)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    # New Level uses an editor template. Keep only WorldSettings so the connected
    # levels inherit the Carnival's own night lighting and weather.
    actors = list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
    for actor in actors:
        if actor.get_class().get_name() != "WorldSettings":
            unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(actor)
    return world


def save_current(path):
    if not unreal.EditorLevelLibrary.save_current_level():
        raise RuntimeError("Could not save " + path)
    REPORT["created_levels"].append({"asset": path, "file_bytes": package_file(path).stat().st_size if package_file(path).exists() else None})


def set_mesh_materials(component, mesh, materials):
    slots = list(mesh.get_editor_property("static_materials"))
    for index in range(min(len(slots), len(materials))):
        if materials[index]:
            component.set_material(index, materials[index])


def spawn_mesh(eas, name, mesh, location, rotation, materials=()):
    if not mesh:
        raise RuntimeError("Missing static mesh " + name)
    actor = eas.spawn_actor_from_class(
        unreal.StaticMeshActor, vec(location),
        unreal.Rotator(pitch=0.0, yaw=float(rotation), roll=0.0),
    )
    if not actor:
        raise RuntimeError("Could not place " + name)
    actor.set_actor_label(name)
    tag(actor)
    component = actor.get_editor_property("static_mesh_component")
    component.set_static_mesh(mesh)
    component.set_collision_profile_name("BlockAll")
    set_mesh_materials(component, mesh, materials)
    return actor


def point_on_route(s):
    points = ROAD_CONTROL_POINTS
    if s <= points[0][0]:
        return points[0]
    for a, b in zip(points, points[1:]):
        if a[0] <= s <= b[0]:
            t = (s - a[0]) / (b[0] - a[0])
            return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))
    return points[-1]


def add_audio(eas, name, sound_path, position, radius=1800.0, falloff=2400.0, volume=0.28):
    sound = unreal.load_asset(sound_path)
    if not sound:
        raise RuntimeError("Missing audio source " + sound_path)
    sound.set_editor_property("looping", True)
    unreal.EditorAssetLibrary.save_loaded_asset(sound, False)
    actor = eas.spawn_actor_from_class(unreal.AmbientSound, vec(position))
    if not actor:
        raise RuntimeError("Could not place audio actor " + name)
    actor.set_actor_label(name)
    tag(actor)
    component = actor.get_editor_property("audio_component")
    component.set_editor_property("sound", sound)
    component.set_editor_property("auto_activate", True)
    component.set_editor_property("volume_multiplier", float(volume))
    component.set_editor_property("override_attenuation", True)
    attenuation = component.get_editor_property("attenuation_overrides")
    attenuation.set_editor_property("attenuation_shape", unreal.AttenuationShape.SPHERE)
    attenuation.set_editor_property("attenuation_shape_extents", unreal.Vector(float(radius), 0.0, 0.0))
    attenuation.set_editor_property("falloff_distance", float(falloff))
    attenuation.set_editor_property("spatialize", True)
    component.set_editor_property("attenuation_overrides", attenuation)
    return actor


def add_fog(eas, name, s, radius_cm, radial_density, height_density, start_distance):
    p = point_on_route(s)
    actor = eas.spawn_actor_from_class(unreal.LocalFogVolume, unreal.Vector(p[0], p[1], p[2] + 1100.0))
    if not actor:
        raise RuntimeError("Could not place local fog volume " + name)
    actor.set_actor_label(name)
    actor.set_actor_scale3d(unreal.Vector(radius_cm / 500.0, radius_cm / 500.0, radius_cm / 500.0))
    tag(actor)
    component = actor.get_editor_property("local_fog_volume_volume")
    component.set_radial_fog_extinction(float(radial_density))
    component.set_height_fog_extinction(float(height_density))
    component.set_height_fog_falloff(1100.0)
    component.set_height_fog_offset(-0.05)
    component.set_fog_phase_g(0.28)
    component.set_fog_albedo(unreal.LinearColor(0.48, 0.56, 0.72, 1.0))
    component.set_fog_start_distance(float(start_distance))
    return actor


def add_point_light(eas, name, position, color, intensity=1100.0, radius=1800.0):
    actor = eas.spawn_actor_from_class(unreal.PointLight, vec(position))
    if not actor:
        raise RuntimeError("Could not place light " + name)
    actor.set_actor_label(name)
    tag(actor)
    light = actor.get_editor_property("light_component")
    light.set_editor_property("intensity", float(intensity))
    light.set_editor_property("attenuation_radius", float(radius))
    light.set_editor_property("light_color", unreal.Color(int(color[0] * 255), int(color[1] * 255), int(color[2] * 255), 255))
    light.set_editor_property("cast_shadows", False)
    return actor


def author_route_level():
    world = empty_or_open_level(ROUTE_LEVEL)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    snow_road = unreal.load_asset("/Game/Hospital_Meshingun/Master_Material/MasterShader_Meshingun/Material/Temp_Material/MI_Pavement_01a_Snow")
    leaf_shoulder = unreal.load_asset("/Game/Hospital_Meshingun/Master_Material/MasterShader_Meshingun/Material/Temp_Material/MI_Pavement_01a_Leaves")
    ground = unreal.load_asset("/Game/IndustrialSlums/Materials/Material_Instances/MI_GroundDisplaced")
    mats = [snow_road, leaf_shoulder, ground]
    if not snow_road or not ground:
        raise RuntimeError("Road surface materials are missing")

    route_report = json.loads((OUT / "Industrial_Hospital_Route_Meshes.json").read_text(encoding="utf-8"))
    route_meshes = []
    for row in route_report["road_meshes"]:
        mesh = unreal.load_asset("/Game/Carnival/World/Meshes/IndustrialHospital/" + row["name"])
        if not mesh:
            raise RuntimeError("Road mesh was not imported: " + row["name"])
        mark_collision(mesh)
        spawn_mesh(eas, row["name"], mesh, (0.0, 0.0, 0.0), 0.0, mats)
        route_meshes.append(row["name"])

    # Add cold local fog and denser snowfall in progressively larger, closer cells.
    fog_cells = [
        (38000.0, 22000.0, 0.0010, 0.0008, 2300.0),
        (69000.0, 27000.0, 0.0015, 0.0010, 1800.0),
        (97000.0, 33000.0, 0.0025, 0.0015, 1100.0),
        (122000.0, 39000.0, 0.0035, 0.0022, 500.0),
        (143000.0, 47000.0, 0.0050, 0.0030, 0.0),
    ]
    for index, (s, radius, radial, height, start) in enumerate(fog_cells, 1):
        add_fog(eas, f"Hospital Approach Fog {index:02d}", s, radius, radial, height, start)

    # Keep using Carnival's active night-snow layer. The local legacy snow
    # flare depended on an absent Village vector field and caused large bloom
    # sprites over the route, so the worsening is expressed through these
    # progressively denser fog cells instead of duplicate particle systems.
    snow_cells = []

    for index, s in enumerate((67000.0, 71000.0, 99000.0, 141000.0), 1):
        p = point_on_route(s)
        side = -1.0 if index % 2 else 1.0
        add_point_light(eas, f"Slum Road Sodium Light {index:02d}", (p[0], p[1] + side * 680.0, p[2] + 430.0), (1.0, 0.43, 0.16), 900.0, 1500.0)

    audio_root = "/Game/Carnival/Audio/IndustrialHospital/"
    outdoor_audio = [
        ("Abandoned Toy Assembly Line", "Abandoned_Toy_Assembly_Line", 66000.0, 0.31),
        ("Night Shift at Toy Factory", "Night_Shift_at_Toy_Factory", 102000.0, 0.24),
        ("Malfunctioning Animatronics", "Malfunctioning_Animatronics", 145000.0, 0.31),
    ]
    for label, asset, s, volume in outdoor_audio:
        p = point_on_route(s)
        add_audio(eas, label, audio_root + asset, (p[0], p[1] + 550.0, p[2] + 80.0), 2300.0, 2400.0, volume)

    # Hospital-local points are turned into the route level's local coordinates.
    door_x, door_y, door_z = HOSPITAL_DOOR_LOCAL
    route_x, route_y, route_z = HOSPITAL_DOOR_ROUTE_POINT
    interior_audio = [
        ("Forgotten Playroom", "Forgotten_Playroom", (6900.0, -4300.0, 90.0), 1500.0, 2100.0, 0.22),
        ("Broken Music Box", "Broken_Music_Box", (8500.0, -1900.0, 90.0), 900.0, 1200.0, 0.24),
        ("Smiling Doll in the Dark", "Smiling_Doll_in_the_Dark", (6500.0, 100.0, 90.0), 1200.0, 1600.0, 0.22),
    ]
    for label, asset, local, radius, falloff, volume in interior_audio:
        dx, dy = local[0] - door_x, local[1] - door_y
        route_position = (route_x + dy, route_y - dx, route_z + local[2] - door_z)
        add_audio(eas, label, audio_root + asset, route_position, radius, falloff, volume)

    REPORT["route_meshes"] = route_meshes
    REPORT["route_audio"] = [row[0] for row in outdoor_audio] + [row[0] for row in interior_audio]
    REPORT["weather_cells"] = len(fog_cells)
    REPORT["snow_emitters"] = len(snow_cells)
    REPORT["route_length_m"] = route_report["route_length_m"]
    save_current(ROUTE_LEVEL)


def author_facade_level():
    empty_or_open_level(HOSPITAL_EXTERIOR_LEVEL)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    mesh = unreal.load_asset("/Game/IndustrialSlums/IndustrialHospital_Facade/SM_IndustrialHospital_FactoryFacade")
    material = unreal.load_asset("/Game/IndustrialSlums/Materials/MI_ConcreteWall")
    if not mesh or not material:
        raise RuntimeError("Factory facade mesh/material is missing")
    mark_collision(mesh)
    facade = spawn_mesh(eas, "Abandoned Hospital Factory-Gate Facade", mesh, FACADE_LOCAL, FACADE_LOCAL_YAW, [material])
    p = FACADE_LOCAL
    add_point_light(eas, "Gate Sodium Lamp West", (p[0] - 3500.0, p[1] + 800.0, p[2] + 1200.0), (1.0, 0.24, 0.09), 2200.0, 3200.0)
    add_point_light(eas, "Gate Sodium Lamp East", (p[0] + 3500.0, p[1] + 800.0, p[2] + 1200.0), (1.0, 0.24, 0.09), 2200.0, 3200.0)
    REPORT["facade"] = {"mesh": mesh.get_path_name(), "material": material.get_path_name(), "local": FACADE_LOCAL, "yaw": FACADE_LOCAL_YAW}
    save_current(HOSPITAL_EXTERIOR_LEVEL)


def duplicate_and_strip(source, destination, classes_to_remove):
    if not unreal.EditorAssetLibrary.does_asset_exist(destination):
        result = unreal.EditorAssetLibrary.duplicate_asset(source, destination)
        if not result:
            raise RuntimeError(f"Could not duplicate {source} to {destination}")
    world = unreal.EditorLoadingAndSavingUtils.load_map(destination)
    if not world:
        raise RuntimeError("Could not load local hospital level " + destination)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    removed = Counter()
    for actor in list(eas.get_all_level_actors()):
        class_name = actor.get_class().get_name()
        if class_name in classes_to_remove:
            if not eas.destroy_actor(actor):
                raise RuntimeError(f"Could not remove {class_name} from {destination}")
            removed[class_name] += 1
    if not unreal.EditorLevelLibrary.save_current_level():
        raise RuntimeError("Could not save modified hospital lighting level " + destination)
    REPORT.setdefault("hospital_level_edits", []).append({"source": source, "copy": destination, "removed_classes": dict(removed)})


def transform(location, yaw):
    result = unreal.Transform()
    result.set_editor_property("translation", vec(location))
    result.set_editor_property(
        "rotation",
        unreal.Rotator(pitch=0.0, yaw=float(yaw), roll=0.0).quaternion(),
    )
    result.set_editor_property("scale3d", unreal.Vector(1.0, 1.0, 1.0))
    return result


def connect_world():
    # Save a recovery copy before adding sublevels to the local licensed root map.
    backup_dir = OUT / "Backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = backup_dir / f"LV_Carnival_before_IndustrialHospital_{stamp}.umap"
    shutil.copy2(MAIN_MAP_FILE, backup)
    built_data = MAIN_MAP_FILE.with_name("LV_Carnival_BuiltData.uasset")
    if built_data.exists():
        shutil.copy2(built_data, backup_dir / f"LV_Carnival_BuiltData_before_IndustrialHospital_{stamp}.uasset")
    REPORT["main_map_backup"] = str(backup)
    REPORT["main_map_backup_sha256"] = __import__("hashlib").sha256(backup.read_bytes()).hexdigest()

    world = unreal.EditorLoadingAndSavingUtils.load_map(MAIN_MAP)
    if not world:
        raise RuntimeError("Could not load Carnival root map")
    existing = {level.get_path_name().split(":PersistentLevel")[0].split(".")[0] for level in unreal.EditorLevelUtils.get_levels(world)}
    hospital_location = hospital_level_transform()
    slum_location, slum_yaw = slum_level_transform()
    placements = [
        (ROUTE_LEVEL, GATE, ROUTE_WORLD_YAW),
        (SLUM_LEVEL, slum_location, slum_yaw),
        (HOSPITAL_EXTERIOR_LEVEL, hospital_location, HOSPITAL_YAW),
        (HOSPITAL_ARCH_LEVEL, hospital_location, HOSPITAL_YAW),
        ("/Game/Hospital_Meshingun/Environment/Map/LV_Hospital_Main_SetDress", hospital_location, HOSPITAL_YAW),
        ("/Game/Hospital_Meshingun/Environment/Map/LV_Hospital_Main_Decal", hospital_location, HOSPITAL_YAW),
        ("/Game/Hospital_Meshingun/Environment/Map/LV_Hospital_VFX", hospital_location, HOSPITAL_YAW),
        ("/Game/Hospital_Meshingun/Environment/Map/LV_Hospital_Volume", hospital_location, HOSPITAL_YAW),
        (HOSPITAL_LIGHT_LEVEL, hospital_location, HOSPITAL_YAW),
    ]
    for path, location, yaw in placements:
        file = package_file(path)
        if not file.exists():
            file = ROOT / ("Content" + path.replace("/Game", "").replace("/", "\\") + ".umap")
        if not file.exists():
            raise FileNotFoundError("Required sublevel is missing: " + path)
        if path not in existing:
            streaming = unreal.EditorLevelUtils.add_level_to_world_with_transform(
                world, path, unreal.LevelStreamingAlwaysLoaded, transform(location, yaw)
            )
            if not streaming:
                raise RuntimeError("Could not attach level " + path)
            streaming.set_editor_property("should_be_loaded", True)
            streaming.set_editor_property("should_be_visible", True)
            REPORT["connected_levels"].append(path)
        else:
            REPORT.setdefault("already_connected", []).append(path)
    if not unreal.EditorLevelLibrary.save_current_level():
        raise RuntimeError("Could not save Carnival root map with new connected levels")
    REPORT["main_map"] = MAIN_MAP
    REPORT["hospital_transform"] = {"location": hospital_location, "yaw": HOSPITAL_YAW}
    REPORT["slums_transform"] = {"location": slum_location, "yaw": slum_yaw}
    REPORT["route_transform"] = {"location": GATE, "yaw": ROUTE_WORLD_YAW}


try:
    REPORT["phase"] = "author_route"
    author_route_level()
    REPORT["phase"] = "complete"
except Exception as exc:
    REPORT["phase"] = "failed"
    REPORT["error"] = repr(exc)
    REPORT["traceback"] = traceback.format_exc()

REPORT_PATH.write_text(json.dumps(REPORT, indent=2), encoding="utf-8")
unreal.log("INDUSTRIAL_HOSPITAL_ROUTE_AUTHORING_" + REPORT["phase"].upper())
unreal.SystemLibrary.quit_editor()
