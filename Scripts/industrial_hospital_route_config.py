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
HOSPITAL_SETDRESS_SOURCE = "/Game/Hospital_Meshingun/Environment/Map/LV_Hospital_Main_SetDress"
HOSPITAL_SETDRESS_LEVEL = BASE + "/Levels/L_IndustrialHospitalSetDress"

def hospital_setdress_level():
    copied = ROOT / "Content/Carnival/World/Levels/L_IndustrialHospitalSetDress.umap"
    return HOSPITAL_SETDRESS_LEVEL if copied.exists() else HOSPITAL_SETDRESS_SOURCE

# The other gate is on the northeast side of the midway.
GATE = (7093.926, 6841.718, 42.781)
ROUTE_WORLD_YAW = 54.0
HOSPITAL_YAW = -36.0

# Each point is a road-centre sample in centimetres from the Carnival gate.
# The 600-760 m district segment is realigned west by apply_slum_street_alignment.
ROAD_CONTROL_POINTS = [
    (0, 0, 0), (9000, 0, 25), (19000, 1800, 55),
    (31000, 2600, 85), (42000, -500, 115), (53500, -1800, 150),
    (60000, 0, 232), (62000, 0, 236), (64000, 0, 236),
    (66000, 0, 282), (68000, 0, 280), (70000, 0, 334),
    (72000, 0, 430), (74000, 0, 430), (76000, 0, 478),
    (82000, 0, 500), (96000, 2500, 515), (111000, 4000, 535),
    (124000, 0, 555), (137000, -2200, 575), (145000, 0, 590),
    # Stop in the forecourt, six metres before the hospital wall. The doorway
    # center is 200 cm to the right of the source modular actor's pivot.
    (150400, -200, 600),
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
# The factory facade stands beside the road at the hospital forecourt.
FACADE_LOCAL = (10150.0, -8000.0, -87.0)
FACADE_LOCAL_YAW = 90.0


def apply_slum_street_alignment(points):
    """Follow the collision-probed west street while retaining every building.

    Saved center and lane-edge capsule probes at offset 6000 cm found no scenery
    obstructions. The old centerline intersected three houses. Heights come
    from the licensed source landscape samples, with a graded road embankment.
    """
    import bisect
    field = json.loads((OUT / "Source/Slum_Terrain_Heightfield.json").read_text())
    xs, ys, heights = field["xs"], field["ys"], field["heights"]
    nx = len(xs)

    def ground(x, y):
        fx = min(nx - 1.001, max(0, (x - xs[0]) / 200))
        fy = min(len(ys) - 1.001, max(0, (y - ys[0]) / 200))
        ix, iy = int(fx), int(fy)
        tx, ty = fx - ix, fy - iy
        return sum(heights[(iy+j)*nx+ix+i] * (tx if i else 1-tx) * (ty if j else 1-ty)
                   for j in (0, 1) for i in (0, 1))

    def ease(value):
        t = min(1, max(0, value))
        return t*t*(3-2*t)

    def lateral(s):
        return 6000 * ease((s - 60000) / 3500) * (1 - ease((s - 76000) / 6000))

    stations = list(range(60000, 76000, 150)) + [76000]
    raw = [max(ground(-12000-lateral(s)+side, s-60000) for side in (-450, 0, 450)) + 30
           for s in stations]
    graded = [max(z - abs(other-s)*.12 for other, z in zip(stations, raw)) for s in stations]

    def height(s):
        i = min(len(stations)-2, max(0, bisect.bisect_right(stations, s)-1))
        t = min(1, max(0, (s-stations[i])/(stations[i+1]-stations[i])))
        return graded[i]*(1-t) + graded[i+1]*t

    result = []
    for s, y, z in points:
        if 58000 < s < 60000:
            z += (graded[0] - 232) * ease((s-58000)/2000)
        elif 60000 <= s <= 76000:
            y, z = lateral(s), height(s)
        elif 76000 < s < 82000:
            y = lateral(s)
            z = graded[-1] + (500 - graded[-1]) * ease((s-76000)/6000)
        result.append((s, y, z))
    return result


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
