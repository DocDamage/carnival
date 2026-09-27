import json
import traceback
import unreal
from pathlib import Path

ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/IndustrialHospital/Source_Probe.json"
result = {}
try:
    project_source = ROOT / "Assets/Abandoned Toy Factory.zip"
    extracted = ROOT / "Saved/IndustrialHospital/Source/Audio/Abandoned Toy Assembly Line.mp3"
    result["audio_source"] = str(extracted)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    task = unreal.AssetImportTask()
    task.filename = str(extracted)
    task.destination_path = "/Game/Carnival/Audio/IndustrialHospital"
    task.destination_name = "Abandoned_Toy_Assembly_Line"
    task.automated = True
    task.save = True
    tools.import_asset_tasks([task])
    assets = [obj.get_path_name() for obj in task.get_editor_property("imported_object_paths")]
    result["audio_imported_paths"] = assets
    result["audio_asset_classes"] = {
        path: (unreal.load_asset(path).get_class().get_name() if unreal.load_asset(path) else None)
        for path in assets
    }
except Exception:
    result["audio_error"] = traceback.format_exc()

try:
    world = unreal.EditorLoadingAndSavingUtils.load_map("/Game/IndustrialSlums/Levels/L_DemoScene")
    landscape = next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
                     if a.get_class().get_name() == "Landscape")
    coords = [(x, y, 0.0) for y in range(0, 20001, 2000) for x in (-18000.0, -15000.0, -12000.0)]
    heights = unreal.CarnivalWorldEditorLibrary.sample_landscape_heights(
        landscape, [unreal.Vector(*p) for p in coords]
    )
    result["slums_ground_samples"] = [
        {"point": p, "height": float(z)} for p, z in zip(coords, heights)
    ]
except Exception:
    result["slums_ground_error"] = traceback.format_exc()

OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log("INDUSTRIAL_HOSPITAL_SOURCE_PROBE_SAVED")
