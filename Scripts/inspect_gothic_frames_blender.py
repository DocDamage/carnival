"""Read-only extract frame mesh dimensions, material slots, and UVs from source FBXs."""
import bpy, json
from pathlib import Path

root = Path(r"G:\3d assets\Medieval3c5a0a999b62V1\Gothic_Props\Assets\Meshes")
out = Path(r"F:\Carnival\Saved\WorldExpansion\Gothic_Frame_Mesh_Inspection.json")
rows = []
for path in sorted(root.glob("SM_Prop_Frame_*.fbx")):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.fbx_import(filepath=str(path), use_custom_normals=True)
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        paint_polys = [p for p in obj.data.polygons if p.material_index == 1]
        avg_normal = [0.0, 0.0, 0.0]
        if paint_polys:
            for poly in paint_polys:
                for i, value in enumerate(poly.normal):
                    avg_normal[i] += value
            avg_normal = [value / len(paint_polys) for value in avg_normal]
        rows.append({
            "source": str(path), "object": obj.name,
            "dimensions_m": list(obj.dimensions),
            "bounds_min_m": [min(v[i] for v in obj.bound_box) for i in range(3)],
            "bounds_max_m": [max(v[i] for v in obj.bound_box) for i in range(3)],
            "materials": [({
                "name": m.name,
                "images": [n.image.filepath for n in m.node_tree.nodes
                           if n.type == "TEX_IMAGE" and n.image] if m and m.use_nodes else [],
            } if m else None) for m in obj.data.materials],
            "uv_layers": [uv.name for uv in obj.data.uv_layers],
            "polygons": len(obj.data.polygons),
            "painting_polygon_count": len(paint_polys),
            "painting_avg_normal": avg_normal,
        })
out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
print(out.read_text(encoding="utf-8"))
