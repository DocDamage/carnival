"""Temporary editor-only A/B views to identify weather washout sources."""
import json
import time
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/IndustrialHospital/Previews/WeatherIsolation"
OUT.mkdir(parents=True, exist_ok=True)
import sys
sys.path.insert(0, str(ROOT / "Scripts"))
from industrial_hospital_route_config import MAIN_MAP, world_point

REPORT = {"map": MAIN_MAP, "captures": [], "hidden_emitters": 0, "hidden_fog_volumes": 0}
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EDITOR = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
STATE = {"phase": "load", "deadline": time.monotonic() + 20,
         "timeout": 0.0, "world": None, "camera": None, "busy": False}
POSITION = world_point((65500.0, -3000.0, 1500.0))
TARGET = world_point((68500.0, 0.0, 300.0))

def finish():
    (OUT / "Report.json").write_text(json.dumps(REPORT, indent=2), encoding="utf-8")
    unreal.unregister_slate_post_tick_callback(HANDLE)
    unreal.SystemLibrary.quit_editor()

def capture(index, name):
    path = OUT / (name + ".png")
    if path.exists():
        path.unlink()
    unreal.SystemLibrary.execute_console_command(
        STATE["world"], 'HighResShot 1600x1000 filename="' + str(path).replace("\\", "/") + '"')
    STATE.update(phase="wait", timeout=time.monotonic() + 90,
                 deadline=time.monotonic() + 0.5, index=index, name=name)

def tick(delta):
    if STATE["busy"]:
        return
    STATE["busy"] = True
    try:
        if time.monotonic() < STATE["deadline"]:
            return
        if STATE["phase"] == "load":
            world = unreal.EditorLoadingAndSavingUtils.load_map(MAIN_MAP)
            if not world:
                raise RuntimeError("Could not load connected Carnival map")
            STATE["world"] = world
            unreal.SystemLibrary.execute_console_command(world, "r.RDG.ParallelExecute 0")
            for level in unreal.EditorLevelUtils.get_levels(world):
                name = level.get_path_name().split(":PersistentLevel")[0].split(".")[0].rsplit("/", 1)[-1]
                if name in ("Lv_LightingDay", "Lv_LightingNight", "Lv_LightingNightSnow"):
                    unreal.EditorLevelUtils.set_level_visibility(level, name == "Lv_LightingNightSnow", True)
            camera = ACTORS.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(0.0, 0.0, 10000.0))
            camera.camera_component.set_editor_property("field_of_view", 72.0)
            camera.set_actor_location(unreal.Vector(*POSITION), False, True)
            camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(POSITION, TARGET), False)
            EDITOR.set_level_viewport_camera_info(camera.get_actor_location(), camera.get_actor_rotation())
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_set_game_view(True)
            STATE["camera"] = camera
            STATE.update(phase="emitters", deadline=time.monotonic() + 6)
        elif STATE["phase"] == "emitters":
            for actor in ACTORS.get_all_level_actors():
                if not actor or "L_IndustrialHospitalRoute" not in actor.get_level().get_path_name():
                    continue
                if actor.get_class().get_name() == "Emitter":
                    component = actor.get_editor_property("particle_system_component")
                    component.set_editor_property("auto_activate", False)
                    try:
                        component.deactivate_system()
                    except Exception:
                        pass
                    component.set_visibility(False)
                    REPORT["hidden_emitters"] += 1
            capture(0, "Slums_Emitters_Off_Fog_On")
        elif STATE["phase"] == "wait":
            path = OUT / (STATE["name"] + ".png")
            if path.exists():
                REPORT["captures"].append(str(path))
                STATE.update(phase="fog", deadline=time.monotonic() + 3)
            elif time.monotonic() > STATE["timeout"]:
                raise TimeoutError("Screenshot was not created: " + str(path))
        elif STATE["phase"] == "fog":
            for actor in ACTORS.get_all_level_actors():
                if not actor or "L_IndustrialHospitalRoute" not in actor.get_level().get_path_name():
                    continue
                if actor.get_class().get_name() == "LocalFogVolume":
                    actor.get_editor_property("local_fog_volume_volume").set_visibility(False)
                    REPORT["hidden_fog_volumes"] += 1
            capture(1, "Slums_All_Local_Weather_Off")
        elif STATE["phase"] == "done":
            finish()
    except Exception:
        REPORT["error"] = traceback.format_exc()
        finish()
    finally:
        STATE["busy"] = False

_old_capture = capture
def capture(index, name):
    _old_capture(index, name)
    STATE["phase_after_wait"] = "fog" if index == 0 else "done"

_old_tick = tick
def tick(delta):
    _old_tick(delta)
    if STATE.get("phase") == "wait" and (OUT / (STATE.get("name", "") + ".png")).exists():
        STATE["phase"] = STATE.pop("phase_after_wait", "done")
        STATE["deadline"] = time.monotonic() + 3

HANDLE = unreal.register_slate_post_tick_callback(tick)
