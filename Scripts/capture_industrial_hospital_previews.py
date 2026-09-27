"""Render source-map views for authoring; no source or project maps are saved."""
import json
import time
import traceback
from pathlib import Path
import unreal

OUT = Path(r"F:\Carnival\Saved\IndustrialHospital\Previews")
OUT.mkdir(parents=True, exist_ok=True)
CASES = [
    ("/Game/IndustrialSlums/Levels/L_DemoScene", "Slums_Overview",
     (18000.0, -42000.0, 32000.0), (-12000.0, 1000.0, 0.0)),
    (None, "Slums_Central_Block",
     (-5000.0, -11000.0, 2600.0), (-5000.0, 6000.0, 0.0)),
    ("/Game/Hospital_Meshingun/Environment/Map/MainMap", "Hospital_Overview",
     (8000.0, -22000.0, 17000.0), (6500.0, -2500.0, 0.0)),
    (None, "Hospital_Entrance",
     (15000.0, -8500.0, 2300.0), (9000.0, -2700.0, 150.0)),
]

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
viewport = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
state = {"index": 0, "phase": "load", "deadline": time.monotonic() + 3,
         "timeout": 0.0, "busy": False, "camera": None, "world": None}
report = {"images": [], "visibility_api": None}

def finish():
    (OUT / "Capture_Report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.unregister_slate_post_tick_callback(handle)
    unreal.SystemLibrary.quit_editor()

def set_night_levels(world):
    names = []
    try:
        levels = list(unreal.EditorLevelUtils.get_levels(world))
        for level in levels:
            path = level.get_path_name()
            if path.endswith("L_Day.L_Day:PersistentLevel") or path.endswith("L_Dawn.L_Dawn:PersistentLevel"):
                if hasattr(unreal.EditorLevelUtils, "set_level_visibility"):
                    unreal.EditorLevelUtils.set_level_visibility(level, False, True)
                    names.append(path)
        report["visibility_api"] = "EditorLevelUtils.set_level_visibility"
        report["hidden_levels"] = names
    except Exception as exc:
        report["visibility_error"] = repr(exc)

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
        map_path, name, camera_pos, target = CASES[state["index"]]
        if state["phase"] == "load":
            if map_path:
                world = unreal.EditorLoadingAndSavingUtils.load_map(map_path)
                state["world"] = world
                report.setdefault("maps", []).append({"asset_path": map_path, "world": world.get_path_name()})
                set_night_levels(world)
                unreal.SystemLibrary.execute_console_command(world, "r.RDG.ParallelExecute 0")
                unreal.SystemLibrary.execute_console_command(world, "r.ScreenPercentage 100")
                state["camera"] = eas.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(0, 0, 10000))
                state["camera"].camera_component.set_editor_property("field_of_view", 65.0)
            world = state["world"]
            camera = state["camera"]
            camera.set_actor_location(unreal.Vector(*camera_pos), False, True)
            camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera_pos, target), False)
            viewport.set_level_viewport_camera_info(camera.get_actor_location(), camera.get_actor_rotation())
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_set_game_view(True)
            state.update(phase="capture", deadline=time.monotonic() + 5)
        elif state["phase"] == "capture":
            image_path = OUT / (name + ".png")
            if image_path.exists():
                image_path.unlink()
            unreal.SystemLibrary.execute_console_command(
                state["world"],
                'HighResShot 1600x1000 filename="' + str(image_path).replace("\\", "/") + '"')
            state.update(phase="wait", timeout=time.monotonic() + 120, deadline=time.monotonic() + 0.4)
        elif state["phase"] == "wait":
            image_path = OUT / (name + ".png")
            if image_path.exists():
                report["images"].append(str(image_path))
                state["index"] += 1
                state["phase"] = "load"
                state["deadline"] = time.monotonic() + (4 if state["index"] in (2,) else 2)
            elif time.monotonic() > state["timeout"]:
                raise TimeoutError("Screenshot was not created: " + str(image_path))
    except Exception:
        report["error"] = traceback.format_exc()
        finish()
    finally:
        state["busy"] = False

handle = unreal.register_slate_post_tick_callback(tick)
