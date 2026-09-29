"""Migrate one verified painting/photo collection and its referenced dependencies."""
import json
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
VOLUME = "HorrorPaintVol48"
SOURCE_PROJECT = Path(r"F:\Carnival\Saved\WorldExpansion\AssetCompatProbe")
DEST_CONTENT = ROOT / "Content"
OUT = ROOT / "Saved/WorldExpansion/HorrorPaintVol48_Migration.json"
report = {"volume": VOLUME, "source_project": str(SOURCE_PROJECT),
          "destination_content": str(DEST_CONTENT), "packages": [],
          "migration_api": None, "success": False, "errors": []}

try:
    packages = [f"/Game/{VOLUME}/Meshes/SM_Picture_{i:02d}" for i in range(1, 15)]
    packages += [f"/Game/{VOLUME}/Meshes/SM_Photo_{i:02d}" for i in range(1, 10)]
    for path in packages:
        asset = unreal.load_asset(path)
        if not asset:
            raise RuntimeError("Could not load source artwork mesh " + path)
        report["packages"].append({"path": path, "class": asset.get_class().get_name()})

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    migrate = getattr(asset_tools, "migrate_packages", None)
    if not migrate:
        raise RuntimeError("AssetTools.migrate_packages is unavailable")
    report["migration_api"] = str(migrate.__doc__)
    migrate(packages, str(DEST_CONTENT))
    report["success"] = True
except Exception:
    report["errors"].append(traceback.format_exc())
finally:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("HORROR_PAINT_MIGRATION_" + ("COMPLETE" if report["success"] else "FAILED"))
    unreal.SystemLibrary.quit_editor()
