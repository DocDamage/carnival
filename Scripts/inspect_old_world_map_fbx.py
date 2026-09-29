"""Inspect the user-supplied antique map FBX without changing its source."""
import json
from pathlib import Path
import bpy

source = Path(r"G:\3d assets\Old_World_Map-b87b32f3\fbx\old-world-map_extracted\source\old-map-iceland.fbx")
output = Path(r"F:\Carnival\Saved\WorldExpansion\Old_World_Map_Source_Inspection.json")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(source), use_custom_normals=True)
rows = []
for obj in bpy.context.scene.objects:
    if obj.type != "MESH":
        continue
    rows.append({
        "object": obj.name,
        "dimensions_m": list(obj.dimensions),
        "bounds_min_m": [min(v[i] for v in obj.bound_box) for i in range(3)],
        "bounds_max_m": [max(v[i] for v in obj.bound_box) for i in range(3)],
        "materials": [({
            "name": material.name,
            "images": [node.image.filepath for node in material.node_tree.nodes
                       if node.type == "TEX_IMAGE" and node.image]
        } if material and material.use_nodes else None) for material in obj.data.materials],
        "uv_layers": [uv.name for uv in obj.data.uv_layers],
        "polygons": len(obj.data.polygons),
    })
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps({"source": str(source), "meshes": rows}, indent=2), encoding="utf-8")
print(output.read_text(encoding="utf-8"))
