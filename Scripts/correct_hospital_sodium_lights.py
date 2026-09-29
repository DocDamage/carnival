"""Correct only the six authored sodium lights; back up their maps first."""
import hashlib
import json
import shutil
import sys
import traceback
from datetime import datetime
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
sys.path.insert(0, str(ROOT / "Scripts"))
from industrial_hospital_route_config import OUT, ROUTE_LEVEL, HOSPITAL_EXTERIOR_LEVEL

report = {"success": False, "changes": [], "backups": [], "errors": []}
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
try:
    for path, labels, rgb in (
        (ROUTE_LEVEL, [f"Slum Road Sodium Light {i:02d}" for i in range(1, 5)], (255, 109, 40)),
        (HOSPITAL_EXTERIOR_LEVEL, ["Gate Sodium Lamp West", "Gate Sodium Lamp East"], (255, 61, 23)),
    ):
        file = ROOT / "Content" / (path.removeprefix("/Game/") + ".umap")
        backup = OUT / "Backups" / f"{file.stem}_before_sodium_correction_{stamp}.umap"
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, backup)
        report["backups"].append({"path": str(backup), "sha256": hashlib.sha256(backup.read_bytes()).hexdigest()})
        world = unreal.EditorLoadingAndSavingUtils.load_map(path)
        if not world:
            raise RuntimeError("Could not load " + path)
        actors = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
        for label in labels:
            actor = actors.get(label)
            if not actor or not isinstance(actor, unreal.PointLight):
                raise RuntimeError("Expected authored point light missing: " + label)
            component = actor.get_editor_property("light_component")
            before = component.get_editor_property("light_color")
            before_rgb = [before.r, before.g, before.b]
            actor.modify()
            component.modify()
            component.set_editor_property("light_color", unreal.Color(r=rgb[0], g=rgb[1], b=rgb[2], a=255))
            after = component.get_editor_property("light_color")
            if (after.r, after.g, after.b) != rgb:
                raise RuntimeError("Light colour did not persist in memory: " + label)
            report["changes"].append({"level": path, "label": label,
                "before_rgb": before_rgb, "after_rgb": [after.r, after.g, after.b]})
        if not unreal.EditorLoadingAndSavingUtils.save_map(world, path):
            raise RuntimeError("Could not save " + path)
    report["success"] = True
except Exception:
    report["errors"].append(traceback.format_exc())
finally:
    (OUT / "Sodium_Light_Correction.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("SODIUM_CORRECTION " + str(report["success"]))
