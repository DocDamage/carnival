"""Stage/import the user's Gothic painting collection and build simple materials."""
import json
import shutil
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
SOURCE = Path(r"G:\3d assets\Medieval3c5a0a999b62V1\Gothic_Props")
STAGING = ROOT / "Saved/WorldExpansion/ExternalSource/AdditionalAssets/GothicPaintings"
MESH_SOURCE = SOURCE / "Assets/Meshes"
TEXTURE_SOURCE = SOURCE / "Textures"
DEST = "/Game/Carnival/WorldExpansion/WallArt/GothicPaintings"
REPORT = ROOT / "Saved/WorldExpansion/Gothic_WallArt_Import.json"
report = {"success": False, "source": str(SOURCE), "destination": DEST,
          "copied": [], "textures": [], "meshes": [], "materials": [], "errors": []}
eal = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

def make_task(filename, path, name, options=None):
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(filename))
    task.set_editor_property("destination_path", path)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    if options:
        task.set_editor_property("options", options)
    return task

def save(asset):
    if not eal.save_loaded_asset(asset):
        raise RuntimeError("Failed to save " + asset.get_path_name())

try:
    if not SOURCE.is_dir():
        raise FileNotFoundError(str(SOURCE))
    STAGING.mkdir(parents=True, exist_ok=True)
    for filename in [*(f"SM_Prop_Frame_{x}.fbx" for x in "ABC"),
                     *(f"T_Props_Painting_{x}.png" for x in "ABCDEFG")]:
        src = (MESH_SOURCE if filename.lower().endswith(".fbx") else TEXTURE_SOURCE) / filename
        dst = STAGING / filename
        if not src.is_file():
            raise FileNotFoundError(str(src))
        shutil.copy2(src, dst)
        report["copied"].append({"source": str(src), "staged": str(dst), "bytes": dst.stat().st_size})

    eal.make_directory(DEST)
    painting_dir = DEST + "/Textures"
    mesh_dir = DEST + "/Meshes"
    material_dir = DEST + "/Materials"
    for path in (painting_dir, mesh_dir, material_dir):
        eal.make_directory(path)

    tex_tasks = [make_task(STAGING / f"T_Props_Painting_{x}.png", painting_dir,
                           f"T_GothicPainting_{x}") for x in "ABCDEFG"]
    asset_tools.import_asset_tasks(tex_tasks)
    textures = {}
    for x in "ABCDEFG":
        tex = unreal.load_asset(painting_dir + f"/T_GothicPainting_{x}")
        if not tex:
            raise RuntimeError("Failed to import Gothic painting texture " + x)
        tex.set_editor_property("srgb", True)
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
        save(tex)
        textures[x] = tex
        report["textures"].append({"name": x, "path": tex.get_path_name(),
                                   "class": tex.get_class().get_name()})

    fbx_tasks = []
    for x in "ABC":
        opts = unreal.FbxImportUI()
        opts.set_editor_property("automated_import_should_detect_type", False)
        opts.set_editor_property("import_as_skeletal", False)
        opts.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
        opts.set_editor_property("import_materials", False)
        opts.set_editor_property("import_textures", False)
        opts.set_editor_property("import_animations", False)
        sm_data = opts.get_editor_property("static_mesh_import_data")
        sm_data.set_editor_property("convert_scene", True)
        sm_data.set_editor_property("convert_scene_unit", True)
        sm_data.set_editor_property("combine_meshes", True)
        sm_data.set_editor_property("generate_lightmap_u_vs", True)
        sm_data.set_editor_property("auto_generate_collision", False)
        try:
            sm_data.set_editor_property("import_mesh_lo_ds", True)
        except Exception as exc:
            report.setdefault("warnings", []).append("FBX LOD setting unavailable: " + repr(exc))
        fbx_tasks.append(make_task(STAGING / f"SM_Prop_Frame_{x}.fbx", mesh_dir,
                                   f"SM_GothicFrame_{x}", opts))
    asset_tools.import_asset_tasks(fbx_tasks)

    mel = unreal.MaterialEditingLibrary
    frame_material_path = material_dir + "/M_GothicFrame"
    frame_mat = unreal.load_asset(frame_material_path)
    if not frame_mat:
        frame_mat = asset_tools.create_asset("M_GothicFrame", material_dir,
                                             unreal.Material, unreal.MaterialFactoryNew())
        frame_mat.set_editor_property("two_sided", True)
        color = mel.create_material_expression(frame_mat, unreal.MaterialExpressionConstant3Vector, -400, -100)
        color.set_editor_property("constant", unreal.LinearColor(0.055, 0.031, 0.016, 1.0))
        mel.connect_material_property(color, "", unreal.MaterialProperty.MP_BASE_COLOR)
        rough = mel.create_material_expression(frame_mat, unreal.MaterialExpressionConstant, -180, 140)
        rough.set_editor_property("r", 0.68)
        mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
        mel.recompile_material(frame_mat)
        save(frame_mat)

    image_material_path = material_dir + "/M_GothicPaintingImage"
    image_mat = unreal.load_asset(image_material_path)
    if not image_mat:
        image_mat = asset_tools.create_asset("M_GothicPaintingImage", material_dir,
                                             unreal.Material, unreal.MaterialFactoryNew())
        image_mat.set_editor_property("two_sided", True)
        image = mel.create_material_expression(image_mat, unreal.MaterialExpressionTextureSampleParameter2D, -400, -100)
        image.set_editor_property("texture", textures["A"])
        image.set_editor_property("parameter_name", "PaintingTexture")
        mel.connect_material_property(image, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
        rough = mel.create_material_expression(image_mat, unreal.MaterialExpressionConstant, -180, 140)
        rough.set_editor_property("r", 0.88)
        mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
        mel.recompile_material(image_mat)
        save(image_mat)

    image_instances = {}
    for x in "ABCDEFG":
        name = f"MI_GothicPainting_{x}"
        path = material_dir + "/" + name
        mi = unreal.load_asset(path)
        if not mi:
            mi = asset_tools.create_asset(name, material_dir, unreal.MaterialInstanceConstant,
                                          unreal.MaterialInstanceConstantFactoryNew())
        mel.set_material_instance_parent(mi, image_mat)
        mel.set_material_instance_texture_parameter_value(mi, "PaintingTexture", textures[x])
        mel.update_material_instance(mi)
        save(mi)
        image_instances[x] = mi
        report["materials"].append({"name": name, "path": mi.get_path_name(),
                                    "texture": textures[x].get_path_name()})

    for x in "ABC":
        name = f"SM_GothicFrame_{x}"
        mesh = unreal.load_asset(mesh_dir + "/" + name)
        if not mesh:
            raise RuntimeError("Failed to import Gothic frame mesh " + x)
        slots = list(mesh.get_editor_property("static_materials"))
        if len(slots) < 2:
            raise RuntimeError(f"Expected frame and painting slots on {name}; got {len(slots)}")
        source_art = {"A": "G", "B": "C", "C": "E"}[x]
        slots[0].set_editor_property("material_interface", frame_mat)
        slots[1].set_editor_property("material_interface", image_instances[source_art])
        mesh.set_editor_property("static_materials", slots)
        save(mesh)
        box = mesh.get_bounding_box()
        report["meshes"].append({"name": mesh.get_name(), "path": mesh.get_path_name(),
                                 "dimensions_cm": [box.max.x-box.min.x, box.max.y-box.min.y,
                                                   box.max.z-box.min.z],
                                 "materials": [slot.material_interface.get_path_name()
                                               if slot.material_interface else None for slot in slots]})
    report["success"] = True
except Exception:
    report["errors"].append(traceback.format_exc())
finally:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("GOTHIC_WALL_ART_IMPORT_" + ("COMPLETE" if report["success"] else "FAILED"))
    unreal.SystemLibrary.quit_editor()
