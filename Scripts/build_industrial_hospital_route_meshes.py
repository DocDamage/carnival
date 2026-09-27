"""Build a continuous, 9 m wide motor-road ribbon and landscape shoulders."""
import bpy
import bisect
import json
import math
import sys
from pathlib import Path

ROOT = Path(r"F:\Carnival")
sys.path.insert(0, str(ROOT / "Scripts"))
from industrial_hospital_route_config import (
    OUT, ROAD_CONTROL_POINTS, ROAD_CHUNK_LENGTH_CM, route_manifest,
)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 0.01
export = OUT / "Source/FBX"
export.mkdir(parents=True, exist_ok=True)

materials = {name: bpy.data.materials.new(name) for name in ("SnowAsphalt", "SnowShoulder", "IndustrialGround")}
manifest = []


def distance(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def smooth_path(controls, step=150.0):
    points = []
    for i in range(len(controls) - 1):
        p0, p1, p2, p3 = controls[max(0, i - 1)], controls[i + 0], controls[i + 1], controls[min(len(controls) - 1, i + 2)]
        count = max(2, math.ceil(distance(p1, p2) / step))
        for j in range(count):
            t = j / count
            t2, t3 = t * t, t * t * t
            points.append(tuple(0.5 * (
                2 * p1[k] + (-p0[k] + p2[k]) * t
                + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3
            ) for k in range(3)))
    points.append(tuple(controls[-1]))
    return points


points = smooth_path(ROAD_CONTROL_POINTS)
distances = [0.0]
for a, b in zip(points, points[1:]):
    distances.append(distances[-1] + distance(a, b))


def at(s):
    index = min(len(points) - 2, max(0, bisect.bisect_right(distances, s) - 1))
    span = distances[index + 1] - distances[index]
    alpha = 0.0 if span < 1e-5 else (s - distances[index]) / span
    p = tuple(points[index][k] * (1 - alpha) + points[index + 1][k] * alpha for k in range(3))
    dx = points[index + 1][0] - points[index][0]
    dy = points[index + 1][1] - points[index][1]
    length = max(1e-6, math.hypot(dx, dy))
    return p, (-dy / length, dx / length)


def export_chunk(name, begin, end):
    # One subtle crossfall keeps the road comfortable at bike speed. A wide,
    # gently sloped bed gives the road a convincing ground join through fog.
    profile = [
        (-3000.0, -48.0), (-1800.0, -14.0), (-650.0, -5.0),
        (-450.0, 0.0), (0.0, 14.0), (450.0, 0.0),
        (650.0, -5.0), (1800.0, -14.0), (3000.0, -48.0),
    ]
    rows = max(2, math.ceil((end - begin) / 100.0) + 1)
    verts, faces, slots, indices = [], [], [], []
    for row in range(rows):
        s = begin + (end - begin) * row / (rows - 1)
        p, normal = at(s)
        for offset, elevation in profile:
            verts.append((p[0] + normal[0] * offset, p[1] + normal[1] * offset, p[2] + elevation))
    for row in range(rows - 1):
        for col in range(len(profile) - 1):
            base = row * len(profile) + col
            faces.append((base, base + len(profile), base + len(profile) + 1, base + 1))
            # Faces across the 9 m paved lane use a snow-covered asphalt;
            # shoulders carry salt, grit and drifted snow; outer banks use dirt.
            if 2 <= col <= 5:
                indices.append(0)
            elif col in (1, 6):
                indices.append(1)
            else:
                indices.append(2)

    mesh = bpy.data.meshes.new(name)
    # Unreal and Blender use opposite handedness for FBX's Y axis.
    mesh.from_pydata([(x, -y, z) for x, y, z in verts], [],
                     [tuple(reversed(face)) for face in faces])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    for mat in materials.values():
        mesh.materials.append(mat)
    for poly, index in zip(mesh.polygons, indices):
        poly.material_index = index
    uv = mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            vertex = mesh.vertices[mesh.loops[loop_index].vertex_index].co
            uv.data[loop_index].uv = (vertex.x / 400.0, vertex.y / 400.0)

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    filepath = export / (name + ".fbx")
    bpy.ops.export_scene.fbx(
        filepath=str(filepath), use_selection=True, object_types={"MESH"}, bake_anim=False,
        axis_forward="-Y", axis_up="Z", apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_UNITS", path_mode="RELATIVE",
        use_mesh_modifiers=True, mesh_smooth_type="FACE",
    )
    manifest.append({
        "name": name, "filepath": str(filepath), "vertices": len(verts), "faces": len(faces),
        "distance_start_cm": begin, "distance_end_cm": end,
        "material_slots": list(materials.keys()),
        "bounds_min": [min(v[i] for v in verts) for i in range(3)],
        "bounds_max": [max(v[i] for v in verts) for i in range(3)],
    })
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.meshes.remove(mesh)


for start in range(0, math.ceil(distances[-1]), int(ROAD_CHUNK_LENGTH_CM)):
    end = min(distances[-1], start + ROAD_CHUNK_LENGTH_CM)
    export_chunk("SM_IndustrialHospital_Road_" + str(start // int(ROAD_CHUNK_LENGTH_CM) + 1).zfill(2), start, end)

report = route_manifest(points)
report.update({
    "road_width_m": 9.0,
    "road_bed_width_m": 60.0,
    "road_mesh_count": len(manifest),
    "road_meshes": manifest,
})
(OUT / "Industrial_Hospital_Route_Meshes.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
(OUT / "Industrial_Hospital_Route_Layout.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "Source/Industrial_Hospital_Route.blend"))
print("INDUSTRIAL_HOSPITAL_ROUTE_MESHES", len(manifest), "length_m", round(distances[-1] / 100.0), flush=True)
