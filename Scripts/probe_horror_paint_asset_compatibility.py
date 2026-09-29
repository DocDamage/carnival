"""Load a representative HorrorPaint volume in a scratch UE project and export previews."""
import json
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival\Saved\WorldExpansion\AssetCompatProbe")
VOLUME = "HorrorPaintVol48"
ASSET_ROOT = "/Game/" + VOLUME
OUT = ROOT / "Compatibility_Report.json"
PREVIEWS = ROOT / "TexturePreviews"
report = {"volume": VOLUME, "assets": [], "exports": [], "errors": []}

try:
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    asset_paths = [ASSET_ROOT + "/Maps/Demo"]
    asset_paths += [ASSET_ROOT + f"/Textures/T_Picture_{i:02d}_D" for i in range(1, 15)]
    asset_paths += [ASSET_ROOT + f"/Textures/T_Photo_{i:02d}_D" for i in range(1, 7)]
    asset_paths += [ASSET_ROOT + f"/Materials/Inst_Picture_{i:02d}" for i in range(1, 15)]
    asset_paths += [ASSET_ROOT + f"/Materials/Inst_Photo_{i:02d}" for i in range(1, 10)]
    asset_paths += [ASSET_ROOT + f"/Meshes/SM_Picture_{i:02d}" for i in range(1, 15)]
    asset_paths += [ASSET_ROOT + f"/Meshes/SM_Photo_{i:02d}" for i in range(1, 10)]
    for path in asset_paths:
        try:
            asset = unreal.load_asset(path)
            row = {"path": path, "loaded": bool(asset)}
            if asset:
                row["class"] = asset.get_class().get_name()
                if isinstance(asset, unreal.Texture2D):
                    filename = str(PREVIEWS / (asset.get_name() + ".tga"))
                    try:
                        task = unreal.AssetExportTask()
                        task.set_editor_property("object", asset)
                        task.set_editor_property("filename", filename)
                        task.set_editor_property("automated", True)
                        task.set_editor_property("prompt", False)
                        task.set_editor_property("replace_identical", True)
                        task.set_editor_property("write_empty_files", False)
                        if hasattr(unreal, "TextureExporterTGA"):
                            task.set_editor_property("exporter", unreal.TextureExporterTGA())
                        ok = unreal.Exporter.run_asset_export_task(task)
                        report["exports"].append({"asset": path, "filename": filename,
                                                  "success": bool(ok),
                                                  "warnings": list(task.get_editor_property("errors"))})
                    except Exception as exc:
                        report["exports"].append({"asset": path, "filename": filename,
                                                  "success": False, "error": repr(exc)})
            report["assets"].append(row)
        except Exception:
            report["assets"].append({"path": path, "loaded": False,
                                     "error": traceback.format_exc()})
except Exception:
    report["errors"].append(traceback.format_exc())
finally:
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("HORROR_PAINT_ASSET_PROBE_" + ("COMPLETE" if not report["errors"] else "FAILED"))
    unreal.SystemLibrary.quit_editor()
