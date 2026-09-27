"""Shared local-centimetre layout for Carnival's industrial hospital branch."""
from pathlib import Path
import json
import math

ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/IndustrialHospital"
BASE = "/Game/Carnival/World"
MAIN_MAP = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
ROUTE_LEVEL = BASE + "/Levels/L_IndustrialHospitalRoute"
SLUM_LEVEL = BASE + "/Levels/L_IndustrialSlums_DistrictFinal"
HOSPITAL_EXTERIOR_LEVEL = BASE + "/Levels/L_IndustrialHospitalExterior"
HOSPITAL_LIGHT_LEVEL = BASE + "/Levels/L_IndustrialHospitalInteriorLights"
HOSPITAL_ARCH_LEVEL = BASE + "/Levels/L_IndustrialHospitalInteriorArchitecture"

# The other gate is on the northeast side of the midway.
GATE = (7093.926, 6841.718, 42.781)
ROUTE_WORLD_YAW = 54.0
HOSPITAL_YAW = -36.0

# Each point is a road-centre sample in centimetres from the Carnival gate.
# From 60-76 km the road follows the selected district's east-side street.
ROAD_CONTROL_POINTS = [
    (0, 0, 0), (9000, 0, 25), (19000, 1800, 55),
    (31000, 2600, 85), (42000, -500, 115), (53500, -1800, 150),
    (60000, 0, 232), (62000, 0, 236), (64000, 0, 236),
    (66000, 0, 282), (68000, 0, 280), (70000, 0, 334),
    (72000, 0, 430), (74000, 0, 430), (76000, 0, 478),
    (82000, 0, 500), (96000, 2500, 515), (111000, 4000, 535),
    (124000, 0, 555), (137000, -2200, 575), (145000, 0, 590),
    (151000, 0, 600),
]
ROAD_HALF_WIDTH_CM = 450.0
ROAD_BED_HALF_WIDTH_CM = 3000.0
ROAD_CHUNK_LENGTH_CM = 25000.0
SLUM_CROP = (-20000.0, -10000.0, 0.0, 16000.0)
SLUM_ROAD_X = -12000.0
SLUM_ROAD_START_Y = 0.0
SLUM_ROAD_END_Y = 16000.0
SLUM_ROAD_START_S = 60000.0
SLUM_CENTER_ROUTE_POINT = (68000.0, 0.0, 280.0)

# The hospital's BO_door_4x5m2 is the entrance to the complete interior.
HOSPITAL_DOOR_LOCAL = (5000.0, -1750.0, 80.0)
HOSPITAL_DOOR_ROUTE_POINT = (151000.0, 0.0, 600.0)
# The factory facade stands across the forecourt at the hospital's front gate.
FACADE_LOCAL = (6150.0, -8000.0, -87.0)
FACADE_LOCAL_YAW = 90.0


def rotate_xy(point, yaw_degrees):
    angle = math.radians(yaw_degrees)
    x, y = point[:2]
    return (x * math.cos(angle) - y * math.sin(angle),
            x * math.sin(angle) + y * math.cos(angle))


def world_point(route_point):
    x, y = rotate_xy(route_point, ROUTE_WORLD_YAW)
    return (GATE[0] + x, GATE[1] + y, GATE[2] + route_point[2])


def hospital_level_transform():
    door_route_x, door_route_y, door_route_z = HOSPITAL_DOOR_ROUTE_POINT
    door_x, door_y, door_z = HOSPITAL_DOOR_LOCAL
    door_offset_x, door_offset_y = rotate_xy((door_x, door_y), HOSPITAL_YAW)
    origin_world = world_point((door_route_x, door_route_y, door_route_z))
    return (origin_world[0] - door_offset_x,
            origin_world[1] - door_offset_y,
            origin_world[2] - door_z)


def slum_level_transform():
    # Local +Y in the source district points down the road; the source map is
    # therefore rotated -90 degrees relative to the route's +X axis.
    x_min, x_max, y_min, y_max = SLUM_CROP
    source_road = (SLUM_ROAD_X, SLUM_ROAD_START_Y)
    route_start = (SLUM_ROAD_START_S, 0.0)
    source_offset = rotate_xy(source_road, -90.0)
    route_origin_xy = (route_start[0] - source_offset[0],
                       route_start[1] - source_offset[1])
    world_xy = rotate_xy(route_origin_xy, ROUTE_WORLD_YAW)
    return (GATE[0] + world_xy[0], GATE[1] + world_xy[1], GATE[2]), -36.0


def path_distance(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def route_manifest(route_points):
    length = sum(path_distance(a, b) for a, b in zip(route_points, route_points[1:]))
    return {
        "main_map": MAIN_MAP,
        "gate_world": GATE,
        "route_world_yaw": ROUTE_WORLD_YAW,
        "route_length_m": length / 100.0,
        "walk_speed_cm_s": 450.0,
        "walk_time_s_estimate": length / 450.0,
        "motorcycle_speed_m_s_assumption": 6.4,
        "motorcycle_time_s_estimate": length / 640.0,
        "motorcycle_clear_width_m": ROAD_HALF_WIDTH_CM * 2.0 / 100.0,
        "route_points_local_cm": route_points,
        "slums_crop_cm": SLUM_CROP,
        "slums_level_location_world_cm": slum_level_transform()[0],
        "slums_level_yaw_world_degrees": slum_level_transform()[1],
        "hospital_door_route_point_cm": HOSPITAL_DOOR_ROUTE_POINT,
        "hospital_level_location_world_cm": hospital_level_transform(),
        "hospital_level_yaw_world_degrees": HOSPITAL_YAW,
        "factory_facade_local_cm": FACADE_LOCAL,
        "factory_facade_local_yaw_degrees": FACADE_LOCAL_YAW,
    }


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = route_manifest(ROAD_CONTROL_POINTS)
    (OUT / "Industrial_Hospital_Route_Layout.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print("Estimated branch:", round(manifest["route_length_m"]), "m",
          "at", round(manifest["walk_time_s_estimate"]), "s on foot",
          "and", round(manifest["motorcycle_time_s_estimate"]), "s on a cautious bike")
