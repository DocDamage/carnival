"""Inspect candidate G-drive meshes without modifying their source files."""
import bpy
import json
from pathlib import Path

ROOT = Path(r"G:\3d assets")
CASES = {
    "zoltar": (ROOT / "Zoltar_Machine-331b8a9b/fbx/zoltar.fbx", "fbx"),
    "wire_coils": (ROOT / "Industrial_Metal_Wire_Coil_Stack___Factory_Props-2380d90f/fbx/fbx.fbx", "fbx"),
    "priming_pump": (ROOT / "Brunel_Museum_Priming_Pump-763300ab/glb/converted/brunel_museum_priming_pump.glb", "glb"),
}
result = {}
for key, (source, kind) in CASES.items():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if kind == "fbx":
        bpy.ops.import_scene.fbx(filepath=str(source))
    else:
        bpy.ops.import_scene.gltf(filepath=str(source))
    items = []
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        vertices = [obj.matrix_world @ v.co for v in obj.data.vertices]
        if vertices:
            mins = [min(v[i] for v in vertices) for i in range(3)]
            maxs = [max(v[i] for v in vertices) for i in range(3)]
        else:
            mins = maxs = [0, 0, 0]
        mats = []
        for material in obj.data.materials:
            if not material:
                mats.append(None)
                continue
            images = []
            for node in material.node_tree.nodes if material.use_nodes else []:
                if node.type == "TEX_IMAGE" and node.image:
                    images.append({"name": node.image.name, "filepath": node.image.filepath,
                                   "size": list(node.image.size), "packed": bool(node.image.packed_file)})
            mats.append({"name": material.name, "diffuse_color": list(material.diffuse_color), "images": images})
        attrs = []
        try:
            attrs = [{"name": a.name, "type": a.data_type, "domain": a.domain} for a in obj.data.color_attributes]
        except Exception:
            pass
        items.append({"name": obj.name, "dimensions_cm": [round(v * 100, 2) for v in obj.dimensions],
                      "vertices": len(obj.data.vertices), "faces": len(obj.data.polygons),
                      "materials": mats, "color_attributes": attrs})
    result[key] = {"source": str(source), "bytes": source.stat().st_size if source.exists() else None,
                   "meshes": items}
Path(r"F:\Carnival\Saved\WorldExpansion\GDrive_Asset_Material_Inspection.json").write_text(
    json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps({k: {"bytes": v["bytes"], "mesh_count": len(v["meshes"]),
                      "meshes": [{"name": m["name"], "dimensions_cm": m["dimensions_cm"],
                                  "vertices": m["vertices"], "materials": m["materials"],
                                  "color_attributes": m["color_attributes"]} for m in v["meshes"]]}
                  for k, v in result.items()}, indent=2))
