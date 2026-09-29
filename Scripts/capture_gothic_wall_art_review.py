"""Capture eye-level reviews of the new Gothic art placements."""
import json
import time
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
MAP = "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Prison"
OUT = ROOT / "Saved/WorldExpansion/Gothic_WallArt_Review"
OUT.mkdir(parents=True, exist_ok=True)
CASES = [
    ("MainTower_Large", (-1000.0, -1732.0, 2022.0), (-222.0, -1732.0, 2022.0)),
    ("MainTower_Pair", (-1000.0, -1132.0, 2022.0), (-222.0, -1132.0, 2022.0)),
    ("Tower_Lower_Pair", (1829.0, -1400.0, 2022.0), (1829.0, -842.0, 2022.0)),
    ("Tower_Upper_Pair", (1500.0, -1132.0, 3822.0), (940.0, -1132.0, 3822.0)),
]
report = {"map": MAP, "captures": [], "errors": []}
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
viewport = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise RuntimeError("Could not load " + MAP)
camera = eas.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(0, 0, 1000))
camera.camera_component.set_editor_property("field_of_view", 55.0)
post = camera.camera_component.get_editor_property("post_process_settings")
for key, value in {
    "override_auto_exposure_method": True,
    "auto_exposure_method": unreal.AutoExposureMethod.AEM_MANUAL,
    "override_auto_exposure_bias": True,
    "auto_exposure_bias": 0.0,
    "override_auto_exposure_apply_physical_camera_exposure": True,
    "auto_exposure_apply_physical_camera_exposure": False,
}.items():
    post.set_editor_property(key, value)
camera.camera_component.set_editor_property("post_process_settings", post)
state = {"index": 0, "phase": "position", "deadline": time.monotonic() + 6,
         "timeout": 0.0, "busy": False}

def finish():
    try:
        eas.destroy_actor(camera)
    except Exception:
        pass
    (OUT / "Capture_Report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.unregister_slate_post_tick_callback(handle)
    unreal.SystemLibrary.quit_editor()

def tick(delta):
    if state["busy"]:
        return
    state["busy"] = True
    try:
        if time.monotonic() < state["deadline"]:
            return
        if state["index"] >= len(CASES):
            finish()
            return
        name, position, target = CASES[state["index"]]
        if state["phase"] == "position":
            camera.set_actor_location(unreal.Vector(*position), False, True)
            camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(position, target), False)
            viewport.set_level_viewport_camera_info(camera.get_actor_location(), camera.get_actor_rotation())
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_set_game_view(True)
            unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
            unreal.SystemLibrary.execute_console_command(world, "r.ScreenPercentage 100")
            state.update(phase="capture", deadline=time.monotonic() + 3)
        elif state["phase"] == "capture":
            path = OUT / (name + ".png")
            if path.exists():
                path.unlink()
            unreal.SystemLibrary.execute_console_command(
                world, 'HighResShot 1440x900 filename="' + str(path).replace("\\", "/") + '"')
            state.update(phase="wait", timeout=time.monotonic() + 60, deadline=time.monotonic() + 1)
        elif state["phase"] == "wait":
            path = OUT / (name + ".png")
            if path.exists() and path.stat().st_size > 10000:
                report["captures"].append({"name": name, "image": str(path), "bytes": path.stat().st_size})
                state.update(index=state["index"] + 1, phase="position", deadline=time.monotonic() + 2)
            elif time.monotonic() > state["timeout"]:
                raise TimeoutError("Screenshot was not produced: " + str(path))
    except Exception:
        report["errors"].append(traceback.format_exc())
        finish()
    finally:
        state["busy"] = False

handle = unreal.register_slate_post_tick_callback(tick)
