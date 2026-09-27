"""Render candidate districts in the supplied slums scene without saving it."""
import json
import time
import traceback
from pathlib import Path
import unreal

OUT = Path(r"F:\Carnival\Saved\IndustrialHospital\Previews")
OUT.mkdir(parents=True, exist_ok=True)
MAP_PATH = "/Game/IndustrialSlums/Levels/L_DemoScene"
CASES = [
    ("Slums_District_South", (-15000.0, -16000.0, 2800.0), (-15000.0, 4000.0, 0.0)),
    ("Slums_District_North", (-15000.0, 4000.0, 3200.0), (-15000.0, 17000.0, 0.0)),
    ("Slums_District_Aerial", (-15000.0, 8000.0, 16000.0), (-15000.0, 8000.0, 0.0)),
]
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
viewport = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
unreal.SystemLibrary.execute_console_command(world, "r.RDG.ParallelExecute 0")
unreal.SystemLibrary.execute_console_command(world, "r.ScreenPercentage 100")
camera = eas.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(0, 0, 10000))
camera.camera_component.set_editor_property("field_of_view", 65.0)
state = {"index": 0, "phase": "position", "deadline": time.monotonic() + 5,
         "timeout": 0.0, "busy": False}
report = {"map": MAP_PATH, "images": []}

def finish():
    (OUT / "Slums_District_Capture.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
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
        if state["phase"] == "position":
            name, position, target = CASES[state["index"]]
            camera.set_actor_location(unreal.Vector(*position), False, True)
            camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(position, target), False)
            viewport.set_level_viewport_camera_info(camera.get_actor_location(), camera.get_actor_rotation())
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_set_game_view(True)
            state.update(phase="capture", deadline=time.monotonic() + 3)
        elif state["phase"] == "capture":
            name = CASES[state["index"]][0]
            path = OUT / (name + ".png")
            if path.exists():
                path.unlink()
            unreal.SystemLibrary.execute_console_command(
                world, 'HighResShot 1600x1000 filename="' + str(path).replace("\\", "/") + '"')
            state.update(phase="wait", timeout=time.monotonic() + 90, deadline=time.monotonic() + 0.3)
        elif state["phase"] == "wait":
            name = CASES[state["index"]][0]
            path = OUT / (name + ".png")
            if path.exists():
                report["images"].append(str(path))
                state["index"] += 1
                state.update(phase="position", deadline=time.monotonic() + 2)
            elif time.monotonic() > state["timeout"]:
                raise TimeoutError("Screenshot was not created: " + str(path))
    except Exception:
        report["error"] = traceback.format_exc()
        finish()
    finally:
        state["busy"] = False

handle = unreal.register_slate_post_tick_callback(tick)
