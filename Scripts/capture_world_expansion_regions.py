"""Capture current project-owned expansion region maps for visual review."""
import json
import math
import time
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/WorldExpansion/Evidence/Regions"
OUT.mkdir(parents=True, exist_ok=True)
LIGHTING = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/Lv_LightingNight"
CASES = [
    ("01_Docks_North", "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_DocksNorth_Layout"),
    ("02_Prison", "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Prison"),
    ("03_Research_Lab_A", "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_LabA"),
    ("04_Research_Lab_B", "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_LabB"),
    ("05_Docks_East", "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_DocksEast"),
    ("06_Sewers", "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Sewers"),
    ("07_Atlantis", "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Atlantis"),
    ("08_Shipwreck", "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Shipwreck"),
]
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
report = {"captures": [], "errors": []}
state = {"index": -1, "phase": "next", "deadline": time.monotonic() + 5,
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
    return tuple((lo[i] + hi[i]) / 2 for i in range(3)), tuple((hi[i] - lo[i]) / 2 for i in range(3))


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
                state.update(phase="next", deadline=time.monotonic() + 5)
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
        camera_pos = (center[0] + max(1600, extent[0] * 1.25),
                      center[1] - max(2600, extent[1] * 1.9),
                      center[2] + max(1700, extent[2] * 1.45))
        camera = eas.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*camera_pos))
        camera.camera_component.set_editor_property("field_of_view", 74.0)
        rotation = unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*camera_pos), unreal.Vector(*center))
        camera.set_actor_rotation(rotation, False)
        state["camera"] = camera
        # Reuse the Carnival's actual night-lighting sublevel in memory only.
        # It is not saved into this standalone region map.
        lighting_transform = unreal.Transform()
        lighting_transform.set_editor_property("translation", unreal.Vector(0, 0, 0))
        lighting_transform.set_editor_property("rotation", unreal.Rotator().quaternion())
        lighting_transform.set_editor_property("scale3d", unreal.Vector(1, 1, 1))
        light_stream = unreal.EditorLevelUtils.add_level_to_world_with_transform(
            world, LIGHTING, unreal.LevelStreamingAlwaysLoaded, lighting_transform)
        if not light_stream:
            raise RuntimeError("Could not load the Carnival night-lighting sublevel")
        light_stream.set_editor_property("should_be_loaded", True)
        light_stream.set_editor_property("should_be_visible", True)
        editor.set_level_viewport_camera_info(camera.get_actor_location(), camera.get_actor_rotation())
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_set_game_view(True)
        report.setdefault("view_setup", []).append({"map": map_path, "actors": len(actors),
                                                     "bounds_center_cm": center, "bounds_extent_cm": extent,
                                                     "camera_location_cm": camera_pos,
                                                     "lighting_context": LIGHTING})
        state.update(phase="capture", deadline=time.monotonic() + 5)
    except Exception:
        report["errors"].append(traceback.format_exc())
        finish()
    finally:
        state["busy"] = False


handle = unreal.register_slate_post_tick_callback(tick)
