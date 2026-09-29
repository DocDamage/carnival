"""Turn the sampled vendor landscape window into a compact authored mesh."""
import bpy
import json
from pathlib import Path

ROOT = Path(r"F:\Carnival")
source = json.loads((ROOT / "Saved/IndustrialHospital/Source/Slum_Terrain_Heightfield.json").read_text(encoding="utf-8"))
export_dir = ROOT / "Saved/IndustrialHospital/Source/FBX"
export_dir.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 0.01

xs, ys, heights = source["xs"], source["ys"], source["heights"]
nx = len(xs)
verts = [(x, -y, heights[j * nx + i] - 8.0) for j, y in enumerate(ys) for i, x in enumerate(xs)]
faces = []
for j in range(len(ys) - 1):
    for i in range(len(xs) - 1):
        a = j * nx + i
        # Mirroring source Y changes handedness; reverse winding so the
        # walkable surface has upward normals in Blender and after FBX import.
        faces.append((a + nx, a + 1 + nx, a + 1, a))

mesh = bpy.data.meshes.new("SM_IndustrialSlums_TerrainPatch")
mesh.from_pydata(verts, [], faces)
mesh.update()
obj = bpy.data.objects.new("SM_IndustrialSlums_TerrainPatch", mesh)
scene.collection.objects.link(obj)
material = bpy.data.materials.new("IndustrialGround")
mesh.materials.append(material)
uv = mesh.uv_layers.new(name="UVMap")
for poly in mesh.polygons:
    poly.use_smooth = True
    for loop_index in poly.loop_indices:
        co = mesh.vertices[mesh.loops[loop_index].vertex_index].co
        uv.data[loop_index].uv = (co.x / 600.0, co.y / 600.0)

bpy.ops.object.select_all(action="DESELECT")
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
fbx = export_dir / "SM_IndustrialSlums_TerrainPatch.fbx"
bpy.ops.export_scene.fbx(
    filepath=str(fbx), use_selection=True, object_types={"MESH"}, bake_anim=False,
    axis_forward="-Y", axis_up="Z", apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_UNITS", path_mode="RELATIVE", use_mesh_modifiers=True,
)

report = {
    "fbx": str(fbx),
    "vertices": len(verts),
    "faces": len(faces),
    "grid_cm": source["grid_cm"],
    "height_min_cm": min(heights),
    "height_max_cm": max(heights),
}
(ROOT / "Saved/IndustrialHospital/Industrial_Slums_Terrain.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("INDUSTRIAL_SLUMS_TERRAIN_MESH", report["vertices"], "vertices", report["faces"], "faces", flush=True)
