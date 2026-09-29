"""Capture representative supplied map assemblies in an off-screen editor viewport."""
import json
import math
import time
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/WorldExpansion/Pack_Previews"
OUT.mkdir(parents=True, exist_ok=True)
CASES = [
    ("Docks_Day_Layout", "/Game/Docks/VOL2_Powell/Maps/LIGHTING_DAY"),
    ("Docks_Night_Layout", "/Game/Docks/VOL2_Powell/Maps/LIGHTING_NIGHT"),
    ("Prison_Overview_Layout", "/Game/HAUNTED_PRISON/Levels/L_Overview"),
    ("Research_Lab_Room_A", "/Game/SciFiWorld/Maps/SciFiCreaturesResearchRoomA"),
    ("Research_Lab_Room_B", "/Game/SciFiWorld/Maps/SciFiCreaturesResearchRoomB"),
    ("Sewer_Core_Layout", "/Game/Sewer/Levels/L_Sewer"),
    ("Sewer_Corridor_Layout", "/Game/Sewer/Levels/L_Sewers_Corridor"),
    ("Sewer_Pier_Layout", "/Game/Sewer/Levels/L_Sewers_Pier"),
    ("Shipwreck_Exterior_Layout", "/Game/UnderwaterShip/Levels/UnderwaterShip_Showcase_Exterior"),
]
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
report = {"captures": [], "errors": []}
state = {"index": -1, "phase": "next", "deadline": time.monotonic() + 8,
         "timeout": 0.0, "busy": False, "world": None, "camera": None}


def finish():
    (OUT / "Capture_Report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.unregister_slate_post_tick_callback(handle)
    unreal.SystemLibrary.quit_editor()


def bounds_for(actors):
    bounds = []
    for actor in actors:
        try:
            center, extent = actor.get_actor_bounds(False, True)
            c, e = center.to_tuple(), extent.to_tuple()
            if max(e) > 0 and max(e) < 50000 and abs(c[2]) < 50000:
                bounds.append((c, e))
        except Exception:
            pass
    if not bounds:
        return (0.0, 0.0, 0.0), (2000.0, 2000.0, 1000.0)
    lo = tuple(min(c[i] - e[i] for c, e in bounds) for i in range(3))
    hi = tuple(max(c[i] + e[i] for c, e in bounds) for i in range(3))
    center = tuple((lo[i] + hi[i]) / 2.0 for i in range(3))
    extent = tuple((hi[i] - lo[i]) / 2.0 for i in range(3))
    return center, extent


def rotation_to(source, target):
    return unreal.MathLibrary.find_look_at_rotation(source, target)


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
                report["captures"].append({"name": name, "map": CASES[state["index"]][1],
                                           "image": str(path), "bytes": path.stat().st_size})
                (OUT / "Capture_Report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
                state.update(phase="next", deadline=time.monotonic() + 8)
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
                state["world"],
                'HighResShot 1440x900 filename="' + str(path).replace("\\", "/") + '"')
            state.update(phase="wait_image", timeout=time.monotonic() + 90,
                         deadline=time.monotonic() + 1)
            return

        state["index"] += 1
        if state["index"] >= len(CASES):
            finish()
            return
        name, map_path = CASES[state["index"]]
        world = unreal.EditorLoadingAndSavingUtils.load_map(map_path)
        if not world:
            raise RuntimeError("Could not load " + map_path)
        state["world"] = world
        actors = list(eas.get_all_level_actors())
        center, extent = bounds_for(actors)
        if state["camera"]:
            try:
                eas.destroy_actor(state["camera"])
            except Exception:
                pass
            state["camera"] = None
        camera_position = (center[0] + max(2500, extent[0] * 1.35),
                           center[1] - max(3500, extent[1] * 2.1),
                           center[2] + max(2500, extent[2] * 1.55))
        camera = eas.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*camera_position))
        position = camera.get_actor_location().to_tuple()
        rotation = rotation_to(position, center)
        camera_source = "generated_bounds_view"
        camera.camera_component.set_editor_property("field_of_view", 72.0)
        camera.set_actor_location(unreal.Vector(*position), False, True)
        camera.set_actor_rotation(rotation, False)
        state["camera"] = camera
        editor.set_level_viewport_camera_info(camera.get_actor_location(), camera.get_actor_rotation())
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_set_game_view(True)
        report.setdefault("view_setup", []).append({"map": map_path, "actors": len(actors),
                                                     "bounds_center_cm": center,
                                                     "bounds_extent_cm": extent,
                                                     "camera_source": camera_source,
                                                     "camera_location_cm": position})
        state.update(phase="capture", deadline=time.monotonic() + 5)
    except Exception:
        report["errors"].append(traceback.format_exc())
        finish()
    finally:
        state["busy"] = False


handle = unreal.register_slate_post_tick_callback(tick)
