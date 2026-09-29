"""Capture the expansion in its integrated Carnival lighting context."""
import json
import time
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
MAIN = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
OUT = ROOT / "Saved/WorldExpansion/Evidence/ConnectedRegions"
OUT.mkdir(parents=True, exist_ok=True)
CASES = [
    ("00_World_Overview", (12500.0, 21500.0, 0.0), (0.0, 0.0, 300000.0), 82.0),
    ("01_Docks_North", (-55000.0, -49000.0, 400.0), (10500.0, -15000.0, 9500.0), 70.0),
    ("02_Prison", (-26000.0, -34000.0, 500.0), (18000.0, -25000.0, 18000.0), 70.0),
    ("03_Research_Lab_A", (-41000.0, -8000.0, 500.0), (6500.0, -8500.0, 6000.0), 70.0),
    ("04_Research_Lab_B", (-41000.0, -4800.0, 500.0), (6500.0, -8500.0, 6000.0), 70.0),
    ("05_Docks_East", (70000.0, 21000.0, 300.0), (14000.0, -21000.0, 12000.0), 70.0),
    ("06_Sewers", (-27000.0, -10500.0, -1800.0), (8500.0, -7000.0, 5500.0), 70.0),
    ("07_Atlantis", (-13000.0, -11000.0, -1700.0), (8500.0, -15000.0, 7500.0), 70.0),
    ("08_Shipwreck", (-6000.0, -10000.0, -2100.0), (7500.0, -13500.0, 8000.0), 70.0),
    ("09_Prison_Sewer_Stair", (-27000.0, -22000.0, -300.0), (4500.0, -8000.0, 5500.0), 72.0),
    ("10_Sewer_Atlantis_Tunnel", (-23000.0, -10300.0, -1800.0), (5000.0, -6500.0, 3500.0), 72.0),
    ("11_Atlantis_Shipwreck_Tunnel", (-6500.0, -10500.0, -1900.0), (3500.0, -5000.0, 2200.0), 72.0),
]
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
report = {"map": MAIN, "captures": [], "errors": []}
state = {"phase": "setup", "index": -1, "deadline": time.monotonic() + 5,
         "timeout": 0.0, "busy": False, "world": None, "camera": None}


def finish():
    (OUT / "Capture_Report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.unregister_slate_post_tick_callback(handle)
    unreal.SystemLibrary.quit_editor()


def aim(camera, target):
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
        camera.get_actor_location(), unreal.Vector(*target)), False)


def tick(delta):
    if state["busy"]:
        return
    state["busy"] = True
    try:
        if time.monotonic() < state["deadline"]:
            return
        if state["phase"] == "wait_image":
            name = CASES[state["index"]][0]
            path = OUT / (name + ".png")
            if path.exists() and path.stat().st_size > 10000:
                report["captures"].append({"name": name, "image": str(path), "bytes": path.stat().st_size,
                                           "camera_location_cm": state["camera"].get_actor_location().to_tuple()})
                (OUT / "Capture_Report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
                state.update(phase="next", deadline=time.monotonic() + 3)
            elif time.monotonic() > state["timeout"]:
                raise TimeoutError("HighResShot did not produce " + str(path))
            else:
                state["deadline"] = time.monotonic() + 1
            return

        if state["phase"] == "capture":
            name = CASES[state["index"]][0]
            path = OUT / (name + ".png")
            if path.exists():
                path.unlink()
            unreal.SystemLibrary.execute_console_command(
                state["world"], 'HighResShot 1440x900 filename="' + str(path).replace("\\", "/") + '"')
            state.update(phase="wait_image", timeout=time.monotonic() + 90,
                         deadline=time.monotonic() + 1)
            return

        if state["phase"] == "setup":
            world = unreal.EditorLoadingAndSavingUtils.load_map(MAIN)
            if not world:
                raise RuntimeError("Could not load the integrated Carnival world")
            state["world"] = world
            camera = eas.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(0, 0, 0))
            camera.camera_component.set_editor_property("field_of_view", 82.0)
            state["camera"] = camera
            state["phase"] = "next"
            state["index"] = -1

        state["index"] += 1
        if state["index"] >= len(CASES):
            finish()
            return
        name, target, offset, fov = CASES[state["index"]]
        camera_pos = tuple(target[i] + offset[i] for i in range(3))
        state["camera"].set_actor_location(unreal.Vector(*camera_pos), False, True)
        state["camera"].camera_component.set_editor_property("field_of_view", fov)
        aim(state["camera"], target)
        editor.set_level_viewport_camera_info(state["camera"].get_actor_location(), state["camera"].get_actor_rotation())
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_set_game_view(True)
        report["active_root_level_count"] = len(unreal.EditorLevelUtils.get_levels(state["world"]))
        state.update(phase="capture", deadline=time.monotonic() + 4)
    except Exception:
        report["errors"].append(traceback.format_exc())
        finish()
    finally:
        state["busy"] = False


handle = unreal.register_slate_post_tick_callback(tick)
