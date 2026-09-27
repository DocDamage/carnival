"""Capture connected Carnival route views without saving or changing the map."""
import json
import math
import time
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/IndustrialHospital/Previews/Connected"
OUT.mkdir(parents=True, exist_ok=True)
import sys
sys.path.insert(0, str(ROOT / "Scripts"))
from industrial_hospital_route_config import (
    GATE, HOSPITAL_YAW, MAIN_MAP, ROAD_CONTROL_POINTS, ROUTE_WORLD_YAW,
    hospital_level_transform, world_point,
)

def rotate_xy(x, y, yaw):
    angle = math.radians(yaw)
    return (x * math.cos(angle) - y * math.sin(angle),
            x * math.sin(angle) + y * math.cos(angle))

def hospital_world(local):
    origin = hospital_level_transform()
    x, y = rotate_xy(local[0], local[1], HOSPITAL_YAW)
    return (origin[0] + x, origin[1] + y, origin[2] + local[2])

CASES = [
    ("01_Carnival_Exit",
     world_point((-1800.0, 0.0, 750.0)), world_point((5000.0, 0.0, 300.0))),
    ("02_Industrial_Slums",
     world_point((65500.0, -3000.0, 1500.0)), world_point((68500.0, 0.0, 300.0))),
    ("03_Hospital_Approach",
     world_point((147500.0, -5000.0, 1900.0)), world_point((151000.0, 0.0, 600.0))),
    ("04_Hospital_Entrance_Interior",
     hospital_world((3900.0, -1750.0, 210.0)), hospital_world((6200.0, -1750.0, 210.0))),
]

report = {"map": MAIN_MAP, "images": [], "cases": [], "errors": []}
editor_actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
state = {"phase": "load", "index": 0, "deadline": time.monotonic() + 18,
         "timeout": 0.0, "busy": False, "world": None, "camera": None}

def finish():
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
        if state["phase"] == "load":
            world = unreal.EditorLoadingAndSavingUtils.load_map(MAIN_MAP)
            if not world:
                raise RuntimeError("Could not load the connected Carnival map")
            state["world"] = world
            unreal.SystemLibrary.execute_console_command(world, "r.RDG.ParallelExecute 0")
            unreal.SystemLibrary.execute_console_command(world, "r.ScreenPercentage 100")
            state["camera"] = editor_actors.spawn_actor_from_class(
                unreal.CameraActor, unreal.Vector(0.0, 0.0, 10000.0))
            state["camera"].camera_component.set_editor_property("field_of_view", 72.0)
            levels = [level.get_path_name() for level in unreal.EditorLevelUtils.get_levels(world)]
            report["loaded_levels"] = levels
            expected = ["L_IndustrialHospitalRoute", "L_IndustrialSlums_DistrictFinal",
                        "L_IndustrialHospitalExterior", "L_IndustrialHospitalInteriorArchitecture",
                        "L_IndustrialHospitalInteriorLights"]
            report["expected_level_presence"] = {
                item: any(item in path for path in levels) for item in expected
            }
            # Match the project's winter-night gameplay lighting for this
            # unsaved preview session. This does not save changes to LV_Carnival.
            report["preview_lighting"] = {}
            for level in unreal.EditorLevelUtils.get_levels(world):
                path = level.get_path_name().split(":PersistentLevel")[0].split(".")[0]
                name = path.rsplit("/", 1)[-1]
                if name in ("Lv_LightingDay", "Lv_LightingNight", "Lv_LightingNightSnow"):
                    visible = name == "Lv_LightingNightSnow"
                    unreal.EditorLevelUtils.set_level_visibility(level, visible, True)
                    report["preview_lighting"][name] = visible
            # Record the streamed actor bounds after the lighting-level
            # selection has had a few frames to settle.
            state.update(phase="audit", deadline=time.monotonic() + 8)
        elif state["phase"] == "audit":
            level_report = []
            for level in unreal.EditorLevelUtils.get_levels(state["world"]):
                path = level.get_path_name()
                if not any(item in path for item in ("IndustrialHospital", "IndustrialSlums", "Hospital_Meshingun")):
                    continue
                level_actors = [a for a in editor_actors.get_all_level_actors()
                                if a and a.get_level().get_path_name() == path]
                notable = []
                bounds = []
                for actor in level_actors:
                    label = actor.get_actor_label()
                    location = actor.get_actor_location().to_tuple()
                    if any(word in label.lower() for word in ("road", "fog", "snow", "facade", "door", "sodium")):
                        notable.append({"label": label, "location": location,
                                        "class": actor.get_class().get_name()})
                    try:
                        origin, extent = actor.get_actor_bounds(False, True)
                        if max(extent.to_tuple()) > 0.0:
                            bounds.append((origin.to_tuple(), extent.to_tuple()))
                    except Exception:
                        pass
                item = {"level": path, "actor_count": len(level_actors), "notable_actors": notable[:80]}
                if bounds:
                    item["world_bounds"] = {
                        "min": [min(c[i] - e[i] for c, e in bounds) for i in range(3)],
                        "max": [max(c[i] + e[i] for c, e in bounds) for i in range(3)],
                    }
                level_report.append(item)
            report["connected_level_audit"] = level_report
            state.update(phase="position", deadline=time.monotonic() + 4)
        elif state["phase"] == "position":
            if state["index"] >= len(CASES):
                finish()
                return
            name, position, target = CASES[state["index"]]
            camera = state["camera"]
            camera.set_actor_location(unreal.Vector(*position), False, True)
            camera.set_actor_rotation(
                unreal.MathLibrary.find_look_at_rotation(position, target), False)
            editor.set_level_viewport_camera_info(camera.get_actor_location(), camera.get_actor_rotation())
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_set_game_view(True)
            report["cases"].append({"name": name, "camera": position, "target": target})
            state.update(phase="capture", deadline=time.monotonic() + 7)
        elif state["phase"] == "capture":
            name = CASES[state["index"]][0]
            path = OUT / (name + ".png")
            if path.exists():
                path.unlink()
            unreal.SystemLibrary.execute_console_command(
                state["world"], 'HighResShot 1600x1000 filename="' + str(path).replace("\\", "/") + '"')
            state.update(phase="wait", timeout=time.monotonic() + 120, deadline=time.monotonic() + 0.5)
        elif state["phase"] == "wait":
            path = OUT / (CASES[state["index"]][0] + ".png")
            if path.exists():
                report["images"].append(str(path))
                state["index"] += 1
                state.update(phase="position", deadline=time.monotonic() + 4)
            elif time.monotonic() > state["timeout"]:
                raise TimeoutError("Screenshot was not created: " + str(path))
    except Exception:
        report["errors"].append(traceback.format_exc())
        finish()
    finally:
        state["busy"] = False

handle = unreal.register_slate_post_tick_callback(tick)
