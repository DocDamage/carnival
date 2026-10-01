"""Water and underwater-region review captures: docks from deck height, Atlantis, Shipwreck, tunnels. Editor game view; no saves."""
import json
import time
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
MAIN = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
OUT = ROOT / "Saved/WorldExpansion/Evidence/WaterReview_20261001"
OUT.mkdir(parents=True, exist_ok=False)
CASES = [
    ("01_NorthDock_Water_From_Deck", (-50000.0, -60000.0, -240.0), (-6000.0, 9000.0, 1000.0), 75.0),
    ("02_NorthDock_EndPlatform_Gap", (-55000.0, -47000.0, 600.0), (2500.0, 4500.0, 1500.0), 75.0),
    ("03_EastDock_Fingers_Gap", (69500.0, 21000.0, 600.0), (-4000.0, -9000.0, 2200.0), 75.0),
    ("04_EastDock_Water", (70000.0, 26000.0, -240.0), (9000.0, -6000.0, 1500.0), 75.0),
    ("05_Atlantis_Interior", (-13000.0, -11000.0, -1750.0), (-2500.0, -1500.0, 500.0), 80.0),
    ("06_Atlantis_Overview", (-13000.0, -11000.0, -1800.0), (6000.0, -9000.0, 5000.0), 70.0),
    ("07_Shipwreck_Interior", (-6033.0, -10010.0, -2050.0), (-1800.0, 1200.0, 400.0), 80.0),
    ("08_Shipwreck_Overview", (-6033.0, -10010.0, -2100.0), (5000.0, -7000.0, 4000.0), 70.0),
    ("09_Sewer_Atlantis_Tunnel", (-21000.0, -11000.0, -1750.0), (-1500.0, 600.0, 250.0), 80.0),
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
