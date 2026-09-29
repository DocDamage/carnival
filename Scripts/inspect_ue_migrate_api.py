"""Inspect the installed editor's Python migration helpers."""
import json
from pathlib import Path
import unreal

classes = ["EditorAssetLibrary", "AssetTools", "AssetToolsHelpers", "EditorUtilityLibrary"]
report = {"classes": {}, "asset_tools_instance": [], "errors": []}
for name in classes:
    obj = getattr(unreal, name, None)
    report["classes"][name] = [entry for entry in dir(obj) if "migrat" in entry.lower()] if obj else None
try:
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    report["asset_tools_instance"] = [entry for entry in dir(tools) if "migrat" in entry.lower()]
    report["asset_tools_type"] = tools.get_class().get_path_name()
    report["migrate_packages_doc"] = str(tools.migrate_packages.__doc__)
except Exception as exc:
    report["errors"].append(repr(exc))
out = Path(r"F:\Carnival\Saved\WorldExpansion\AssetCompatProbe\Migration_API.json")
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.SystemLibrary.quit_editor()
