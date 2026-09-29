"""Inspect the available GLB warning-sign set for import readiness."""
import bpy
import json
from pathlib import Path

source = Path(r"G:\3d assets\Russian_Rusted_Signs_Pack-3863f305\glb\converted\russian_rusted_signs_pack.glb")
texture_dir = Path(r"F:\Carnival\Saved\WorldExpansion\ExternalSource\AdditionalAssets\RustedSigns\Textures")
texture_dir.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(source))
meshes = []
for obj in bpy.context.scene.objects:
    if obj.type != "MESH":
        continue
    materials = []
    for material in obj.data.materials:
        images = []
        if material and material.use_nodes:
            for node in material.node_tree.nodes:
                if node.type == "TEX_IMAGE" and node.image:
                    image_path = texture_dir / (node.image.name + ".png")
                    if not image_path.exists():
                        node.image.filepath_raw = str(image_path)
                        node.image.file_format = "PNG"
                        node.image.save()
                    targets = [f"{link.to_node.name}.{link.to_socket.name}" for link in node.outputs["Color"].links]
                    images.append({"name": node.image.name, "size": list(node.image.size),
                                   "packed": bool(node.image.packed_file), "targets": targets,
                                   "saved_copy": str(image_path)})
        materials.append({"name": material.name if material else None, "images": images})
    verts = [obj.matrix_world @ v.co for v in obj.data.vertices]
    mins = [min(v[i] for v in verts) * 100 for i in range(3)] if verts else [0, 0, 0]
    maxs = [max(v[i] for v in verts) * 100 for i in range(3)] if verts else [0, 0, 0]
    uv_values = [loop.uv for loop in obj.data.uv_layers.active.data] if obj.data.uv_layers.active else []
    uv_bounds = [round(min(v[i] for v in uv_values), 6) for i in range(2)] + [
        round(max(v[i] for v in uv_values), 6) for i in range(2)] if uv_values else None
    meshes.append({"name": obj.name, "location_cm": [round(v * 100, 2) for v in obj.location],
                   "dimensions_cm": [round(maxs[i] - mins[i], 2) for i in range(3)],
                   "uv_bounds": uv_bounds, "vertices": len(obj.data.vertices),
                   "faces": len(obj.data.polygons), "materials": materials})
report = {"source": str(source), "bytes": source.stat().st_size, "meshes": meshes}
Path(r"F:\Carnival\Saved\WorldExpansion\Rusted_Signs_Inspection.json").write_text(
    json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"source": report["source"], "bytes": report["bytes"], "mesh_count": len(meshes),
                  "mesh_summaries": [{"name": m["name"], "dimensions_cm": m["dimensions_cm"],
                                      "faces": m["faces"], "materials": m["materials"]} for m in meshes]}, indent=2))
